#!/usr/bin/env python3
"""Larry Williams Short-Term Trading Tools: volatility breakouts, range analysis, swing identification, chart pattern detection, and composite trade setup.

Implements Larry Williams' core short-term trading techniques from
"Long-Term Secrets to Short-Term Trading." Includes Williams %R oscillator,
volatility breakout signals (his primary entry system), daily range
expansion/contraction analysis, mechanical swing point identification,
chart pattern detection (5 reversal patterns), and a composite trade setup
that runs all five filters (TDW, TDM, bond trend, 20-day MA, patterns)
to produce a single conviction score with position sizing.

Williams' central thesis: trends are set in motion by "explosions of price
activity" — when volatility expands beyond recent proportion, the trend
continues until an equal or greater explosion occurs in the opposite
direction. The volatility breakout entry, filtered by Trading Day of Week
and trend confirmation, is the most consistently profitable mechanical
entry technique he has found across decades of trading.

Commands:
	williams_r: Williams %R oscillator calculation with overbought/oversold signals
	volatility_breakout: Volatility breakout buy/sell signals (Williams' core entry system)
	range_analysis: Daily range expansion/contraction analysis with True Range
	swing_points: Mechanical swing high/low identification and trend direction
	pattern_scan: Detect Williams chart patterns (outside day, smash day, Oops!, specialists' trap)
	trade_setup: Composite trade setup running all 5 filters with conviction scoring and position sizing

Args:
	ticker (str): Ticker symbol (e.g., "AAPL", "NVDA", "SPY")
	--period (int): Williams %R lookback period in days (default: 14)
	--lookback (int): Historical data lookback in trading days (default: 60)
	--multiplier (float): Volatility breakout multiplier (default: 1.0)
	--window (int): Swing point identification window in bars (default: 5)
	--bond-ticker (str): Bond ETF ticker for intermarket filter in trade_setup (default: "TLT")
	--account (float): Account balance for position sizing in trade_setup (optional)

Returns:
	For williams_r:
	dict: {
		"symbol": str,
		"date": str,
		"current_price": float,
		"period": int,
		"lookback_days": int,
		"latest": {
			"williams_r": float,
			"zone": str,
			"close": float
		},
		"history": [
			{
				"date": str,
				"close": float,
				"williams_r": float,
				"zone": str
			}
		],
		"summary": {
			"current_zone": str,
			"days_in_current_zone": int,
			"overbought_pct": float,
			"oversold_pct": float,
			"neutral_pct": float,
			"mean_r": float
		}
	}

	For volatility_breakout:
	dict: {
		"symbol": str,
		"date": str,
		"current_price": float,
		"multiplier": float,
		"lookback_days": int,
		"next_session": {
			"buy_level": float,
			"sell_level": float,
			"reference_close": float,
			"true_range": float,
			"atr_3": float
		},
		"recent_signals": [
			{
				"date": str,
				"signal": str,
				"entry_level": float,
				"close": float,
				"result_pct": float
			}
		],
		"summary": {
			"total_signals": int,
			"buy_signals": int,
			"sell_signals": int,
			"avg_true_range": float,
			"current_range_vs_avg": float
		}
	}

	For range_analysis:
	dict: {
		"symbol": str,
		"date": str,
		"current_price": float,
		"period": int,
		"latest": {
			"true_range": float,
			"true_range_pct": float,
			"avg_true_range": float,
			"range_ratio": float,
			"phase": str
		},
		"history": [
			{
				"date": str,
				"true_range": float,
				"true_range_pct": float,
				"range_ratio": float,
				"phase": str
			}
		],
		"summary": {
			"current_phase": str,
			"expansion_days": int,
			"contraction_days": int,
			"normal_days": int,
			"avg_true_range": float,
			"max_true_range": float,
			"min_true_range": float,
			"current_percentile": float
		}
	}

	For swing_points:
	dict: {
		"symbol": str,
		"date": str,
		"current_price": float,
		"window": int,
		"lookback_days": int,
		"swing_highs": [
			{
				"date": str,
				"price": float,
				"level": str
			}
		],
		"swing_lows": [
			{
				"date": str,
				"price": float,
				"level": str
			}
		],
		"trend": {
			"short_term": str,
			"intermediate": str,
			"last_swing_high": float,
			"last_swing_low": float,
			"current_position": str
		}
	}

	For pattern_scan:
	dict: {
		"symbol": str,
		"date": str,
		"current_price": float,
		"lookback_days": int,
		"patterns_detected": [
			{
				"date": str,
				"pattern": str,
				"direction": str,
				"details": dict,
				"entry_level": float,
				"signal_status": str,
				"trigger_date": str or null
			}
		],
		"active_setups": [filtered list of active/triggered patterns],
		"summary": {
			"total_patterns": int,
			"active_setups": int,
			"pattern_counts": dict
		}
	}

	For trade_setup:
	dict: {
		"symbol": str,
		"date": str,
		"current_price": float,
		"filters": {
			"tdw": {"favorable": bool, "bias": str, "score": int, "day": str, "prev_close": str},
			"tdm": {"favorable": bool, "bias": str, "score": int, "trading_day": int},
			"bond": {"favorable": bool, "status": str, "current": float, "five_days_ago": float, "change_pct": float},
			"ma20": {"favorable": bool, "trend": str, "ma20": float, "prev_ma20": float, "price_vs_ma": str},
			"pattern": {"favorable": bool, "active_count": int, "bullish_count": int, "patterns": list}
		},
		"alignment": {
			"favorable_count": int,
			"total_filters": 5,
			"conviction": str,
			"risk_pct": float
		},
		"williams_r": {"williams_r": float, "zone": str, "close": float},
		"breakout_levels": {"buy_level": float, "sell_level": float, "reference_close": float, "true_range": float, "atr_3": float},
		"range_phase": str,
		"recent_patterns": list,
		"position_sizing": dict or null
	}

Example:
	>>> python williams.py williams_r AAPL --period 14 --lookback 60
	{
		"symbol": "AAPL",
		"date": "2026-02-20",
		"current_price": 245.50,
		"period": 14,
		"latest": {
			"williams_r": -25.3,
			"zone": "overbought",
			"close": 245.50
		},
		"summary": {
			"current_zone": "overbought",
			"days_in_current_zone": 3,
			"overbought_pct": 28.3,
			"oversold_pct": 15.0,
			"neutral_pct": 56.7,
			"mean_r": -48.2
		}
	}

	>>> python williams.py volatility_breakout SPY --multiplier 0.6 --lookback 60
	{
		"symbol": "SPY",
		"date": "2026-02-20",
		"current_price": 502.30,
		"multiplier": 0.6,
		"next_session": {
			"buy_level": 505.12,
			"sell_level": 499.48,
			"reference_close": 502.30,
			"true_range": 4.70,
			"atr_3": 4.82
		}
	}

	>>> python williams.py pattern_scan SPY --lookback 60
	{
		"symbol": "SPY",
		"date": "2026-02-20",
		"current_price": 502.30,
		"lookback_days": 60,
		"active_setups": [
			{"date": "2026-02-19", "pattern": "smash_day_naked", "direction": "bullish",
			 "signal_status": "active"}
		],
		"summary": {"total_patterns": 12, "active_setups": 1}
	}

	>>> python williams.py trade_setup AAPL --multiplier 0.8 --account 100000
	{
		"symbol": "AAPL",
		"date": "2026-02-20",
		"current_price": 245.50,
		"alignment": {
			"favorable_count": 4,
			"total_filters": 5,
			"conviction": "very_high",
			"risk_pct": 4.0
		},
		"breakout_levels": {"buy_level": 248.12, "sell_level": 242.88},
		"position_sizing": {"account": 100000, "risk_pct": 4.0, "shares": 553}
	}

Use Cases:
	- Generate daily volatility breakout entry levels for next-session trading
	- Identify overbought/oversold conditions with Williams %R for timing entries
	- Detect range expansion phases that signal new trend legs forming
	- Map mechanical swing highs/lows to determine market structure and trend
	- Combine range analysis with breakout signals for conviction filtering
	- Scan for Williams reversal patterns (outside day, smash day, Oops!, specialists' trap)
	- Run composite trade setup with all 5 filters for conviction-based entry decisions
	- Calculate position size based on conviction level and account balance

Notes:
	- Williams %R scale: -100 (extreme oversold) to 0 (extreme overbought)
	- Overbought zone: %R > -20; Oversold zone: %R < -80; Neutral: between
	- Volatility breakout formula: Entry = Close + (multiplier x ATR(3))
	- True Range = max(H-L, |H-prevClose|, |L-prevClose|)
	- Range ratio > 1.5 = expansion (trending); ratio < 0.5 = contraction
	- Swing points use Williams' nested structure: short -> intermediate -> long
	- TDW score: -2 to +2; favorable when score > 0
	- TDM score: -1 to +2; favorable when score > 0
	- Conviction levels: 0-1 filters = low (0%), 2 = moderate (2%), 3 = high (3%), 4-5 = very_high (4%)
	- Pattern types: outside_day_down_close, smash_day_naked, smash_day_hidden, oops_gap_reversal, specialists_trap
	- Signal status: "active" (within trigger window), "triggered" (entry confirmed), "expired" (window passed)

See Also:
	- closing_range.py: Bar classification for institutional accumulation signals
	- volume_edge.py: Volume edge detection for breakout confirmation
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import yfinance as yf
from utils import output_json, safe_run


# ── TDW / TDM Lookup Tables ─────────────────────────────────────────────────
# Williams' Trading Day of Week bias based on decades of research.
# Key: (weekday_name, previous_close_direction) → {"bias": str, "score": int}
TDW_BIAS = {
	("Monday", "down"):    {"bias": "strong_bullish", "score": 2},
	("Monday", "up"):      {"bias": "bullish",        "score": 1},
	("Tuesday", "down"):   {"bias": "bullish",        "score": 1},
	("Tuesday", "up"):     {"bias": "neutral",        "score": 0},
	("Wednesday", "down"): {"bias": "avoid",          "score": -1},
	("Wednesday", "up"):   {"bias": "bullish",        "score": 1},
	("Thursday", "down"):  {"bias": "bullish",        "score": 1},
	("Thursday", "up"):    {"bias": "bullish",        "score": 1},
	("Friday", "down"):    {"bias": "bullish",        "score": 1},
	("Friday", "up"):      {"bias": "avoid",          "score": -1},
}

# Williams' Trading Day of Month bias.
# Key: trading_day_number (1-22) → {"bias": str, "score": int}
TDM_BIAS = {
	1:  {"bias": "strong_buy", "score": 2},
	2:  {"bias": "strong_buy", "score": 2},
	3:  {"bias": "strong_buy", "score": 2},
	4:  {"bias": "strong_buy", "score": 2},
	5:  {"bias": "weak",       "score": -1},
	6:  {"bias": "weak",       "score": -1},
	7:  {"bias": "weak",       "score": -1},
	8:  {"bias": "buy",        "score": 1},
	9:  {"bias": "neutral",    "score": 0},
	10: {"bias": "neutral",    "score": 0},
	11: {"bias": "neutral",    "score": 0},
	12: {"bias": "weak",       "score": -1},
	13: {"bias": "weak",       "score": -1},
	14: {"bias": "neutral",    "score": 0},
	15: {"bias": "neutral",    "score": 0},
	16: {"bias": "neutral",    "score": 0},
	17: {"bias": "neutral",    "score": 0},
	18: {"bias": "strong_buy", "score": 2},
	19: {"bias": "strong_buy", "score": 2},
	20: {"bias": "strong_buy", "score": 2},
	21: {"bias": "strong_buy", "score": 2},
	22: {"bias": "strong_buy", "score": 2},
}


# ── Small Helpers ────────────────────────────────────────────────────────────

def _true_range(high, low, prev_close):
	"""Calculate True Range: max(H-L, |H-prevC|, |L-prevC|)."""
	return max(high - low, abs(high - prev_close), abs(low - prev_close))


def _classify_wr_zone(wr):
	"""Classify Williams %R value into overbought/oversold/neutral."""
	if wr > -20:
		return "overbought"
	if wr < -80:
		return "oversold"
	return "neutral"


# ── Data Helpers ─────────────────────────────────────────────────────────────

def _fetch_data(symbol, days):
	"""Fetch OHLCV data via yfinance. Returns DataFrame or None if empty."""
	ticker = yf.Ticker(symbol)
	data = ticker.history(period=f"{days}d", interval="1d")
	if data.empty:
		return None
	return data


def _get_trading_day_of_month(target_date, all_dates):
	"""Return 1-based trading day of month for target_date within all_dates."""
	def _d(x):
		return x.date() if hasattr(x, "date") and callable(x.date) else x

	target = _d(target_date)
	same_month = sorted(set(
		_d(d) for d in all_dates
		if _d(d).month == target.month and _d(d).year == target.year
	))
	try:
		return same_month.index(target) + 1
	except ValueError:
		return None


# ── Calculation Helpers ──────────────────────────────────────────────────────

def _calculate_wr(data, period, lookback):
	"""Calculate Williams %R values from price data.

	Returns dict with latest, history, summary, or None if insufficient data.
	"""
	if len(data) < period + 5:
		return None

	highs = data["High"]
	lows = data["Low"]
	closes = data["Close"]

	results = []
	start_idx = max(period, len(data) - lookback)
	for i in range(start_idx, len(data)):
		highest_high = float(highs.iloc[i - period + 1:i + 1].max())
		lowest_low = float(lows.iloc[i - period + 1:i + 1].min())
		close = float(closes.iloc[i])

		if highest_high == lowest_low:
			wr = -50.0
		else:
			wr = round((highest_high - close) / (highest_high - lowest_low) * -100, 1)

		zone = _classify_wr_zone(wr)
		results.append({
			"date": str(data.index[i].date()),
			"close": round(close, 2),
			"williams_r": wr,
			"zone": zone,
		})

	if not results:
		return None

	latest = results[-1]

	days_in_zone = 0
	for r in reversed(results):
		if r["zone"] == latest["zone"]:
			days_in_zone += 1
		else:
			break

	total = len(results)
	overbought_count = sum(1 for r in results if r["zone"] == "overbought")
	oversold_count = sum(1 for r in results if r["zone"] == "oversold")
	neutral_count = total - overbought_count - oversold_count
	mean_r = round(sum(r["williams_r"] for r in results) / total, 1)

	return {
		"latest": latest,
		"history": results,
		"summary": {
			"current_zone": latest["zone"],
			"days_in_current_zone": days_in_zone,
			"overbought_pct": round(overbought_count / total * 100, 1),
			"oversold_pct": round(oversold_count / total * 100, 1),
			"neutral_pct": round(neutral_count / total * 100, 1),
			"mean_r": mean_r,
		},
	}


def _calculate_breakout_levels(data, multiplier, lookback):
	"""Calculate volatility breakout levels and signals from price data.

	Returns dict with next_session, recent_signals, summary, lookback_tr_count,
	or None if insufficient data.
	"""
	if len(data) < 10:
		return None

	highs = data["High"]
	lows = data["Low"]
	closes = data["Close"]
	opens = data["Open"]

	# Calculate True Range series
	tr_list = []
	for i in range(1, len(data)):
		h = float(highs.iloc[i])
		l = float(lows.iloc[i])
		pc = float(closes.iloc[i - 1])
		tr_list.append(_true_range(h, l, pc))

	# Generate breakout signals for lookback period
	signals = []
	start_idx = max(4, len(data) - lookback)
	for i in range(start_idx, len(data)):
		tr_idx = i - 1  # tr_list is offset by 1
		if tr_idx < 3:
			continue

		# ATR of past 3 days
		atr3 = sum(tr_list[tr_idx - 2:tr_idx + 1]) / 3
		prev_close = float(closes.iloc[i - 1])
		close_price = float(closes.iloc[i])
		high_price = float(highs.iloc[i])
		low_price = float(lows.iloc[i])

		buy_level = round(prev_close + multiplier * atr3, 2)
		sell_level = round(prev_close - multiplier * atr3, 2)

		signal = None
		entry_level = None
		if high_price >= buy_level:
			signal = "buy"
			entry_level = buy_level
		elif low_price <= sell_level:
			signal = "sell"
			entry_level = sell_level

		if signal:
			if signal == "buy":
				result_pct = round((close_price - entry_level) / entry_level * 100, 2)
			else:
				result_pct = round((entry_level - close_price) / entry_level * 100, 2)

			signals.append({
				"date": str(data.index[i].date()),
				"signal": signal,
				"entry_level": entry_level,
				"close": round(close_price, 2),
				"result_pct": result_pct,
			})

	# Next session levels
	last_tr_idx = len(tr_list) - 1
	if last_tr_idx >= 2:
		next_atr3 = sum(tr_list[last_tr_idx - 2:last_tr_idx + 1]) / 3
	else:
		next_atr3 = tr_list[-1] if tr_list else 0

	last_close = round(float(closes.iloc[-1]), 2)
	last_tr = round(tr_list[-1], 2) if tr_list else 0

	# Summary stats
	total_tr = tr_list[max(0, len(tr_list) - lookback):]
	avg_tr = round(sum(total_tr) / len(total_tr), 2) if total_tr else 0
	current_range_vs_avg = round(last_tr / avg_tr, 2) if avg_tr > 0 else 0

	buy_signals = sum(1 for s in signals if s["signal"] == "buy")
	sell_signals = sum(1 for s in signals if s["signal"] == "sell")

	return {
		"lookback_tr_count": len(total_tr),
		"next_session": {
			"buy_level": round(last_close + multiplier * next_atr3, 2),
			"sell_level": round(last_close - multiplier * next_atr3, 2),
			"reference_close": last_close,
			"true_range": last_tr,
			"atr_3": round(next_atr3, 2),
		},
		"recent_signals": signals[-20:],
		"summary": {
			"total_signals": len(signals),
			"buy_signals": buy_signals,
			"sell_signals": sell_signals,
			"avg_true_range": avg_tr,
			"current_range_vs_avg": current_range_vs_avg,
		},
	}


def _calculate_range_phase(data, period):
	"""Calculate range expansion/contraction phase from price data.

	Returns dict with latest, history, summary, or None if insufficient data.
	"""
	if len(data) < period + 5:
		return None

	highs = data["High"]
	lows = data["Low"]
	closes = data["Close"]

	# Calculate True Range series
	tr_values = []
	for i in range(1, len(data)):
		h = float(highs.iloc[i])
		l = float(lows.iloc[i])
		pc = float(closes.iloc[i - 1])
		tr_values.append({
			"index": i,
			"date": str(data.index[i].date()),
			"true_range": round(_true_range(h, l, pc), 4),
			"close": round(float(closes.iloc[i]), 2),
		})

	# Compute rolling ATR and classify phases
	results = []
	for j, tr in enumerate(tr_values):
		if j < period:
			continue
		window = tr_values[j - period:j]
		atr = sum(w["true_range"] for w in window) / period
		tr_pct = round(tr["true_range"] / tr["close"] * 100, 2) if tr["close"] > 0 else 0
		ratio = round(tr["true_range"] / atr, 2) if atr > 0 else 0

		if ratio >= 1.5:
			phase = "expansion"
		elif ratio <= 0.5:
			phase = "contraction"
		else:
			phase = "normal"

		results.append({
			"date": tr["date"],
			"true_range": tr["true_range"],
			"true_range_pct": tr_pct,
			"avg_true_range": round(atr, 4),
			"range_ratio": ratio,
			"phase": phase,
		})

	if not results:
		return None

	latest = results[-1]

	# Percentile of current True Range
	all_tr = sorted(r["true_range"] for r in results)
	current_rank = sum(1 for t in all_tr if t <= latest["true_range"])
	current_percentile = round(current_rank / len(all_tr) * 100, 1)

	expansion_days = sum(1 for r in results if r["phase"] == "expansion")
	contraction_days = sum(1 for r in results if r["phase"] == "contraction")
	normal_days = len(results) - expansion_days - contraction_days

	return {
		"latest": latest,
		"history": results,
		"summary": {
			"current_phase": latest["phase"],
			"expansion_days": expansion_days,
			"contraction_days": contraction_days,
			"normal_days": normal_days,
			"avg_true_range": latest["avg_true_range"],
			"max_true_range": round(max(r["true_range"] for r in results), 4),
			"min_true_range": round(min(r["true_range"] for r in results), 4),
			"current_percentile": current_percentile,
		},
	}


# ── Pattern Detection Helpers ────────────────────────────────────────────────

def _pattern_signal_status(data, pattern_idx, entry_level, trigger_direction, window=3):
	"""Determine signal status for a detected pattern.

	Args:
		data: DataFrame with OHLC data
		pattern_idx: Index of the pattern bar in data
		entry_level: Price level that triggers the entry
		trigger_direction: "above" (high must reach level) or "below" (low must reach level)
		window: Number of subsequent bars to check (default 3)

	Returns:
		dict with "status" ("active"/"triggered"/"expired") and optionally "trigger_date"
	"""
	n = len(data)
	for j in range(pattern_idx + 1, min(pattern_idx + 1 + window, n)):
		if trigger_direction == "above" and float(data["High"].iloc[j]) >= entry_level:
			return {"status": "triggered", "trigger_date": str(data.index[j].date())}
		if trigger_direction == "below" and float(data["Low"].iloc[j]) <= entry_level:
			return {"status": "triggered", "trigger_date": str(data.index[j].date())}

	# Check if still within trigger window
	bars_since = n - 1 - pattern_idx
	if bars_since <= window:
		return {"status": "active", "trigger_date": None}

	return {"status": "expired", "trigger_date": None}


def _detect_specialists_trap(data, i):
	"""Detect specialists' trap at bar i: congestion -> false breakout -> reversal.

	Returns dict with direction, zone_high, zone_low, entry_level, breakout_type,
	or None if no trap detected.
	"""
	c = float(data["Close"].iloc[i])

	for cong_len in range(5, 11):
		total_needed = cong_len + 3
		if i < total_needed:
			continue

		# Congestion zone: bars before the breakout attempt
		cong_start = i - total_needed
		cong_end = i - 3

		zone_highs = [float(data["High"].iloc[j]) for j in range(cong_start, cong_end)]
		zone_lows = [float(data["Low"].iloc[j]) for j in range(cong_start, cong_end)]

		zone_high = max(zone_highs)
		zone_low = min(zone_lows)
		zone_range = zone_high - zone_low

		# Check congestion tightness: zone range < 3x average daily range
		avg_daily = sum(
			float(data["High"].iloc[j]) - float(data["Low"].iloc[j])
			for j in range(cong_start, cong_end)
		) / cong_len

		if avg_daily <= 0 or zone_range > avg_daily * 3:
			continue

		# Check for breakout in bars [i-3, i), then reversal at bar i
		broke_up = False
		broke_down = False
		for j in range(i - 3, i):
			if j < 0:
				continue
			if float(data["High"].iloc[j]) > zone_high * 1.001:
				broke_up = True
			if float(data["Low"].iloc[j]) < zone_low * 0.999:
				broke_down = True

		# False upside breakout (upthrust) -> bearish signal
		if broke_up and not broke_down and c <= zone_high:
			return {
				"direction": "bearish",
				"zone_high": zone_high,
				"zone_low": zone_low,
				"entry_level": zone_low,
				"breakout_type": "false_upside",
			}

		# False downside breakout (spring) -> bullish signal
		if broke_down and not broke_up and c >= zone_low:
			return {
				"direction": "bullish",
				"zone_high": zone_high,
				"zone_low": zone_low,
				"entry_level": zone_high,
				"breakout_type": "false_downside",
			}

	return None


def _detect_patterns(data, lookback=60):
	"""Detect Williams chart patterns in price data.

	Scans for 5 pattern types:
	- Outside Day with Down Close (bullish reversal)
	- Smash Day Naked (both directions)
	- Smash Day Hidden (both directions)
	- Oops! Gap Reversal (bullish)
	- Specialists' Trap (both directions)

	Returns list of detected pattern dicts.
	"""
	patterns = []
	n = len(data)
	scan_start = max(1, n - lookback)

	highs = data["High"]
	lows = data["Low"]
	closes = data["Close"]
	opens = data["Open"]

	for i in range(scan_start, n):
		h = float(highs.iloc[i])
		l = float(lows.iloc[i])
		c = float(closes.iloc[i])
		o = float(opens.iloc[i])
		date_str = str(data.index[i].date())

		if i < 1:
			continue

		ph = float(highs.iloc[i - 1])
		pl = float(lows.iloc[i - 1])
		pc = float(closes.iloc[i - 1])
		day_range = h - l

		# --- Outside Day with Down Close (bullish) ---
		if h > ph and l < pl and c < pl:
			entry_level = round(h, 2)
			status = _pattern_signal_status(data, i, entry_level, "above")
			patterns.append({
				"date": date_str,
				"pattern": "outside_day_down_close",
				"direction": "bullish",
				"details": {
					"high": round(h, 2), "low": round(l, 2), "close": round(c, 2),
					"prev_high": round(ph, 2), "prev_low": round(pl, 2),
				},
				"entry_level": entry_level,
				"signal_status": status["status"],
				"trigger_date": status.get("trigger_date"),
			})

		# --- Smash Day Naked ---
		# Bearish smash (close < prev low) -> bullish reversal signal
		if c < pl and not (h > ph and l < pl):
			# Exclude bars already captured as outside day down close
			entry_level = round(h, 2)
			status = _pattern_signal_status(data, i, entry_level, "above")
			patterns.append({
				"date": date_str,
				"pattern": "smash_day_naked",
				"direction": "bullish",
				"details": {
					"high": round(h, 2), "low": round(l, 2), "close": round(c, 2),
					"prev_low": round(pl, 2),
				},
				"entry_level": entry_level,
				"signal_status": status["status"],
				"trigger_date": status.get("trigger_date"),
			})
		# Bullish smash (close > prev high) -> bearish reversal signal
		if c > ph:
			entry_level = round(l, 2)
			status = _pattern_signal_status(data, i, entry_level, "below")
			patterns.append({
				"date": date_str,
				"pattern": "smash_day_naked",
				"direction": "bearish",
				"details": {
					"high": round(h, 2), "low": round(l, 2), "close": round(c, 2),
					"prev_high": round(ph, 2),
				},
				"entry_level": entry_level,
				"signal_status": status["status"],
				"trigger_date": status.get("trigger_date"),
			})

		# --- Smash Day Hidden ---
		if day_range > 0:
			close_position = (c - l) / day_range  # 0=at low, 1=at high
			# Hidden bullish: up close but close in lower 25% of range
			if c > pc and close_position < 0.25:
				entry_level = round(h, 2)
				status = _pattern_signal_status(data, i, entry_level, "above")
				patterns.append({
					"date": date_str,
					"pattern": "smash_day_hidden",
					"direction": "bullish",
					"details": {
						"high": round(h, 2), "low": round(l, 2), "close": round(c, 2),
						"close_position_pct": round(close_position * 100, 1),
					},
					"entry_level": entry_level,
					"signal_status": status["status"],
					"trigger_date": status.get("trigger_date"),
				})
			# Hidden bearish: down close but close in upper 75% of range
			if c < pc and close_position > 0.75:
				entry_level = round(l, 2)
				status = _pattern_signal_status(data, i, entry_level, "below")
				patterns.append({
					"date": date_str,
					"pattern": "smash_day_hidden",
					"direction": "bearish",
					"details": {
						"high": round(h, 2), "low": round(l, 2), "close": round(c, 2),
						"close_position_pct": round(close_position * 100, 1),
					},
					"entry_level": entry_level,
					"signal_status": status["status"],
					"trigger_date": status.get("trigger_date"),
				})

		# --- Oops! Gap Reversal (bullish) ---
		if o < pl and h >= pl:
			patterns.append({
				"date": date_str,
				"pattern": "oops_gap_reversal",
				"direction": "bullish",
				"details": {
					"open": round(o, 2), "high": round(h, 2), "low": round(l, 2),
					"close": round(c, 2), "prev_low": round(pl, 2),
				},
				"entry_level": round(pl, 2),
				"signal_status": "triggered",
				"trigger_date": date_str,
			})

		# --- Specialists' Trap ---
		if i >= 8:
			trap = _detect_specialists_trap(data, i)
			if trap:
				patterns.append({
					"date": date_str,
					"pattern": "specialists_trap",
					"direction": trap["direction"],
					"details": {
						"zone_high": round(trap["zone_high"], 2),
						"zone_low": round(trap["zone_low"], 2),
						"breakout_type": trap["breakout_type"],
					},
					"entry_level": round(trap["entry_level"], 2),
					"signal_status": "triggered",
					"trigger_date": date_str,
				})

	return patterns


# ── Command Functions ────────────────────────────────────────────────────────

@safe_run
def cmd_williams_r(args):
	"""Williams %R oscillator with overbought/oversold signal detection."""
	symbol = args.ticker.upper()
	period = args.period
	lookback = args.lookback

	fetch_days = lookback + period + 30
	data = _fetch_data(symbol, fetch_days)
	if data is None or len(data) < period + 5:
		output_json({
			"error": f"Insufficient data for {symbol}. Need at least {period + 5} trading days.",
			"data_points": len(data) if data is not None else 0,
		})
		return

	result = _calculate_wr(data, period, lookback)
	if result is None:
		output_json({"error": f"No Williams %R values could be computed for {symbol}."})
		return

	output_json({
		"symbol": symbol,
		"date": result["latest"]["date"],
		"current_price": result["latest"]["close"],
		"period": period,
		"lookback_days": len(result["history"]),
		"latest": {
			"williams_r": result["latest"]["williams_r"],
			"zone": result["latest"]["zone"],
			"close": result["latest"]["close"],
		},
		"history": result["history"],
		"summary": result["summary"],
	})


@safe_run
def cmd_volatility_breakout(args):
	"""Volatility breakout signals based on Williams' core entry system."""
	symbol = args.ticker.upper()
	lookback = args.lookback
	multiplier = args.multiplier

	fetch_days = lookback + 30
	data = _fetch_data(symbol, fetch_days)
	if data is None or len(data) < 10:
		output_json({
			"error": f"Insufficient data for {symbol}. Need at least 10 trading days.",
			"data_points": len(data) if data is not None else 0,
		})
		return

	result = _calculate_breakout_levels(data, multiplier, lookback)
	if result is None:
		output_json({"error": f"Could not compute breakout levels for {symbol}."})
		return

	output_json({
		"symbol": symbol,
		"date": str(data.index[-1].date()),
		"current_price": result["next_session"]["reference_close"],
		"multiplier": multiplier,
		"lookback_days": result["lookback_tr_count"],
		"next_session": result["next_session"],
		"recent_signals": result["recent_signals"],
		"summary": result["summary"],
	})


@safe_run
def cmd_range_analysis(args):
	"""Daily range expansion/contraction analysis with True Range."""
	symbol = args.ticker.upper()
	period = args.period

	fetch_days = period + 60
	data = _fetch_data(symbol, fetch_days)
	if data is None or len(data) < period + 5:
		output_json({
			"error": f"Insufficient data for {symbol}. Need at least {period + 5} trading days.",
			"data_points": len(data) if data is not None else 0,
		})
		return

	result = _calculate_range_phase(data, period)
	if result is None:
		output_json({"error": f"Could not compute range analysis for {symbol}."})
		return

	output_json({
		"symbol": symbol,
		"date": result["latest"]["date"],
		"current_price": round(float(data["Close"].iloc[-1]), 2),
		"period": period,
		"latest": {
			"true_range": result["latest"]["true_range"],
			"true_range_pct": result["latest"]["true_range_pct"],
			"avg_true_range": result["latest"]["avg_true_range"],
			"range_ratio": result["latest"]["range_ratio"],
			"phase": result["latest"]["phase"],
		},
		"history": result["history"],
		"summary": result["summary"],
	})


@safe_run
def cmd_swing_points(args):
	"""Swing high/low identification with trend direction analysis."""
	symbol = args.ticker.upper()
	window = args.window
	lookback = args.lookback

	fetch_days = lookback + 30
	data = _fetch_data(symbol, fetch_days)
	if data is None or len(data) < window * 3:
		output_json({
			"error": f"Insufficient data for {symbol}. Need at least {window * 3} trading days.",
			"data_points": len(data) if data is not None else 0,
		})
		return

	# Trim to lookback
	if len(data) > lookback:
		data = data.iloc[-lookback:]

	highs = data["High"]
	lows = data["Low"]
	closes = data["Close"]

	# Identify short-term swing highs: a day with lower highs on both sides
	swing_highs = []
	swing_lows = []

	for i in range(window, len(data) - window):
		h = float(highs.iloc[i])
		l = float(lows.iloc[i])

		# Check for swing high: all surrounding highs are lower
		is_high = True
		for j in range(1, window + 1):
			if float(highs.iloc[i - j]) >= h or float(highs.iloc[i + j]) >= h:
				is_high = False
				break

		if is_high:
			swing_highs.append({
				"date": str(data.index[i].date()),
				"price": round(h, 2),
				"index": i,
			})

		# Check for swing low: all surrounding lows are higher
		is_low = True
		for j in range(1, window + 1):
			if float(lows.iloc[i - j]) <= l or float(lows.iloc[i + j]) <= l:
				is_low = False
				break

		if is_low:
			swing_lows.append({
				"date": str(data.index[i].date()),
				"price": round(l, 2),
				"index": i,
			})

	# Classify intermediate-term swings
	for i, sh in enumerate(swing_highs):
		if i > 0 and i < len(swing_highs) - 1:
			if swing_highs[i - 1]["price"] < sh["price"] and swing_highs[i + 1]["price"] < sh["price"]:
				sh["level"] = "intermediate"
			else:
				sh["level"] = "short_term"
		else:
			sh["level"] = "short_term"

	for i, sl in enumerate(swing_lows):
		if i > 0 and i < len(swing_lows) - 1:
			if swing_lows[i - 1]["price"] > sl["price"] and swing_lows[i + 1]["price"] > sl["price"]:
				sl["level"] = "intermediate"
			else:
				sl["level"] = "short_term"
		else:
			sl["level"] = "short_term"

	# Determine trend from swing points
	current_price = round(float(closes.iloc[-1]), 2)

	st_trend = "neutral"
	if len(swing_highs) >= 2 and len(swing_lows) >= 2:
		if swing_highs[-1]["price"] > swing_highs[-2]["price"] and swing_lows[-1]["price"] > swing_lows[-2]["price"]:
			st_trend = "up"
		elif swing_highs[-1]["price"] < swing_highs[-2]["price"] and swing_lows[-1]["price"] < swing_lows[-2]["price"]:
			st_trend = "down"

	int_highs = [sh for sh in swing_highs if sh["level"] == "intermediate"]
	int_lows = [sl for sl in swing_lows if sl["level"] == "intermediate"]

	int_trend = "neutral"
	if len(int_highs) >= 2 and len(int_lows) >= 2:
		if int_highs[-1]["price"] > int_highs[-2]["price"] and int_lows[-1]["price"] > int_lows[-2]["price"]:
			int_trend = "up"
		elif int_highs[-1]["price"] < int_highs[-2]["price"] and int_lows[-1]["price"] < int_lows[-2]["price"]:
			int_trend = "down"

	last_sh = swing_highs[-1]["price"] if swing_highs else None
	last_sl = swing_lows[-1]["price"] if swing_lows else None

	if last_sh and last_sl:
		if current_price > last_sh:
			current_position = "above_last_swing_high"
		elif current_price < last_sl:
			current_position = "below_last_swing_low"
		else:
			current_position = "between_swings"
	else:
		current_position = "insufficient_data"

	# Clean output (remove internal index field)
	out_highs = [{"date": sh["date"], "price": sh["price"], "level": sh["level"]} for sh in swing_highs]
	out_lows = [{"date": sl["date"], "price": sl["price"], "level": sl["level"]} for sl in swing_lows]

	output_json({
		"symbol": symbol,
		"date": str(data.index[-1].date()),
		"current_price": current_price,
		"window": window,
		"lookback_days": len(data),
		"swing_highs": out_highs,
		"swing_lows": out_lows,
		"trend": {
			"short_term": st_trend,
			"intermediate": int_trend,
			"last_swing_high": last_sh,
			"last_swing_low": last_sl,
			"current_position": current_position,
		},
	})


@safe_run
def cmd_pattern_scan(args):
	"""Detect Williams chart patterns in recent price action."""
	symbol = args.ticker.upper()
	lookback = args.lookback

	fetch_days = lookback + 30
	data = _fetch_data(symbol, fetch_days)
	if data is None or len(data) < 10:
		output_json({
			"error": f"Insufficient data for {symbol}.",
			"data_points": len(data) if data is not None else 0,
		})
		return

	current_price = round(float(data["Close"].iloc[-1]), 2)
	patterns = _detect_patterns(data, lookback=lookback)

	active_setups = [p for p in patterns if p["signal_status"] in ("active", "triggered")]

	pattern_counts = {}
	for p in patterns:
		name = p["pattern"]
		pattern_counts[name] = pattern_counts.get(name, 0) + 1

	output_json({
		"symbol": symbol,
		"date": str(data.index[-1].date()),
		"current_price": current_price,
		"lookback_days": lookback,
		"patterns_detected": patterns,
		"active_setups": active_setups,
		"summary": {
			"total_patterns": len(patterns),
			"active_setups": len(active_setups),
			"pattern_counts": pattern_counts,
		},
	})


@safe_run
def cmd_trade_setup(args):
	"""Composite trade setup: run all 5 Williams filters and score conviction."""
	symbol = args.ticker.upper()
	multiplier = args.multiplier
	bond_ticker = args.bond_ticker.upper()

	# 1. Fetch stock data (extra buffer for MA calculation)
	data = _fetch_data(symbol, 150)
	if data is None or len(data) < 30:
		output_json({
			"error": f"Insufficient data for {symbol}. Need at least 30 trading days.",
			"data_points": len(data) if data is not None else 0,
		})
		return

	current_price = round(float(data["Close"].iloc[-1]), 2)
	latest_date = str(data.index[-1].date())

	# 2. Fetch bond ETF data
	bond_data = _fetch_data(bond_ticker, 40)

	# 3. Run calculation helpers
	wr_result = _calculate_wr(data, 14, 30)
	breakout_result = _calculate_breakout_levels(data, multiplier, 60)
	range_result = _calculate_range_phase(data, 20)
	patterns = _detect_patterns(data, lookback=20)

	# 4. TDW bias
	day_name = data.index[-1].strftime("%A")
	if len(data) >= 3:
		prev_close = float(data["Close"].iloc[-2])
		prev_prev_close = float(data["Close"].iloc[-3])
		prev_close_dir = "down" if prev_close < prev_prev_close else "up"
	else:
		prev_close_dir = "up"

	tdw_key = (day_name, prev_close_dir)
	tdw_entry = TDW_BIAS.get(tdw_key, {"bias": "neutral", "score": 0})
	tdw_favorable = tdw_entry["score"] > 0

	# 5. TDM bias
	all_dates = list(data.index)
	tdm_num = _get_trading_day_of_month(data.index[-1], all_dates)
	tdm_entry = TDM_BIAS.get(tdm_num, {"bias": "neutral", "score": 0}) if tdm_num else {"bias": "neutral", "score": 0}
	tdm_favorable = tdm_entry["score"] > 0

	# 6. Bond trend filter
	bond_filter = {
		"favorable": False, "status": "unavailable",
		"current": None, "five_days_ago": None, "change_pct": None,
	}
	if bond_data is not None and len(bond_data) >= 6:
		bond_current = round(float(bond_data["Close"].iloc[-1]), 2)
		bond_5_ago = round(float(bond_data["Close"].iloc[-6]), 2)
		bond_change = round((bond_current - bond_5_ago) / bond_5_ago * 100, 2) if bond_5_ago else 0
		bond_status = "rising" if bond_current > bond_5_ago else "falling"
		bond_filter = {
			"favorable": bond_status == "rising",
			"status": bond_status,
			"current": bond_current,
			"five_days_ago": bond_5_ago,
			"change_pct": bond_change,
		}

	# 7. 20-day MA trend filter
	ma20_filter = {
		"favorable": False, "trend": "unavailable",
		"ma20": None, "prev_ma20": None, "price_vs_ma": None,
	}
	closes = data["Close"]
	if len(closes) >= 22:
		ma20_series = closes.rolling(20).mean()
		ma20_today = round(float(ma20_series.iloc[-1]), 2)
		ma20_yesterday = round(float(ma20_series.iloc[-2]), 2)
		ma20_trend = "rising" if ma20_today > ma20_yesterday else "falling"
		price_vs_ma = "above" if current_price > ma20_today else "below"
		ma20_filter = {
			"favorable": ma20_trend == "rising",
			"trend": ma20_trend,
			"ma20": ma20_today,
			"prev_ma20": ma20_yesterday,
			"price_vs_ma": price_vs_ma,
		}

	# 8. Pattern filter
	bullish_active = [
		p for p in patterns
		if p["direction"] == "bullish" and p["signal_status"] in ("active", "triggered")
	]
	pattern_filter = {
		"favorable": len(bullish_active) > 0,
		"active_count": len([p for p in patterns if p["signal_status"] in ("active", "triggered")]),
		"bullish_count": len(bullish_active),
		"patterns": bullish_active[:5],
	}

	# 9. Filter alignment count
	favorable_count = sum([
		tdw_favorable,
		tdm_favorable,
		bond_filter["favorable"],
		ma20_filter["favorable"],
		pattern_filter["favorable"],
	])

	# 10. Conviction level and risk percentage
	if favorable_count <= 1:
		conviction = "low"
		risk_pct = 0.0
	elif favorable_count == 2:
		conviction = "moderate"
		risk_pct = 2.0
	elif favorable_count == 3:
		conviction = "high"
		risk_pct = 3.0
	else:
		conviction = "very_high"
		risk_pct = 4.0

	alignment = {
		"favorable_count": favorable_count,
		"total_filters": 5,
		"conviction": conviction,
		"risk_pct": risk_pct,
	}

	# 11. Position sizing (if account provided and conviction > low)
	position_sizing = None
	if args.account and args.account > 0 and risk_pct > 0 and breakout_result:
		stop_distance = abs(current_price - breakout_result["next_session"]["sell_level"])
		if stop_distance > 0:
			risk_amount = round(args.account * risk_pct / 100, 2)
			shares = int(risk_amount / stop_distance)
			position_value = round(shares * current_price, 2)
			position_pct = round(position_value / args.account * 100, 1)
			position_sizing = {
				"account": args.account,
				"risk_pct": risk_pct,
				"risk_amount": risk_amount,
				"stop_distance": round(stop_distance, 2),
				"shares": shares,
				"position_value": position_value,
				"position_pct": position_pct,
			}

	# Build output
	result = {
		"symbol": symbol,
		"date": latest_date,
		"current_price": current_price,
		"filters": {
			"tdw": {
				"favorable": tdw_favorable,
				"bias": tdw_entry["bias"],
				"score": tdw_entry["score"],
				"day": day_name,
				"prev_close": prev_close_dir,
			},
			"tdm": {
				"favorable": tdm_favorable,
				"bias": tdm_entry["bias"],
				"score": tdm_entry["score"],
				"trading_day": tdm_num or 0,
			},
			"bond": bond_filter,
			"ma20": ma20_filter,
			"pattern": pattern_filter,
		},
		"alignment": alignment,
	}

	if wr_result:
		result["williams_r"] = {
			"williams_r": wr_result["latest"]["williams_r"],
			"zone": wr_result["latest"]["zone"],
			"close": wr_result["latest"]["close"],
		}

	if breakout_result:
		ns = breakout_result["next_session"]
		result["breakout_levels"] = {
			"buy_level": ns["buy_level"],
			"sell_level": ns["sell_level"],
			"reference_close": ns["reference_close"],
			"true_range": ns["true_range"],
			"atr_3": ns["atr_3"],
		}

	if range_result:
		result["range_phase"] = range_result["latest"]["phase"]

	result["recent_patterns"] = patterns[-10:]

	if position_sizing:
		result["position_sizing"] = position_sizing

	output_json(result)


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
	parser = argparse.ArgumentParser(
		description="Larry Williams Short-Term Trading Tools"
	)
	sub = parser.add_subparsers(dest="command", required=True)

	# williams_r
	sp = sub.add_parser("williams_r", help="Williams %%R oscillator")
	sp.add_argument("ticker", help="Ticker symbol")
	sp.add_argument("--period", type=int, default=14, help="Lookback period (default: 14)")
	sp.add_argument("--lookback", type=int, default=60, help="Historical days to compute (default: 60)")
	sp.set_defaults(func=cmd_williams_r)

	# volatility_breakout
	sp = sub.add_parser("volatility_breakout", help="Volatility breakout signals")
	sp.add_argument("ticker", help="Ticker symbol")
	sp.add_argument("--lookback", type=int, default=60, help="Historical days (default: 60)")
	sp.add_argument("--multiplier", type=float, default=1.0, help="ATR multiplier (default: 1.0)")
	sp.set_defaults(func=cmd_volatility_breakout)

	# range_analysis
	sp = sub.add_parser("range_analysis", help="Range expansion/contraction analysis")
	sp.add_argument("ticker", help="Ticker symbol")
	sp.add_argument("--period", type=int, default=20, help="ATR averaging period (default: 20)")
	sp.set_defaults(func=cmd_range_analysis)

	# swing_points
	sp = sub.add_parser("swing_points", help="Swing high/low identification")
	sp.add_argument("ticker", help="Ticker symbol")
	sp.add_argument("--window", type=int, default=5, help="Bars on each side for swing ID (default: 5)")
	sp.add_argument("--lookback", type=int, default=120, help="Historical days (default: 120)")
	sp.set_defaults(func=cmd_swing_points)

	# pattern_scan
	sp = sub.add_parser("pattern_scan", help="Chart pattern detection")
	sp.add_argument("ticker", help="Ticker symbol")
	sp.add_argument("--lookback", type=int, default=60, help="Historical days to scan (default: 60)")
	sp.set_defaults(func=cmd_pattern_scan)

	# trade_setup
	sp = sub.add_parser("trade_setup", help="Composite trade setup with filter alignment")
	sp.add_argument("ticker", help="Ticker symbol")
	sp.add_argument("--multiplier", type=float, default=0.8, help="ATR multiplier (default: 0.8)")
	sp.add_argument("--account", type=float, default=None, help="Account balance for position sizing")
	sp.add_argument("--bond-ticker", type=str, default="TLT", help="Bond ETF ticker (default: TLT)")
	sp.set_defaults(func=cmd_trade_setup)

	args = parser.parse_args()
	args.func(args)


if __name__ == "__main__":
	main()
