#!/usr/bin/env python3
"""Low Cheat Setup detection for Minervini SEPA methodology.

Detects tight consolidation zones just below a pivot price, allowing entry at a
lower price than the actual pivot breakout. This reduces risk because the
stop-loss distance is smaller, giving a better risk/reward ratio compared to
buying at the pivot.

Commands:
	detect: Detect low cheat setup opportunities

Args:
	symbol (str): Ticker symbol (e.g., "AAPL", "NVDA", "META")
	--period (str): Historical data period (default: "1y")

Returns:
	dict: {
		"symbol": str,
		"date": str,
		"current_price": float,
		"low_cheat_detected": bool,
		"pivot_price": float,
		"tight_zone": {
			"start_date": str,
			"end_date": str,
			"duration_days": int,
			"min_close": float,
			"max_close": float,
			"range_pct": float,
			"min_low": float,
			"max_high": float
		},
		"volume_analysis": {
			"tight_zone_avg_vol": int,
			"vol_50d_avg": int,
			"volume_dryup_ratio": float
		},
		"entry_analysis": {
			"low_cheat_entry": float,
			"stop_loss": float,
			"risk_pct": float,
			"pivot_entry": float,
			"pivot_entry_risk": float,
			"risk_reduction_pct": float
		},
		"quality": str
	}

	When no low cheat is detected:
	dict: {
		"symbol": str,
		"date": str,
		"current_price": float,
		"low_cheat_detected": false,
		"pivot_price": float,
		"reason": str
	}

Example:
	>>> python low_cheat.py detect NVDA --period 1y
	{
		"symbol": "NVDA",
		"date": "2025-12-01",
		"current_price": 142.30,
		"low_cheat_detected": true,
		"pivot_price": 145.00,
		"tight_zone": {
			"start_date": "2025-11-20",
			"end_date": "2025-11-29",
			"duration_days": 8,
			"min_close": 140.50,
			"max_close": 141.80,
			"range_pct": 0.93,
			"min_low": 139.80,
			"max_high": 142.10
		},
		"volume_analysis": {
			"tight_zone_avg_vol": 32000000,
			"vol_50d_avg": 65000000,
			"volume_dryup_ratio": 0.49
		},
		"entry_analysis": {
			"low_cheat_entry": 141.94,
			"stop_loss": 139.10,
			"risk_pct": 2.0,
			"pivot_entry": 145.00,
			"pivot_entry_risk": 4.07,
			"risk_reduction_pct": 50.9
		},
		"quality": "high"
	}

Use Cases:
	- Enter a stock below the pivot for reduced risk and better R/R ratio
	- Identify tight, low-volume consolidations that precede breakouts
	- Compare low cheat entry risk vs standard pivot entry risk
	- Grade setup quality for position sizing decisions

Notes:
	- Pivot is identified as the highest swing high in the last 60 trading days
	- Tight zone requires range < 3%, within 5% below pivot, minimum 3 days
	- Volume dryup ratio < 0.5 with range < 1.5% indicates institutional accumulation
	- Quality grades: high, moderate, low based on tightness, volume, and duration
	- Risk reduction of 30%+ is typical for well-formed low cheat setups

See Also:
	- vcp.py: VCP detection for base patterns
	- pocket_pivot.py: Alternative entry via pocket pivots
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import numpy as np
import yfinance as yf
from utils import output_json, safe_run


def _find_swing_highs(highs, window=5):
	"""Find swing highs in price data.

	A swing high is a high that is higher than `window` bars on each side.
	Returns a list of (index, price) tuples.
	"""
	highs_arr = highs.values.astype(float)
	swing_highs = []

	for i in range(window, len(highs_arr) - window):
		if all(highs_arr[i] >= highs_arr[i - j] for j in range(1, window + 1)) and all(
			highs_arr[i] >= highs_arr[i + j] for j in range(1, window + 1)
		):
			swing_highs.append((i, highs_arr[i]))

	return swing_highs


def _find_pivot_price(swing_highs, total_bars, lookback=60):
	"""Get the highest swing high in the last `lookback` trading days.

	Returns (pivot_index, pivot_price) or (None, None) if no swing highs
	exist within the lookback window.
	"""
	cutoff = total_bars - lookback
	recent_highs = [(idx, price) for idx, price in swing_highs if idx >= cutoff]

	if not recent_highs:
		return None, None

	best = max(recent_highs, key=lambda x: x[1])
	return best[0], best[1]


def _find_tight_zone(closes, lows, highs, volumes, pivot_price, lookback=20):
	"""Scan the last `lookback` days for a tight consolidation zone below the pivot.

	Criteria:
	- Range < 3% ((max_close - min_close) / min_close * 100)
	- All closes in the zone must be >= pivot_price * 0.95 (within 5% below pivot)
	- Minimum 3 consecutive days in the zone

	Returns a dict with tight zone details, or None if no zone is found.
	"""
	close_arr = closes.values.astype(float)
	low_arr = lows.values.astype(float)
	high_arr = highs.values.astype(float)
	vol_arr = volumes.values.astype(float)
	dates = closes.index

	n = len(close_arr)
	scan_start = max(0, n - lookback)
	threshold = pivot_price * 0.95

	best_zone = None
	best_duration = 0

	# Sliding window approach: try all contiguous windows of length >= 3
	for start in range(scan_start, n):
		# Check if starting close is within 5% below pivot
		if close_arr[start] < threshold:
			continue
		# The close must be below pivot (otherwise it's a breakout, not a cheat)
		if close_arr[start] >= pivot_price:
			continue

		for end in range(start + 2, n):  # minimum 3 days (start, start+1, end)
			segment_closes = close_arr[start : end + 1]
			seg_min_close = float(np.min(segment_closes))
			seg_max_close = float(np.max(segment_closes))

			# All closes must be within 5% below pivot and below pivot
			if seg_min_close < threshold:
				break
			if seg_max_close >= pivot_price:
				break

			# Range check
			range_pct = (seg_max_close - seg_min_close) / seg_min_close * 100 if seg_min_close > 0 else 999
			if range_pct >= 3.0:
				break

			duration = end - start + 1
			if duration >= 3 and duration > best_duration:
				seg_lows = low_arr[start : end + 1]
				seg_highs = high_arr[start : end + 1]
				seg_vols = vol_arr[start : end + 1]

				best_zone = {
					"start_idx": start,
					"end_idx": end,
					"start_date": str(dates[start].date()),
					"end_date": str(dates[end].date()),
					"duration_days": duration,
					"min_close": round(seg_min_close, 2),
					"max_close": round(seg_max_close, 2),
					"range_pct": round(range_pct, 2),
					"min_low": round(float(np.min(seg_lows)), 2),
					"max_high": round(float(np.max(seg_highs)), 2),
					"avg_vol": round(float(np.mean(seg_vols))),
				}
				best_duration = duration

	return best_zone


def _calculate_entry_risk(tight_zone, pivot_price):
	"""Calculate low cheat entry, stop loss, and risk comparison vs pivot entry.

	Entry: max close in tight zone + 0.1% buffer
	Stop: min low in tight zone - 0.5% buffer
	"""
	low_cheat_entry = round(tight_zone["max_close"] * 1.001, 2)
	stop_loss = round(tight_zone["min_low"] * 0.995, 2)

	risk_pct = round((low_cheat_entry - stop_loss) / low_cheat_entry * 100, 2) if low_cheat_entry > 0 else 0.0
	pivot_entry_risk = round((pivot_price - stop_loss) / pivot_price * 100, 2) if pivot_price > 0 else 0.0
	risk_reduction_pct = (
		round((pivot_entry_risk - risk_pct) / pivot_entry_risk * 100, 1) if pivot_entry_risk > 0 else 0.0
	)

	return {
		"low_cheat_entry": low_cheat_entry,
		"stop_loss": stop_loss,
		"risk_pct": risk_pct,
		"pivot_entry": round(pivot_price, 2),
		"pivot_entry_risk": pivot_entry_risk,
		"risk_reduction_pct": risk_reduction_pct,
	}


def _grade_quality(tight_zone, volume_dryup_ratio):
	"""Assess quality grade of the low cheat setup.

	High:     range < 1.5%, volume_dryup_ratio < 0.5, duration >= 5 days
	Moderate: range < 2.5%, volume_dryup_ratio < 0.7, duration >= 3 days
	Low:      everything else that meets basic criteria (range < 3%, within 5% of pivot)
	"""
	range_pct = tight_zone["range_pct"]
	duration = tight_zone["duration_days"]

	if range_pct < 1.5 and volume_dryup_ratio < 0.5 and duration >= 5:
		return "high"
	elif range_pct < 2.5 and volume_dryup_ratio < 0.7 and duration >= 3:
		return "moderate"
	else:
		return "low"


@safe_run
def cmd_detect(args):
	"""Detect low cheat setup in a ticker's price data."""
	symbol = args.symbol.upper()
	ticker = yf.Ticker(symbol)
	data = ticker.history(period=args.period, interval="1d")

	if data.empty or len(data) < 60:
		output_json(
			{
				"error": f"Insufficient data for {symbol}. Need at least 60 trading days.",
				"data_points": len(data),
			}
		)
		return

	closes = data["Close"]
	highs = data["High"]
	lows = data["Low"]
	volumes = data["Volume"]
	current_price = round(float(closes.iloc[-1]), 2)
	analysis_date = str(data.index[-1].date())

	# Step 1: Find swing highs using 5-bar confirmation
	swing_highs = _find_swing_highs(highs, window=5)

	# Step 2: Identify pivot price (highest swing high in last 60 days)
	pivot_idx, pivot_price = _find_pivot_price(swing_highs, len(data), lookback=60)

	if pivot_price is None:
		output_json(
			{
				"symbol": symbol,
				"date": analysis_date,
				"current_price": current_price,
				"low_cheat_detected": False,
				"pivot_price": None,
				"reason": "No swing highs found in last 60 trading days",
			}
		)
		return

	pivot_price = round(pivot_price, 2)

	# Step 3: Scan last 20 days for tight consolidation zone
	tight_zone = _find_tight_zone(closes, lows, highs, volumes, pivot_price, lookback=20)

	if tight_zone is None:
		output_json(
			{
				"symbol": symbol,
				"date": analysis_date,
				"current_price": current_price,
				"low_cheat_detected": False,
				"pivot_price": pivot_price,
				"reason": "No tight consolidation within 5% below pivot in last 20 days",
			}
		)
		return

	# Step 4: Volume dryup analysis
	vol_arr = volumes.values.astype(float)
	tight_zone_avg_vol = tight_zone["avg_vol"]
	vol_50d_avg = round(float(np.mean(vol_arr[-50:]))) if len(vol_arr) >= 50 else round(float(np.mean(vol_arr)))
	volume_dryup_ratio = round(tight_zone_avg_vol / vol_50d_avg, 2) if vol_50d_avg > 0 else 1.0

	# Step 5: Calculate entry and risk
	entry_analysis = _calculate_entry_risk(tight_zone, pivot_price)

	# Step 6: Quality grade
	quality = _grade_quality(tight_zone, volume_dryup_ratio)

	# Build output
	output_json(
		{
			"symbol": symbol,
			"date": analysis_date,
			"current_price": current_price,
			"low_cheat_detected": True,
			"pivot_price": pivot_price,
			"tight_zone": {
				"start_date": tight_zone["start_date"],
				"end_date": tight_zone["end_date"],
				"duration_days": tight_zone["duration_days"],
				"min_close": tight_zone["min_close"],
				"max_close": tight_zone["max_close"],
				"range_pct": tight_zone["range_pct"],
				"min_low": tight_zone["min_low"],
				"max_high": tight_zone["max_high"],
			},
			"volume_analysis": {
				"tight_zone_avg_vol": tight_zone_avg_vol,
				"vol_50d_avg": vol_50d_avg,
				"volume_dryup_ratio": volume_dryup_ratio,
			},
			"entry_analysis": entry_analysis,
			"quality": quality,
		}
	)


def main():
	parser = argparse.ArgumentParser(description="Low Cheat Setup Detection")
	sub = parser.add_subparsers(dest="command", required=True)

	sp = sub.add_parser("detect", help="Detect low cheat setups")
	sp.add_argument("symbol", help="Ticker symbol")
	sp.add_argument("--period", default="1y", help="Data period (default: 1y)")
	sp.set_defaults(func=cmd_detect)

	args = parser.parse_args()
	args.func(args)


if __name__ == "__main__":
	main()
