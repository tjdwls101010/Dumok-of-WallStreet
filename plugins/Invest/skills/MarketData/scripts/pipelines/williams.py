#!/usr/bin/env python3
"""Williams Pipeline: full short-term volatility breakout analysis integrating
Williams %R, volatility breakout levels, range analysis, swing points, pattern
scanning, TDW/TDM calendar bias, bond inter-market filter, and composite trade
qualification scoring.

Orchestrates the complete Williams short-term trading analysis by running pattern
detection, volatility breakout calculation, range analysis, swing point identification,
Williams %R momentum, TDW/TDM calendar bias, and bond inter-market filter in parallel.
Produces a conviction score (0-100) with position sizing.

Commands:
	trade-setup: Primary composite trade qualification for a single ticker
	analyze: Full Williams analysis for a single ticker (all indicators)
	pattern-scan: Multi-ticker Williams pattern scanning
	market-context: Market environment: bond trend, TDW/TDM, COT positioning
	watchlist: Batch trade-setup for multiple tickers
	dashboard: Quick overview: today's bias + bond filter status

Args:
	For trade-setup:
		symbol (str): Ticker symbol (e.g., "AAPL", "SPY")
		--risk-pct (float): Risk percentage per trade (default: 3.0)
		--account-size (float): Account size for position sizing (default: 100000)

	For analyze:
		symbol (str): Ticker symbol (e.g., "AAPL", "SPY")

	For pattern-scan:
		symbols (list): Ticker symbols to scan (e.g., "AAPL MSFT NVDA")
		--lookback (int): Pattern scan window in days (default: 5)

	For market-context:
		(no arguments)

	For watchlist:
		symbols (list): Ticker symbols (e.g., "AAPL MSFT NVDA AMZN")
		--risk-pct (float): Risk percentage per trade (default: 3.0)
		--account-size (float): Account size (default: 100000)

	For dashboard:
		(no arguments)

Returns:
	For trade-setup:
		dict: {
			"symbol": str,
			"conviction_score": float,
			"signal": str,
			"signal_reason_codes": [str],
			"hard_gates": {
				"bond_contradiction": bool,
				"no_pattern": bool,
				"signal_capped": bool
			},
			"components": {
				"pattern_signal": {"score": float, "max": 25, "detail": str},
				"bond_intermarket": {"score": float, "max": 20, "detail": str},
				"tdw_alignment": {"score": float, "max": 15, "detail": str},
				"tdm_alignment": {"score": float, "max": 15, "detail": str},
				"ma_trend": {"score": float, "max": 15, "detail": str},
				"williams_r": {"score": float, "max": 10, "detail": str}
			},
			"volatility_breakout": dict,
			"range_analysis": dict,
			"swing_points": dict,
			"position_sizing": dict,
			"missing_components": [str],
			"recommendation_text": str
		}

	For analyze:
		dict: {
			"symbol": str,
			"trade_setup": dict,
			"williams_r": dict,
			"volatility_breakout": dict,
			"range_analysis": dict,
			"swing_points_short": dict,
			"swing_points_intermediate": dict,
			"pattern_scan": dict,
			"trend_ma": dict,
			"tdw_tdm": dict,
			"missing_components": [str]
		}

	For pattern-scan:
		dict: {
			"results": [{
				"symbol": str,
				"patterns_detected": list,
				"pattern_count": int
			}],
			"total_patterns": int,
			"symbols_scanned": int
		}

	For market-context:
		dict: {
			"tdw_tdm": dict,
			"bond_status": {
				"tlt_price": float,
				"tlt_trend": str,
				"bond_stock_signal": str
			},
			"cot_summary": dict or null,
			"market_bias": str,
			"missing_components": [str]
		}

	For watchlist:
		dict: {
			"results": [{
				"symbol": str,
				"conviction_score": float,
				"signal": str,
				"pattern_count": int,
				"hard_gates_triggered": bool
			}],
			"ranked_by": "conviction_score",
			"count": int
		}

	For dashboard:
		dict: {
			"date": str,
			"tdw_tdm": dict,
			"bond_filter": dict,
			"overall_bias": str
		}

Example:
	>>> python pipelines/williams.py trade-setup AAPL --risk-pct 3 --account-size 100000
	{
		"symbol": "AAPL",
		"conviction_score": 75.0,
		"signal": "BUY",
		"components": {...},
		"position_sizing": {"contracts": 150, "dollar_risk": 3000},
		"recommendation_text": "AAPL: Conviction 75/100 — BUY | Smash day pattern + bonds bullish"
	}

	>>> python pipelines/williams.py market-context
	{
		"tdw_tdm": {"combined_bias": "slightly_bullish"},
		"bond_status": {"tlt_trend": "bullish", "bond_stock_signal": "favorable"},
		"market_bias": "moderately_bullish"
	}

	>>> python pipelines/williams.py pattern-scan AAPL MSFT NVDA GOOGL
	{
		"results": [
			{"symbol": "AAPL", "pattern_count": 1, "patterns_detected": [...]},
			{"symbol": "NVDA", "pattern_count": 0, "patterns_detected": []}
		],
		"total_patterns": 1,
		"symbols_scanned": 4
	}

Use Cases:
	- Complete short-term trade qualification using Williams' methodology
	- Batch pattern scanning across a watchlist
	- Daily market environment check (bond trend + calendar bias)
	- Quick dashboard for morning trading preparation
	- Multi-factor conviction scoring for position sizing decisions

Notes:
	- Conviction score weights: Pattern 25, Bond 20, TDW 15, TDM 15, MA 15, %R 10
	- Signals: STRONG_BUY 80+, BUY 60-79, HOLD 40-59, MONITOR 20-39, AVOID <20
	- Hard gates: bond contradiction (bearish bonds + stock buy) → HOLD cap, no pattern → HOLD cap
	- Bond data uses TLT ETF as Treasury Bond proxy
	- COT data from CFTC (weekly update, may be 3-7 days stale)
	- Pipeline continues even if individual components fail (graceful degradation)
	- Scripts execute in parallel via ThreadPoolExecutor for performance
	- Each script runs in independent subprocess (no shared state)
	- Watchlist mode remains sequential per-ticker

See Also:
	- technical/williams.py: Williams-specific indicators and patterns
	- data_sources/price.py: Historical OHLCV data
	- technical/trend.py: SMA/EMA trend indicators
	- data_advanced/cftc/cftc.py: COT positioning data
"""

import argparse
import concurrent.futures
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from utils import output_json, safe_run

SCRIPTS_DIR = os.path.dirname(os.path.dirname(__file__))


def _run_script(script_path, args_list):
	"""Run a script and capture its JSON output."""
	full_path = os.path.join(SCRIPTS_DIR, script_path)
	cmd = [sys.executable, full_path] + args_list

	try:
		result = subprocess.run(
			cmd,
			capture_output=True,
			text=True,
			timeout=60,
			cwd=SCRIPTS_DIR,
		)
		if result.returncode == 0 and result.stdout.strip():
			return json.loads(result.stdout)
		else:
			return {"error": result.stderr.strip() or "Script returned no output"}
	except subprocess.TimeoutExpired:
		return {"error": "Script timed out (60s)"}
	except json.JSONDecodeError:
		return {"error": "Invalid JSON output from script"}
	except Exception as e:
		return {"error": str(e)}


# ---------------------------------------------------------------------------
# Signal and scoring helpers
# ---------------------------------------------------------------------------

def _determine_signal(conviction):
	"""Map conviction score to signal level."""
	if conviction >= 80:
		return "STRONG_BUY"
	elif conviction >= 60:
		return "BUY"
	elif conviction >= 40:
		return "HOLD"
	elif conviction >= 20:
		return "MONITOR"
	return "AVOID"


def _build_signal_reason_codes(signal, components, hard_gates, missing):
	"""Build human-readable signal reason codes."""
	codes = []

	# Hard gate codes
	if hard_gates.get("bond_contradiction"):
		codes.append("BOND_CONTRADICTION_CAP")
	if hard_gates.get("no_pattern"):
		codes.append("NO_PATTERN_CAP")

	# Component strength codes
	pattern = components.get("pattern_signal", {})
	if pattern.get("score", 0) >= 20:
		codes.append("STRONG_PATTERN")
	elif pattern.get("score", 0) >= 10:
		codes.append("PATTERN_PRESENT")

	bond = components.get("bond_intermarket", {})
	if bond.get("score", 0) >= 18:
		codes.append("BONDS_BULLISH")
	elif bond.get("score", 0) <= 5:
		codes.append("BONDS_BEARISH")

	tdw = components.get("tdw_alignment", {})
	if tdw.get("score", 0) >= 12:
		codes.append("TDW_FAVORABLE")

	tdm = components.get("tdm_alignment", {})
	if tdm.get("score", 0) >= 12:
		codes.append("TDM_FAVORABLE")

	ma = components.get("ma_trend", {})
	if ma.get("score", 0) >= 12:
		codes.append("MA_UPTREND")
	elif ma.get("score", 0) <= 3:
		codes.append("MA_DOWNTREND")

	wr = components.get("williams_r", {})
	if wr.get("score", 0) >= 8:
		codes.append("WR_OVERSOLD_OPPORTUNITY")
	elif wr.get("score", 0) <= 2:
		codes.append("WR_OVERBOUGHT_CAUTION")

	if missing:
		codes.append(f"MISSING_{len(missing)}_COMPONENTS")

	return codes


def _generate_recommendation(symbol, signal, conviction, components, hard_gates, patterns_info):
	"""Generate one-line recommendation text."""
	parts = [f"{symbol}: Conviction {conviction}/100 — {signal}"]

	# Key drivers
	drivers = []
	if components.get("pattern_signal", {}).get("score", 0) >= 15:
		detail = components["pattern_signal"].get("detail", "")
		drivers.append(detail)
	if components.get("bond_intermarket", {}).get("score", 0) >= 15:
		drivers.append("bonds favorable")
	if components.get("tdw_alignment", {}).get("score", 0) >= 12:
		drivers.append("TDW bullish")
	if components.get("tdm_alignment", {}).get("score", 0) >= 12:
		drivers.append("TDM bullish")

	if drivers:
		parts.append(" | " + " + ".join(drivers[:3]))

	# Warnings
	if hard_gates.get("bond_contradiction"):
		parts.append(" [BOND CONTRADICTION — signal capped]")
	if hard_gates.get("no_pattern"):
		parts.append(" [NO PATTERN — signal capped]")

	return "".join(parts)


# ---------------------------------------------------------------------------
# Compress helpers (response compression)
# ---------------------------------------------------------------------------

def _compress_trade_setup(raw):
	"""Compress trade-setup output, keeping scores and evidence."""
	if raw.get("error"):
		return raw
	return {
		"symbol": raw.get("symbol"),
		"conviction_score": raw.get("conviction_score"),
		"signal": raw.get("signal"),
		"components": raw.get("components"),
		"hard_gates": raw.get("hard_gates"),
		"position_sizing": raw.get("position_sizing"),
		"missing_components": raw.get("missing_components", []),
	}


def _compress_williams_r(raw):
	"""Keep current value, signal, and basic stats."""
	if raw.get("error"):
		return raw
	return {
		"symbol": raw.get("symbol"),
		"current_wr": raw.get("current_wr"),
		"signal": raw.get("signal"),
		"period": raw.get("period"),
		"statistics": raw.get("statistics"),
	}


def _compress_volatility_breakout(raw):
	"""Keep levels and trigger status."""
	if raw.get("error"):
		return raw
	return {
		"symbol": raw.get("symbol"),
		"date": raw.get("date"),
		"open": raw.get("open"),
		"atr_3day": raw.get("atr_3day"),
		"classic_buy_level": raw.get("classic_buy_level"),
		"classic_sell_level": raw.get("classic_sell_level"),
		"electronic_buy_level": raw.get("electronic_buy_level"),
		"electronic_sell_level": raw.get("electronic_sell_level"),
		"yesterday_close_direction": raw.get("yesterday_close_direction"),
		"active_signal": raw.get("active_signal"),
		"current_price": raw.get("current_price"),
		"breakout_triggered": raw.get("breakout_triggered"),
	}


def _compress_range_analysis(raw):
	"""Keep phase and axiom signal, limit history."""
	if raw.get("error"):
		return raw
	return {
		"symbol": raw.get("symbol"),
		"current_range_pct": raw.get("current_range_pct"),
		"avg_range_pct": raw.get("avg_range_pct"),
		"range_ratio": raw.get("range_ratio"),
		"phase": raw.get("phase"),
		"consecutive_small_ranges": raw.get("consecutive_small_ranges"),
		"axiom_signal": raw.get("axiom_signal"),
	}


def _compress_swing_points(raw):
	"""Keep trend and last swing points only."""
	if raw.get("error"):
		return raw
	return {
		"symbol": raw.get("symbol"),
		"level": raw.get("level"),
		"current_trend": raw.get("current_trend"),
		"last_swing_high": raw.get("last_swing_high"),
		"last_swing_low": raw.get("last_swing_low"),
		"projected_target": raw.get("projected_target"),
		"current_price": raw.get("current_price"),
	}


def _compress_trend(raw):
	"""Keep SMA values and distances."""
	if raw.get("error"):
		return raw
	return {
		"symbol": raw.get("symbol"),
		"current_price": raw.get("current_price"),
		"sma": raw.get("sma"),
	}


# ---------------------------------------------------------------------------
# Bond status helper
# ---------------------------------------------------------------------------

def _get_bond_status():
	"""Fetch TLT status for bond inter-market filter."""
	try:
		price_data = _run_script("data_sources/price.py", ["history", "TLT", "--period", "3mo"])
		if price_data.get("error"):
			return {"error": "TLT data unavailable"}

		# price.py returns column-oriented: {"Close": {"date": value, ...}, "Open": {...}}
		close_col = price_data.get("Close", {})
		if not close_col or not isinstance(close_col, dict):
			return {"error": "Unexpected TLT data format"}

		closes = []
		for date_str in sorted(close_col.keys()):
			val = close_col[date_str]
			if val is not None:
				closes.append(float(val))

		if len(closes) < 14:
			return {"error": "Insufficient TLT data"}

		current = closes[-1]
		# 14-day channel
		high_14 = max(closes[-14:])
		low_14 = min(closes[-14:])
		# 20-day SMA
		sma_20 = sum(closes[-20:]) / min(20, len(closes[-20:])) if len(closes) >= 5 else current

		if current >= high_14:
			trend = "bullish"
			signal = "bonds_breaking_up_favorable_stocks"
		elif current <= low_14:
			trend = "bearish"
			signal = "bonds_breaking_down_unfavorable_stocks"
		elif current > sma_20:
			trend = "mildly_bullish"
			signal = "bonds_above_20ma_neutral_positive"
		else:
			trend = "mildly_bearish"
			signal = "bonds_below_20ma_neutral_negative"

		return {
			"tlt_price": round(current, 2),
			"tlt_14d_high": round(high_14, 2),
			"tlt_14d_low": round(low_14, 2),
			"tlt_sma_20": round(sma_20, 2),
			"tlt_trend": trend,
			"bond_stock_signal": signal,
		}
	except Exception as e:
		return {"error": str(e)}


# ---------------------------------------------------------------------------
# Command: trade-setup
# ---------------------------------------------------------------------------

@safe_run
def cmd_trade_setup(args):
	"""Primary composite trade qualification for a single ticker."""
	symbol = args.symbol.upper()
	missing_components = []

	# Run williams trade-setup + supplementary scripts in parallel
	scripts = {
		"trade_setup": ("technical/williams.py", [
			"trade-setup", symbol,
			"--risk-pct", str(args.risk_pct),
			"--account-size", str(args.account_size),
		]),
		"volatility_breakout": ("technical/williams.py", ["volatility-breakout", symbol]),
		"range_analysis": ("technical/williams.py", ["range-analysis", symbol]),
		"swing_points": ("technical/williams.py", ["swing-points", symbol, "--level", "intermediate"]),
		"trend_ma": ("technical/trend.py", ["sma", symbol, "--periods", "20,50,200"]),
	}

	with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
		futures = {name: executor.submit(_run_script, path, a) for name, (path, a) in scripts.items()}
		results = {name: future.result() for name, future in futures.items()}

	ts = results["trade_setup"]
	vb = results["volatility_breakout"]
	ra = results["range_analysis"]
	sp = results["swing_points"]
	trend = results["trend_ma"]

	# Track missing components
	for name, data in results.items():
		if data.get("error"):
			missing_components.append(name)

	# Extract core fields from trade-setup result
	if not ts.get("error"):
		conviction = ts.get("conviction_score", 0)
		signal = ts.get("signal", "AVOID")
		components = ts.get("components", {})
		hard_gates = ts.get("hard_gates", {})
		pos_sizing = ts.get("position_sizing", {})
		ts_missing = ts.get("missing_components", [])
		missing_components.extend(ts_missing)
	else:
		# Fallback: cannot determine conviction
		conviction = 0
		signal = "AVOID"
		components = {}
		hard_gates = {"bond_contradiction": False, "no_pattern": True, "signal_capped": True}
		pos_sizing = {}
		missing_components.append("trade_setup_core")

	# Build signal reason codes
	reason_codes = _build_signal_reason_codes(signal, components, hard_gates, missing_components)

	# Generate recommendation
	recommendation = _generate_recommendation(
		symbol, signal, conviction, components, hard_gates,
		ts.get("components", {}).get("pattern_signal", {}).get("detail", "")
	)

	output_json({
		"symbol": symbol,
		"conviction_score": conviction,
		"signal": signal,
		"signal_reason_codes": reason_codes,
		"hard_gates": hard_gates,
		"components": components,
		"volatility_breakout": _compress_volatility_breakout(vb),
		"range_analysis": _compress_range_analysis(ra),
		"swing_points": _compress_swing_points(sp),
		"trend_ma": _compress_trend(trend),
		"position_sizing": pos_sizing,
		"missing_components": list(set(missing_components)),
		"recommendation_text": recommendation,
	})


# ---------------------------------------------------------------------------
# Command: analyze
# ---------------------------------------------------------------------------

@safe_run
def cmd_analyze(args):
	"""Full Williams analysis for a single ticker — all indicators."""
	symbol = args.symbol.upper()
	missing_components = []

	scripts = {
		"trade_setup": ("technical/williams.py", ["trade-setup", symbol]),
		"williams_r": ("technical/williams.py", ["williams-r", symbol, "--period", "14"]),
		"volatility_breakout": ("technical/williams.py", ["volatility-breakout", symbol]),
		"range_analysis": ("technical/williams.py", ["range-analysis", symbol]),
		"swing_short": ("technical/williams.py", ["swing-points", symbol, "--level", "short"]),
		"swing_intermediate": ("technical/williams.py", ["swing-points", symbol, "--level", "intermediate"]),
		"pattern_scan": ("technical/williams.py", ["pattern-scan", symbol, "--lookback", "10"]),
		"trend_ma": ("technical/trend.py", ["sma", symbol, "--periods", "20,50,200"]),
		"tdw_tdm": ("technical/williams.py", ["tdw-tdm"]),
	}

	with concurrent.futures.ThreadPoolExecutor(max_workers=9) as executor:
		futures = {name: executor.submit(_run_script, path, a) for name, (path, a) in scripts.items()}
		results = {name: future.result() for name, future in futures.items()}

	for name, data in results.items():
		if data.get("error"):
			missing_components.append(name)

	output_json({
		"symbol": symbol,
		"trade_setup": _compress_trade_setup(results["trade_setup"]),
		"williams_r": _compress_williams_r(results["williams_r"]),
		"volatility_breakout": _compress_volatility_breakout(results["volatility_breakout"]),
		"range_analysis": _compress_range_analysis(results["range_analysis"]),
		"swing_points_short": _compress_swing_points(results["swing_short"]),
		"swing_points_intermediate": _compress_swing_points(results["swing_intermediate"]),
		"pattern_scan": results["pattern_scan"],
		"trend_ma": _compress_trend(results["trend_ma"]),
		"tdw_tdm": results["tdw_tdm"],
		"missing_components": missing_components,
	})


# ---------------------------------------------------------------------------
# Command: pattern-scan (multi-ticker)
# ---------------------------------------------------------------------------

@safe_run
def cmd_pattern_scan(args):
	"""Multi-ticker Williams pattern scanning."""
	symbols = [s.upper() for s in args.symbols]

	results = []
	total_patterns = 0

	for sym in symbols:
		data = _run_script("technical/williams.py", ["pattern-scan", sym, "--lookback", str(args.lookback)])
		if not data.get("error"):
			count = data.get("pattern_count", 0)
			total_patterns += count
			results.append({
				"symbol": sym,
				"patterns_detected": data.get("patterns_detected", []),
				"pattern_count": count,
			})
		else:
			results.append({
				"symbol": sym,
				"error": data.get("error"),
				"patterns_detected": [],
				"pattern_count": 0,
			})

	# Sort by pattern count descending
	results.sort(key=lambda x: x.get("pattern_count", 0), reverse=True)

	output_json({
		"results": results,
		"total_patterns": total_patterns,
		"symbols_scanned": len(symbols),
		"lookback_days": args.lookback,
	})


# ---------------------------------------------------------------------------
# Command: market-context
# ---------------------------------------------------------------------------

@safe_run
def cmd_market_context(args):
	"""Market environment: bond trend, TDW/TDM, COT positioning."""
	missing_components = []

	# Parallel: TDW/TDM + Bond + COT
	with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
		tdw_future = executor.submit(_run_script, "technical/williams.py", ["tdw-tdm"])
		bond_future = executor.submit(_get_bond_status)
		cot_future = executor.submit(
			_run_script,
			"data_advanced/cftc/cftc.py",
			["cot", "ES", "--limit", "4"],
		)

		tdw_tdm = tdw_future.result()
		bond_status = bond_future.result()
		cot_data = cot_future.result()

	if tdw_tdm.get("error"):
		missing_components.append("tdw_tdm")
	if bond_status.get("error"):
		missing_components.append("bond_status")

	# Process COT data
	cot_summary = None
	if not cot_data.get("error"):
		cot_records = cot_data.get("data", [])
		if cot_records:
			latest = cot_records[0]
			comm_long = latest.get("comm_positions_long_all", 0)
			comm_short = latest.get("comm_positions_short_all", 0)
			comm_net = comm_long - comm_short if comm_long and comm_short else None
			oi = latest.get("open_interest_all", 1)

			# Williams COT Index approximation
			comm_pct = None
			if comm_long and comm_short and oi:
				comm_pct = round((comm_long / (comm_long + comm_short)) * 100, 1) if (comm_long + comm_short) > 0 else None

			cot_summary = {
				"date": latest.get("date", "unknown"),
				"commercial_net": comm_net,
				"commercial_long_pct": comm_pct,
				"open_interest": oi,
				"signal": "bullish" if comm_pct and comm_pct > 75 else ("bearish" if comm_pct and comm_pct < 25 else "neutral"),
				"note": "COT data is weekly (as of prior Tuesday)",
			}
	else:
		missing_components.append("cot_data")

	# Determine market bias
	bias_score = 0
	if not tdw_tdm.get("error"):
		cb = tdw_tdm.get("combined_bias", "neutral")
		if "bullish" in cb:
			bias_score += 1
		elif "bearish" in cb:
			bias_score -= 1

	if not bond_status.get("error"):
		bt = bond_status.get("tlt_trend", "")
		if "bullish" in bt:
			bias_score += 1
		elif "bearish" in bt:
			bias_score -= 1

	if cot_summary:
		cs = cot_summary.get("signal", "neutral")
		if cs == "bullish":
			bias_score += 1
		elif cs == "bearish":
			bias_score -= 1

	if bias_score >= 2:
		market_bias = "bullish"
	elif bias_score == 1:
		market_bias = "moderately_bullish"
	elif bias_score == -1:
		market_bias = "moderately_bearish"
	elif bias_score <= -2:
		market_bias = "bearish"
	else:
		market_bias = "neutral"

	output_json({
		"tdw_tdm": tdw_tdm if not tdw_tdm.get("error") else {"error": tdw_tdm.get("error")},
		"bond_status": bond_status,
		"cot_summary": cot_summary,
		"market_bias": market_bias,
		"missing_components": missing_components,
	})


# ---------------------------------------------------------------------------
# Command: watchlist (batch trade-setup)
# ---------------------------------------------------------------------------

@safe_run
def cmd_watchlist(args):
	"""Batch trade-setup for multiple tickers."""
	symbols = [s.upper() for s in args.symbols]
	results = []

	for sym in symbols:
		data = _run_script("technical/williams.py", [
			"trade-setup", sym,
			"--risk-pct", str(args.risk_pct),
			"--account-size", str(args.account_size),
		])
		if not data.get("error"):
			results.append({
				"symbol": sym,
				"conviction_score": data.get("conviction_score", 0),
				"signal": data.get("signal", "AVOID"),
				"pattern_count": len([
					p for c in [data.get("components", {}).get("pattern_signal", {}).get("detail", "")]
					if c and c != "no_patterns"
					for p in [c]
				]),
				"hard_gates_triggered": data.get("hard_gates", {}).get("signal_capped", False),
				"position_sizing": data.get("position_sizing", {}),
				"components_summary": {
					k: v.get("score", 0) for k, v in data.get("components", {}).items()
				},
			})
		else:
			results.append({
				"symbol": sym,
				"conviction_score": 0,
				"signal": "ERROR",
				"error": data.get("error"),
			})

	# Sort by conviction score descending
	results.sort(key=lambda x: x.get("conviction_score", 0), reverse=True)

	output_json({
		"results": results,
		"ranked_by": "conviction_score",
		"count": len(results),
		"risk_pct": args.risk_pct,
		"account_size": args.account_size,
	})


# ---------------------------------------------------------------------------
# Command: dashboard
# ---------------------------------------------------------------------------

@safe_run
def cmd_dashboard(args):
	"""Quick overview: today's bias + bond filter status."""
	with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
		tdw_future = executor.submit(_run_script, "technical/williams.py", ["tdw-tdm"])
		bond_future = executor.submit(_get_bond_status)

		tdw_tdm = tdw_future.result()
		bond_status = bond_future.result()

	# Overall bias
	bias_score = 0
	if not tdw_tdm.get("error"):
		cb = tdw_tdm.get("combined_bias", "neutral")
		if "bullish" in cb:
			bias_score += 1
		elif "bearish" in cb:
			bias_score -= 1
	if not bond_status.get("error"):
		bt = bond_status.get("tlt_trend", "")
		if "bullish" in bt:
			bias_score += 1
		elif "bearish" in bt:
			bias_score -= 1

	if bias_score >= 2:
		overall = "bullish"
	elif bias_score == 1:
		overall = "slightly_bullish"
	elif bias_score == -1:
		overall = "slightly_bearish"
	elif bias_score <= -2:
		overall = "bearish"
	else:
		overall = "neutral"

	import datetime
	output_json({
		"date": datetime.date.today().isoformat(),
		"tdw_tdm": tdw_tdm if not tdw_tdm.get("error") else {"error": tdw_tdm.get("error")},
		"bond_filter": bond_status,
		"overall_bias": overall,
	})


# ---------------------------------------------------------------------------
# Main dispatch
# ---------------------------------------------------------------------------

def main():
	parser = argparse.ArgumentParser(
		description="Williams Pipeline: Short-Term Volatility Breakout Analysis"
	)
	sub = parser.add_subparsers(dest="command", required=True)

	# trade-setup
	sp = sub.add_parser("trade-setup", help="Composite trade qualification for a ticker")
	sp.add_argument("symbol", help="Ticker symbol")
	sp.add_argument("--risk-pct", type=float, default=3.0, help="Risk %% per trade (default: 3.0)")
	sp.add_argument("--account-size", type=float, default=100000, help="Account size (default: 100000)")
	sp.set_defaults(func=cmd_trade_setup)

	# analyze
	sp = sub.add_parser("analyze", help="Full Williams analysis for a ticker")
	sp.add_argument("symbol", help="Ticker symbol")
	sp.set_defaults(func=cmd_analyze)

	# pattern-scan
	sp = sub.add_parser("pattern-scan", help="Multi-ticker pattern scanning")
	sp.add_argument("symbols", nargs="+", help="Ticker symbols to scan")
	sp.add_argument("--lookback", type=int, default=5, help="Scan window days (default: 5)")
	sp.set_defaults(func=cmd_pattern_scan)

	# market-context
	sp = sub.add_parser("market-context", help="Market environment assessment")
	sp.set_defaults(func=cmd_market_context)

	# watchlist
	sp = sub.add_parser("watchlist", help="Batch trade-setup for multiple tickers")
	sp.add_argument("symbols", nargs="+", help="Ticker symbols")
	sp.add_argument("--risk-pct", type=float, default=3.0, help="Risk %% per trade (default: 3.0)")
	sp.add_argument("--account-size", type=float, default=100000, help="Account size (default: 100000)")
	sp.set_defaults(func=cmd_watchlist)

	# dashboard
	sp = sub.add_parser("dashboard", help="Quick overview: bias + bond status")
	sp.set_defaults(func=cmd_dashboard)

	args = parser.parse_args()
	args.func(args)


if __name__ == "__main__":
	main()
