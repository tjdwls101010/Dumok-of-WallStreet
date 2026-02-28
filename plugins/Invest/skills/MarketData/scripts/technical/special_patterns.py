#!/usr/bin/env python3
"""Special Pattern Detection: hidden institutional demand in structurally ambiguous situations.

Detects three advanced patterns that reveal supply/demand imbalances beneath
the surface — a stock "should" go down but instead absorbs selling and reverses,
indicating large players are accumulating. Positive Expectation Breaker (bearish
setup that breaks out), No Follow-Through Down (bearish event that fails to
sustain), and Undercut & Rally (shakeout of weak holders followed by recovery).

Persona-neutral module — reusable by any pipeline or analysis workflow
(TraderLion, Minervini, Williams, etc.).

Commands:
	scan: Scan last 20 trading days for special patterns

Args:
	symbol (str): Ticker symbol (e.g., "AAPL", "NVDA", "META")

Returns:
	dict: {
		"symbol": str,
		"patterns_detected": list[dict],
		"pattern_count": int
	}

	Each pattern dict contains:
		POSITIVE_EXPECTATION_BREAKER: {
			"pattern": str,
			"date": str,
			"prior_structure": "below_21ema_with_lower_high",
			"breakout_level": float,
			"closing_range": float,
			"volume_ratio": float,
			"interpretation": "hidden_accumulation_breakout"
		}
		NO_FOLLOW_THROUGH_DOWN: {
			"pattern": str,
			"event_date": str,
			"event_type": str ("gap_down" or "50sma_break"),
			"event_magnitude": float,
			"recovery_days": int,
			"recovery_volume_ratio": float,
			"interpretation": "demand_absorbed_selling"
		}
		UNDERCUT_AND_RALLY: {
			"pattern": str,
			"event_date": str,
			"swing_low": float,
			"undercut_low": float,
			"undercut_pct": float,
			"recovery_days": int,
			"recovery_volume_ratio": float,
			"interpretation": "shakeout_reversal"
		}

Example:
	>>> python special_patterns.py scan NVDA
	{
		"symbol": "NVDA",
		"patterns_detected": [
			{
				"pattern": "NO_FOLLOW_THROUGH_DOWN",
				"event_date": "2026-02-25",
				"event_type": "gap_down",
				"event_magnitude": -2.5,
				"recovery_days": 2,
				"recovery_volume_ratio": 1.4,
				"interpretation": "demand_absorbed_selling"
			}
		],
		"pattern_count": 1
	}

	>>> python special_patterns.py scan AAPL
	{
		"symbol": "AAPL",
		"patterns_detected": [],
		"pattern_count": 0
	}

Use Cases:
	- Identify hidden accumulation beneath bearish price action
	- Detect institutional buying when retail sentiment is negative
	- Find stocks where bearish expectations have been invalidated
	- Combine with volume edge or stage analysis for high-conviction entries
	- Screen for reversal setups after pullbacks or corrections

Notes:
	- POSITIVE_EXPECTATION_BREAKER: Bearish structure (below 21 EMA with lower
	  high) that breaks above prior 5-day swing high with strong close and volume.
	  Requires: at least one close below 21 EMA in prior 5 days, lower high
	  formation, close > max(High D-5..D-1), closing range > 50%, volume > 50-day avg
	- NO_FOLLOW_THROUGH_DOWN: Gap down >2% or close below 50 SMA that recovers
	  within 1-3 days. Up-day volume during recovery must exceed event-day volume
	- UNDERCUT_AND_RALLY: Price undercuts a prior swing low (defined as low < 3
	  bars before and after) by 1-3%, then reclaims above that low within 3 days
	  with higher recovery volume
	- Multiple patterns can fire simultaneously
	- Conservative thresholds to minimize false positives
	- Requires minimum 60 trading days of data (1-year fetch for warmup)
	- 21 EMA: ewm(span=21, adjust=False); 50 SMA: rolling(50).mean()
	- Closing range: (Close - Low) / (High - Low); returns 0.5 if H == L

See Also:
	- entry_patterns.py: Actionable entry setups (pullback, inside day, etc.)
	- sell_signals.py: Bearish sell signal detection (inverse perspective)
	- volume_edge.py: Institutional volume events for breakout confirmation
	- volume_analysis.py: Accumulation/distribution grading
	- closing_range.py: Bar quality classification
"""

import argparse
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import yfinance as yf
from utils import output_json, safe_run


def _closing_range(close, high, low):
	"""Calculate closing range: (Close - Low) / (High - Low). Returns 0.5 if H == L."""
	if high == low:
		return 0.5
	return round((close - low) / (high - low), 2)


def _avg_volume_50(volumes):
	"""Calculate 50-day average volume (or all available if < 50 days)."""
	if len(volumes) >= 50:
		return float(volumes.iloc[-50:].mean())
	return float(volumes.mean())


def _find_swing_lows(data, lookback=60):
	"""Find swing lows in the last `lookback` days.

	A swing low is a bar whose low is lower than the lows of 3 bars before
	and 3 bars after it.
	"""
	low = data["Low"]
	n = len(data)
	swing_lows = []

	start = max(n - lookback, 3)
	end = n - 3  # need 3 bars after

	for i in range(start, end):
		current_low = float(low.iloc[i])
		if np.isnan(current_low) or current_low <= 0:
			continue

		is_swing = True
		# Check 3 bars before
		for j in range(i - 3, i):
			if j < 0:
				is_swing = False
				break
			if current_low >= float(low.iloc[j]):
				is_swing = False
				break
		if not is_swing:
			continue

		# Check 3 bars after
		for j in range(i + 1, i + 4):
			if j >= n:
				is_swing = False
				break
			if current_low >= float(low.iloc[j]):
				is_swing = False
				break
		if is_swing:
			swing_lows.append((i, current_low))

	return swing_lows


def _detect_positive_expectation_breaker(data, ema21):
	"""Detect Positive Expectation Breaker pattern.

	Scans each day in the last 20 trading days for:
	  a) At least one close below 21 EMA in the prior 5 days (bearish structure)
	  b) Lower high formation: any high in D-5..D-1 < max high in D-10..D-6
	  c) Close > max(High of D-5..D-1) — breaks above prior swing high
	  d) Closing range > 50%
	  e) Volume > 50-day average volume
	All of b+c+d+e must be true AND bearish context (a) confirmed.
	"""
	results = []
	close = data["Close"]
	high = data["High"]
	low = data["Low"]
	volumes = data["Volume"]

	avg_vol = _avg_volume_50(volumes)
	n = len(data)

	# Need EMA warmup (21) + lookback (10) + scan window
	if n < 31:
		return results

	scan_start = max(n - 20, 11)
	for idx in range(scan_start, n):
		# --- (a) Bearish context: at least one close below 21 EMA in prior 5 days ---
		prior_start = idx - 5
		if prior_start < 0:
			continue
		has_below_ema = False
		for j in range(prior_start, idx):
			if float(close.iloc[j]) < float(ema21.iloc[j]):
				has_below_ema = True
				break
		if not has_below_ema:
			continue

		# --- (b) Lower high formation ---
		# Max high of D-10 to D-6 (the earlier window)
		far_start = idx - 10
		far_end = idx - 5
		if far_start < 0:
			continue
		far_high = float(high.iloc[far_start:far_end].max())
		# Check if any high in D-5..D-1 is lower than far_high
		near_highs = high.iloc[idx - 5:idx]
		has_lower_high = False
		for h_val in near_highs:
			if float(h_val) < far_high:
				has_lower_high = True
				break
		if not has_lower_high:
			continue

		# --- (c) Close > max(High of D-5..D-1) — breakout above prior swing high ---
		breakout_level = float(near_highs.max())
		c = float(close.iloc[idx])
		if c <= breakout_level:
			continue

		# --- (d) Closing range > 50% ---
		h = float(high.iloc[idx])
		l = float(low.iloc[idx])
		cr = _closing_range(c, h, l)
		if cr <= 0.5:
			continue

		# --- (e) Volume > 50-day average ---
		v = float(volumes.iloc[idx])
		vol_ratio = round(v / avg_vol, 2) if avg_vol > 0 else 0.0
		if vol_ratio <= 1.0:
			continue

		results.append({
			"pattern": "POSITIVE_EXPECTATION_BREAKER",
			"date": str(data.index[idx].date()),
			"prior_structure": "below_21ema_with_lower_high",
			"breakout_level": round(breakout_level, 2),
			"closing_range": cr,
			"volume_ratio": vol_ratio,
			"interpretation": "hidden_accumulation_breakout",
		})

	return results


def _detect_no_follow_through_down(data, sma50):
	"""Detect No Follow-Through Down pattern.

	Scans the last 20 trading days for a bearish event:
	  a) Gap down: Open < prior Close by >2%
	  b) Or: Close breaks below 50 SMA
	Then checks next 1-3 days for:
	  c) Price recovers above trigger level (prior Close for gap, 50 SMA for break)
	  d) Sum of up-day volume during recovery > event-day volume
	"""
	results = []
	close = data["Close"]
	opn = data["Open"]
	volumes = data["Volume"]

	n = len(data)
	if n < 55:
		return results

	# Scan events in last 20 days, leaving room for 3-day recovery
	event_start = max(n - 20, 1)
	event_end = n - 1  # need at least 1 day for recovery

	for idx in range(event_start, event_end):
		prior_close = float(close.iloc[idx - 1])
		day_open = float(opn.iloc[idx])
		day_close = float(close.iloc[idx])
		sma50_val = float(sma50.iloc[idx])
		prior_sma50 = float(sma50.iloc[idx - 1])

		if np.isnan(sma50_val) or np.isnan(prior_sma50):
			# 50 SMA not available yet; only check gap down
			sma50_val = 0.0
			prior_sma50 = 0.0

		event_type = None
		event_magnitude = 0.0
		trigger_level = 0.0

		# Check gap down > 2%
		if prior_close > 0:
			gap_pct = (day_open - prior_close) / prior_close * 100
			if gap_pct < -2.0:
				event_type = "gap_down"
				event_magnitude = round(gap_pct, 2)
				trigger_level = prior_close

		# Check close breaks below 50 SMA (was above prior day)
		if event_type is None and sma50_val > 0 and prior_sma50 > 0:
			prior_close_val = float(close.iloc[idx - 1])
			if prior_close_val > prior_sma50 and day_close < sma50_val:
				distance_below = (day_close - sma50_val) / sma50_val * 100
				event_type = "50sma_break"
				event_magnitude = round(distance_below, 2)
				trigger_level = sma50_val

		if event_type is None:
			continue

		# --- Recovery check: within 1-3 days, close above trigger ---
		max_recovery_end = min(idx + 4, n)
		recovered = False
		recovery_days = 0

		for r in range(idx + 1, max_recovery_end):
			recovery_days = r - idx
			if float(close.iloc[r]) > trigger_level:
				recovered = True
				break

		if not recovered:
			continue

		# --- Volume check: sum of up-day volume in recovery > down event volume ---
		event_volume = float(volumes.iloc[idx])

		recovery_up_volume_sum = 0.0
		for r in range(idx + 1, min(idx + 1 + recovery_days, n)):
			r_close = float(close.iloc[r])
			r_prev_close = float(close.iloc[r - 1])
			if r_close > r_prev_close:
				recovery_up_volume_sum += float(volumes.iloc[r])

		if event_volume <= 0 or recovery_up_volume_sum <= event_volume:
			recovery_volume_ratio = round(recovery_up_volume_sum / event_volume, 2) if event_volume > 0 else 0.0
			if recovery_volume_ratio <= 1.0:
				continue

		recovery_volume_ratio = round(recovery_up_volume_sum / event_volume, 2) if event_volume > 0 else 0.0

		results.append({
			"pattern": "NO_FOLLOW_THROUGH_DOWN",
			"event_date": str(data.index[idx].date()),
			"event_type": event_type,
			"event_magnitude": event_magnitude,
			"recovery_days": recovery_days,
			"recovery_volume_ratio": recovery_volume_ratio,
			"interpretation": "demand_absorbed_selling",
		})

	return results


def _detect_undercut_and_rally(data):
	"""Detect Undercut & Rally pattern.

	Find swing lows in the last 60 days (low < 3 bars before and after).
	Scan last 20 trading days for:
	  a) Low undercuts a prior swing low by 1-3%
	  b) Within 3 days, close reclaims above the swing low
	  c) Recovery volume > undercut day volume
	"""
	results = []
	close = data["Close"]
	low = data["Low"]
	volumes = data["Volume"]

	n = len(data)
	if n < 30:
		return results

	# Find swing lows in the last 60 days
	swing_lows = _find_swing_lows(data, lookback=60)

	if not swing_lows:
		return results

	# Scan last 20 trading days for undercuts of any swing low
	scan_start = max(n - 20, 0)
	seen_dates = set()

	for idx in range(scan_start, n):
		day_low = float(low.iloc[idx])
		if np.isnan(day_low) or day_low <= 0:
			continue

		for swing_idx, swing_low_val in swing_lows:
			# Swing low must be BEFORE the current scan day
			if swing_idx >= idx:
				continue

			# Undercut by 1-3%: Low < swing_low AND Low > swing_low * 0.97
			if day_low >= swing_low_val:
				continue
			if day_low < swing_low_val * 0.97:
				continue

			undercut_pct = round((day_low - swing_low_val) / swing_low_val * 100, 2)

			# Recovery: within 3 days, close > swing_low
			max_recovery_end = min(idx + 4, n)
			recovered = False
			recovery_days = 0

			for r in range(idx, max_recovery_end):
				days_after = r - idx
				if float(close.iloc[r]) > swing_low_val:
					recovered = True
					recovery_days = max(days_after, 1)
					break

			if not recovered:
				continue

			# Volume check: recovery volume > undercut day volume
			undercut_vol = float(volumes.iloc[idx])
			if undercut_vol <= 0:
				continue

			recovery_vol_sum = 0.0
			recovery_vol_count = 0
			for r in range(idx, min(idx + recovery_days + 1, n)):
				if float(close.iloc[r]) > float(close.iloc[r - 1]) if r > 0 else False:
					recovery_vol_sum += float(volumes.iloc[r])
					recovery_vol_count += 1

			# If no clear up days, use the recovery day's volume directly
			if recovery_vol_count == 0:
				recovery_end_idx = min(idx + recovery_days, n - 1)
				recovery_vol_sum = float(volumes.iloc[recovery_end_idx])

			recovery_volume_ratio = round(recovery_vol_sum / undercut_vol, 2) if undercut_vol > 0 else 0.0
			if recovery_volume_ratio <= 1.0:
				continue

			date_str = str(data.index[idx].date())
			if date_str in seen_dates:
				continue
			seen_dates.add(date_str)

			results.append({
				"pattern": "UNDERCUT_AND_RALLY",
				"event_date": date_str,
				"swing_low": round(swing_low_val, 2),
				"undercut_low": round(day_low, 2),
				"undercut_pct": undercut_pct,
				"recovery_days": recovery_days,
				"recovery_volume_ratio": recovery_volume_ratio,
				"interpretation": "shakeout_reversal",
			})
			break  # One pattern per scan day

	return results


@safe_run
def cmd_scan(args):
	"""Scan last 20 trading days for special patterns."""
	symbol = args.symbol.upper()
	ticker = yf.Ticker(symbol)
	data = ticker.history(period="1y", interval="1d")

	if data.empty or len(data) < 60:
		output_json({
			"error": f"Insufficient data for {symbol}. Need at least 60 trading days.",
			"data_points": len(data),
		})
		return

	close = data["Close"]
	ema21 = close.ewm(span=21, adjust=False).mean()
	sma50 = close.rolling(50).mean()

	patterns = []
	patterns.extend(_detect_positive_expectation_breaker(data, ema21))
	patterns.extend(_detect_no_follow_through_down(data, sma50))
	patterns.extend(_detect_undercut_and_rally(data))

	output_json({
		"symbol": symbol,
		"patterns_detected": patterns,
		"pattern_count": len(patterns),
	})


def main():
	parser = argparse.ArgumentParser(
		description="Special Pattern Detection: hidden institutional demand"
	)
	sub = parser.add_subparsers(dest="command", required=True)

	# scan
	sp = sub.add_parser("scan", help="Scan for special patterns")
	sp.add_argument("symbol", help="Ticker symbol")
	sp.set_defaults(func=cmd_scan)

	args = parser.parse_args()
	args.func(args)


if __name__ == "__main__":
	main()
