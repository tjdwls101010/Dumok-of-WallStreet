#!/usr/bin/env python3
"""Post-breakout monitoring for Minervini SEPA methodology.

Tracks stock behavior after a breakout above a pivot point to determine
whether to hold, watch, reduce, or sell the position. Classifies pullback
behavior as "tennis ball" (constructive) or "egg" (destructive), detects
squat patterns, and monitors the 20-day moving average sell rule.

Commands:
	monitor: Monitor post-breakout behavior for a ticker

Args:
	symbol (str): Ticker symbol (e.g., "AAPL", "NVDA", "META")
	--entry-price (float): Breakout entry price
	--entry-date (str): Entry date in YYYY-MM-DD format
	--stop-loss (float): Custom stop-loss percentage (default: 7.0)

Returns:
	dict: {
		"symbol": str,
		"entry_price": float,
		"entry_date": str,
		"current_price": float,
		"days_since_entry": int,
		"gain_loss_pct": float,
		"behavior": str,
		"squat_detected": bool,
		"above_20ma": bool,
		"closed_below_20ma_count": int,
		"hold_sell_signal": str,
		"failure_reset": {
			"applicable": bool,
			"pivot_reset_detected": bool,
			"base_reset_detected": bool,
			"reset_pivot_price": float or None,
			"days_since_stopout": int,
			"watch_recommendation": str
		},
		"squat_detail": {
			"detected": bool,
			"recovery_days": int,
			"recovery_quality": str,
			"closed_below_20ma_during_squat": bool,
			"price_tightening_after_squat": bool,
			"volume_contracting_after_squat": bool
		}
	}

Example:
	>>> python post_breakout.py monitor NVDA --entry-price 140 --entry-date 2025-11-01
	{
		"symbol": "NVDA",
		"entry_price": 140.0,
		"entry_date": "2025-11-01",
		"current_price": 152.30,
		"days_since_entry": 45,
		"gain_loss_pct": 8.79,
		"behavior": "tennis_ball",
		"squat_detected": false,
		"above_20ma": true,
		"closed_below_20ma_count": 0,
		"hold_sell_signal": "hold"
	}

Use Cases:
	- Monitor newly entered positions after VCP breakout
	- Determine hold vs sell using Minervini's post-breakout rules
	- Detect early failure signals (egg behavior, squat, 20MA violation)
	- Automate trailing stop and sell discipline

Notes:
	- Tennis ball: pullback 3-7 days, <7% depth, declining volume, recovers to new high
	- Egg: pullback 10+ days OR >10% depth OR increasing volume during pullback
	- Squat: breakout day close > 3% below day's high; watch 10 days for recovery
	- 20MA sell rule: 3+ consecutive closes below 20-day MA = sell signal
	- Default stop-loss: 7% (Minervini standard initial stop)
	- hold_sell_signal: hold > watch > reduce > sell (escalating urgency)
	- Failure reset: after stop-out, stock may form new tight pivot (2-4 weeks) or new base (5-15 weeks)
	- Squat detail: enhanced analysis with 20MA check, tightening, volume contraction, recovery quality grading

See Also:
	- vcp.py: VCP detection for identifying breakout candidates
	- base_count.py: Base counting context for position risk
	- volume_analysis.py: Volume confirmation for breakout quality
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import numpy as np
import yfinance as yf
from technical.indicators import calculate_sma
from utils import output_json, safe_run


def _classify_pullback_behavior(closes, volumes, entry_idx, vol_50d_avg):
	"""Classify pullback as tennis_ball or egg.

	Tennis ball: bounces back quickly with declining volume (constructive).
	Egg: drops and stays down or worsens (destructive).
	"""
	close_arr = closes.values.astype(float)
	vol_arr = volumes.values.astype(float)

	if entry_idx >= len(close_arr) - 1:
		return "no_pullback", {}

	# Find the post-entry high
	post_entry = close_arr[entry_idx:]
	post_high_offset = np.argmax(post_entry)
	post_high_idx = entry_idx + post_high_offset
	post_high = post_entry[post_high_offset]

	if post_high_idx >= len(close_arr) - 1:
		return "no_pullback", {}

	# Find pullback from post-entry high
	after_high = close_arr[post_high_idx:]
	pullback_low_offset = np.argmin(after_high)
	pullback_low_idx = post_high_idx + pullback_low_offset
	pullback_low = after_high[pullback_low_offset]

	if post_high <= 0:
		return "no_pullback", {}

	pullback_depth_pct = (post_high - pullback_low) / post_high * 100
	pullback_days = pullback_low_idx - post_high_idx

	# No meaningful pullback yet
	if pullback_depth_pct < 1.0:
		return "no_pullback", {
			"pullback_depth_pct": round(pullback_depth_pct, 2),
			"pullback_days": pullback_days,
		}

	# Volume during pullback
	pb_start = post_high_idx
	pb_end = min(pullback_low_idx + 1, len(vol_arr))
	pullback_vols = vol_arr[pb_start:pb_end]
	if len(pullback_vols) >= 2:
		first_half = np.mean(pullback_vols[: len(pullback_vols) // 2])
		second_half = np.mean(pullback_vols[len(pullback_vols) // 2 :])
		vol_declining_during_pb = second_half < first_half
	else:
		vol_declining_during_pb = True

	# Check if price recovered to new high after pullback
	recovered_to_new_high = False
	if pullback_low_idx < len(close_arr) - 1:
		after_pullback = close_arr[pullback_low_idx:]
		if np.max(after_pullback) > post_high:
			recovered_to_new_high = True

	details = {
		"pullback_depth_pct": round(pullback_depth_pct, 2),
		"pullback_days": pullback_days,
		"vol_declining_during_pullback": vol_declining_during_pb,
		"recovered_to_new_high": recovered_to_new_high,
	}

	# Tennis ball criteria
	if pullback_days <= 7 and pullback_depth_pct < 7 and vol_declining_during_pb:
		if recovered_to_new_high:
			return "tennis_ball", details
		else:
			return "tennis_ball_pending", details

	# Egg criteria
	if pullback_days >= 10 or pullback_depth_pct >= 10 or not vol_declining_during_pb:
		return "egg", details

	# In between -- mild pullback, not yet classified
	return "pending", details


def _detect_squat(closes, highs, entry_idx):
	"""Detect squat pattern on breakout day.

	A squat occurs when the breakout day closes more than 3% below
	the day's high, suggesting selling into strength.  Monitor the
	next 10 days for recovery.
	"""
	close_arr = closes.values.astype(float)
	high_arr = highs.values.astype(float)

	if entry_idx >= len(close_arr) or entry_idx >= len(high_arr):
		return False, "no_data"

	day_high = high_arr[entry_idx]
	day_close = close_arr[entry_idx]

	if day_high <= 0:
		return False, "no_data"

	gap_pct = (day_high - day_close) / day_high * 100

	if gap_pct <= 3.0:
		return False, "clean_close"

	# Squat detected -- check 10-day recovery window
	recovery_end = min(entry_idx + 11, len(close_arr))
	recovery_window = close_arr[entry_idx + 1 : recovery_end]

	if len(recovery_window) == 0:
		return True, "squat_pending"

	if np.max(recovery_window) > day_high:
		return True, "squat_recovered"
	else:
		days_elapsed = len(recovery_window)
		if days_elapsed >= 10:
			return True, "squat_failed"
		return True, "squat_pending"


def _check_20ma_rule(closes, sma20, entry_idx):
	"""Check consecutive closes below 20-day MA.

	3+ consecutive closes below 20MA = sell signal per Minervini.
	"""
	close_arr = closes.values.astype(float)
	sma20_arr = sma20.values.astype(float)

	consecutive_below = 0
	max_consecutive = 0
	current_above = True

	# Check from entry forward
	for i in range(entry_idx, len(close_arr)):
		if np.isnan(sma20_arr[i]):
			continue
		if close_arr[i] < sma20_arr[i]:
			consecutive_below += 1
			max_consecutive = max(max_consecutive, consecutive_below)
			current_above = False
		else:
			consecutive_below = 0
			current_above = True

	return {
		"above_20ma": current_above,
		"current_consecutive_below": consecutive_below,
		"max_consecutive_below": max_consecutive,
	}


def _detect_failure_reset(closes, volumes, entry_idx, entry_price, stop_loss_pct, vol_50d_avg):
	"""Detect failure reset pattern after a stop-out event.

	Checks whether a stock has formed a reset pattern after being
	stopped out. Two reset types are evaluated: a short-term pivot
	failure reset (2-4 weeks) and a long-term base failure reset
	(5-15 weeks).

	Returns:
		dict: Failure reset analysis with applicable flag, pivot
		and base reset detection, new pivot price, days since
		stop-out, and watch recommendation.

	Notes:
		- Only relevant when sell signal (stop-loss hit) is triggered.
		- Pivot reset: tight range near entry with declining volume, 3+ days.
		- Base reset: two successive pullbacks, second shallower than first.

	Example:
		>>> result = _detect_failure_reset(
		...     closes, volumes, 0, 150.0, 7.0, 1000000
		... )
		>>> result["applicable"]
		True
	"""
	close_arr = closes.values.astype(float)
	vol_arr = volumes.values.astype(float)
	n = len(close_arr)

	default = {
		"applicable": False,
		"pivot_reset_detected": False,
		"base_reset_detected": False,
		"reset_pivot_price": None,
		"days_since_stopout": 0,
		"watch_recommendation": "no_reset",
	}

	stop_price = entry_price * (1 - stop_loss_pct / 100)

	# Find the stop-out point: first day after entry where close
	# drops below the stop price
	stopout_idx = None
	for i in range(entry_idx + 1, n):
		if close_arr[i] < stop_price:
			stopout_idx = i
			break

	if stopout_idx is None:
		return default

	days_since_stopout = n - 1 - stopout_idx
	result = {
		"applicable": True,
		"pivot_reset_detected": False,
		"base_reset_detected": False,
		"reset_pivot_price": None,
		"days_since_stopout": days_since_stopout,
		"watch_recommendation": "no_reset",
	}

	# --- Pivot Failure Reset (short-term, 10-20 days) ---
	pivot_start = stopout_idx + 1
	pivot_end = min(stopout_idx + 21, n)
	if pivot_end - pivot_start >= 10:
		pivot_closes = close_arr[pivot_start:pivot_end]
		pivot_vols = vol_arr[pivot_start:pivot_end]
		entry_lo = entry_price * 0.95
		entry_hi = entry_price * 1.05

		# Scan for 3+ consecutive days of tight range near
		# entry price with declining volume
		consec = 0
		best_run = 0
		for j in range(len(pivot_closes)):
			c = pivot_closes[j]
			if entry_lo <= c <= entry_hi:
				consec += 1
				if consec > best_run:
					best_run = consec
			else:
				consec = 0

		# Check overall range tightness (max-min < 5%)
		range_pct = 0.0
		if np.min(pivot_closes) > 0:
			spread = np.max(pivot_closes) - np.min(pivot_closes)
			range_pct = spread / np.min(pivot_closes) * 100

		# Volume declining: second half avg < first half avg
		half = len(pivot_vols) // 2
		vol_declining = False
		if half > 0:
			first_avg = np.mean(pivot_vols[:half])
			second_avg = np.mean(pivot_vols[half:])
			vol_declining = second_avg < first_avg

		if best_run >= 3 and range_pct < 5.0 and vol_declining:
			result["pivot_reset_detected"] = True
			result["reset_pivot_price"] = round(float(np.max(pivot_closes)), 2)

	# --- Base Failure Reset (long-term, 25-75 days) ---
	base_start = stopout_idx + 1
	base_end = min(stopout_idx + 76, n)
	if base_end - base_start >= 25:
		base_closes = close_arr[base_start:base_end]

		# Find pullbacks: local peaks followed by troughs
		pullback_depths = []
		i = 1
		while i < len(base_closes) - 1:
			# Find local peak
			if base_closes[i] >= base_closes[i - 1] and base_closes[i] >= base_closes[i + 1]:
				peak = base_closes[i]
				# Find subsequent trough
				trough = peak
				for k in range(i + 1, len(base_closes)):
					if base_closes[k] < trough:
						trough = base_closes[k]
					elif base_closes[k] > trough * 1.02:
						break
				if peak > 0:
					depth = (peak - trough) / peak * 100
					if depth > 1.0:
						pullback_depths.append(depth)
				i += 1
			else:
				i += 1

		# Two successive pullbacks, second shallower
		if len(pullback_depths) >= 2:
			for p in range(len(pullback_depths) - 1):
				if pullback_depths[p + 1] < pullback_depths[p]:
					result["base_reset_detected"] = True
					if result["reset_pivot_price"] is None:
						result["reset_pivot_price"] = round(float(np.max(base_closes)), 2)
					break

	# Determine watch recommendation
	if result["pivot_reset_detected"] or result["base_reset_detected"]:
		result["watch_recommendation"] = "reset_detected"
	elif days_since_stopout <= 20:
		result["watch_recommendation"] = "monitor_for_pivot_reset"
	elif days_since_stopout <= 75:
		result["watch_recommendation"] = "monitor_for_base_reset"

	return result


def _analyze_squat_detail(closes, highs, volumes, entry_idx, vol_50d_avg):
	"""Analyze squat recovery with detailed quality metrics.

	Extends the basic squat detection with 20-day MA checks,
	price tightening analysis, volume contraction tracking, and
	recovery quality grading.

	Returns:
		dict: Squat detail with detected flag, recovery days,
		recovery quality, 20MA violation, price tightening, and
		volume contraction indicators.

	Notes:
		- Recovery quality: strong (3d), normal (4-10d), extended (10+d), failed.
		- Price tightening: last 5 closes range vs first 5 in recovery window.
		- Volume contraction: avg volume last 5 days vs first 5 post-squat.

	Example:
		>>> detail = _analyze_squat_detail(
		...     closes, highs, volumes, 0, 1000000
		... )
		>>> detail["recovery_quality"]
		'strong'
	"""
	close_arr = closes.values.astype(float)
	high_arr = highs.values.astype(float)
	vol_arr = volumes.values.astype(float)
	n = len(close_arr)

	default = {
		"detected": False,
		"recovery_days": 0,
		"recovery_quality": "n/a",
		"closed_below_20ma_during_squat": False,
		"price_tightening_after_squat": False,
		"volume_contracting_after_squat": False,
	}

	if entry_idx >= n or entry_idx >= len(high_arr):
		return default

	day_high = high_arr[entry_idx]
	day_close = close_arr[entry_idx]

	if day_high <= 0:
		return default

	gap_pct = (day_high - day_close) / day_high * 100
	if gap_pct <= 3.0:
		return default

	# Squat detected -- analyze recovery
	result = {
		"detected": True,
		"recovery_days": 0,
		"recovery_quality": "extended",
		"closed_below_20ma_during_squat": False,
		"price_tightening_after_squat": False,
		"volume_contracting_after_squat": False,
	}

	# Recovery window: up to 10 days after squat
	rec_start = entry_idx + 1
	rec_end = min(entry_idx + 11, n)
	rec_closes = close_arr[rec_start:rec_end]
	rec_vols = vol_arr[rec_start:rec_end]

	if len(rec_closes) == 0:
		result["recovery_quality"] = "extended"
		return result

	# Calculate 20-day SMA for the post-entry period
	sma_start = max(0, entry_idx - 19)
	sma_window = close_arr[sma_start:rec_end]
	if len(sma_window) >= 20:
		sma20_vals = []
		for i in range(len(sma_window)):
			if i < 19:
				sma20_vals.append(np.nan)
			else:
				sma20_vals.append(np.mean(sma_window[i - 19 : i + 1]))
		sma20_arr = np.array(sma20_vals)
		# Align to recovery period
		offset = rec_start - sma_start
		rec_sma = sma20_arr[offset : offset + len(rec_closes)]
	else:
		rec_sma = np.full(len(rec_closes), np.nan)

	# Check if any close during recovery is below 20MA
	for i in range(len(rec_closes)):
		if not np.isnan(rec_sma[i]):
			if rec_closes[i] < rec_sma[i]:
				result["closed_below_20ma_during_squat"] = True
				break

	# Price tightening: compare range of first 5 vs last 5
	if len(rec_closes) >= 10:
		first5 = rec_closes[:5]
		last5 = rec_closes[5:10]
		range_first = np.max(first5) - np.min(first5)
		range_last = np.max(last5) - np.min(last5)
		if range_last < range_first:
			result["price_tightening_after_squat"] = True
	elif len(rec_closes) >= 6:
		half = len(rec_closes) // 2
		first_half = rec_closes[:half]
		second_half = rec_closes[half:]
		r_first = np.max(first_half) - np.min(first_half)
		r_second = np.max(second_half) - np.min(second_half)
		if r_second < r_first:
			result["price_tightening_after_squat"] = True

	# Volume contraction: last 5 avg < first 5 avg
	if len(rec_vols) >= 10:
		vol_first5 = np.mean(rec_vols[:5])
		vol_last5 = np.mean(rec_vols[5:10])
		if vol_last5 < vol_first5:
			result["volume_contracting_after_squat"] = True
	elif len(rec_vols) >= 6:
		half = len(rec_vols) // 2
		vf = np.mean(rec_vols[:half])
		vl = np.mean(rec_vols[half:])
		if vl < vf:
			result["volume_contracting_after_squat"] = True

	# Recovery quality determination
	breakout_high = day_high
	# Strong: price exceeds breakout day high within 3 days
	for i in range(min(3, len(rec_closes))):
		if rec_closes[i] > breakout_high:
			result["recovery_days"] = i + 1
			result["recovery_quality"] = "strong"
			return result

	# Normal: recovery within 4-10 days
	for i in range(3, min(10, len(rec_closes))):
		if rec_closes[i] > breakout_high:
			result["recovery_days"] = i + 1
			result["recovery_quality"] = "normal"
			return result

	# Check if stop-loss was hit during squat recovery
	if len(rec_closes) > 0:
		entry_price = close_arr[entry_idx]
		stop_price = entry_price * 0.93  # ~7% default stop
		if np.min(rec_closes) < stop_price:
			result["recovery_quality"] = "failed"
			result["recovery_days"] = len(rec_closes)
			return result

	# Extended: more than 10 days or still pending
	result["recovery_days"] = len(rec_closes)
	result["recovery_quality"] = "extended"
	return result


def _determine_signal(behavior, squat_detected, squat_status, ma20_info, gain_loss_pct, stop_loss_pct):
	"""Determine hold/watch/reduce/sell signal.

	Signal hierarchy:
	- sell: 20MA 3d+ violation OR stop-loss hit OR failed behavior
	- reduce: egg behavior OR 20MA 2d violation
	- watch: squat_pending OR 20MA 1d violation
	- hold: tennis ball + above 20MA
	"""
	consecutive_below = ma20_info["current_consecutive_below"]

	# Hard sell signals
	if gain_loss_pct <= -stop_loss_pct:
		return "sell"
	if consecutive_below >= 3:
		return "sell"
	if behavior == "egg" and not ma20_info["above_20ma"]:
		return "sell"
	if squat_status == "squat_failed":
		return "sell"

	# Reduce signals
	if behavior == "egg":
		return "reduce"
	if consecutive_below == 2:
		return "reduce"

	# Watch signals
	if squat_detected and squat_status == "squat_pending":
		return "watch"
	if consecutive_below == 1:
		return "watch"
	if behavior == "tennis_ball_pending":
		return "watch"

	# Hold
	return "hold"


@safe_run
def cmd_monitor(args):
	"""Monitor post-breakout behavior for a ticker."""
	symbol = args.symbol.upper()
	entry_price = args.entry_price
	entry_date = args.entry_date
	stop_loss_pct = args.stop_loss

	ticker = yf.Ticker(symbol)
	data = ticker.history(start=entry_date, interval="1d")

	if data.empty or len(data) < 2:
		output_json(
			{
				"error": f"Insufficient post-entry data for {symbol} since {entry_date}.",
				"data_points": len(data),
			}
		)
		return

	closes = data["Close"]
	highs = data["High"]
	volumes = data["Volume"]
	current_price = float(closes.iloc[-1])
	days_since_entry = len(data) - 1
	gain_loss_pct = round((current_price - entry_price) / entry_price * 100, 2)

	# 20-day SMA (need more history for accurate 20MA)
	extended_data = ticker.history(period="3mo", interval="1d")
	if len(extended_data) >= 20:
		sma20 = calculate_sma(extended_data["Close"], 20)
		# Align to post-entry data
		sma20_aligned = sma20.reindex(data.index)
	else:
		sma20_aligned = calculate_sma(closes, min(20, len(closes)))

	# 50-day average volume for context
	vol_arr = volumes.values.astype(float)
	vol_50d_avg = float(np.mean(vol_arr[:50])) if len(vol_arr) >= 50 else float(np.mean(vol_arr))

	entry_idx = 0  # First day in post-entry data

	# Classify pullback behavior
	behavior, behavior_details = _classify_pullback_behavior(closes, volumes, entry_idx, vol_50d_avg)

	# Detect squat
	squat_detected, squat_status = _detect_squat(closes, highs, entry_idx)

	# 20MA rule
	ma20_info = _check_20ma_rule(closes, sma20_aligned, entry_idx)

	# Determine signal
	signal = _determine_signal(
		behavior,
		squat_detected,
		squat_status,
		ma20_info,
		gain_loss_pct,
		stop_loss_pct,
	)

	# Failure reset analysis (only when sell signal triggered)
	if signal == "sell":
		failure_reset = _detect_failure_reset(
			closes,
			volumes,
			entry_idx,
			entry_price,
			stop_loss_pct,
			vol_50d_avg,
		)
	else:
		failure_reset = {
			"applicable": False,
			"pivot_reset_detected": False,
			"base_reset_detected": False,
			"reset_pivot_price": None,
			"days_since_stopout": 0,
			"watch_recommendation": "no_reset",
		}

	# Squat detail analysis
	squat_detail = _analyze_squat_detail(
		closes,
		highs,
		volumes,
		entry_idx,
		vol_50d_avg,
	)

	output_json(
		{
			"symbol": symbol,
			"entry_price": entry_price,
			"entry_date": entry_date,
			"current_price": round(current_price, 2),
			"days_since_entry": days_since_entry,
			"gain_loss_pct": gain_loss_pct,
			"behavior": behavior,
			"behavior_details": behavior_details,
			"squat_detected": squat_detected,
			"squat_status": squat_status,
			"above_20ma": ma20_info["above_20ma"],
			"closed_below_20ma_count": ma20_info["current_consecutive_below"],
			"max_consecutive_below_20ma": ma20_info["max_consecutive_below"],
			"stop_loss_pct": stop_loss_pct,
			"stop_loss_price": round(entry_price * (1 - stop_loss_pct / 100), 2),
			"hold_sell_signal": signal,
			"failure_reset": failure_reset,
			"squat_detail": squat_detail,
		}
	)


def main():
	parser = argparse.ArgumentParser(description="Post-Breakout Monitoring")
	sub = parser.add_subparsers(dest="command", required=True)

	sp = sub.add_parser("monitor", help="Monitor post-breakout behavior")
	sp.add_argument("symbol", help="Ticker symbol")
	sp.add_argument("--entry-price", type=float, required=True, help="Breakout entry price")
	sp.add_argument("--entry-date", required=True, help="Entry date (YYYY-MM-DD)")
	sp.add_argument("--stop-loss", type=float, default=7.0, help="Stop-loss percentage (default: 7.0)")
	sp.set_defaults(func=cmd_monitor)

	args = parser.parse_args()
	args.func(args)


if __name__ == "__main__":
	main()
