#!/usr/bin/env python3
"""Base Counting: track base number within a Stage 2 advance.

Identifies and counts price bases (consolidation patterns) that form during
a stock's Stage 2 uptrend. Earlier bases (1-2) have higher success rates,
while later bases (4+) carry increased failure risk per Minervini methodology.

Commands:
		count: Count bases and assess current base stage for a ticker

Args:
		symbol (str): Ticker symbol (e.g., "AAPL", "NVDA", "META")
		--period (str): Historical data period (default: "2y")
		--min-base-weeks (int): Minimum weeks for a formation to count as base (default: 3)

Returns:
		dict: {
				"symbol": str,
				"current_base_number": int,
				"base_history": [
						{
								"base_number": int,
								"start_date": str,
								"end_date": str,
								"duration_weeks": int,
								"correction_depth_pct": float,
								"pattern_type": str,
								"relative_correction_ratio": float|null,
								"correction_severity": str
						}
				],
				"base_stage_assessment": str,
				"risk_level": str
		}

Example:
		>>> python base_count.py count NVDA --period 2y
		{
				"symbol": "NVDA",
				"current_base_number": 2,
				"base_history": [
						{"base_number": 1, "start_date": "2025-03-15", "end_date": "2025-06-20",
						 "duration_weeks": 14, "correction_depth_pct": 22.5, "pattern_type": "Cup"},
						{"base_number": 2, "start_date": "2025-09-01", "end_date": "2025-11-15",
						 "duration_weeks": 10, "correction_depth_pct": 15.3, "pattern_type": "Flat Base"}
				],
				"base_stage_assessment": "Early stage - optimal entry zone",
				"risk_level": "low"
		}

Use Cases:
		- Determine if a stock is in early (base 1-2) or late (base 4+) stage
		- Adjust position sizing based on base number risk
		- Identify reset events that restart the base count
		- Track base progression for exit timing

Notes:
		- Base 1-2: Most reliable breakouts, largest average gains
		- Base 3: Still tradeable but less reliable
		- Base 4+: Late stage, higher failure rate, smaller average gains
		- Base count resets after a Stage 4 decline (below 200-day MA for extended period)
		- Typical base duration: 5-26 weeks
		- Correction depth: 10-35% is constructive
		- Relative correction: stock correction / SPY correction during same period
		- correction_severity: normal (<=2x SPY), elevated (<=3x), excessive (>3x), unknown (no SPY data)

See Also:
		- vcp.py: VCP detection within individual bases
		- stage_analysis.py: Stage classification for context
		- volume_analysis.py: Volume patterns during base formation
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import numpy as np
import yfinance as yf
from technical.indicators import calculate_sma
from utils import output_json, safe_run


def _find_bases(closes, highs, lows, sma200, min_base_weeks=3):
	"""Identify bases within a Stage 2 advance.

	A base forms when price pulls back from a high and consolidates
	before breaking out to new highs. Detection logic:
	1. Find local highs (potential base start)
	2. Find subsequent pullback low
	3. Find breakout above prior high (base completion)
	4. Measure duration and depth
	"""
	closes_arr = closes.values.astype(float)
	highs_arr = highs.values.astype(float)
	lows_arr = lows.values.astype(float)
	sma200_arr = sma200.values.astype(float)
	dates = closes.index

	bases = []
	min_base_days = min_base_weeks * 5  # Trading days

	i = 0
	while i < len(closes_arr) - min_base_days:
		# Skip if price is below 200-day MA (not Stage 2)
		if np.isnan(sma200_arr[i]) or closes_arr[i] < sma200_arr[i]:
			i += 1
			continue

		# Find a swing high (local maximum over 10-day window)
		is_high = True
		window = min(10, len(closes_arr) - i - 1)
		for j in range(1, window + 1):
			if i + j < len(highs_arr) and highs_arr[i + j] > highs_arr[i]:
				is_high = False
				break
		for j in range(1, min(10, i + 1)):
			if highs_arr[i - j] > highs_arr[i]:
				is_high = False
				break

		if not is_high:
			i += 1
			continue

		base_high = highs_arr[i]
		base_start_idx = i

		# Find the lowest point after this high (pullback low)
		search_end = min(i + 130, len(lows_arr))  # Max ~26 weeks
		if search_end <= i + min_base_days:
			i += 1
			continue

		segment_lows = lows_arr[i:search_end]
		low_offset = np.argmin(segment_lows)
		base_low_idx = i + low_offset
		base_low = lows_arr[base_low_idx]

		correction_depth = (base_high - base_low) / base_high * 100

		# Skip if correction too shallow (< 5%) or too deep (> 60%)
		if correction_depth < 5 or correction_depth > 60:
			i += 5
			continue

		# Find breakout: price closes above the base high
		breakout_idx = None
		for k in range(base_low_idx, min(base_low_idx + 130, len(closes_arr))):
			if closes_arr[k] > base_high:
				breakout_idx = k
				break

		if breakout_idx is None:
			# Base still forming or failed
			if base_low_idx > len(closes_arr) - 20:
				# Recent base, might still be forming
				duration_days = len(closes_arr) - 1 - base_start_idx
				duration_weeks = max(1, duration_days // 5)
				if duration_weeks >= min_base_weeks:
					bases.append(
						{
							"start_idx": base_start_idx,
							"end_idx": len(closes_arr) - 1,
							"start_date": str(dates[base_start_idx].date()),
							"end_date": str(dates[-1].date()),
							"duration_weeks": duration_weeks,
							"correction_depth_pct": round(correction_depth, 1),
							"high_price": round(base_high, 2),
							"low_price": round(base_low, 2),
							"status": "forming",
						}
					)
			i = base_low_idx + 5
			continue

		duration_days = breakout_idx - base_start_idx
		duration_weeks = max(1, duration_days // 5)

		if duration_weeks >= min_base_weeks:
			bases.append(
				{
					"start_idx": base_start_idx,
					"end_idx": breakout_idx,
					"start_date": str(dates[base_start_idx].date()),
					"end_date": str(dates[breakout_idx].date()),
					"duration_weeks": duration_weeks,
					"correction_depth_pct": round(correction_depth, 1),
					"high_price": round(base_high, 2),
					"low_price": round(base_low, 2),
					"status": "completed",
				}
			)

		i = breakout_idx + 1

	return bases


def _classify_base_pattern(depth, duration_weeks):
	"""Classify base pattern type based on depth and duration."""
	if depth < 15 and duration_weeks >= 5:
		return "Flat Base"
	elif depth >= 15 and depth <= 35 and duration_weeks >= 7:
		return "Cup"
	elif depth < 20 and duration_weeks <= 4:
		return "Power Play"
	elif depth >= 10 and depth <= 25 and duration_weeks >= 3:
		return "Standard Base"
	else:
		return "Wide Base"


def _check_base_reset(closes, sma200):
	"""Check if base count should be reset (Stage 4 decline).

	Reset criteria: price below 200-day MA for 40+ trading days.
	"""
	closes_arr = closes.values.astype(float)
	sma200_arr = sma200.values.astype(float)

	below_200_streak = 0
	reset_points = []

	for i in range(len(closes_arr)):
		if np.isnan(sma200_arr[i]):
			continue
		if closes_arr[i] < sma200_arr[i]:
			below_200_streak += 1
			if below_200_streak == 40:  # 2 months below 200MA = reset
				reset_points.append(i)
		else:
			below_200_streak = 0

	return reset_points


def _compute_relative_correction(dates, start_idx, end_idx, stock_correction_pct):
	"""Compute stock correction depth relative to SPY during the same period.

	Per Minervini (p.211): "stocks that correct more than two or three
	times the decline of the general market should be avoided."
	"""
	start_date = str(dates[start_idx].date())
	end_date = str(dates[end_idx].date())

	try:
		spy = yf.Ticker("SPY")
		spy_data = spy.history(start=start_date, end=end_date, interval="1d")
		if spy_data.empty or len(spy_data) < 5:
			return None, "unknown"

		spy_high = float(spy_data["High"].max())
		spy_low = float(spy_data["Low"].min())
		if spy_high <= 0:
			return None, "unknown"

		spy_correction = (spy_high - spy_low) / spy_high * 100
		if spy_correction < 0.5:
			# SPY barely moved; ratio would be misleading
			return None, "unknown"

		ratio = round(stock_correction_pct / spy_correction, 2)

		if ratio <= 2.0:
			severity = "normal"
		elif ratio <= 3.0:
			severity = "elevated"
		else:
			severity = "excessive"

		return ratio, severity
	except Exception:
		return None, "unknown"


@safe_run
def cmd_count(args):
	"""Count bases and assess current base stage."""
	symbol = args.symbol.upper()
	ticker = yf.Ticker(symbol)
	data = ticker.history(period=args.period, interval="1d")

	if data.empty or len(data) < 200:
		output_json(
			{
				"error": f"Insufficient data for {symbol}. Need at least 200 trading days.",
				"data_points": len(data),
			}
		)
		return

	closes = data["Close"]
	highs = data["High"]
	lows = data["Low"]
	sma200 = calculate_sma(closes, 200)

	# Check for base count resets
	reset_points = _check_base_reset(closes, sma200)

	# Find bases
	all_bases = _find_bases(closes, highs, lows, sma200, args.min_base_weeks)

	# Apply reset: only count bases after the last reset
	if reset_points and all_bases:
		last_reset = reset_points[-1]
		all_bases = [b for b in all_bases if b["start_idx"] > last_reset]

	# Number the bases and compute relative correction
	dates = closes.index
	for i, base in enumerate(all_bases):
		base["base_number"] = i + 1
		base["pattern_type"] = _classify_base_pattern(
			base["correction_depth_pct"],
			base["duration_weeks"],
		)
		# Relative correction vs SPY (computed before index fields are removed)
		ratio, severity = _compute_relative_correction(
			dates, base["start_idx"], base["end_idx"], base["correction_depth_pct"]
		)
		base["relative_correction_ratio"] = ratio
		base["correction_severity"] = severity
		# Remove internal index fields
		base.pop("start_idx", None)
		base.pop("end_idx", None)

	current_base_number = len(all_bases) if all_bases else 0

	# Assessment based on base number
	if current_base_number == 0:
		assessment = "No bases detected - may be pre-Stage 2 or Stage 4"
		risk_level = "unknown"
	elif current_base_number <= 2:
		assessment = "Early stage - optimal entry zone (base 1-2 have highest success rates)"
		risk_level = "low"
	elif current_base_number == 3:
		assessment = "Mid stage - still tradeable but becoming more obvious to market"
		risk_level = "moderate"
	elif current_base_number <= 5:
		assessment = "Late stage - higher failure rate, smaller average gains expected"
		risk_level = "high"
	else:
		assessment = "Very late stage - extreme caution, most breakouts fail at this point"
		risk_level = "very_high"

	# Correction severity adjustment: excessive correction bumps risk up one tier
	if all_bases:
		latest_severity = all_bases[-1].get("correction_severity", "normal")
		if latest_severity == "excessive":
			severity_upgrade = {
				"low": "moderate",
				"moderate": "high",
				"high": "very_high",
			}
			if risk_level in severity_upgrade:
				risk_level = severity_upgrade[risk_level]
				assessment += " (risk elevated due to excessive correction vs SPY)"

	output_json(
		{
			"symbol": symbol,
			"date": str(data.index[-1].date()),
			"current_price": round(float(closes.iloc[-1]), 2),
			"current_base_number": current_base_number,
			"base_history": all_bases,
			"base_stage_assessment": assessment,
			"risk_level": risk_level,
			"base_count_reset_detected": len(reset_points) > 0,
			"analysis_period": args.period,
		}
	)


def main():
	parser = argparse.ArgumentParser(description="Base Counting for Stage 2 Advance")
	sub = parser.add_subparsers(dest="command", required=True)

	sp = sub.add_parser("count", help="Count bases and assess base stage")
	sp.add_argument("symbol", help="Ticker symbol")
	sp.add_argument("--period", default="2y", help="Data period (default: 2y)")
	sp.add_argument("--min-base-weeks", type=int, default=3, help="Minimum weeks per base (default: 3)")
	sp.set_defaults(func=cmd_count)

	args = parser.parse_args()
	args.func(args)


if __name__ == "__main__":
	main()
