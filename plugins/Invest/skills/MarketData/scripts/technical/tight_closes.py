#!/usr/bin/env python3
"""Tight Closes detection for Minervini SEPA methodology.

Detects clusters of consecutive trading days/weeks where closing prices fall
within a narrow range, indicating supply drying up and potential breakout
setup. Scans multiple window sizes, merges overlapping clusters, and grades
each cluster by spread tightness, volume behavior, and location relative to
the recent price structure.

Commands:
	daily: Detect tight closes on daily data
	weekly: Detect tight closes on weekly data

Args:
	symbol (str): Ticker symbol (e.g., "AAPL", "NVDA", "META")
	--period (str): Historical data period (default: "6mo" for daily, "1y" for weekly)
	--tolerance (float): Close range tolerance percentage (default: 1.0 for daily, 1.5 for weekly)

Returns:
	dict: {
		"symbol": str,
		"date": str,
		"current_price": float,
		"interval": str,
		"tight_close_clusters": [
			{
				"start_date": str,
				"end_date": str,
				"duration_days": int,
				"min_close": float,
				"max_close": float,
				"spread_pct": float,
				"avg_close": float,
				"volume_trend": str,
				"volume_dryup_ratio": float,
				"location": str,
				"quality": str
			}
		],
		"cluster_count": int,
		"best_cluster": {
			"start_date": str,
			"end_date": str,
			"spread_pct": float,
			"quality": str
		},
		"signal_strength": str
	}

Example:
	>>> python tight_closes.py daily NVDA --period 6mo
	{
		"symbol": "NVDA",
		"date": "2025-12-01",
		"current_price": 142.30,
		"interval": "daily",
		"tight_close_clusters": [
			{
				"start_date": "2025-11-10",
				"end_date": "2025-11-18",
				"duration_days": 7,
				"min_close": 139.50,
				"max_close": 140.80,
				"spread_pct": 0.93,
				"avg_close": 140.15,
				"volume_trend": "declining",
				"volume_dryup_ratio": 0.62,
				"location": "pivot_area",
				"quality": "high"
			}
		],
		"cluster_count": 1,
		"best_cluster": {
			"start_date": "2025-11-10",
			"end_date": "2025-11-18",
			"spread_pct": 0.93,
			"quality": "high"
		},
		"signal_strength": "strong"
	}

	>>> python tight_closes.py weekly NVDA --period 1y
	{
		"symbol": "NVDA",
		"interval": "weekly",
		"tight_close_clusters": [...],
		"signal_strength": "strong"
	}

Use Cases:
	- Identify supply drying up before breakout
	- Confirm VCP pattern tightening near pivot area
	- Detect institutional accumulation via low-volume tight price action
	- Compare daily vs weekly tight close signals for confluence

Notes:
	- Tight closes indicate decreasing selling pressure and supply exhaustion
	- Sliding window scan uses sizes 3-20 for daily, 2-10 for weekly
	- Overlapping clusters are merged, keeping the longest span
	- Volume dryup ratio < 0.7 indicates significant supply reduction
	- Location classification: pivot_area (within 3% of recent high),
	  base_consolidation (>3% below high, in base range),
	  pullback (lower half of recent range)
	- Daily quality: high (spread < 1%, vol declining, pivot, 5+ days),
	  moderate (spread < 1.5%, partial criteria, 3+ days), low (basic)
	- Weekly quality: high (spread < 1.5%, vol declining, 3+ weeks),
	  moderate (spread < 2%, 2+ weeks), low (basic)
	- Weekly signals carry higher weight than daily in signal_strength

See Also:
	- vcp.py: VCP detection with progressive contraction tightening
	- volume_analysis.py: Volume confirmation for breakout validation
	- base_count.py: Base counting context for position risk assessment
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import numpy as np
import yfinance as yf
from utils import output_json, safe_run


def _find_tight_clusters(closes, volumes, tolerance_pct, min_duration):
	"""Scan for consecutive close clusters within tolerance using sliding windows.

	Uses multiple window sizes (min_duration to max_window) to find all
	possible tight close clusters. For each window position, checks if
	the spread between max and min close is within tolerance.
	"""
	close_arr = closes.values.astype(float)
	vol_arr = volumes.values.astype(float)
	dates = closes.index
	n = len(close_arr)
	max_window = min(20, n)

	raw_clusters = []

	for window in range(min_duration, max_window + 1):
		for start in range(n - window + 1):
			end = start + window - 1
			segment = close_arr[start : end + 1]
			min_close = float(np.min(segment))
			max_close = float(np.max(segment))

			if min_close <= 0:
				continue

			spread_pct = (max_close - min_close) / min_close * 100

			if spread_pct <= tolerance_pct:
				avg_close = float(np.mean(segment))
				vol_segment = vol_arr[start : end + 1]
				avg_volume = float(np.mean(vol_segment))

				raw_clusters.append(
					{
						"start_idx": start,
						"end_idx": end,
						"start_date": str(dates[start].date()),
						"end_date": str(dates[end].date()),
						"duration": end - start + 1,
						"min_close": round(min_close, 2),
						"max_close": round(max_close, 2),
						"spread_pct": round(spread_pct, 2),
						"avg_close": round(avg_close, 2),
						"avg_volume": round(avg_volume),
					}
				)

	return raw_clusters


def _merge_overlapping_clusters(clusters):
	"""Merge overlapping clusters, keeping the longest span.

	Sorts clusters by start index then end index descending. When two
	clusters overlap, the longer one absorbs the shorter one.
	"""
	if not clusters:
		return []

	# Sort by start_idx ascending, then by duration descending (keep longest)
	sorted_clusters = sorted(clusters, key=lambda c: (c["start_idx"], -c["duration"]))

	merged = []
	current = sorted_clusters[0]

	for cluster in sorted_clusters[1:]:
		# Check overlap: next cluster starts before current ends
		if cluster["start_idx"] <= current["end_idx"]:
			# Keep the one with longer duration
			if cluster["duration"] > current["duration"]:
				current = cluster
			# If same duration, keep the one with tighter spread
			elif cluster["duration"] == current["duration"] and cluster["spread_pct"] < current["spread_pct"]:
				current = cluster
		else:
			merged.append(current)
			current = cluster

	merged.append(current)
	return merged


def _classify_location(cluster, closes, highs):
	"""Determine cluster location relative to recent price structure.

	pivot_area: cluster avg close within 3% of recent high (potential breakout zone)
	base_consolidation: more than 3% below high but in upper half of range
	pullback: lower half of recent price range
	"""
	close_arr = closes.values.astype(float)
	high_arr = highs.values.astype(float)

	# Use data up to and including the cluster end
	end_idx = min(cluster["end_idx"] + 1, len(high_arr))
	lookback = min(50, end_idx)
	recent_highs = high_arr[end_idx - lookback : end_idx]
	recent_closes = close_arr[end_idx - lookback : end_idx]

	if len(recent_highs) == 0 or len(recent_closes) == 0:
		return "base_consolidation"

	recent_high = float(np.max(recent_highs))
	recent_low = float(np.min(recent_closes))
	avg_close = cluster["avg_close"]

	if recent_high <= 0:
		return "base_consolidation"

	pct_from_high = (recent_high - avg_close) / recent_high * 100

	if pct_from_high <= 3.0:
		return "pivot_area"

	# Check if in upper or lower half of range
	price_range = recent_high - recent_low
	if price_range > 0:
		position_in_range = (avg_close - recent_low) / price_range
		if position_in_range >= 0.5:
			return "base_consolidation"

	return "pullback"


def _compute_volume_metrics(cluster, volumes, vol_50d_avg):
	"""Compute volume trend and dryup ratio for a cluster.

	Volume trend compares average volume of first half vs second half.
	Dryup ratio compares cluster average volume to 50-day average volume.
	"""
	vol_arr = volumes.values.astype(float)
	start = cluster["start_idx"]
	end = cluster["end_idx"]
	segment = vol_arr[start : end + 1]

	if len(segment) < 2:
		return "flat", 1.0

	mid = len(segment) // 2
	first_half_avg = float(np.mean(segment[:mid])) if mid > 0 else float(segment[0])
	second_half_avg = float(np.mean(segment[mid:])) if mid < len(segment) else float(segment[-1])

	if first_half_avg > 0:
		ratio = second_half_avg / first_half_avg
		if ratio < 0.85:
			volume_trend = "declining"
		elif ratio > 1.15:
			volume_trend = "increasing"
		else:
			volume_trend = "flat"
	else:
		volume_trend = "flat"

	cluster_avg_vol = float(np.mean(segment))
	if vol_50d_avg > 0:
		dryup_ratio = round(cluster_avg_vol / vol_50d_avg, 2)
	else:
		dryup_ratio = 1.0

	return volume_trend, dryup_ratio


def _grade_cluster(cluster, interval):
	"""Assign quality grade to a tight close cluster.

	Daily grading:
	  high: spread < 1%, volume declining, location = pivot_area, duration >= 5
	  moderate: spread < 1.5%, (volume declining OR dryup < 0.7), duration >= 3
	  low: everything else meeting basic criteria

	Weekly grading:
	  high: spread < 1.5%, volume declining, duration >= 3
	  moderate: spread < 2%, duration >= 2
	  low: everything else
	"""
	spread = cluster["spread_pct"]
	vol_trend = cluster["volume_trend"]
	dryup = cluster["volume_dryup_ratio"]
	location = cluster["location"]
	duration = cluster["duration_days"]

	if interval == "daily":
		if spread < 1.0 and vol_trend == "declining" and location == "pivot_area" and duration >= 5:
			return "high"
		if spread < 1.5 and (vol_trend == "declining" or dryup < 0.7) and duration >= 3:
			return "moderate"
		return "low"
	else:
		# weekly
		if spread < 1.5 and vol_trend == "declining" and duration >= 3:
			return "high"
		if spread < 2.0 and duration >= 2:
			return "moderate"
		return "low"


def _determine_signal_strength(clusters):
	"""Determine overall signal strength from cluster qualities.

	strong: any high-quality cluster exists
	moderate: any moderate-quality cluster exists
	weak: only low-quality clusters
	none: no tight close clusters found
	"""
	if not clusters:
		return "none"

	qualities = [c["quality"] for c in clusters]

	if "high" in qualities:
		return "strong"
	if "moderate" in qualities:
		return "moderate"
	return "weak"


def _analyze_tight_closes(data, interval, tolerance_pct):
	"""Shared analysis logic for both daily and weekly tight close detection.

	Downloads data, scans for tight close clusters, merges overlapping,
	classifies location, grades quality, and determines signal strength.
	"""
	closes = data["Close"]
	highs = data["High"]
	volumes = data["Volume"]
	current_price = round(float(closes.iloc[-1]), 2)
	date_str = str(data.index[-1].date())

	vol_arr = volumes.values.astype(float)
	vol_50d_avg = float(np.mean(vol_arr[-50:])) if len(vol_arr) >= 50 else float(np.mean(vol_arr))

	# Set min duration based on interval
	if interval == "daily":
		min_duration = 3
	else:
		min_duration = 2

	# Find all tight close clusters
	raw_clusters = _find_tight_clusters(closes, volumes, tolerance_pct, min_duration)

	# Merge overlapping clusters
	merged = _merge_overlapping_clusters(raw_clusters)

	# Enrich each cluster with volume metrics, location, and quality grade
	enriched_clusters = []
	for cluster in merged:
		location = _classify_location(cluster, closes, highs)
		volume_trend, dryup_ratio = _compute_volume_metrics(cluster, volumes, vol_50d_avg)

		enriched = {
			"start_date": cluster["start_date"],
			"end_date": cluster["end_date"],
			"duration_days": cluster["duration"],
			"min_close": cluster["min_close"],
			"max_close": cluster["max_close"],
			"spread_pct": cluster["spread_pct"],
			"avg_close": cluster["avg_close"],
			"volume_trend": volume_trend,
			"volume_dryup_ratio": dryup_ratio,
			"location": location,
		}

		quality = _grade_cluster(enriched, interval)
		enriched["quality"] = quality
		enriched_clusters.append(enriched)

	# Determine best cluster (highest quality, then longest duration, then tightest spread)
	quality_order = {"high": 0, "moderate": 1, "low": 2}
	best_cluster = None
	if enriched_clusters:
		sorted_clusters = sorted(
			enriched_clusters,
			key=lambda c: (quality_order.get(c["quality"], 3), -c["duration_days"], c["spread_pct"]),
		)
		best = sorted_clusters[0]
		best_cluster = {
			"start_date": best["start_date"],
			"end_date": best["end_date"],
			"spread_pct": best["spread_pct"],
			"quality": best["quality"],
		}

	signal_strength = _determine_signal_strength(enriched_clusters)

	return {
		"symbol": None,  # filled by caller
		"date": date_str,
		"current_price": current_price,
		"interval": interval,
		"tight_close_clusters": enriched_clusters,
		"cluster_count": len(enriched_clusters),
		"best_cluster": best_cluster,
		"signal_strength": signal_strength,
	}


@safe_run
def cmd_daily(args):
	"""Detect tight closes on daily price data."""
	symbol = args.symbol.upper()
	ticker = yf.Ticker(symbol)
	data = ticker.history(period=args.period, interval="1d")

	if data.empty or len(data) < 20:
		output_json(
			{
				"error": f"Insufficient data for {symbol}. Need at least 20 trading days.",
				"data_points": len(data),
			}
		)
		return

	result = _analyze_tight_closes(data, "daily", args.tolerance)
	result["symbol"] = symbol

	output_json(result)


@safe_run
def cmd_weekly(args):
	"""Detect tight closes on weekly price data."""
	symbol = args.symbol.upper()
	ticker = yf.Ticker(symbol)
	data = ticker.history(period=args.period, interval="1wk")

	if data.empty or len(data) < 20:
		output_json(
			{
				"error": f"Insufficient data for {symbol}. Need at least 20 weekly bars.",
				"data_points": len(data),
			}
		)
		return

	result = _analyze_tight_closes(data, "weekly", args.tolerance)
	result["symbol"] = symbol

	output_json(result)


def main():
	parser = argparse.ArgumentParser(description="Tight Closes Detection")
	sub = parser.add_subparsers(dest="command", required=True)

	# daily
	sp = sub.add_parser("daily", help="Detect tight closes on daily data")
	sp.add_argument("symbol", help="Ticker symbol")
	sp.add_argument("--period", default="6mo", help="Data period (default: 6mo)")
	sp.add_argument("--tolerance", type=float, default=1.0, help="Close tolerance %% (default: 1.0)")
	sp.set_defaults(func=cmd_daily)

	# weekly
	sp = sub.add_parser("weekly", help="Detect tight closes on weekly data")
	sp.add_argument("symbol", help="Ticker symbol")
	sp.add_argument("--period", default="1y", help="Data period (default: 1y)")
	sp.add_argument("--tolerance", type=float, default=1.5, help="Close tolerance %% (default: 1.5)")
	sp.set_defaults(func=cmd_weekly)

	args = parser.parse_args()
	args.func(args)


if __name__ == "__main__":
	main()
