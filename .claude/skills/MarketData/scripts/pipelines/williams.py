#!/usr/bin/env python3
"""Williams Pipeline (Pipeline-Complete): full short-term volatility breakout
analysis integrating all Williams methodology modules with composite scoring,
hard/soft gates, evidence building, position sizing, and dual LONG/SHORT
signal system.

Orchestrates 12+ atomic module calls in parallel, applies Williams' methodology
to produce conviction scores (0-100) for BOTH long and short directions,
signal determinations, and structured evidence for LLM interpretation. The
pipeline is the SOLE data interface -- individual module calls are never made
outside this pipeline.

Commands:
	trade-setup: Primary composite trade qualification for a single ticker
	analyze: Full deep analysis for a single ticker (all indicators + long-term swing)
	pattern-scan: Multi-ticker Williams pattern scanning with accuracy metadata
	market-context: Market environment: bond trend, TDW/TDM, COT, gold-bond
	watchlist: Batch trade-setup for multiple tickers (provisional mode)
	dashboard: Quick overview: today's bias + bond filter status
	recheck: Position management — exit signal evaluation for held positions

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

	For recheck:
		symbol (str): Ticker symbol
		--entry-price (float): Original entry price (required)
		--entry-date (str): Entry date YYYY-MM-DD (required)
		--entry-stop (float): Entry stop price (optional)
		--direction (str): Position direction "long" or "short" (default: "long")

Returns:
	For trade-setup:
		dict: {
			"symbol": str,
			"conviction_score": float,         # 0-100 composite score (dominant direction)
			"signal": str,                     # STRONG_BUY/BUY/HOLD/MONITOR/AVOID/SELL/STRONG_SELL
			"direction": str,                  # "long" or "short" (dominant direction)
			"long_score": float,               # 0-100 long conviction score
			"short_score": float,              # 0-100 short conviction score
			"signal_reason_codes": [str],
			"hard_gates": {
				"triggered": [str],            # gate codes that fired
				"signal_capped": bool
			},
			"short_hard_gates": {
				"triggered": [str],
				"signal_capped": bool
			},
			"soft_gates": {
				"penalties": [{"code": str, "penalty": int}],
				"total_penalty": int
			},
			"bonuses": {
				"applied": [{"code": str, "points": int}],
				"total_bonus": int
			},
			"components": {
				"pattern_signal": {"score": float, "max": 25, "detail": str},
				"volatility_breakout": {"score": float, "max": 15, "detail": str},
				"bond_intermarket": {"score": float, "max": 15, "detail": str},
				"tdw_alignment": {"score": float, "max": 10, "detail": str},
				"tdm_alignment": {"score": float, "max": 10, "detail": str},
				"range_phase": {"score": float, "max": 10, "detail": str},
				"ma_trend": {"score": float, "max": 10, "detail": str},
				"williams_r": {"score": float, "max": 10, "detail": str},
				"close_position": {"score": float, "max": 5, "detail": str},
				"swing_structure": {"score": float, "max": 5, "detail": str}
			},
			"short_components": {
				"pattern_signal": {"score": float, "max": 25, "detail": str},
				"volatility_breakout": {"score": float, "max": 15, "detail": str},
				"bond_intermarket": {"score": float, "max": 15, "detail": str},
				"tdw_alignment": {"score": float, "max": 10, "detail": str},
				"tdm_alignment": {"score": float, "max": 10, "detail": str},
				"range_phase": {"score": float, "max": 10, "detail": str},
				"ma_trend": {"score": float, "max": 10, "detail": str},
				"williams_r": {"score": float, "max": 10, "detail": str},
				"close_position": {"score": float, "max": 5, "detail": str},
				"swing_structure": {"score": float, "max": 5, "detail": str}
			},
			"evidence": {
				"bond_filter": dict,
				"pattern": dict,
				"range": dict,
				"swing": dict,
				"gsv": dict,
				"cot": dict or null
			},
			"position_sizing": dict,
			"missing_components": [str],
			"recommendation_text": str
		}

	For analyze:
		dict: {
			"symbol": str,
			"trade_setup_summary": dict,
			"williams_r": dict,
			"volatility_breakout": dict,
			"range_analysis": dict,
			"swing_points_short": dict,
			"swing_points_intermediate": dict,
			"swing_points_long": dict,
			"pattern_scan": dict,
			"gsv": dict,
			"trend_ma": dict,
			"tdw_tdm": dict,
			"bond_filter": dict,
			"closing_range": dict,
			"cot_summary": dict or null,
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
			"bond_filter": dict,
			"gold_bond_signal": dict or null,
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
				"hard_gates_triggered": bool,
				"components_summary": dict
			}],
			"ranked_by": "conviction_score",
			"count": int,
			"mode": "provisional"
		}

	For dashboard:
		dict: {
			"date": str,
			"tdw_tdm": dict,
			"bond_filter": dict,
			"overall_bias": str
		}

	For recheck:
		dict: {
			"symbol": str,
			"direction": str,                  # "long" or "short"
			"entry_price": float,
			"current_price": float,
			"days_held": int,
			"unrealized_pnl_pct": float,
			"exit_signals": [{"code": str, "triggered": bool, "detail": str}],
			"verdict": str,                    # EXIT_REVERSE/EXIT_STOP/EXIT_TIME/EXIT_BAILOUT/COVER/HOLD
			"verdict_reason": str,
			"bailout_triggered": bool,         # LONG: open > entry; SHORT: open < entry
			"first_profitable_open": bool,     # LONG: open > entry; SHORT: open < entry
			"reverse_signal": bool,            # True if opposite volatility breakout signal detected
			"current_stop": float,
			"williams_r": dict,
			"range_phase": str,
			"swing_status": dict,
			"missing_components": [str]
		}

Example:
	>>> python pipelines/williams.py trade-setup AAPL --risk-pct 3 --account-size 100000
	{
		"symbol": "AAPL",
		"conviction_score": 72.0,
		"signal": "BUY",
		"components": {...},
		"position_sizing": {"contracts": 150, "dollar_risk": 3000},
		"recommendation_text": "AAPL: Conviction 72/100 — BUY | smash_day + bonds favorable"
	}

	>>> python pipelines/williams.py market-context
	{
		"tdw_tdm": {"combined_bias": "slightly_bullish"},
		"bond_filter": {"trend": "bullish", "signal": "favorable"},
		"market_bias": "moderately_bullish"
	}

	>>> python pipelines/williams.py recheck AAPL --entry-price 200 --entry-date 2026-02-25
	{
		"symbol": "AAPL",
		"days_held": 3,
		"exit_signals": [...],
		"verdict": "HOLD",
		"verdict_reason": "Within optimal 2-5 day window, no exit signals triggered"
	}

Use Cases:
	- Complete short-term trade qualification using Williams' methodology
	- Batch pattern scanning across a watchlist
	- Daily market environment check (bond trend + calendar bias + COT)
	- Quick dashboard for morning trading preparation
	- Multi-factor conviction scoring for position sizing decisions
	- Position management with exit signal monitoring

Notes:
	- Scoring weights (115 max, capped at 100): Pattern 25, Volatility Breakout 15,
	  Bond 15, TDW 10, TDM 10, Range 10, MA 10, %R 10, Close 5, Swing 5
	- Volatility Breakout is the CORE of Williams' methodology (Ch.4):
	  Active buy breakout = 15, near buy level = 8, no breakout = 3, sell signal = 0
	- Long signals: STRONG_BUY 80+, BUY 60-79, HOLD 40-59, MONITOR 20-39, AVOID <20
	- Short signals: STRONG_SELL 80+, SELL 60-79, HOLD 40-59, MONITOR 20-39, AVOID <20
	- Dual scoring: trade-setup computes both long_score and short_score;
	  the dominant direction determines the primary signal
	- Long hard gates cap signal to HOLD (conviction ≤ 59):
	  BOND_CONTRADICTION (bonds bearish AND buy signal active),
	  NO_PATTERN, CHASING_MOMENTUM
	- Short hard gates cap signal to HOLD (conviction ≤ 59):
	  SHORT_BOND_CONTRADICTION (bonds bullish AND sell signal active),
	  NO_BEARISH_PATTERN, CHASING_WEAKNESS (%R oversold AND no bearish pattern)
	- Soft gates apply score penalties: RANGE_EXPANSION -5, SELLING_PRESSURE -3,
	  SWING_DOWNTREND -3, CONSECUTIVE_LARGE_RANGES -3, GSV_EXHAUSTION -3
	- Short soft gates: RANGE_EXPANSION -5, BUYING_PRESSURE -3 (close_pct > 75),
	  SWING_UPTREND -3, CONSECUTIVE_LARGE_RANGES -3, GSV_EXHAUSTION -3
	- Bonus points: MULTI_PATTERN +3, RANGE_COILED +3, STRONG_CLOSES +2,
	  COT_COMMERCIAL_BULLISH +2
	- Short bonuses: MULTI_BEARISH_PATTERN +3, RANGE_COILED +3, WEAK_CLOSES +2,
	  COT_COMMERCIAL_BEARISH +2
	- Position sizing: Williams formula — contracts = dollar_risk / stop_distance
	- Bond data uses TLT ETF as Treasury Bond proxy
	- COT data from CFTC (weekly update, may be 3-7 days stale)
	- Pipeline continues even if individual components fail (graceful degradation)
	- Scripts execute in parallel via ThreadPoolExecutor for performance
	- Each script runs in independent subprocess (no shared state)
	- Watchlist mode caps STRONG_BUY to BUY (provisional mode)
	- Recheck exit signals: BAILOUT_OPPORTUNITY (first profitable open, Williams Ch.11),
	  TIME_STOP, DOLLAR_STOP_HIT, WR_OVERBOUGHT_EXIT, SWING_VIOLATION,
	  REVERSE_SIGNAL (opposite breakout triggers EXIT_REVERSE verdict)
	- Recheck --direction short: BAILOUT (open < entry), DOLLAR_STOP (price > stop),
	  WR_OVERSOLD_EXIT (WR < -80), SWING_VIOLATION (above swing high),
	  REVERSE_SIGNAL (buy breakout → EXIT_REVERSE), COVER_SIGNAL (bullish pattern)
	- Recheck verdict priority: EXIT_REVERSE > EXIT_STOP > EXIT_TIME >
	  EXIT_BAILOUT > COVER > HOLD

See Also:
	- technical/williams_r.py: Williams %R oscillator
	- technical/atr_breakout.py: ATR-based volatility breakout levels
	- technical/range_analysis.py: Range expansion/contraction detection
	- technical/swing_points.py: Swing point identification (3 levels)
	- technical/bar_patterns.py: Williams chart pattern detection (5 patterns)
	- technical/gsv.py: Greatest Swing Value analysis
	- technical/calendar_bias.py: TDW/TDM calendar bias
	- technical/trend.py: SMA/EMA trend indicators
	- technical/closing_range.py: Close position bar classification
	- data_sources/price.py: Historical OHLCV data
	- data_advanced/cftc/cftc.py: COT positioning data
"""

import argparse
import concurrent.futures
import datetime
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
# Evidence builder functions (pipeline-internal, _ prefix)
# ---------------------------------------------------------------------------

def _build_bond_filter(tlt_data):
	"""Build bond intermarket filter from TLT price data.

	Calculates 14-day channel breakout and 20-day SMA to determine
	bond trend and its implication for stock trading.
	"""
	if tlt_data.get("error"):
		return {"error": "TLT data unavailable"}

	# price.py history returns column-oriented: {"Close": {"date": value}, ...}
	close_col = tlt_data.get("Close", {})
	if not close_col or not isinstance(close_col, dict):
		return {"error": "Unexpected TLT data format"}

	closes = []
	for date_str in sorted(close_col.keys()):
		val = close_col[date_str]
		if val is not None:
			closes.append(float(val))

	if len(closes) < 20:
		return {"error": "Insufficient TLT data"}

	current = closes[-1]
	high_14 = max(closes[-14:])
	low_14 = min(closes[-14:])
	sma_20 = sum(closes[-20:]) / 20

	if current >= high_14:
		trend = "bullish"
		signal = "bonds_breaking_up_favorable_stocks"
		score = 15
	elif current <= low_14:
		trend = "bearish"
		signal = "bonds_breaking_down_unfavorable_stocks"
		score = 0
	elif current > sma_20:
		trend = "mildly_bullish"
		signal = "bonds_above_20ma_neutral_positive"
		score = 10
	else:
		trend = "mildly_bearish"
		signal = "bonds_below_20ma_neutral_negative"
		score = 5

	return {
		"tlt_price": round(current, 2),
		"tlt_14d_high": round(high_14, 2),
		"tlt_14d_low": round(low_14, 2),
		"tlt_sma_20": round(sma_20, 2),
		"trend": trend,
		"signal": signal,
		"score": score,
		"contradiction": trend == "bearish",
	}


def _build_pattern_evidence(scan_result):
	"""Extract and structure pattern information from scan result."""
	if scan_result.get("error"):
		return {"patterns": [], "count": 0, "has_non_caveat": False}

	patterns = scan_result.get("patterns_detected", [])
	non_caveat = [p for p in patterns if not p.get("electronic_era_caveat")]

	return {
		"patterns": [
			{
				"name": p.get("pattern"),
				"direction": p.get("direction"),
				"accuracy": p.get("historical_accuracy"),
				"strength": p.get("strength"),
				"entry": p.get("entry_price"),
				"stop": p.get("stop_price"),
				"confirmation": p.get("confirmation_needed"),
				"confirmed": p.get("confirmed"),
			}
			for p in patterns
		],
		"count": len(patterns),
		"non_caveat_count": len(non_caveat),
		"has_non_caveat": len(non_caveat) > 0,
	}


def _build_range_evidence(range_data):
	"""Build range analysis evidence from range-analysis output."""
	if range_data.get("error"):
		return {"error": "range data unavailable"}

	close_pos = range_data.get("close_position", {})
	return {
		"phase": range_data.get("phase"),
		"range_ratio": range_data.get("range_ratio"),
		"axiom_signal": range_data.get("axiom_signal"),
		"consecutive_small": range_data.get("consecutive_small_ranges", 0),
		"consecutive_large": range_data.get("consecutive_large_ranges", 0),
		"close_pct": close_pos.get("close_pct"),
		"buying_power": close_pos.get("buying_power"),
		"selling_pressure": close_pos.get("selling_pressure"),
		"recent_bias": close_pos.get("recent_bias"),
		"consecutive_upper_closes": close_pos.get("consecutive_upper_closes", 0),
		"consecutive_lower_closes": close_pos.get("consecutive_lower_closes", 0),
	}


def _build_swing_evidence(short_swing, intermediate_swing):
	"""Build swing point evidence from short and intermediate data."""
	result = {
		"short_trend": "unknown",
		"intermediate_trend": "unknown",
		"last_short_low": None,
		"last_intermediate_low": None,
		"support": None,
		"resistance": None,
	}

	if not short_swing.get("error"):
		result["short_trend"] = short_swing.get("current_trend", "neutral")
		last_low = short_swing.get("last_swing_low")
		if last_low:
			result["last_short_low"] = last_low.get("price")
			result["support"] = last_low.get("price")
		last_high = short_swing.get("last_swing_high")
		if last_high:
			result["resistance"] = last_high.get("price")

	if not intermediate_swing.get("error"):
		result["intermediate_trend"] = intermediate_swing.get("current_trend", "neutral")
		last_low = intermediate_swing.get("last_swing_low")
		if last_low:
			result["last_intermediate_low"] = last_low.get("price")

	return result


def _build_gsv_evidence(gsv_data):
	"""Build GSV evidence from gsv subcommand output."""
	if gsv_data.get("error"):
		return {"error": "GSV data unavailable"}

	return {
		"avg_buy_swing": gsv_data.get("avg_buy_swing"),
		"avg_sell_swing": gsv_data.get("avg_sell_swing"),
		"buy_entry": gsv_data.get("buy_entry_level"),
		"buy_stop": gsv_data.get("buy_stop_level"),
		"sell_entry": gsv_data.get("sell_entry_level"),
		"sell_stop": gsv_data.get("sell_stop_level"),
		"exhaustion": gsv_data.get("recent_gsv_exceeded", False),
	}


def _build_cot_evidence(cot_data):
	"""Build COT evidence with Williams COT Index calculation."""
	if cot_data.get("error"):
		return None

	records = cot_data.get("data", [])
	if not records:
		return None

	latest = records[0]
	comm_long = latest.get("comm_positions_long_all", 0)
	comm_short = latest.get("comm_positions_short_all", 0)
	comm_net = comm_long - comm_short if comm_long and comm_short else None
	oi = latest.get("open_interest_all", 1)

	# Williams COT Index: commercial long as % of total commercial positions
	comm_pct = None
	if comm_long and comm_short and (comm_long + comm_short) > 0:
		comm_pct = round((comm_long / (comm_long + comm_short)) * 100, 1)

	if comm_pct and comm_pct > 75:
		signal = "bullish"
	elif comm_pct and comm_pct < 25:
		signal = "bearish"
	else:
		signal = "neutral"

	return {
		"date": latest.get("date", "unknown"),
		"commercial_net": comm_net,
		"commercial_long_pct": comm_pct,
		"open_interest": oi,
		"signal": signal,
		"note": "COT data is weekly (as of prior Tuesday)",
	}


# ---------------------------------------------------------------------------
# Scoring and gate evaluation
# ---------------------------------------------------------------------------

def _calc_composite_score(components):
	"""Calculate weighted composite score from all component scores.

	Weights (115 max, capped at 100):
	  Pattern 25, Volatility Breakout 15, Bond 15, TDW 10, TDM 10,
	  Range 10, MA 10, %R 10, Close 5, Swing 5
	"""
	total = 0
	for comp in components.values():
		total += comp.get("score", 0)
	return round(min(100, total), 1)


def _evaluate_hard_gates(components, pattern_evidence, bond_filter, vb_data=None):
	"""Evaluate hard gate conditions that cap signal to HOLD.

	Hard gates:
	  BOND_CONTRADICTION: TLT 14-day breakout down + stock buy signal active
	  NO_PATTERN: no pattern detected in scan window
	  CHASING_MOMENTUM: Williams %R overbought (>-20) AND no pattern
	"""
	triggered = []

	# BOND_CONTRADICTION: only trigger when bonds bearish AND there is a
	# buy/long signal. Williams Ch.6: bonds bearish is only contradictory
	# when you are trying to go LONG. If no signal or signal is sell, bond
	# direction is irrelevant as a hard gate.
	if bond_filter.get("contradiction"):
		has_buy_signal = False
		if vb_data and not vb_data.get("error"):
			active = vb_data.get("active_signal", "none")
			has_buy_signal = active == "buy"
		# Also check if patterns suggest bullish direction
		if not has_buy_signal and pattern_evidence.get("count", 0) > 0:
			bullish_patterns = [
				p for p in pattern_evidence.get("patterns", [])
				if p.get("direction") == "bullish"
			]
			has_buy_signal = len(bullish_patterns) > 0
		if has_buy_signal:
			triggered.append("BOND_CONTRADICTION")

	# NO_PATTERN
	pattern_count = pattern_evidence.get("count", 0)
	no_pattern = pattern_count == 0
	if no_pattern:
		triggered.append("NO_PATTERN")

	# CHASING_MOMENTUM: overbought + no pattern
	wr_comp = components.get("williams_r", {})
	wr_detail = wr_comp.get("detail", "")
	is_overbought = "overbought" in wr_detail
	if is_overbought and no_pattern:
		triggered.append("CHASING_MOMENTUM")

	return {
		"triggered": triggered,
		"signal_capped": len(triggered) > 0,
	}


def _evaluate_soft_gates(components, range_evidence, gsv_evidence):
	"""Evaluate soft gate conditions that apply score penalties.

	Soft gates:
	  RANGE_EXPANSION: range phase = expansion (-5)
	  SELLING_PRESSURE: close_pct < 25% (-3)
	  SWING_DOWNTREND: swing structure = downtrend (-3)
	  CONSECUTIVE_LARGE_RANGES: 3+ expansion days (-3)
	  GSV_EXHAUSTION: GSV 225% threshold exceeded (-3)
	"""
	penalties = []

	# RANGE_EXPANSION
	if range_evidence.get("phase") == "expansion":
		penalties.append({"code": "RANGE_EXPANSION", "penalty": -5})

	# SELLING_PRESSURE
	close_pct = range_evidence.get("close_pct")
	if close_pct is not None and close_pct < 25:
		penalties.append({"code": "SELLING_PRESSURE", "penalty": -3})

	# SWING_DOWNTREND
	swing_comp = components.get("swing_structure", {})
	if swing_comp.get("detail", "").startswith("downtrend"):
		penalties.append({"code": "SWING_DOWNTREND", "penalty": -3})

	# CONSECUTIVE_LARGE_RANGES
	if range_evidence.get("consecutive_large", 0) >= 3:
		penalties.append({"code": "CONSECUTIVE_LARGE_RANGES", "penalty": -3})

	# GSV_EXHAUSTION
	if gsv_evidence.get("exhaustion"):
		penalties.append({"code": "GSV_EXHAUSTION", "penalty": -3})

	total = sum(p["penalty"] for p in penalties)
	return {
		"penalties": penalties,
		"total_penalty": total,
	}


def _evaluate_bonuses(pattern_evidence, range_evidence, cot_evidence):
	"""Evaluate bonus point conditions.

	Bonuses:
	  MULTI_PATTERN: 2+ active patterns (+3)
	  RANGE_COILED: 3+ consecutive contraction days (+3)
	  STRONG_CLOSES: 3+ consecutive upper 65% closes (+2)
	  COT_COMMERCIAL_BULLISH: COT commercial % > 75% (+2)
	"""
	applied = []

	if pattern_evidence.get("count", 0) >= 2:
		applied.append({"code": "MULTI_PATTERN", "points": 3})

	if range_evidence.get("consecutive_small", 0) >= 3:
		applied.append({"code": "RANGE_COILED", "points": 3})

	if range_evidence.get("consecutive_upper_closes", 0) >= 3:
		applied.append({"code": "STRONG_CLOSES", "points": 2})

	if cot_evidence and cot_evidence.get("signal") == "bullish":
		applied.append({"code": "COT_COMMERCIAL_BULLISH", "points": 2})

	total = sum(b["points"] for b in applied)
	return {
		"applied": applied,
		"total_bonus": total,
	}


def _determine_signal(conviction, hard_gates):
	"""Map conviction score to signal level, applying hard gate caps."""
	if hard_gates.get("signal_capped"):
		conviction = min(conviction, 59)

	if conviction >= 80:
		return "STRONG_BUY", conviction
	elif conviction >= 60:
		return "BUY", conviction
	elif conviction >= 40:
		return "HOLD", conviction
	elif conviction >= 20:
		return "MONITOR", conviction
	return "AVOID", conviction


def _build_signal_reason_codes(signal, components, hard_gates, soft_gates, bonuses, missing):
	"""Build comprehensive signal reason codes."""
	codes = []

	# Hard gate codes
	for gate in hard_gates.get("triggered", []):
		codes.append(gate)

	# Component strength codes
	pattern = components.get("pattern_signal", {})
	if pattern.get("score", 0) >= 20:
		codes.append("STRONG_PATTERN")
	elif pattern.get("score", 0) >= 15:
		codes.append("PATTERN_PRESENT")

	bond = components.get("bond_intermarket", {})
	if bond.get("score", 0) >= 15:
		codes.append("BONDS_BULLISH")
	elif bond.get("score", 0) <= 5:
		codes.append("BONDS_BEARISH")

	tdw = components.get("tdw_alignment", {})
	if tdw.get("score", 0) >= 10:
		codes.append("TDW_FAVORABLE")

	tdm = components.get("tdm_alignment", {})
	if tdm.get("score", 0) >= 10:
		codes.append("TDM_FAVORABLE")

	ma = components.get("ma_trend", {})
	if ma.get("score", 0) >= 10:
		codes.append("MA_UPTREND")
	elif ma.get("score", 0) <= 3:
		codes.append("MA_DOWNTREND")

	wr = components.get("williams_r", {})
	if wr.get("score", 0) >= 10:
		codes.append("WR_OVERSOLD_OPPORTUNITY")
	elif wr.get("score", 0) <= 1:
		codes.append("WR_OVERBOUGHT_CAUTION")

	# Soft gate codes
	for penalty in soft_gates.get("penalties", []):
		codes.append(penalty["code"])

	# Bonus codes
	for bonus in bonuses.get("applied", []):
		codes.append(bonus["code"])

	if missing:
		codes.append(f"MISSING_{len(missing)}_COMPONENTS")

	return codes


def _generate_recommendation(symbol, signal, conviction, components, hard_gates, pattern_evidence):
	"""Generate one-line recommendation text."""
	parts = [f"{symbol}: Conviction {conviction}/100 — {signal}"]

	drivers = []
	if pattern_evidence.get("count", 0) > 0:
		names = [p["name"] for p in pattern_evidence.get("patterns", [])[:2]]
		drivers.append(", ".join(names))

	if components.get("bond_intermarket", {}).get("score", 0) >= 10:
		drivers.append("bonds favorable")
	if components.get("tdw_alignment", {}).get("score", 0) >= 10:
		drivers.append("TDW bullish")
	if components.get("tdm_alignment", {}).get("score", 0) >= 10:
		drivers.append("TDM bullish")

	if drivers:
		parts.append(" | " + " + ".join(drivers[:3]))

	for gate in hard_gates.get("triggered", []):
		parts.append(f" [{gate} — signal capped]")

	return "".join(parts)


# ---------------------------------------------------------------------------
# Compression helpers
# ---------------------------------------------------------------------------

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
	"""Keep phase, axiom signal, close position, limit history."""
	if raw.get("error"):
		return raw
	return {
		"symbol": raw.get("symbol"),
		"current_range_pct": raw.get("current_range_pct"),
		"avg_range_pct": raw.get("avg_range_pct"),
		"range_ratio": raw.get("range_ratio"),
		"phase": raw.get("phase"),
		"consecutive_small_ranges": raw.get("consecutive_small_ranges"),
		"consecutive_large_ranges": raw.get("consecutive_large_ranges"),
		"axiom_signal": raw.get("axiom_signal"),
		"close_position": raw.get("close_position"),
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


def _compress_gsv(raw):
	"""Keep GSV levels and exhaustion flag."""
	if raw.get("error"):
		return raw
	return {
		"symbol": raw.get("symbol"),
		"avg_buy_swing": raw.get("avg_buy_swing"),
		"avg_sell_swing": raw.get("avg_sell_swing"),
		"buy_entry_level": raw.get("buy_entry_level"),
		"buy_stop_level": raw.get("buy_stop_level"),
		"sell_entry_level": raw.get("sell_entry_level"),
		"sell_stop_level": raw.get("sell_stop_level"),
		"recent_gsv_exceeded": raw.get("recent_gsv_exceeded"),
	}


def _compress_closing_range(raw):
	"""Keep latest bar classification and trend."""
	if raw.get("error"):
		return raw
	return {
		"symbol": raw.get("symbol"),
		"latest_bar": raw.get("latest_bar"),
		"constructive_ratio": raw.get("constructive_ratio"),
		"consecutive_constructive": raw.get("consecutive_constructive"),
		"recent_trend": raw.get("recent_trend"),
		"avg_closing_range_pct": raw.get("avg_closing_range_pct"),
	}


# ---------------------------------------------------------------------------
# Component scoring functions
# ---------------------------------------------------------------------------

def _score_pattern(pattern_evidence):
	"""Score pattern signal component (max 25 points).

	0 patterns = 0, 1 pattern = 15, 2+ = 20, non-caveat bonus +5.
	"""
	count = pattern_evidence.get("count", 0)
	has_non_caveat = pattern_evidence.get("has_non_caveat", False)

	if count == 0:
		return 0, "no_patterns"

	if count >= 2:
		score = 20
	else:
		score = 15

	if has_non_caveat:
		score = min(25, score + 5)

	names = [p.get("name", "?") for p in pattern_evidence.get("patterns", [])]
	detail = f"{count} patterns: {', '.join(names)}"
	return score, detail


def _score_bond(bond_filter):
	"""Score bond intermarket component (max 15 points)."""
	if bond_filter.get("error"):
		return 0, "unavailable"
	return bond_filter.get("score", 0), f"{bond_filter.get('trend', 'unknown')} ({bond_filter.get('signal', '')})"


def _score_tdw(tdw_data):
	"""Score TDW alignment component (max 10 points)."""
	if tdw_data.get("error"):
		return 5, "unavailable"
	bias = tdw_data.get("tdw_bias", "neutral")
	if bias == "bullish":
		return 10, f"bullish ({tdw_data.get('tdw_note', '')})"
	elif bias == "neutral":
		return 5, f"neutral ({tdw_data.get('tdw_note', '')})"
	return 2, f"bearish ({tdw_data.get('tdw_note', '')})"


def _score_tdm(tdw_data):
	"""Score TDM alignment component (max 10 points)."""
	if tdw_data.get("error"):
		return 5, "unavailable"
	bias = tdw_data.get("tdm_bias", "neutral")
	if bias == "bullish":
		return 10, f"bullish ({tdw_data.get('tdm_note', '')})"
	elif bias == "neutral":
		return 5, f"neutral ({tdw_data.get('tdm_note', '')})"
	return 2, f"bearish ({tdw_data.get('tdm_note', '')})"


def _score_range_phase(range_data):
	"""Score range phase component (max 10 points)."""
	if range_data.get("error"):
		return 5, "unavailable"
	phase = range_data.get("phase", "neutral")
	axiom = range_data.get("axiom_signal", "neutral")
	if phase == "contraction":
		return 10, f"contraction (axiom: {axiom})"
	elif phase == "neutral":
		return 5, f"neutral (axiom: {axiom})"
	return 2, f"expansion (axiom: {axiom})"


def _score_ma_trend(trend_data):
	"""Score MA trend component (max 10 points).

	Uses 18-day MA (Williams' preferred period). Falls back to 20-day
	if 18-day unavailable.
	"""
	if trend_data.get("error"):
		return 5, "unavailable"

	sma_dict = trend_data.get("sma", {})
	current_price = trend_data.get("current_price", 0)

	# Look for SMA18 first, then SMA20
	sma_key = None
	for key in ["SMA18", "SMA20"]:
		if key in sma_dict:
			sma_key = key
			break

	if not sma_key or not current_price:
		return 5, "insufficient_data"

	sma_val = sma_dict[sma_key].get("value", 0)
	distance_pct = sma_dict[sma_key].get("distance_pct", 0)

	if current_price > sma_val and distance_pct > 0:
		# Price above rising MA
		return 10, f"price_above_rising_{sma_key} ({sma_val:.2f}, +{distance_pct:.1f}%)"
	elif current_price > sma_val:
		return 7, f"price_above_flat_{sma_key} ({sma_val:.2f})"
	elif distance_pct < -3:
		return 0, f"price_below_falling_{sma_key} ({sma_val:.2f}, {distance_pct:.1f}%)"
	else:
		return 3, f"price_below_{sma_key} ({sma_val:.2f}, {distance_pct:.1f}%)"


def _score_williams_r(wr_data):
	"""Score Williams %R component (max 10 points)."""
	if wr_data.get("error"):
		return 5, "unavailable"

	wr_val = wr_data.get("current_wr", -50)
	if wr_val < -80:
		return 10, f"oversold ({wr_val})"
	elif wr_val < -50:
		return 7, f"neutral_low ({wr_val})"
	elif wr_val < -20:
		return 4, f"neutral_high ({wr_val})"
	return 1, f"overbought ({wr_val})"


def _score_close_position(range_data):
	"""Score close position component (max 5 points)."""
	if range_data.get("error"):
		return 3, "unavailable"

	close_pos = range_data.get("close_position", {})
	close_pct = close_pos.get("close_pct")

	if close_pct is None:
		return 3, "unavailable"

	if close_pct >= 65:
		return 5, f"upper_range ({close_pct}%, bias: {close_pos.get('recent_bias', 'unknown')})"
	elif close_pct >= 35:
		return 3, f"middle_range ({close_pct}%)"
	return 0, f"lower_range ({close_pct}%, bias: {close_pos.get('recent_bias', 'unknown')})"


def _score_volatility_breakout(vb_data):
	"""Score volatility breakout component (max 15 points).

	This is the CORE of Williams' methodology. A volatility breakout (price
	exceeding open ± ATR-based level) signals the trend change. Williams Ch.4:
	"Trends are set in motion by explosions of price activity."

	Scoring:
	  Active buy signal = 15 (breakout triggered in long direction)
	  No breakout but near level = 5 (within 25% of triggering)
	  No breakout = 0
	  Active sell signal = 0 (wrong direction for long setup)
	"""
	if vb_data.get("error"):
		return 5, "unavailable"

	active_signal = vb_data.get("active_signal", "none")
	breakout_triggered = vb_data.get("breakout_triggered", False)

	if breakout_triggered and active_signal == "buy":
		return 15, f"breakout_buy_active (level: {vb_data.get('electronic_buy_level', '?')})"
	elif breakout_triggered and active_signal == "sell":
		return 0, f"breakout_sell_active (opposing direction)"
	elif not breakout_triggered:
		# Check proximity to buy level
		current = vb_data.get("current_price", 0)
		buy_level = vb_data.get("electronic_buy_level") or vb_data.get("classic_buy_level")
		if current and buy_level and buy_level > 0:
			distance_pct = ((buy_level - current) / current) * 100
			if 0 < distance_pct <= 0.5:
				return 8, f"near_buy_level ({distance_pct:.2f}% away)"
			elif distance_pct <= 0:
				# Price above buy level but breakout not flagged — treat as borderline
				return 10, f"above_buy_level_unconfirmed"
		return 3, f"no_breakout (signal: {active_signal})"

	return 5, f"signal_{active_signal}"


def _score_swing_structure(short_swing, intermediate_swing):
	"""Score swing structure component (max 5 points)."""
	short_trend = "neutral"
	if not short_swing.get("error"):
		short_trend = short_swing.get("current_trend", "neutral")

	int_trend = "neutral"
	if not intermediate_swing.get("error"):
		int_trend = intermediate_swing.get("current_trend", "neutral")

	if short_trend == "up" and int_trend == "up":
		return 5, f"uptrend (short: {short_trend}, intermediate: {int_trend})"
	elif short_trend == "up" or int_trend == "up":
		return 3, f"mixed (short: {short_trend}, intermediate: {int_trend})"
	elif short_trend == "down" and int_trend == "down":
		return 0, f"downtrend (short: {short_trend}, intermediate: {int_trend})"
	return 3, f"neutral (short: {short_trend}, intermediate: {int_trend})"


# ---------------------------------------------------------------------------
# SHORT-side component scoring (mirrors of LONG scoring)
# ---------------------------------------------------------------------------

def _score_pattern_short(pattern_evidence):
	"""Score bearish pattern signal component (max 25 points).

	Only counts bearish-direction patterns. 0 = 0, 1 = 15, 2+ = 20,
	non-caveat bonus +5.
	"""
	patterns = pattern_evidence.get("patterns", [])
	bearish = [p for p in patterns if p.get("direction") == "bearish"]
	count = len(bearish)
	non_caveat = [p for p in bearish if not p.get("electronic_era_caveat")]

	if count == 0:
		return 0, "no_bearish_patterns"

	if count >= 2:
		score = 20
	else:
		score = 15

	if non_caveat:
		score = min(25, score + 5)

	names = [p.get("name", "?") for p in bearish]
	detail = f"{count} bearish patterns: {', '.join(names)}"
	return score, detail


def _score_bond_short(bond_filter):
	"""Score bond intermarket for SHORT (max 15 points).

	Inverse of long: bonds bearish = favorable for shorts (stocks likely to drop).
	Bonds bullish = unfavorable for shorts (stocks supported).
	"""
	if bond_filter.get("error"):
		return 0, "unavailable"
	trend = bond_filter.get("trend", "unknown")
	if trend == "bearish":
		return 15, f"bearish ({bond_filter.get('signal', '')}) — favorable for shorts"
	elif trend == "mildly_bearish":
		return 10, f"mildly_bearish — neutral_favorable for shorts"
	elif trend == "mildly_bullish":
		return 5, f"mildly_bullish — neutral_unfavorable for shorts"
	return 0, f"bullish ({bond_filter.get('signal', '')}) — unfavorable for shorts"


def _score_tdw_short(tdw_data):
	"""Score TDW alignment for SHORT (max 10 points).

	Thursday = best sell day. Monday/Tuesday bearish for shorts (strong buy days).
	"""
	if tdw_data.get("error"):
		return 5, "unavailable"
	bias = tdw_data.get("tdw_bias", "neutral")
	if bias == "bearish":
		return 10, f"bearish ({tdw_data.get('tdw_note', '')}) — favorable for shorts"
	elif bias == "neutral":
		return 5, f"neutral ({tdw_data.get('tdw_note', '')})"
	return 2, f"bullish ({tdw_data.get('tdw_note', '')}) — unfavorable for shorts"


def _score_tdm_short(tdw_data):
	"""Score TDM alignment for SHORT (max 10 points).

	Midmonth weakness (TDM 5-7, 12-13) = favorable for shorts.
	"""
	if tdw_data.get("error"):
		return 5, "unavailable"
	bias = tdw_data.get("tdm_bias", "neutral")
	if bias == "bearish":
		return 10, f"bearish ({tdw_data.get('tdm_note', '')}) — favorable for shorts"
	elif bias == "neutral":
		return 5, f"neutral ({tdw_data.get('tdm_note', '')})"
	return 2, f"bullish ({tdw_data.get('tdm_note', '')}) — unfavorable for shorts"


def _score_ma_trend_short(trend_data):
	"""Score MA trend for SHORT (max 10 points).

	Price below falling MA = favorable for shorts (downtrend confirmed).
	"""
	if trend_data.get("error"):
		return 5, "unavailable"

	sma_dict = trend_data.get("sma", {})
	current_price = trend_data.get("current_price", 0)

	sma_key = None
	for key in ["SMA18", "SMA20"]:
		if key in sma_dict:
			sma_key = key
			break

	if not sma_key or not current_price:
		return 5, "insufficient_data"

	sma_val = sma_dict[sma_key].get("value", 0)
	distance_pct = sma_dict[sma_key].get("distance_pct", 0)

	if current_price < sma_val and distance_pct < 0:
		return 10, f"price_below_falling_{sma_key} ({sma_val:.2f}, {distance_pct:.1f}%)"
	elif current_price < sma_val:
		return 7, f"price_below_flat_{sma_key} ({sma_val:.2f})"
	elif distance_pct > 3:
		return 0, f"price_above_rising_{sma_key} ({sma_val:.2f}, +{distance_pct:.1f}%)"
	else:
		return 3, f"price_above_{sma_key} ({sma_val:.2f}, +{distance_pct:.1f}%)"


def _score_williams_r_short(wr_data):
	"""Score Williams %R for SHORT (max 10 points).

	Overbought (> -20) = opportunity for shorts. Oversold (< -80) = caution.
	"""
	if wr_data.get("error"):
		return 5, "unavailable"

	wr_val = wr_data.get("current_wr", -50)
	if wr_val > -20:
		return 10, f"overbought ({wr_val}) — short opportunity"
	elif wr_val > -50:
		return 7, f"neutral_high ({wr_val})"
	elif wr_val > -80:
		return 4, f"neutral_low ({wr_val})"
	return 1, f"oversold ({wr_val}) — caution for shorts"


def _score_close_position_short(range_data):
	"""Score close position for SHORT (max 5 points).

	Lower close = favorable for shorts (selling pressure dominant).
	"""
	if range_data.get("error"):
		return 3, "unavailable"

	close_pos = range_data.get("close_position", {})
	close_pct = close_pos.get("close_pct")

	if close_pct is None:
		return 3, "unavailable"

	if close_pct <= 35:
		return 5, f"lower_range ({close_pct}%) — favorable for shorts"
	elif close_pct <= 65:
		return 3, f"middle_range ({close_pct}%)"
	return 0, f"upper_range ({close_pct}%) — unfavorable for shorts"


def _score_volatility_breakout_short(vb_data):
	"""Score volatility breakout for SHORT (max 15 points).

	Active sell signal = 15 (breakout triggered in short direction).
	Active buy signal = 0 (wrong direction for short setup).
	"""
	if vb_data.get("error"):
		return 5, "unavailable"

	active_signal = vb_data.get("active_signal", "none")
	breakout_triggered = vb_data.get("breakout_triggered", False)

	if breakout_triggered and active_signal == "sell":
		return 15, f"breakout_sell_active (level: {vb_data.get('electronic_sell_level', '?')})"
	elif breakout_triggered and active_signal == "buy":
		return 0, f"breakout_buy_active (opposing direction for short)"
	elif not breakout_triggered:
		current = vb_data.get("current_price", 0)
		sell_level = vb_data.get("electronic_sell_level") or vb_data.get("classic_sell_level")
		if current and sell_level and sell_level > 0:
			distance_pct = ((current - sell_level) / current) * 100
			if 0 < distance_pct <= 0.5:
				return 8, f"near_sell_level ({distance_pct:.2f}% away)"
			elif distance_pct <= 0:
				return 10, f"below_sell_level_unconfirmed"
		return 3, f"no_breakout (signal: {active_signal})"

	return 5, f"signal_{active_signal}"


def _score_swing_structure_short(short_swing, intermediate_swing):
	"""Score swing structure for SHORT (max 5 points).

	Downtrend = favorable for shorts. Uptrend = unfavorable.
	"""
	short_trend = "neutral"
	if not short_swing.get("error"):
		short_trend = short_swing.get("current_trend", "neutral")

	int_trend = "neutral"
	if not intermediate_swing.get("error"):
		int_trend = intermediate_swing.get("current_trend", "neutral")

	if short_trend == "down" and int_trend == "down":
		return 5, f"downtrend (short: {short_trend}, intermediate: {int_trend}) — favorable"
	elif short_trend == "down" or int_trend == "down":
		return 3, f"mixed (short: {short_trend}, intermediate: {int_trend})"
	elif short_trend == "up" and int_trend == "up":
		return 0, f"uptrend (short: {short_trend}, intermediate: {int_trend}) — unfavorable"
	return 3, f"neutral (short: {short_trend}, intermediate: {int_trend})"


def _evaluate_hard_gates_short(components, pattern_evidence, bond_filter, vb_data=None):
	"""Evaluate hard gate conditions for SHORT direction.

	Hard gates:
	  SHORT_BOND_CONTRADICTION: TLT bullish + sell signal (bonds support stocks)
	  NO_BEARISH_PATTERN: no bearish pattern detected
	  CHASING_WEAKNESS: Williams %R oversold (<-80) AND no bearish pattern
	"""
	triggered = []

	# SHORT_BOND_CONTRADICTION: bonds bullish is contradictory for shorts
	if not bond_filter.get("error"):
		trend = bond_filter.get("trend", "")
		is_bonds_bullish = trend == "bullish"
		if is_bonds_bullish:
			has_sell_signal = False
			if vb_data and not vb_data.get("error"):
				active = vb_data.get("active_signal", "none")
				has_sell_signal = active == "sell"
			if not has_sell_signal and pattern_evidence.get("count", 0) > 0:
				bearish_patterns = [
					p for p in pattern_evidence.get("patterns", [])
					if p.get("direction") == "bearish"
				]
				has_sell_signal = len(bearish_patterns) > 0
			if has_sell_signal:
				triggered.append("SHORT_BOND_CONTRADICTION")

	# NO_BEARISH_PATTERN
	bearish_patterns = [
		p for p in pattern_evidence.get("patterns", [])
		if p.get("direction") == "bearish"
	]
	no_bearish = len(bearish_patterns) == 0
	if no_bearish:
		triggered.append("NO_BEARISH_PATTERN")

	# CHASING_WEAKNESS: oversold + no bearish pattern
	wr_comp = components.get("williams_r", {})
	wr_detail = wr_comp.get("detail", "")
	is_oversold = "oversold" in wr_detail
	if is_oversold and no_bearish:
		triggered.append("CHASING_WEAKNESS")

	return {
		"triggered": triggered,
		"signal_capped": len(triggered) > 0,
	}


def _evaluate_soft_gates_short(components, range_evidence, gsv_evidence):
	"""Evaluate soft gate conditions for SHORT direction.

	Soft gates:
	  RANGE_EXPANSION: range phase = expansion (-5) [same as long]
	  BUYING_PRESSURE: close_pct > 75% (-3) [inverse of selling_pressure]
	  SWING_UPTREND: swing structure = uptrend (-3) [inverse of downtrend]
	  CONSECUTIVE_LARGE_RANGES: 3+ expansion days (-3) [same as long]
	  GSV_EXHAUSTION: GSV 225% threshold exceeded (-3) [same as long]
	"""
	penalties = []

	if range_evidence.get("phase") == "expansion":
		penalties.append({"code": "RANGE_EXPANSION", "penalty": -5})

	close_pct = range_evidence.get("close_pct")
	if close_pct is not None and close_pct > 75:
		penalties.append({"code": "BUYING_PRESSURE", "penalty": -3})

	swing_comp = components.get("swing_structure", {})
	if swing_comp.get("detail", "").startswith("uptrend"):
		penalties.append({"code": "SWING_UPTREND", "penalty": -3})

	if range_evidence.get("consecutive_large", 0) >= 3:
		penalties.append({"code": "CONSECUTIVE_LARGE_RANGES", "penalty": -3})

	if gsv_evidence.get("exhaustion"):
		penalties.append({"code": "GSV_EXHAUSTION", "penalty": -3})

	total = sum(p["penalty"] for p in penalties)
	return {
		"penalties": penalties,
		"total_penalty": total,
	}


def _evaluate_bonuses_short(pattern_evidence, range_evidence, cot_evidence):
	"""Evaluate bonus point conditions for SHORT direction.

	Bonuses:
	  MULTI_BEARISH_PATTERN: 2+ bearish patterns (+3)
	  RANGE_COILED: 3+ consecutive contraction days (+3) [same as long]
	  WEAK_CLOSES: 3+ consecutive lower 35% closes (+2)
	  COT_COMMERCIAL_BEARISH: COT commercial % < 25% (+2)
	"""
	applied = []

	bearish = [p for p in pattern_evidence.get("patterns", []) if p.get("direction") == "bearish"]
	if len(bearish) >= 2:
		applied.append({"code": "MULTI_BEARISH_PATTERN", "points": 3})

	if range_evidence.get("consecutive_small", 0) >= 3:
		applied.append({"code": "RANGE_COILED", "points": 3})

	if range_evidence.get("consecutive_lower_closes", 0) >= 3:
		applied.append({"code": "WEAK_CLOSES", "points": 2})

	if cot_evidence and cot_evidence.get("signal") == "bearish":
		applied.append({"code": "COT_COMMERCIAL_BEARISH", "points": 2})

	total = sum(b["points"] for b in applied)
	return {
		"applied": applied,
		"total_bonus": total,
	}


def _determine_signal_short(conviction, hard_gates):
	"""Map SHORT conviction score to signal level, applying hard gate caps."""
	if hard_gates.get("signal_capped"):
		conviction = min(conviction, 59)

	if conviction >= 80:
		return "STRONG_SELL", conviction
	elif conviction >= 60:
		return "SELL", conviction
	elif conviction >= 40:
		return "HOLD", conviction
	elif conviction >= 20:
		return "MONITOR", conviction
	return "AVOID", conviction


# ---------------------------------------------------------------------------
# Command: trade-setup
# ---------------------------------------------------------------------------

@safe_run
def cmd_trade_setup(args):
	"""Primary composite trade qualification for a single ticker.

	Calls 12 atomic scripts in parallel, applies Williams methodology
	scoring (10 components, 100 points), evaluates hard/soft gates,
	calculates position sizing, and produces a signal with evidence.
	"""
	symbol = args.symbol.upper()
	missing_components = []

	# --- Parallel module calls (12 scripts) ---
	scripts = {
		"volatility_breakout": ("technical/atr_breakout.py", ["breakout", symbol]),
		"range_analysis": ("technical/range_analysis.py", ["analyze", symbol]),
		"swing_short": ("technical/swing_points.py", ["detect", symbol, "--level", "short"]),
		"swing_intermediate": ("technical/swing_points.py", ["detect", symbol, "--level", "intermediate"]),
		"pattern_scan": ("technical/bar_patterns.py", ["scan", symbol, "--lookback", "10"]),
		"williams_r": ("technical/williams_r.py", ["calculate", symbol, "--period", "14"]),
		"tdw_tdm": ("technical/calendar_bias.py", ["today"]),
		"gsv": ("technical/gsv.py", ["analyze", symbol]),
		"trend_ma": ("technical/trend.py", ["sma", symbol, "--periods", "18,50,200"]),
		"closing_range": ("technical/closing_range.py", ["analyze", symbol]),
		"tlt_data": ("data_sources/price.py", ["history", "TLT", "--period", "3mo"]),
		"cot_data": ("data_advanced/cftc/cftc.py", ["cot", "ES", "--limit", "4"]),
	}

	with concurrent.futures.ThreadPoolExecutor(max_workers=12) as executor:
		futures = {name: executor.submit(_run_script, path, a) for name, (path, a) in scripts.items()}
		results = {name: future.result() for name, future in futures.items()}

	# Track missing components
	for name, data in results.items():
		if data.get("error"):
			missing_components.append(name)

	# --- Build evidence ---
	bond_filter = _build_bond_filter(results["tlt_data"])
	if bond_filter.get("error"):
		missing_components.append("bond_filter")

	pattern_evidence = _build_pattern_evidence(results["pattern_scan"])
	range_evidence = _build_range_evidence(results["range_analysis"])
	swing_evidence = _build_swing_evidence(results["swing_short"], results["swing_intermediate"])
	gsv_evidence = _build_gsv_evidence(results["gsv"])
	cot_evidence = _build_cot_evidence(results["cot_data"])

	# --- Score each LONG component ---
	pattern_score, pattern_detail = _score_pattern(pattern_evidence)
	bond_score, bond_detail = _score_bond(bond_filter)
	tdw_score, tdw_detail = _score_tdw(results["tdw_tdm"])
	tdm_score, tdm_detail = _score_tdm(results["tdw_tdm"])
	range_score, range_detail = _score_range_phase(results["range_analysis"])
	ma_score, ma_detail = _score_ma_trend(results["trend_ma"])
	wr_score, wr_detail = _score_williams_r(results["williams_r"])
	close_score, close_detail = _score_close_position(results["range_analysis"])
	swing_score, swing_detail = _score_swing_structure(results["swing_short"], results["swing_intermediate"])
	vb_score, vb_detail = _score_volatility_breakout(results["volatility_breakout"])

	components = {
		"pattern_signal": {"score": pattern_score, "max": 25, "detail": pattern_detail},
		"volatility_breakout": {"score": vb_score, "max": 15, "detail": vb_detail},
		"bond_intermarket": {"score": bond_score, "max": 15, "detail": bond_detail},
		"tdw_alignment": {"score": tdw_score, "max": 10, "detail": tdw_detail},
		"tdm_alignment": {"score": tdm_score, "max": 10, "detail": tdm_detail},
		"range_phase": {"score": range_score, "max": 10, "detail": range_detail},
		"ma_trend": {"score": ma_score, "max": 10, "detail": ma_detail},
		"williams_r": {"score": wr_score, "max": 10, "detail": wr_detail},
		"close_position": {"score": close_score, "max": 5, "detail": close_detail},
		"swing_structure": {"score": swing_score, "max": 5, "detail": swing_detail},
	}

	# --- Score each SHORT component ---
	sp_score, sp_detail = _score_pattern_short(pattern_evidence)
	sb_score, sb_detail = _score_bond_short(bond_filter)
	stw_score, stw_detail = _score_tdw_short(results["tdw_tdm"])
	stm_score, stm_detail = _score_tdm_short(results["tdw_tdm"])
	sma_score, sma_detail = _score_ma_trend_short(results["trend_ma"])
	swr_score, swr_detail = _score_williams_r_short(results["williams_r"])
	scp_score, scp_detail = _score_close_position_short(results["range_analysis"])
	svb_score, svb_detail = _score_volatility_breakout_short(results["volatility_breakout"])
	sss_score, sss_detail = _score_swing_structure_short(results["swing_short"], results["swing_intermediate"])

	short_components = {
		"pattern_signal": {"score": sp_score, "max": 25, "detail": sp_detail},
		"volatility_breakout": {"score": svb_score, "max": 15, "detail": svb_detail},
		"bond_intermarket": {"score": sb_score, "max": 15, "detail": sb_detail},
		"tdw_alignment": {"score": stw_score, "max": 10, "detail": stw_detail},
		"tdm_alignment": {"score": stm_score, "max": 10, "detail": stm_detail},
		"range_phase": {"score": range_score, "max": 10, "detail": range_detail},
		"ma_trend": {"score": sma_score, "max": 10, "detail": sma_detail},
		"williams_r": {"score": swr_score, "max": 10, "detail": swr_detail},
		"close_position": {"score": scp_score, "max": 5, "detail": scp_detail},
		"swing_structure": {"score": sss_score, "max": 5, "detail": sss_detail},
	}

	# --- Calculate LONG raw score ---
	raw_score = _calc_composite_score(components)
	hard_gates = _evaluate_hard_gates(components, pattern_evidence, bond_filter, vb_data=results["volatility_breakout"])
	soft_gates = _evaluate_soft_gates(components, range_evidence, gsv_evidence)
	bonuses = _evaluate_bonuses(pattern_evidence, range_evidence, cot_evidence)
	long_conviction = raw_score + soft_gates["total_penalty"] + bonuses["total_bonus"]
	long_conviction = round(max(0, min(100, long_conviction)), 1)
	long_signal, long_conviction = _determine_signal(long_conviction, hard_gates)

	# --- Calculate SHORT raw score ---
	short_raw = _calc_composite_score(short_components)
	short_hard_gates = _evaluate_hard_gates_short(short_components, pattern_evidence, bond_filter, vb_data=results["volatility_breakout"])
	short_soft_gates = _evaluate_soft_gates_short(short_components, range_evidence, gsv_evidence)
	short_bonuses = _evaluate_bonuses_short(pattern_evidence, range_evidence, cot_evidence)
	short_conviction = short_raw + short_soft_gates["total_penalty"] + short_bonuses["total_bonus"]
	short_conviction = round(max(0, min(100, short_conviction)), 1)
	short_signal, short_conviction = _determine_signal_short(short_conviction, short_hard_gates)

	# --- Determine dominant direction ---
	if long_conviction >= short_conviction:
		dominant_direction = "long"
		conviction = long_conviction
		signal = long_signal
		dominant_components = components
		dominant_hard_gates = hard_gates
		dominant_soft_gates = soft_gates
		dominant_bonuses = bonuses
	else:
		dominant_direction = "short"
		conviction = short_conviction
		signal = short_signal
		dominant_components = short_components
		dominant_hard_gates = short_hard_gates
		dominant_soft_gates = short_soft_gates
		dominant_bonuses = short_bonuses

	# --- Signal reason codes (from dominant direction) ---
	reason_codes = _build_signal_reason_codes(
		signal, dominant_components, dominant_hard_gates, dominant_soft_gates,
		dominant_bonuses, missing_components
	)

	# --- Position sizing (Williams formula) ---
	pos_sizing = {}
	vb = results["volatility_breakout"]
	if not vb.get("error"):
		atr_val = vb.get("atr_3day", 0)
		current_price = vb.get("current_price", 0)
		entry_price = current_price
		stop_distance = atr_val if atr_val > 0 else current_price * 0.02
		if dominant_direction == "long":
			stop_price = round(entry_price - stop_distance, 2)
		else:
			stop_price = round(entry_price + stop_distance, 2)
		dollar_risk = args.account_size * (args.risk_pct / 100)
		contracts = int(dollar_risk / stop_distance) if stop_distance > 0 else 0

		pos_sizing = {
			"direction": dominant_direction,
			"risk_pct": args.risk_pct,
			"account_size": args.account_size,
			"contracts": contracts,
			"dollar_risk": round(dollar_risk, 2),
			"entry_price": round(entry_price, 2),
			"stop_price": stop_price,
			"stop_distance": round(stop_distance, 2),
		}

	# --- Recommendation ---
	recommendation = _generate_recommendation(
		symbol, signal, conviction, dominant_components, dominant_hard_gates, pattern_evidence
	)

	output_json({
		"symbol": symbol,
		"conviction_score": conviction,
		"signal": signal,
		"direction": dominant_direction,
		"long_score": long_conviction,
		"short_score": short_conviction,
		"signal_reason_codes": reason_codes,
		"hard_gates": hard_gates,
		"short_hard_gates": short_hard_gates,
		"soft_gates": soft_gates,
		"bonuses": bonuses,
		"components": components,
		"short_components": short_components,
		"evidence": {
			"bond_filter": bond_filter if not bond_filter.get("error") else None,
			"pattern": pattern_evidence,
			"range": range_evidence if not range_evidence.get("error") else None,
			"swing": swing_evidence,
			"gsv": gsv_evidence if not gsv_evidence.get("error") else None,
			"cot": cot_evidence,
		},
		"volatility_breakout": _compress_volatility_breakout(vb),
		"position_sizing": pos_sizing,
		"missing_components": list(set(missing_components)),
		"recommendation_text": recommendation,
	})


# ---------------------------------------------------------------------------
# Command: analyze
# ---------------------------------------------------------------------------

@safe_run
def cmd_analyze(args):
	"""Full deep analysis for a single ticker — all indicators + long-term swing.

	Runs trade-setup's 12 modules + long-term swing points. Returns all
	compressed module outputs plus the trade-setup conviction score.
	"""
	symbol = args.symbol.upper()
	missing_components = []

	scripts = {
		"williams_r": ("technical/williams_r.py", ["calculate", symbol, "--period", "14"]),
		"volatility_breakout": ("technical/atr_breakout.py", ["breakout", symbol]),
		"range_analysis": ("technical/range_analysis.py", ["analyze", symbol]),
		"swing_short": ("technical/swing_points.py", ["detect", symbol, "--level", "short"]),
		"swing_intermediate": ("technical/swing_points.py", ["detect", symbol, "--level", "intermediate"]),
		"swing_long": ("technical/swing_points.py", ["detect", symbol, "--level", "long"]),
		"pattern_scan": ("technical/bar_patterns.py", ["scan", symbol, "--lookback", "10"]),
		"tdw_tdm": ("technical/calendar_bias.py", ["today"]),
		"gsv": ("technical/gsv.py", ["analyze", symbol]),
		"trend_ma": ("technical/trend.py", ["sma", symbol, "--periods", "18,50,200"]),
		"closing_range": ("technical/closing_range.py", ["analyze", symbol]),
		"tlt_data": ("data_sources/price.py", ["history", "TLT", "--period", "3mo"]),
		"cot_data": ("data_advanced/cftc/cftc.py", ["cot", "ES", "--limit", "4"]),
	}

	with concurrent.futures.ThreadPoolExecutor(max_workers=13) as executor:
		futures = {name: executor.submit(_run_script, path, a) for name, (path, a) in scripts.items()}
		results = {name: future.result() for name, future in futures.items()}

	for name, data in results.items():
		if data.get("error"):
			missing_components.append(name)

	# Build evidence for trade-setup summary
	bond_filter = _build_bond_filter(results["tlt_data"])
	pattern_evidence = _build_pattern_evidence(results["pattern_scan"])
	range_evidence = _build_range_evidence(results["range_analysis"])
	gsv_evidence = _build_gsv_evidence(results["gsv"])
	cot_evidence = _build_cot_evidence(results["cot_data"])

	# Score components
	pattern_score, pattern_detail = _score_pattern(pattern_evidence)
	bond_score, bond_detail = _score_bond(bond_filter)
	tdw_score, tdw_detail = _score_tdw(results["tdw_tdm"])
	tdm_score, tdm_detail = _score_tdm(results["tdw_tdm"])
	range_score, range_detail = _score_range_phase(results["range_analysis"])
	ma_score, ma_detail = _score_ma_trend(results["trend_ma"])
	wr_score, wr_detail = _score_williams_r(results["williams_r"])
	close_score, close_detail = _score_close_position(results["range_analysis"])
	swing_score, swing_detail = _score_swing_structure(results["swing_short"], results["swing_intermediate"])
	vb_score, vb_detail = _score_volatility_breakout(results["volatility_breakout"])

	components = {
		"pattern_signal": {"score": pattern_score, "max": 25, "detail": pattern_detail},
		"volatility_breakout": {"score": vb_score, "max": 15, "detail": vb_detail},
		"bond_intermarket": {"score": bond_score, "max": 15, "detail": bond_detail},
		"tdw_alignment": {"score": tdw_score, "max": 10, "detail": tdw_detail},
		"tdm_alignment": {"score": tdm_score, "max": 10, "detail": tdm_detail},
		"range_phase": {"score": range_score, "max": 10, "detail": range_detail},
		"ma_trend": {"score": ma_score, "max": 10, "detail": ma_detail},
		"williams_r": {"score": wr_score, "max": 10, "detail": wr_detail},
		"close_position": {"score": close_score, "max": 5, "detail": close_detail},
		"swing_structure": {"score": swing_score, "max": 5, "detail": swing_detail},
	}

	raw_score = _calc_composite_score(components)
	hard_gates = _evaluate_hard_gates(components, pattern_evidence, bond_filter, vb_data=results["volatility_breakout"])
	soft_gates = _evaluate_soft_gates(components, range_evidence, gsv_evidence)
	bonuses = _evaluate_bonuses(pattern_evidence, range_evidence, cot_evidence)
	conviction = round(max(0, min(100, raw_score + soft_gates["total_penalty"] + bonuses["total_bonus"])), 1)
	signal, conviction = _determine_signal(conviction, hard_gates)

	trade_setup_summary = {
		"conviction_score": conviction,
		"signal": signal,
		"components": components,
		"hard_gates": hard_gates,
		"soft_gates": soft_gates,
		"bonuses": bonuses,
	}

	output_json({
		"symbol": symbol,
		"trade_setup_summary": trade_setup_summary,
		"williams_r": _compress_williams_r(results["williams_r"]),
		"volatility_breakout": _compress_volatility_breakout(results["volatility_breakout"]),
		"range_analysis": _compress_range_analysis(results["range_analysis"]),
		"swing_points_short": _compress_swing_points(results["swing_short"]),
		"swing_points_intermediate": _compress_swing_points(results["swing_intermediate"]),
		"swing_points_long": _compress_swing_points(results["swing_long"]),
		"pattern_scan": results["pattern_scan"] if not results["pattern_scan"].get("error") else results["pattern_scan"],
		"gsv": _compress_gsv(results["gsv"]),
		"trend_ma": _compress_trend(results["trend_ma"]),
		"tdw_tdm": results["tdw_tdm"] if not results["tdw_tdm"].get("error") else results["tdw_tdm"],
		"bond_filter": bond_filter if not bond_filter.get("error") else bond_filter,
		"closing_range": _compress_closing_range(results["closing_range"]),
		"cot_summary": cot_evidence,
		"missing_components": missing_components,
	})


# ---------------------------------------------------------------------------
# Command: pattern-scan (multi-ticker)
# ---------------------------------------------------------------------------

@safe_run
def cmd_pattern_scan(args):
	"""Multi-ticker Williams pattern scanning with accuracy metadata."""
	symbols = [s.upper() for s in args.symbols]

	def _scan_one(sym):
		return _run_script("technical/bar_patterns.py", ["scan", sym, "--lookback", str(args.lookback)])

	results = []
	total_patterns = 0

	with concurrent.futures.ThreadPoolExecutor(max_workers=min(5, len(symbols))) as executor:
		futures = {sym: executor.submit(_scan_one, sym) for sym in symbols}
		for sym in symbols:
			data = futures[sym].result()
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
	"""Market environment: bond trend, TDW/TDM, COT, gold-bond relationship."""
	missing_components = []

	# Parallel calls
	with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
		tdw_future = executor.submit(_run_script, "technical/calendar_bias.py", ["today"])
		tlt_future = executor.submit(_run_script, "data_sources/price.py", ["history", "TLT", "--period", "3mo"])
		cot_future = executor.submit(_run_script, "data_advanced/cftc/cftc.py", ["cot", "ES", "--limit", "4"])
		gld_future = executor.submit(_run_script, "data_sources/price.py", ["history", "GLD", "--period", "3mo"])

		tdw_tdm = tdw_future.result()
		tlt_data = tlt_future.result()
		cot_data = cot_future.result()
		gld_data = gld_future.result()

	if tdw_tdm.get("error"):
		missing_components.append("tdw_tdm")

	# Bond filter
	bond_filter = _build_bond_filter(tlt_data)
	if bond_filter.get("error"):
		missing_components.append("bond_filter")

	# COT evidence
	cot_summary = _build_cot_evidence(cot_data)
	if not cot_summary:
		missing_components.append("cot_data")

	# Gold-Bond relationship: Gold close < 20-24 days ago → bonds bullish
	gold_bond_signal = None
	if not gld_data.get("error"):
		gld_close_col = gld_data.get("Close", {})
		if gld_close_col and isinstance(gld_close_col, dict):
			gld_closes = []
			for date_str in sorted(gld_close_col.keys()):
				val = gld_close_col[date_str]
				if val is not None:
					gld_closes.append(float(val))

			if len(gld_closes) >= 24:
				current_gold = gld_closes[-1]
				gold_20d_ago = gld_closes[-20]
				gold_24d_ago = gld_closes[-24]

				if current_gold < gold_20d_ago and current_gold < gold_24d_ago:
					gold_bond_signal = {
						"signal": "gold_weak_bonds_bullish",
						"current_gold": round(current_gold, 2),
						"gold_20d_ago": round(gold_20d_ago, 2),
						"gold_24d_ago": round(gold_24d_ago, 2),
						"interpretation": "Gold weakness signals deflationary pressure — bullish for bonds",
					}
				elif current_gold > gold_20d_ago:
					gold_bond_signal = {
						"signal": "gold_strong_bonds_neutral",
						"current_gold": round(current_gold, 2),
						"gold_20d_ago": round(gold_20d_ago, 2),
						"interpretation": "Gold strength may pressure bonds — neutral to bearish for bonds",
					}
	else:
		missing_components.append("gold_data")

	# Market bias calculation
	bias_score = 0
	if not tdw_tdm.get("error"):
		cb = tdw_tdm.get("combined_bias", "neutral")
		if "bullish" in cb:
			bias_score += 1
		elif "bearish" in cb:
			bias_score -= 1

	if not bond_filter.get("error"):
		bt = bond_filter.get("trend", "")
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
		"bond_filter": bond_filter,
		"gold_bond_signal": gold_bond_signal,
		"cot_summary": cot_summary,
		"market_bias": market_bias,
		"missing_components": missing_components,
	})


# ---------------------------------------------------------------------------
# Command: watchlist (batch trade-setup)
# ---------------------------------------------------------------------------

@safe_run
def cmd_watchlist(args):
	"""Batch trade-setup for multiple tickers (provisional mode).

	Runs trade-setup logic for each ticker. STRONG_BUY is capped to BUY
	in provisional mode. Results sorted by conviction score descending.
	"""
	symbols = [s.upper() for s in args.symbols]

	def _setup_one(sym):
		"""Run trade-setup logic for a single ticker (inline for batch)."""
		scripts = {
			"volatility_breakout": ("technical/atr_breakout.py", ["breakout", sym]),
			"range_analysis": ("technical/range_analysis.py", ["analyze", sym]),
			"swing_short": ("technical/swing_points.py", ["detect", sym, "--level", "short"]),
			"swing_intermediate": ("technical/swing_points.py", ["detect", sym, "--level", "intermediate"]),
			"pattern_scan": ("technical/bar_patterns.py", ["scan", sym, "--lookback", "10"]),
			"williams_r": ("technical/williams_r.py", ["calculate", sym, "--period", "14"]),
			"tdw_tdm": ("technical/calendar_bias.py", ["today"]),
			"gsv": ("technical/gsv.py", ["analyze", sym]),
			"trend_ma": ("technical/trend.py", ["sma", sym, "--periods", "18,50,200"]),
			"tlt_data": ("data_sources/price.py", ["history", "TLT", "--period", "3mo"]),
		}

		with concurrent.futures.ThreadPoolExecutor(max_workers=10) as ex:
			futs = {n: ex.submit(_run_script, p, a) for n, (p, a) in scripts.items()}
			res = {n: f.result() for n, f in futs.items()}

		missing = [n for n, d in res.items() if d.get("error")]
		bond = _build_bond_filter(res["tlt_data"])
		pat_ev = _build_pattern_evidence(res["pattern_scan"])
		rng_ev = _build_range_evidence(res["range_analysis"])
		gsv_ev = _build_gsv_evidence(res["gsv"])

		ps, pd = _score_pattern(pat_ev)
		vbs, vbd = _score_volatility_breakout(res["volatility_breakout"])
		bs, bd = _score_bond(bond)
		ts, td = _score_tdw(res["tdw_tdm"])
		tms, tmd = _score_tdm(res["tdw_tdm"])
		rs, rd = _score_range_phase(res["range_analysis"])
		ms, md = _score_ma_trend(res["trend_ma"])
		ws, wd = _score_williams_r(res["williams_r"])
		cs, cd = _score_close_position(res["range_analysis"])
		ss, sd = _score_swing_structure(res["swing_short"], res["swing_intermediate"])

		comps = {
			"pattern_signal": {"score": ps, "max": 25, "detail": pd},
			"volatility_breakout": {"score": vbs, "max": 15, "detail": vbd},
			"bond_intermarket": {"score": bs, "max": 15, "detail": bd},
			"tdw_alignment": {"score": ts, "max": 10, "detail": td},
			"tdm_alignment": {"score": tms, "max": 10, "detail": tmd},
			"range_phase": {"score": rs, "max": 10, "detail": rd},
			"ma_trend": {"score": ms, "max": 10, "detail": md},
			"williams_r": {"score": ws, "max": 10, "detail": wd},
			"close_position": {"score": cs, "max": 5, "detail": cd},
			"swing_structure": {"score": ss, "max": 5, "detail": sd},
		}

		raw = _calc_composite_score(comps)
		hg = _evaluate_hard_gates(comps, pat_ev, bond, vb_data=res["volatility_breakout"])
		sg = _evaluate_soft_gates(comps, rng_ev, gsv_ev)
		bn = _evaluate_bonuses(pat_ev, rng_ev, None)  # No COT in watchlist mode

		conv = round(max(0, min(100, raw + sg["total_penalty"] + bn["total_bonus"])), 1)
		sig, conv = _determine_signal(conv, hg)

		# Provisional mode: cap STRONG_BUY to BUY
		if sig == "STRONG_BUY":
			sig = "BUY"

		return {
			"symbol": sym,
			"conviction_score": conv,
			"signal": sig,
			"pattern_count": pat_ev.get("count", 0),
			"hard_gates_triggered": hg.get("signal_capped", False),
			"components_summary": {k: v["score"] for k, v in comps.items()},
			"missing_components": missing,
		}

	# Run tickers in parallel (max 5 concurrent)
	results = []
	with concurrent.futures.ThreadPoolExecutor(max_workers=min(5, len(symbols))) as executor:
		futures = {sym: executor.submit(_setup_one, sym) for sym in symbols}
		for sym in symbols:
			try:
				results.append(futures[sym].result())
			except Exception as e:
				results.append({
					"symbol": sym,
					"conviction_score": 0,
					"signal": "ERROR",
					"error": str(e),
				})

	results.sort(key=lambda x: x.get("conviction_score", 0), reverse=True)

	output_json({
		"results": results,
		"ranked_by": "conviction_score",
		"count": len(results),
		"mode": "provisional",
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
		tdw_future = executor.submit(_run_script, "technical/calendar_bias.py", ["today"])
		tlt_future = executor.submit(_run_script, "data_sources/price.py", ["history", "TLT", "--period", "3mo"])

		tdw_tdm = tdw_future.result()
		tlt_data = tlt_future.result()

	bond_filter = _build_bond_filter(tlt_data)

	# Overall bias
	bias_score = 0
	if not tdw_tdm.get("error"):
		cb = tdw_tdm.get("combined_bias", "neutral")
		if "bullish" in cb:
			bias_score += 1
		elif "bearish" in cb:
			bias_score -= 1
	if not bond_filter.get("error"):
		bt = bond_filter.get("trend", "")
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

	output_json({
		"date": datetime.date.today().isoformat(),
		"tdw_tdm": tdw_tdm if not tdw_tdm.get("error") else {"error": tdw_tdm.get("error")},
		"bond_filter": bond_filter,
		"overall_bias": overall,
	})


# ---------------------------------------------------------------------------
# Command: recheck (position management)
# ---------------------------------------------------------------------------

@safe_run
def cmd_recheck(args):
	"""Position management — exit signal evaluation for held positions.

	Evaluates time-in-trade, Williams %R dual timeframe exit, swing violation,
	dollar stop, and bailout opportunity. Supports both LONG and SHORT positions
	via --direction argument.
	"""
	symbol = args.symbol.upper()
	direction = getattr(args, "direction", "long")
	is_short = direction == "short"
	missing_components = []

	# Parse entry date
	try:
		entry_date = datetime.datetime.strptime(args.entry_date, "%Y-%m-%d").date()
	except (ValueError, TypeError):
		entry_date = datetime.date.today()

	entry_price = args.entry_price
	entry_stop = args.entry_stop

	# Parallel module calls (add pattern_scan for short cover detection)
	scripts = {
		"williams_r": ("technical/williams_r.py", ["calculate", symbol, "--period", "14"]),
		"range_analysis": ("technical/range_analysis.py", ["analyze", symbol]),
		"swing_short": ("technical/swing_points.py", ["detect", symbol, "--level", "short"]),
		"volatility_breakout": ("technical/atr_breakout.py", ["breakout", symbol]),
		"tdw_tdm": ("technical/calendar_bias.py", ["today"]),
	}
	if is_short:
		scripts["pattern_scan"] = ("technical/bar_patterns.py", ["scan", symbol, "--lookback", "5"])

	with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
		futures = {name: executor.submit(_run_script, path, a) for name, (path, a) in scripts.items()}
		results = {name: future.result() for name, future in futures.items()}

	for name, data in results.items():
		if data.get("error"):
			missing_components.append(name)

	# Current price from volatility breakout
	current_price = None
	vb = results["volatility_breakout"]
	if not vb.get("error"):
		current_price = vb.get("current_price")
	if current_price is None:
		wr = results["williams_r"]
		if not wr.get("error"):
			current_price = entry_price  # fallback

	if current_price is None:
		current_price = entry_price

	# Days held
	today = datetime.date.today()
	days_held = (today - entry_date).days

	# Unrealized P&L (inverted for shorts: profit when price drops)
	if is_short:
		unrealized_pnl_pct = round((entry_price - current_price) / entry_price * 100, 2) if entry_price > 0 else 0
	else:
		unrealized_pnl_pct = round((current_price - entry_price) / entry_price * 100, 2) if entry_price > 0 else 0

	# Current stop from volatility breakout ATR
	current_stop = entry_stop
	if not vb.get("error") and vb.get("atr_3day"):
		if is_short:
			# SHORT stop is ABOVE entry: price rising = loss
			atr_stop = round(current_price + vb["atr_3day"], 2)
			if current_stop is None or atr_stop < current_stop:
				current_stop = atr_stop
		else:
			atr_stop = round(current_price - vb["atr_3day"], 2)
			if current_stop is None or atr_stop > current_stop:
				current_stop = atr_stop

	if current_stop is None and not vb.get("error"):
		atr_val = vb.get("atr_3day", current_price * 0.02)
		if is_short:
			current_stop = round(current_price + atr_val, 2)
		else:
			current_stop = round(current_price - atr_val, 2)

	# --- Evaluate exit signals ---
	exit_signals = []
	today_open = None
	if not vb.get("error"):
		today_open = vb.get("open")

	if is_short:
		# === SHORT position exit signals ===

		# 1. BAILOUT: first profitable open (open < entry for shorts)
		first_profitable_open = False
		if today_open and entry_price and today_open < entry_price and days_held >= 1:
			first_profitable_open = True

		bailout_triggered = (first_profitable_open or
			(current_price < entry_price and days_held >= 1))
		exit_signals.append({
			"code": "BAILOUT_OPPORTUNITY",
			"triggered": bailout_triggered,
			"detail": (f"First profitable open: {today_open} < entry {entry_price} (short profit)" if first_profitable_open
				else f"Current {current_price} vs entry {entry_price}, held {days_held} days" if bailout_triggered
				else f"No profit yet (current {current_price} vs entry {entry_price})"),
		})

		# 2. TIME_STOP
		time_stop = days_held > 5
		exit_signals.append({
			"code": "TIME_STOP",
			"triggered": time_stop,
			"detail": f"Held {days_held} days — exceeds 5-day optimal window" if time_stop
			else f"Within window ({days_held}/5 days)",
		})

		# 3. DOLLAR_STOP_HIT: price rises above stop (short stop is above)
		stop_hit = False
		if current_stop is not None:
			stop_hit = current_price >= current_stop
		exit_signals.append({
			"code": "DOLLAR_STOP_HIT",
			"triggered": stop_hit,
			"detail": f"Price {current_price} hit stop {current_stop} (above stop)" if stop_hit
			else f"Price {current_price} below stop {current_stop}",
		})

		# 4. WR_OVERSOLD_EXIT: Williams %R < -80 → cover short (momentum exhausted)
		wr_exit = False
		wr_data = results["williams_r"]
		if not wr_data.get("error"):
			wr_val = wr_data.get("current_wr", -50)
			wr_exit = wr_val < -80
			exit_signals.append({
				"code": "WR_OVERSOLD_EXIT",
				"triggered": wr_exit,
				"detail": f"Williams %R = {wr_val} (oversold — cover short)" if wr_exit
				else f"Williams %R = {wr_val} (not oversold)",
			})
		else:
			exit_signals.append({
				"code": "WR_OVERSOLD_EXIT",
				"triggered": False,
				"detail": "Williams %R unavailable",
			})

		# 5. SWING_VIOLATION: price above recent short-term swing high (for shorts)
		swing_violated = False
		swing_data = results["swing_short"]
		if not swing_data.get("error"):
			last_high = swing_data.get("last_swing_high", {})
			if last_high and last_high.get("price"):
				swing_violated = current_price > last_high["price"]
				exit_signals.append({
					"code": "SWING_VIOLATION",
					"triggered": swing_violated,
					"detail": f"Price {current_price} above swing high {last_high['price']} (short violated)" if swing_violated
					else f"Price {current_price} below swing high {last_high['price']}",
				})
		else:
			exit_signals.append({
				"code": "SWING_VIOLATION",
				"triggered": False,
				"detail": "Swing data unavailable",
			})

		# 6. REVERSE_SIGNAL: buy breakout while holding short → EXIT_REVERSE
		reverse_signal = False
		reverse_direction = None
		if not vb.get("error"):
			active_signal = vb.get("active_signal", "none")
			breakout_triggered = vb.get("breakout_triggered", False)
			if breakout_triggered and active_signal == "buy":
				reverse_signal = True
				reverse_direction = "buy"
		exit_signals.append({
			"code": "REVERSE_SIGNAL",
			"triggered": reverse_signal,
			"detail": (f"Opposite breakout signal: {reverse_direction} — cover and reverse" if reverse_signal
				else "No opposing breakout signal"),
		})

		# 7. COVER_SIGNAL: bullish pattern detected → suggest cover
		cover_signal = False
		pattern_data = results.get("pattern_scan", {})
		if not pattern_data.get("error"):
			bullish_patterns = [
				p for p in pattern_data.get("patterns_detected", [])
				if p.get("direction") == "bullish"
			]
			cover_signal = len(bullish_patterns) > 0
		exit_signals.append({
			"code": "COVER_SIGNAL",
			"triggered": cover_signal,
			"detail": ("Bullish pattern detected — consider covering short" if cover_signal
				else "No bullish cover patterns"),
		})

		# --- SHORT verdict ---
		if reverse_signal:
			verdict = "EXIT_REVERSE"
			verdict_reason = f"Volatility breakout generated BUY signal while holding short. Cover and reverse per Williams Ch.11."
		elif stop_hit:
			verdict = "EXIT_STOP"
			verdict_reason = f"Dollar stop hit at {current_stop}. Cover short immediately."
		elif swing_violated:
			verdict = "EXIT_STOP"
			verdict_reason = "Short-term swing high violated. Uptrend structure confirmed — cover short."
		elif time_stop and unrealized_pnl_pct <= 1.0:
			verdict = "EXIT_TIME"
			verdict_reason = f"Held {days_held} days with {unrealized_pnl_pct}% gain. Condition has evaporated."
		elif first_profitable_open:
			verdict = "EXIT_BAILOUT"
			verdict_reason = f"First profitable opening at {today_open} (entry {entry_price}). Williams bailout — cover short."
		elif cover_signal and bailout_triggered:
			verdict = "COVER"
			verdict_reason = f"Bullish pattern detected + profitable ({unrealized_pnl_pct}%). Cover short position."
		elif bailout_triggered and wr_exit:
			verdict = "COVER"
			verdict_reason = f"Profitable ({unrealized_pnl_pct}%) + Williams %R oversold. Downside exhausted — cover."
		elif bailout_triggered and days_held >= 3:
			verdict = "HOLD"
			verdict_reason = f"Profitable ({unrealized_pnl_pct}%), within optimal 2-5 day window. Consider covering."
		else:
			verdict = "HOLD"
			verdict_reason = f"Within optimal window ({days_held} days), no exit signals triggered."

	else:
		# === LONG position exit signals (original logic) ===

		# 1. FIRST_PROFITABLE_OPEN bailout
		first_profitable_open = False
		if today_open and entry_price and today_open > entry_price and days_held >= 1:
			first_profitable_open = True

		bailout_triggered = (first_profitable_open or
			(current_price > entry_price and days_held >= 1))
		exit_signals.append({
			"code": "BAILOUT_OPPORTUNITY",
			"triggered": bailout_triggered,
			"detail": (f"First profitable open: {today_open} > entry {entry_price}" if first_profitable_open
				else f"Current {current_price} vs entry {entry_price}, held {days_held} days" if bailout_triggered
				else f"No profit yet (current {current_price} vs entry {entry_price})"),
		})

		# 2. TIME_STOP
		time_stop = days_held > 5
		exit_signals.append({
			"code": "TIME_STOP",
			"triggered": time_stop,
			"detail": f"Held {days_held} days — exceeds 5-day optimal window" if time_stop
			else f"Within window ({days_held}/5 days)",
		})

		# 3. DOLLAR_STOP_HIT
		stop_hit = False
		if current_stop is not None:
			stop_hit = current_price <= current_stop
		exit_signals.append({
			"code": "DOLLAR_STOP_HIT",
			"triggered": stop_hit,
			"detail": f"Price {current_price} hit stop {current_stop}" if stop_hit
			else f"Price {current_price} above stop {current_stop}",
		})

		# 4. WR_OVERBOUGHT_EXIT
		wr_exit = False
		wr_data = results["williams_r"]
		if not wr_data.get("error"):
			wr_val = wr_data.get("current_wr", -50)
			wr_exit = wr_val > -20
			exit_signals.append({
				"code": "WR_OVERBOUGHT_EXIT",
				"triggered": wr_exit,
				"detail": f"Williams %R = {wr_val} (overbought zone)" if wr_exit
				else f"Williams %R = {wr_val} (not overbought)",
			})
		else:
			exit_signals.append({
				"code": "WR_OVERBOUGHT_EXIT",
				"triggered": False,
				"detail": "Williams %R unavailable",
			})

		# 5. SWING_VIOLATION
		swing_violated = False
		swing_data = results["swing_short"]
		if not swing_data.get("error"):
			last_low = swing_data.get("last_swing_low", {})
			if last_low and last_low.get("price"):
				swing_violated = current_price < last_low["price"]
				exit_signals.append({
					"code": "SWING_VIOLATION",
					"triggered": swing_violated,
					"detail": f"Price {current_price} below swing low {last_low['price']}" if swing_violated
					else f"Price {current_price} above swing low {last_low['price']}",
				})
		else:
			exit_signals.append({
				"code": "SWING_VIOLATION",
				"triggered": False,
				"detail": "Swing data unavailable",
			})

		# 6. REVERSE_SIGNAL
		reverse_signal = False
		reverse_direction = None
		if not vb.get("error"):
			active_signal = vb.get("active_signal", "none")
			breakout_triggered = vb.get("breakout_triggered", False)
			if breakout_triggered and active_signal == "sell":
				reverse_signal = True
				reverse_direction = "sell"
		exit_signals.append({
			"code": "REVERSE_SIGNAL",
			"triggered": reverse_signal,
			"detail": (f"Opposite breakout signal: {reverse_direction} — exit and reverse" if reverse_signal
				else "No opposing breakout signal"),
		})

		cover_signal = False

		# --- LONG verdict ---
		if reverse_signal:
			verdict = "EXIT_REVERSE"
			verdict_reason = f"Volatility breakout generated opposite ({reverse_direction}) signal. Exit and reverse per Williams Ch.11."
		elif stop_hit:
			verdict = "EXIT_STOP"
			verdict_reason = f"Dollar stop hit at {current_stop}. Exit immediately."
		elif swing_violated:
			verdict = "EXIT_STOP"
			verdict_reason = "Short-term swing low violated. Trend structure broken."
		elif time_stop and unrealized_pnl_pct <= 1.0:
			verdict = "EXIT_TIME"
			verdict_reason = f"Held {days_held} days with {unrealized_pnl_pct}% gain. Condition has evaporated."
		elif first_profitable_open:
			verdict = "EXIT_BAILOUT"
			verdict_reason = f"First profitable opening at {today_open} (entry {entry_price}). Williams bailout rule triggered."
		elif bailout_triggered and wr_exit:
			verdict = "EXIT_BAILOUT"
			verdict_reason = f"Profitable ({unrealized_pnl_pct}%) + Williams %R overbought. Take profit."
		elif bailout_triggered and days_held >= 3:
			verdict = "HOLD"
			verdict_reason = f"Profitable ({unrealized_pnl_pct}%), within optimal 2-5 day window. Consider bailout."
		else:
			verdict = "HOLD"
			verdict_reason = f"Within optimal window ({days_held} days), no exit signals triggered."

	# Range phase
	range_phase = "unknown"
	ra = results["range_analysis"]
	if not ra.get("error"):
		range_phase = ra.get("phase", "unknown")

	# Swing status
	swing_status = {}
	if not swing_data.get("error"):
		swing_status = {
			"trend": swing_data.get("current_trend"),
			"last_low": swing_data.get("last_swing_low"),
			"last_high": swing_data.get("last_swing_high"),
		}

	output_json({
		"symbol": symbol,
		"direction": direction,
		"entry_price": entry_price,
		"current_price": current_price,
		"days_held": days_held,
		"unrealized_pnl_pct": unrealized_pnl_pct,
		"exit_signals": exit_signals,
		"verdict": verdict,
		"verdict_reason": verdict_reason,
		"bailout_triggered": bailout_triggered,
		"first_profitable_open": first_profitable_open,
		"reverse_signal": reverse_signal,
		"current_stop": current_stop,
		"williams_r": _compress_williams_r(wr_data),
		"range_phase": range_phase,
		"swing_status": swing_status,
		"missing_components": missing_components,
	})


# ---------------------------------------------------------------------------
# Main dispatch
# ---------------------------------------------------------------------------

def main():
	parser = argparse.ArgumentParser(
		description="Williams Pipeline (Pipeline-Complete): Short-Term Volatility Breakout Analysis"
	)
	sub = parser.add_subparsers(dest="command", required=True)

	# trade-setup
	sp = sub.add_parser("trade-setup", help="Composite trade qualification for a ticker")
	sp.add_argument("symbol", help="Ticker symbol")
	sp.add_argument("--risk-pct", type=float, default=3.0, help="Risk %% per trade (default: 3.0)")
	sp.add_argument("--account-size", type=float, default=100000, help="Account size (default: 100000)")
	sp.set_defaults(func=cmd_trade_setup)

	# analyze
	sp = sub.add_parser("analyze", help="Full deep analysis for a ticker")
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

	# recheck
	sp = sub.add_parser("recheck", help="Position management: exit signal evaluation")
	sp.add_argument("symbol", help="Ticker symbol")
	sp.add_argument("--entry-price", type=float, required=True, help="Original entry price")
	sp.add_argument("--entry-date", type=str, required=True, help="Entry date (YYYY-MM-DD)")
	sp.add_argument("--entry-stop", type=float, default=None, help="Entry stop price (optional)")
	sp.add_argument("--direction", type=str, default="long", choices=["long", "short"],
		help="Position direction: long or short (default: long)")
	sp.set_defaults(func=cmd_recheck)

	args = parser.parse_args()
	args.func(args)


if __name__ == "__main__":
	main()
