#!/usr/bin/env python3
"""Closing Range & Bar Classification: price action quality assessment.

Analyzes where price closes within the day's range (Closing Range) and
classifies daily bars as Constructive or Non-Constructive based on the
relationship between price action and volume. Key tool for TraderLion's
methodology to evaluate institutional conviction and supply/demand dynamics.

Constructive bars indicate controlled institutional accumulation (high close
on low volume, or price advance on quiet volume). Non-constructive bars
signal distribution or lack of demand (low close on high volume, or price
decline on heavy volume).

Commands:
	analyze: Single stock Closing Range analysis with bar classification
	screen: Multiple stocks Constructive bar ratio comparison

Args:
	symbol (str): Ticker symbol (e.g., "AAPL", "NVDA", "META")
	symbols (list[str]): Multiple ticker symbols for screening
	--period (str): Historical data period (default: "6mo")
	--avg-period (int): Volume average lookback in days (default: 50)

Returns:
	For analyze:
	dict: {
		"symbol": str,
		"date": str,
		"current_price": float,
		"period_analyzed": str,
		"total_bars": int,
		"latest_bar": {
			"closing_range_pct": float,
			"classification": str,
			"close": float,
			"volume_vs_avg_pct": float
		},
		"constructive_ratio": float,
		"constructive_bars": int,
		"non_constructive_bars": int,
		"neutral_bars": int,
		"consecutive_constructive": int,
		"consecutive_non_constructive": int,
		"recent_trend": {
			"last_5_constructive": int,
			"last_10_constructive": int,
			"last_20_constructive": int,
			"trend_direction": str
		},
		"avg_closing_range_pct": float,
		"assessment": str
	}

	For screen:
	dict: {
		"results": [
			{
				"symbol": str,
				"constructive_ratio": float,
				"consecutive_constructive": int,
				"last_10_constructive": int,
				"avg_closing_range_pct": float,
				"assessment": str
			}
		],
		"ranked_by": str
	}

Example:
	>>> python closing_range.py analyze NVDA --period 6mo
	{
		"symbol": "NVDA",
		"date": "2026-02-19",
		"current_price": 142.50,
		"total_bars": 125,
		"latest_bar": {
			"closing_range_pct": 78.5,
			"classification": "constructive",
			"close": 142.50,
			"volume_vs_avg_pct": 85.3
		},
		"constructive_ratio": 0.56,
		"constructive_bars": 70,
		"non_constructive_bars": 40,
		"consecutive_constructive": 3,
		"recent_trend": {
			"last_5_constructive": 4,
			"last_10_constructive": 7,
			"last_20_constructive": 12,
			"trend_direction": "improving"
		},
		"avg_closing_range_pct": 52.3,
		"assessment": "accumulation"
	}

	>>> python closing_range.py screen AAPL NVDA MSFT META --period 3mo
	{
		"results": [
			{"symbol": "NVDA", "constructive_ratio": 0.58, "consecutive_constructive": 3, ...},
			{"symbol": "META", "constructive_ratio": 0.54, "consecutive_constructive": 1, ...}
		],
		"ranked_by": "constructive_ratio"
	}

Use Cases:
	- Evaluate daily bar quality to confirm institutional accumulation during base
	- Compare multiple stocks' constructive ratios for relative strength screening
	- Track consecutive constructive bars to identify momentum shifts
	- Distinguish healthy pullbacks (constructive bars) from distribution
	- Monitor recent trend improvement as early entry signal

Notes:
	- Closing Range = (Close - Low) / (High - Low) * 100
	- CR >= 50% on below-avg volume = Constructive (buyers in control quietly)
	- CR < 50% on above-avg volume = Non-Constructive (sellers overwhelming)
	- Price up on low volume can also be constructive (effortless advance)
	- Price down on high volume is always non-constructive (forced selling)
	- Bars with zero range (High == Low) are classified as neutral
	- Constructive ratio > 0.55 suggests accumulation phase
	- Consecutive constructive bars signal building institutional conviction

See Also:
	- volume_analysis.py: Accumulation/distribution grading and up/down ratio
	- volume_edge.py: Volume edge detection for breakout confirmation
	- vcp.py: VCP detection uses volume contraction as confirmation
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import yfinance as yf
from utils import output_json, safe_run


def _calc_closing_range(high, low, close):
	"""Calculate Closing Range percentage.

	CR = (Close - Low) / (High - Low) * 100
	Returns 50.0 if High == Low (zero-range bar).
	"""
	if high == low:
		return 50.0
	return round((close - low) / (high - low) * 100, 1)


def _classify_bar(cr_pct, volume, avg_volume, price_change_pct):
	"""Classify a bar as constructive, non_constructive, or neutral.

	Constructive: (CR >= 50% AND Volume < Avg) OR (price up on low volume)
	Non-constructive: (CR < 50% AND Volume > Avg) OR (price down on high volume)
	"""
	vol_ratio = volume / avg_volume if avg_volume > 0 else 1.0
	low_volume = vol_ratio < 1.0
	high_volume = vol_ratio >= 1.0

	# Strong constructive: high close on quiet volume
	if cr_pct >= 50 and low_volume:
		return "constructive"
	# Constructive: price advance on low volume (effortless move up)
	if price_change_pct > 0 and low_volume:
		return "constructive"
	# Strong non-constructive: low close on heavy volume
	if cr_pct < 50 and high_volume:
		return "non_constructive"
	# Non-constructive: price decline on heavy volume
	if price_change_pct < 0 and high_volume:
		return "non_constructive"
	# Edge cases
	if cr_pct >= 70:
		return "constructive"
	if cr_pct <= 30:
		return "non_constructive"
	return "neutral"


def _analyze_bars(data, avg_period=50):
	"""Analyze all bars in the dataset for closing range and classification."""
	closes = data["Close"]
	highs = data["High"]
	lows = data["Low"]
	volumes = data["Volume"]

	results = []
	for i in range(1, len(data)):
		h = float(highs.iloc[i])
		l = float(lows.iloc[i])
		c = float(closes.iloc[i])
		v = float(volumes.iloc[i])
		prev_c = float(closes.iloc[i - 1])
		price_chg = ((c / prev_c) - 1) * 100 if prev_c != 0 else 0

		# Rolling average volume
		start_idx = max(0, i - avg_period)
		avg_vol = float(volumes.iloc[start_idx:i].mean()) if i > 0 else v

		cr = _calc_closing_range(h, l, c)
		classification = _classify_bar(cr, v, avg_vol, price_chg)

		results.append({
			"date": str(data.index[i].date()),
			"close": round(c, 2),
			"closing_range_pct": cr,
			"classification": classification,
			"volume": int(v),
			"avg_volume": int(avg_vol),
			"volume_vs_avg_pct": round(v / avg_vol * 100, 1) if avg_vol > 0 else 0,
			"price_change_pct": round(price_chg, 2),
		})

	return results


def _count_consecutive(bars, classification, from_end=True):
	"""Count consecutive bars of a given classification from the end."""
	count = 0
	sequence = reversed(bars) if from_end else iter(bars)
	for bar in sequence:
		if bar["classification"] == classification:
			count += 1
		else:
			break
	return count


def _recent_trend(bars, windows=(5, 10, 20)):
	"""Analyze constructive bar count over recent windows."""
	trend = {}
	for w in windows:
		recent = bars[-w:] if len(bars) >= w else bars
		c_count = sum(1 for b in recent if b["classification"] == "constructive")
		trend[f"last_{w}_constructive"] = c_count

	# Determine trend direction
	if len(bars) >= 20:
		first_half = sum(1 for b in bars[-20:-10] if b["classification"] == "constructive")
		second_half = sum(1 for b in bars[-10:] if b["classification"] == "constructive")
		if second_half > first_half + 1:
			trend["trend_direction"] = "improving"
		elif second_half < first_half - 1:
			trend["trend_direction"] = "deteriorating"
		else:
			trend["trend_direction"] = "stable"
	else:
		trend["trend_direction"] = "insufficient_data"

	return trend


def _assess(constructive_ratio, consecutive_constructive, trend_direction):
	"""Overall assessment based on bar quality metrics."""
	if constructive_ratio >= 0.6 and consecutive_constructive >= 3:
		return "strong_accumulation"
	if constructive_ratio >= 0.55:
		return "accumulation"
	if constructive_ratio >= 0.45:
		if trend_direction == "improving":
			return "transitioning_bullish"
		if trend_direction == "deteriorating":
			return "transitioning_bearish"
		return "neutral"
	if constructive_ratio >= 0.35:
		return "distribution"
	return "heavy_distribution"


@safe_run
def cmd_analyze(args):
	"""Single stock Closing Range analysis with bar classification."""
	symbol = args.symbol.upper()
	ticker = yf.Ticker(symbol)
	data = ticker.history(period=args.period, interval="1d")

	if data.empty or len(data) < 20:
		output_json({
			"error": f"Insufficient data for {symbol}. Need at least 20 trading days.",
			"data_points": len(data),
		})
		return

	bars = _analyze_bars(data, avg_period=args.avg_period)

	constructive = sum(1 for b in bars if b["classification"] == "constructive")
	non_constructive = sum(1 for b in bars if b["classification"] == "non_constructive")
	neutral = sum(1 for b in bars if b["classification"] == "neutral")
	total = len(bars)
	ratio = round(constructive / total, 3) if total > 0 else 0

	consec_c = _count_consecutive(bars, "constructive")
	consec_nc = _count_consecutive(bars, "non_constructive")
	trend = _recent_trend(bars)
	avg_cr = round(sum(b["closing_range_pct"] for b in bars) / total, 1) if total > 0 else 0

	assessment = _assess(ratio, consec_c, trend.get("trend_direction", "stable"))

	latest = bars[-1] if bars else {}

	output_json({
		"symbol": symbol,
		"date": str(data.index[-1].date()),
		"current_price": round(float(data["Close"].iloc[-1]), 2),
		"period_analyzed": args.period,
		"total_bars": total,
		"latest_bar": {
			"closing_range_pct": latest.get("closing_range_pct", 0),
			"classification": latest.get("classification", "unknown"),
			"close": latest.get("close", 0),
			"volume_vs_avg_pct": latest.get("volume_vs_avg_pct", 0),
		},
		"constructive_ratio": ratio,
		"constructive_bars": constructive,
		"non_constructive_bars": non_constructive,
		"neutral_bars": neutral,
		"consecutive_constructive": consec_c,
		"consecutive_non_constructive": consec_nc,
		"recent_trend": trend,
		"avg_closing_range_pct": avg_cr,
		"assessment": assessment,
	})


@safe_run
def cmd_screen(args):
	"""Multiple stocks Constructive bar ratio comparison."""
	results = []

	for sym in args.symbols:
		sym = sym.upper()
		try:
			ticker = yf.Ticker(sym)
			data = ticker.history(period=args.period, interval="1d")

			if data.empty or len(data) < 20:
				results.append({
					"symbol": sym,
					"error": "Insufficient data",
				})
				continue

			bars = _analyze_bars(data, avg_period=args.avg_period)
			total = len(bars)
			constructive = sum(1 for b in bars if b["classification"] == "constructive")
			ratio = round(constructive / total, 3) if total > 0 else 0
			consec_c = _count_consecutive(bars, "constructive")
			trend = _recent_trend(bars)
			avg_cr = round(sum(b["closing_range_pct"] for b in bars) / total, 1) if total > 0 else 0
			assessment = _assess(ratio, consec_c, trend.get("trend_direction", "stable"))

			results.append({
				"symbol": sym,
				"constructive_ratio": ratio,
				"constructive_bars": constructive,
				"total_bars": total,
				"consecutive_constructive": consec_c,
				"last_10_constructive": trend.get("last_10_constructive", 0),
				"avg_closing_range_pct": avg_cr,
				"trend_direction": trend.get("trend_direction", "unknown"),
				"assessment": assessment,
			})
		except Exception as e:
			results.append({
				"symbol": sym,
				"error": f"{type(e).__name__}: {e}",
			})

	# Sort by constructive_ratio descending (errors at end)
	valid = [r for r in results if "constructive_ratio" in r]
	errors = [r for r in results if "constructive_ratio" not in r]
	valid.sort(key=lambda x: x["constructive_ratio"], reverse=True)

	output_json({
		"results": valid + errors,
		"ranked_by": "constructive_ratio",
		"period": args.period,
		"symbols_analyzed": len(results),
	})


def main():
	parser = argparse.ArgumentParser(
		description="Closing Range & Bar Classification"
	)
	sub = parser.add_subparsers(dest="command", required=True)

	# analyze
	sp = sub.add_parser("analyze", help="Single stock Closing Range analysis")
	sp.add_argument("symbol", help="Ticker symbol")
	sp.add_argument("--period", default="6mo", help="Data period (default: 6mo)")
	sp.add_argument(
		"--avg-period", type=int, default=50,
		help="Volume average lookback in days (default: 50)",
	)
	sp.set_defaults(func=cmd_analyze)

	# screen
	sp = sub.add_parser("screen", help="Multi-stock Constructive bar comparison")
	sp.add_argument("symbols", nargs="+", help="Ticker symbols to screen")
	sp.add_argument("--period", default="3mo", help="Data period (default: 3mo)")
	sp.add_argument(
		"--avg-period", type=int, default=50,
		help="Volume average lookback in days (default: 50)",
	)
	sp.set_defaults(func=cmd_screen)

	args = parser.parse_args()
	args.func(args)


if __name__ == "__main__":
	main()
