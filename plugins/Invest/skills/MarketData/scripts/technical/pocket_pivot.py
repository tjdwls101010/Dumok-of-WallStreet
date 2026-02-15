#!/usr/bin/env python3
"""Pocket Pivot detection for Minervini SEPA methodology.

Detects Pocket Pivot buy signals where an up-day's volume exceeds the maximum
down-day volume in the prior 10 sessions, indicating institutional buying within
a base formation. Provides an alternative entry technique to traditional breakout
buying by identifying accumulation before the pivot point is reached.

Commands:
	detect: Detect pocket pivots in a ticker's recent price action

Args:
	symbol (str): Ticker symbol (e.g., "AAPL", "NVDA", "META")
	--period (str): Historical data period (default: "1y")

Returns:
	dict: {
		"symbol": str,  # ticker symbol
		"date": str,  # analysis date
		"current_price": float,  # latest close
		"pocket_pivots": [dict],  # list of detected pocket pivot events
		"pocket_pivot_count": int,  # total pocket pivots found
		"most_recent_pp": dict,  # summary of the most recent pocket pivot
		"base_context": dict,  # current moving average and base context
	}

Example:
	>>> python pocket_pivot.py detect NVDA --period 1y
	{
		"symbol": "NVDA",
		"date": "2025-12-01",
		"current_price": 142.30,
		"pocket_pivots": [
			{
				"date": "2025-11-15",
				"close": 138.50,
				"volume": 85000000,
				"max_down_vol_10d": 42000000,
				"volume_ratio": 2.02,
				"close_range_pct": 0.75,
				"above_50ma": true,
				"in_base": true,
				"location": "right_side",
				"quality": "high"
			}
		],
		"pocket_pivot_count": 3,
		"most_recent_pp": {
			"date": "2025-11-15",
			"days_ago": 10,
			"quality": "high"
		},
		"base_context": {
			"above_50ma": true,
			"pct_above_50ma": 3.5,
			"pct_above_10ma": 1.2,
			"in_base": true
		}
	}

Use Cases:
	- Identify early institutional accumulation within a base before breakout
	- Find alternative entry points in Stage 2 uptrends without waiting for pivot
	- Confirm constructive base-building activity via volume footprints
	- Filter high-quality pocket pivots for position initiation

Notes:
	- A pocket pivot is an up-day where volume exceeds max down-day volume in prior 10 sessions
	- Close position within day's range >= 50% from low filters weak closes
	- Quality grades: high (vol_ratio >= 2.0, close_range >= 0.7, above 50MA), moderate, low
	- Location classification: right_side (constructive), handle (late-base), extended (risky)
	- Best signals occur above the 50MA and within a base (not extended >10% above 10MA)
	- Scanning window covers the last 60 trading days for recent signals

See Also:
	- vcp.py: VCP detection for base pattern identification
	- volume_analysis.py: Volume pattern analysis for accumulation/distribution
	- stage_analysis.py: Stage classification to confirm Stage 2 context
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import numpy as np
import yfinance as yf
from utils import output_json, safe_run


def _calculate_close_range_pct(close, high, low):
	"""Calculate where the close sits within the day's range.

	Returns a value between 0.0 (closed at the low) and 1.0 (closed at
	the high).  Used to filter pocket pivots that close in the upper
	portion of the day's range, which indicates buying conviction.
	"""
	day_range = high - low
	if day_range <= 0:
		return 0.5
	return round((close - low) / day_range, 2)


def _get_max_down_volume(closes, volumes, idx, lookback=10):
	"""Find the maximum volume on down-days within the prior lookback sessions.

	An down-day is defined as a day where close < prior close.  Returns the
	maximum volume among those down-days, which is the threshold a pocket
	pivot must exceed.
	"""
	start = max(0, idx - lookback)
	max_down_vol = 0

	close_arr = closes.values.astype(float)
	vol_arr = volumes.values.astype(float)

	for i in range(start, idx):
		if i == 0:
			continue
		if close_arr[i] < close_arr[i - 1]:
			if vol_arr[i] > max_down_vol:
				max_down_vol = vol_arr[i]

	return max_down_vol


def _classify_location(pct_above_50ma, pct_above_10ma, in_base):
	"""Classify the pocket pivot's location context.

	right_side: above 50MA and within base (constructive accumulation zone)
	handle: above 50MA but close to breakout area (late-stage base)
	extended: above 50MA but extended beyond 10% above 10MA (risky chase)
	"""
	if not in_base:
		return "extended"
	if pct_above_50ma >= 0 and pct_above_10ma <= 5:
		return "right_side"
	return "handle"


def _grade_pocket_pivot(volume_ratio, close_range_pct, above_50ma):
	"""Assign quality grade to a pocket pivot signal.

	high: volume_ratio >= 2.0 AND close_range >= 0.7 AND above 50MA
	moderate: volume_ratio >= 1.5 AND close_range >= 0.5 AND above 50MA
	low: meets basic pocket pivot criteria but fails higher thresholds
	"""
	if volume_ratio >= 2.0 and close_range_pct >= 0.7 and above_50ma:
		return "high"
	if volume_ratio >= 1.5 and close_range_pct >= 0.5 and above_50ma:
		return "moderate"
	return "low"


def _compute_base_context(current_price, sma50_val, sma10_val):
	"""Compute moving average context for the current price.

	Determines whether price is above the 50MA, the percentage distance
	from both 50MA and 10MA, and whether the stock is in a base
	(not extended >10% above the 10MA).
	"""
	above_50ma = current_price > sma50_val if sma50_val > 0 else False
	pct_above_50ma = round((current_price - sma50_val) / sma50_val * 100, 2) if sma50_val > 0 else 0.0
	pct_above_10ma = round((current_price - sma10_val) / sma10_val * 100, 2) if sma10_val > 0 else 0.0
	in_base = pct_above_10ma <= 10.0

	return {
		"above_50ma": above_50ma,
		"pct_above_50ma": pct_above_50ma,
		"pct_above_10ma": pct_above_10ma,
		"in_base": in_base,
	}


@safe_run
def cmd_detect(args):
	"""Detect pocket pivots in a ticker's price data."""
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

	close_arr = closes.values.astype(float)
	high_arr = highs.values.astype(float)
	low_arr = lows.values.astype(float)
	vol_arr = volumes.values.astype(float)
	dates = data.index

	current_price = round(float(close_arr[-1]), 2)

	# Calculate moving averages
	sma50 = np.full(len(close_arr), np.nan)
	sma10 = np.full(len(close_arr), np.nan)
	for i in range(49, len(close_arr)):
		sma50[i] = np.mean(close_arr[i - 49 : i + 1])
	for i in range(9, len(close_arr)):
		sma10[i] = np.mean(close_arr[i - 9 : i + 1])

	# Scan last 60 trading days for pocket pivots
	scan_start = max(11, len(close_arr) - 60)
	pocket_pivots = []

	for i in range(scan_start, len(close_arr)):
		# Must be an up-day: close > prior close
		if close_arr[i] <= close_arr[i - 1]:
			continue

		# Get max down-day volume in prior 10 sessions
		max_down_vol = _get_max_down_volume(closes, volumes, i, lookback=10)

		# Volume must exceed max down-day volume
		if max_down_vol <= 0 or vol_arr[i] <= max_down_vol:
			continue

		# Validate close position within day's range (>= 50% from low)
		close_range_pct = _calculate_close_range_pct(close_arr[i], high_arr[i], low_arr[i])
		if close_range_pct < 0.5:
			continue

		# Volume ratio
		volume_ratio = round(vol_arr[i] / max_down_vol, 2)

		# Context checks using moving averages at this bar
		above_50ma = bool(not np.isnan(sma50[i]) and close_arr[i] > sma50[i])
		pct_above_50ma = (
			round((close_arr[i] - sma50[i]) / sma50[i] * 100, 2) if not np.isnan(sma50[i]) and sma50[i] > 0 else 0.0
		)
		pct_above_10ma = (
			round((close_arr[i] - sma10[i]) / sma10[i] * 100, 2) if not np.isnan(sma10[i]) and sma10[i] > 0 else 0.0
		)
		in_base = pct_above_10ma <= 10.0

		# Location classification
		location = _classify_location(pct_above_50ma, pct_above_10ma, in_base)

		# Quality grade
		quality = _grade_pocket_pivot(volume_ratio, close_range_pct, above_50ma)

		pocket_pivots.append(
			{
				"date": str(dates[i].date()),
				"close": round(float(close_arr[i]), 2),
				"volume": round(float(vol_arr[i])),
				"max_down_vol_10d": round(float(max_down_vol)),
				"volume_ratio": volume_ratio,
				"close_range_pct": close_range_pct,
				"above_50ma": above_50ma,
				"in_base": in_base,
				"location": location,
				"quality": quality,
			}
		)

	# Most recent pocket pivot summary
	most_recent_pp = None
	if pocket_pivots:
		last_pp = pocket_pivots[-1]
		last_pp_date = last_pp["date"]
		# Calculate days ago from the last trading day
		last_trade_date = str(dates[-1].date())
		days_ago = 0
		for j in range(len(dates) - 1, -1, -1):
			if str(dates[j].date()) == last_pp_date:
				days_ago = len(dates) - 1 - j
				break
		most_recent_pp = {
			"date": last_pp_date,
			"days_ago": days_ago,
			"quality": last_pp["quality"],
		}

	# Current base context
	sma50_current = float(sma50[-1]) if not np.isnan(sma50[-1]) else 0.0
	sma10_current = float(sma10[-1]) if not np.isnan(sma10[-1]) else 0.0
	base_context = _compute_base_context(current_price, sma50_current, sma10_current)

	output_json(
		{
			"symbol": symbol,
			"date": str(dates[-1].date()),
			"current_price": current_price,
			"pocket_pivots": pocket_pivots,
			"pocket_pivot_count": len(pocket_pivots),
			"most_recent_pp": most_recent_pp,
			"base_context": base_context,
		}
	)


def main():
	parser = argparse.ArgumentParser(description="Pocket Pivot Detection")
	sub = parser.add_subparsers(dest="command", required=True)

	sp = sub.add_parser("detect", help="Detect pocket pivots")
	sp.add_argument("symbol", help="Ticker symbol")
	sp.add_argument("--period", default="1y", help="Data period (default: 1y)")
	sp.set_defaults(func=cmd_detect)

	args = parser.parse_args()
	args.func(args)


if __name__ == "__main__":
	main()
