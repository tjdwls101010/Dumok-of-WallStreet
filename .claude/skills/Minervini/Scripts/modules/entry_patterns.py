#!/usr/bin/env python3
"""Entry pattern detection for actionable trade setups.

Scans for currently active entry patterns on individual stocks or batches.
Detects MA pullback, consolidation pivot, and support reclaim setups — all
grounded in Minervini's Chapter 10 methodology. Each pattern includes
trigger price, stop price, and quality grading. Persona-neutral module
reusable by any pipeline.

Commands:
	scan: Scan for currently active entry patterns on a single stock
	screen: Batch scan multiple stocks for entry patterns

Args:
	symbol (str): Ticker symbol (e.g., "AAPL", "NVDA", "META")
	symbols (str): Space-separated ticker symbols for screen command

Returns:
	For scan:
	dict: {
		"symbol": str,
		"active_patterns": [
			{
				"pattern": str,
				"trigger_price": float,
				"stop_price": float,
				"stop_pct": float,
				"quality": str,
				...pattern-specific fields
			}
		],
		"pattern_count": int,
		"setup_readiness": {
			"classification": str,
			"thresholds": {...}
		}
	}

	For screen:
	dict: {
		"results": [
			{
				"symbol": str,
				"pattern_count": int,
				"best_pattern": str,
				"best_quality": str,
				"setup_readiness": str
			}
		],
		"ranked_by": "pattern_count"
	}

Example:
	>>> python entry_patterns.py scan NVDA
	{
		"symbol": "NVDA",
		"active_patterns": [
			{
				"pattern": "MA_PULLBACK",
				"ma_type": "21_EMA",
				"distance_pct": 0.3,
				"pullback_volume_ratio": 0.65,
				"trigger_price": 142.50,
				"stop_price": 138.80,
				"stop_pct": 2.6,
				"quality": "high"
			}
		],
		"pattern_count": 1,
		"setup_readiness": {"classification": "actionable", "thresholds": {...}}
	}

Use Cases:
	- Identify low-risk pullback entries into leading stocks
	- Detect consolidation pivot breakout setups
	- Find shakeout recovery (support reclaim) patterns
	- Screen a watchlist for actionable setups ranked by pattern count and quality

Notes:
	- MA_PULLBACK: Price within 1% of 10 SMA, 21 EMA, or 50 SMA with below-avg volume (Ch.10: "lower volume on pullbacks")
	- CONSOLIDATION_PIVOT: 10-25 day tight range (<10%) with trigger above resistance (Ch.10: "pivot point, line of least resistance")
	- SUPPORT_RECLAIM: Undercut 50 SMA then reclaimed with volume (Ch.10: "after a shakeout, rallies back on big volume")
	- Quality: "high" (strongest conviction), "moderate" (developing)
	- stop_pct = abs(trigger_price - stop_price) / trigger_price * 100
	- All calculations use yfinance daily data with 1-year history
	- Minimum 50 trading days required for meaningful analysis

See Also:
	- vcp.py: VCP detection for primary base breakout entries
	- sell_signals.py: Sell signal detection for position management
	- pocket_pivot.py: Pocket pivot buy signals for base accumulation
	- tight_closes.py: Tight close cluster detection for supply drying up
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import numpy as np
import yfinance as yf
from utils import output_json, safe_run


def _stop_pct(entry_price, stop_price):
	"""Calculate stop percentage: abs(entry - stop) / entry * 100."""
	if entry_price <= 0:
		return 0.0
	return round(abs(entry_price - stop_price) / entry_price * 100, 2)


def _detect_ma_pullback(close_arr, vol_arr):
	"""Detect MA_PULLBACK pattern.

	Ch.10: "pullbacks to key MAs with lower volume on pullbacks"
	For each key MA (10 SMA, 21 EMA, 50 SMA):
	- Check if current price is within 1% of the MA
	- Check if pullback volume (last 3 days avg) < 80% of 50-day avg volume
	Quality: high if near 21 EMA or 50 SMA with declining volume; moderate otherwise.
	"""
	n = len(close_arr)
	if n < 50:
		return []

	current_price = float(close_arr[-1])

	# Calculate MAs
	sma10 = np.mean(close_arr[-10:])
	sma50 = np.mean(close_arr[-50:])
	# EMA 21
	ema21_arr = np.full(n, np.nan)
	if n >= 21:
		ema21_arr[20] = np.mean(close_arr[:21])
		mult = 2.0 / (21 + 1)
		for i in range(21, n):
			ema21_arr[i] = close_arr[i] * mult + ema21_arr[i - 1] * (1 - mult)
	ema21 = float(ema21_arr[-1]) if not np.isnan(ema21_arr[-1]) else 0.0

	# Pullback volume: avg of last 3 days
	pullback_vol = float(np.mean(vol_arr[-3:]))
	avg_vol_50 = float(np.mean(vol_arr[-50:]))
	if avg_vol_50 <= 0:
		return []
	pullback_vol_ratio = round(pullback_vol / avg_vol_50, 2)
	low_volume = pullback_vol_ratio < 0.8

	if not low_volume:
		return []

	ma_configs = [
		("10_SMA", sma10),
		("21_EMA", ema21),
		("50_SMA", sma50),
	]

	patterns = []
	for ma_type, ma_val in ma_configs:
		if ma_val <= 0 or np.isnan(ma_val):
			continue

		distance_pct = abs(current_price - ma_val) / ma_val * 100
		if distance_pct > 1.0:
			continue

		trigger_price = round(ma_val * 1.005, 2)
		stop_price = round(ma_val * 0.985, 2)

		if ma_type in ("21_EMA", "50_SMA") and pullback_vol_ratio < 0.8:
			quality = "high"
		else:
			quality = "moderate"

		patterns.append({
			"pattern": "MA_PULLBACK",
			"ma_type": ma_type,
			"distance_pct": round(distance_pct, 2),
			"distance_pct_unit": "% from MA",
			"pullback_volume_ratio": pullback_vol_ratio,
			"pullback_volume_ratio_unit": "3d avg vol / 50d avg vol",
			"trigger_price": trigger_price,
			"stop_price": stop_price,
			"stop_pct": _stop_pct(trigger_price, stop_price),
			"stop_pct_unit": "% risk from trigger to stop",
			"quality": quality,
		})

	return patterns


def _detect_consolidation_pivot(high_arr, low_arr):
	"""Detect CONSOLIDATION_PIVOT pattern.

	Ch.10: "pivot point = line of least resistance after tight consolidation"
	Look at last 10-25 days. Find range high (resistance) = max(High).
	Range is tight if (max High - min Low) / min Low < 10%.
	"""
	n = len(high_arr)
	if n < 10:
		return []

	for window in range(min(25, n), 9, -1):
		segment_high = high_arr[-window:]
		segment_low = low_arr[-window:]

		resistance = float(np.max(segment_high))
		support = float(np.min(segment_low))

		if support <= 0:
			continue

		range_pct = (resistance - support) / support * 100
		if range_pct >= 10.0:
			continue

		pivot_price = round(resistance, 2)
		trigger_price = round(resistance * 1.003, 2)
		stop_price = round(support, 2)

		if range_pct < 7.0 and window >= 15:
			quality = "high"
		else:
			quality = "moderate"

		return [{
			"pattern": "CONSOLIDATION_PIVOT",
			"pivot_price": pivot_price,
			"range_pct": round(range_pct, 2),
			"range_pct_unit": "% price range over N days",
			"days_in_range": window,
			"trigger_price": trigger_price,
			"stop_price": stop_price,
			"stop_pct": _stop_pct(trigger_price, stop_price),
			"stop_pct_unit": "% risk from trigger to stop",
			"quality": quality,
		}]

	return []


def _detect_support_reclaim(close_arr, low_arr, vol_arr, dates):
	"""Detect SUPPORT_RECLAIM pattern.

	Ch.10: "After a price shakeout, it's a good sign if the stock rallies back
	on big volume." Detects undercut of 50 SMA by >1% within last 5 days,
	followed by reclaim above 50 SMA. Volume surge on reclaim = higher quality.
	"""
	n = len(close_arr)
	if n < 50:
		return []

	sma50_current = float(np.mean(close_arr[-50:]))
	if sma50_current <= 0:
		return []

	# Current close must be above 50 SMA (reclaimed)
	if close_arr[-1] <= sma50_current:
		return []

	# Check last 5 days for undercut (Low < 50 SMA * 0.99)
	for offset in range(1, 6):
		idx = n - 1 - offset
		if idx < 49:
			break

		sma50_at_idx = float(np.mean(close_arr[idx - 49 : idx + 1]))
		if sma50_at_idx <= 0:
			continue

		if low_arr[idx] < sma50_at_idx * 0.99:
			undercut_pct = round((sma50_at_idx - low_arr[idx]) / sma50_at_idx * 100, 2)

			# Volume surge check: reclaim day volume vs 50d avg
			avg_vol_50 = float(np.mean(vol_arr[-50:]))
			reclaim_vol = float(vol_arr[-1])
			vol_surge = reclaim_vol > avg_vol_50 * 1.5 if avg_vol_50 > 0 else False

			# Quality: "high" if volume surge on reclaim (Minervini: "rallies back on big volume")
			quality = "high" if vol_surge else "moderate"

			trigger_price = round(sma50_current, 2)
			stop_price = round(float(low_arr[idx]), 2)

			return [{
				"pattern": "SUPPORT_RECLAIM",
				"support_level": round(sma50_current, 2),
				"undercut_pct": undercut_pct,
				"undercut_pct_unit": "% below 50 SMA",
				"reclaim_date": str(dates[-1].date()),
				"volume_surge_on_reclaim": vol_surge,
				"trigger_price": trigger_price,
				"stop_price": stop_price,
				"stop_pct": _stop_pct(trigger_price, stop_price),
				"stop_pct_unit": "% risk from trigger to stop",
				"quality": quality,
			}]

	return []


def _determine_readiness(patterns):
	"""Determine setup readiness from detected patterns."""
	if not patterns:
		classification = "none"
	elif any(p["quality"] == "high" for p in patterns):
		classification = "actionable"
	elif any(p["quality"] == "moderate" for p in patterns):
		classification = "developing"
	else:
		classification = "none"

	return {
		"classification": classification,
		"thresholds": {
			"actionable": "1+ high-quality pattern",
			"developing": "1+ moderate-quality pattern (no high)",
			"none": "no patterns detected",
		},
	}


def _scan_symbol(symbol):
	"""Core scan logic for a single symbol. Returns the result dict."""
	ticker = yf.Ticker(symbol)
	data = ticker.history(period="1y", interval="1d")

	if data.empty or len(data) < 50:
		return {
			"error": f"Insufficient data for {symbol}. Need at least 50 trading days.",
			"data_points": len(data),
		}

	close_arr = data["Close"].values.astype(float)
	high_arr = data["High"].values.astype(float)
	low_arr = data["Low"].values.astype(float)
	vol_arr = data["Volume"].values.astype(float)
	dates = data.index

	# Run detectors (Minervini-grounded patterns only)
	active_patterns = []
	active_patterns.extend(_detect_ma_pullback(close_arr, vol_arr))
	active_patterns.extend(_detect_consolidation_pivot(high_arr, low_arr))
	active_patterns.extend(_detect_support_reclaim(close_arr, low_arr, vol_arr, dates))

	return {
		"symbol": symbol,
		"active_patterns": active_patterns,
		"pattern_count": len(active_patterns),
		"setup_readiness": _determine_readiness(active_patterns),
	}


@safe_run
def cmd_scan(args):
	"""Scan for currently active entry patterns on a single stock."""
	symbol = args.symbol.upper()
	result = _scan_symbol(symbol)
	output_json(result)


@safe_run
def cmd_screen(args):
	"""Batch scan multiple stocks for entry patterns."""
	symbols = [s.upper() for s in args.symbols]
	results = []

	for symbol in symbols:
		scan = _scan_symbol(symbol)

		if "error" in scan:
			results.append({
				"symbol": symbol,
				"pattern_count": 0,
				"best_pattern": None,
				"best_quality": None,
				"setup_readiness": "none",
			})
			continue

		best_pattern = None
		best_quality = None
		quality_rank = {"high": 2, "moderate": 1}

		for p in scan["active_patterns"]:
			q = p["quality"]
			if best_quality is None or quality_rank.get(q, 0) > quality_rank.get(best_quality, 0):
				best_pattern = p["pattern"]
				best_quality = q

		sr = scan["setup_readiness"]
		results.append({
			"symbol": symbol,
			"pattern_count": scan["pattern_count"],
			"best_pattern": best_pattern,
			"best_quality": best_quality,
			"setup_readiness": sr["classification"] if isinstance(sr, dict) else sr,
		})

	results.sort(key=lambda r: r["pattern_count"], reverse=True)

	output_json({
		"results": results,
		"ranked_by": "pattern_count",
	})


def main():
	parser = argparse.ArgumentParser(description="Entry Pattern Detection")
	sub = parser.add_subparsers(dest="command", required=True)

	sp = sub.add_parser("scan", help="Scan entry patterns for a single stock")
	sp.add_argument("symbol", help="Ticker symbol")
	sp.set_defaults(func=cmd_scan)

	sp = sub.add_parser("screen", help="Batch scan multiple stocks")
	sp.add_argument("symbols", nargs="+", help="Ticker symbols")
	sp.set_defaults(func=cmd_screen)

	args = parser.parse_args()
	args.func(args)


if __name__ == "__main__":
	main()
