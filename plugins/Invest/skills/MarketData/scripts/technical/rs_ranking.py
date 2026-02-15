#!/usr/bin/env python3
"""RS (Relative Strength) Ranking: dual-approach relative strength scoring.

Provides two complementary methods for evaluating a stock's relative strength:
1. YFinance-based individual RS score calculation (weighted multi-period returns)
2. Finviz-based high-RS universe screening (performance filters)

Based on IBD's Relative Strength Rating methodology adapted for open data sources.

Commands:
	score: Calculate RS score (0-99) for a single ticker vs S&P 500
	screen: Screen for high-RS stocks using Finviz performance filters
	compare: Compare RS scores across multiple tickers

Args:
	For score:
		symbol (str): Ticker symbol (e.g., "AAPL", "NVDA")
		--benchmark (str): Benchmark symbol (default: "SPY")
		--period (str): Data period for calculation (default: "1y")

	For screen:
		--min-year-perf (float): Minimum 1-year performance % (default: 20)
		--min-quarter-perf (float): Minimum quarterly performance % (default: 10)
		--max-from-high (str): Maximum distance from 52-week high (default: "0-10%")
		--limit (int): Maximum results (default: 50)

	For compare:
		symbols (list): List of ticker symbols to compare
		--benchmark (str): Benchmark symbol (default: "SPY")

Returns:
	For score:
		dict: {
			"symbol": str,
			"rs_score": int,
			"percentile_approx": int,
			"period_returns": {
				"3m": float, "6m": float, "9m": float, "12m": float
			},
			"benchmark_returns": {
				"3m": float, "6m": float, "9m": float, "12m": float
			},
			"weighted_composite": float,
			"vs_benchmark_ratio": float
		}

	For screen:
		dict: {
			"data": [...],
			"metadata": {"count": int, "filters": dict}
		}

	For compare:
		dict: {
			"rankings": [
				{"symbol": str, "rs_score": int, "12m_return": float}
			],
			"benchmark": str
		}

Example:
	>>> python rs_ranking.py score NVDA
	{
		"symbol": "NVDA",
		"rs_score": 92,
		"period_returns": {"3m": 25.3, "6m": 45.2, "9m": 68.1, "12m": 120.5},
		"weighted_composite": 284.2,
		"vs_benchmark_ratio": 2.85
	}

	>>> python rs_ranking.py screen --min-year-perf 30 --limit 20
	{
		"data": [{"Ticker": "NVDA", "Perf Year": "120.5%", ...}],
		"metadata": {"count": 20}
	}

	>>> python rs_ranking.py compare NVDA AMD AVGO MRVL
	{
		"rankings": [
			{"symbol": "NVDA", "rs_score": 92, "12m_return": 120.5},
			{"symbol": "AVGO", "rs_score": 85, "12m_return": 78.2},
			...
		]
	}

Use Cases:
	- Identify market leaders with strongest relative price performance
	- Filter SEPA candidates by RS >= 70 (Trend Template criterion 8)
	- Compare sector peers to find the strongest name
	- Screen for high-momentum universe using Finviz data
	- Track RS divergences (price at new high but RS declining)

Notes:
	- RS scoring uses weighted returns: 3m(2x) + 6m(1x) + 9m(1x) + 12m(1x)
	- Weight emphasis on recent 3-month performance captures current momentum
	- Score 0-99 approximation based on ratio vs benchmark composite
	- Finviz screen approximates IBD RS 80+ stocks per MEMO methodology
	- For full S&P 500 percentile ranking, use the score command with live data

See Also:
	- trend_template.py: Uses RS >= 70 as criterion 8
	- stage_analysis.py: RS improving is a Stage 1->2 transition signal
	- sepa_pipeline.py: RS ranking integrated in full SEPA pipeline
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import yfinance as yf
from utils import error_json, output_json, safe_run


def _period_return(closes, days):
	"""Calculate return over a specific number of trading days."""
	if len(closes) < days:
		return None
	return round((float(closes.iloc[-1]) / float(closes.iloc[-days]) - 1) * 100, 2)


def _compute_rs(symbol, benchmark="SPY", period="1y"):
	"""Compute RS score for a symbol vs benchmark.

	Weighted composite: 3m(2x) + 6m(1x) + 9m(1x) + 12m(1x)
	Score mapped to 0-99 scale based on ratio to benchmark.
	"""
	data_stock = yf.Ticker(symbol).history(period=period)
	data_bench = yf.Ticker(benchmark).history(period=period)

	if data_stock.empty or data_bench.empty:
		return None

	closes_stock = data_stock["Close"]
	closes_bench = data_bench["Close"]

	periods_config = [
		("3m", 63, 2),
		("6m", 126, 1),
		("9m", 189, 1),
		("12m", 252, 1),
	]

	stock_returns = {}
	bench_returns = {}
	stock_weighted = 0
	bench_weighted = 0

	for label, days, weight in periods_config:
		s_ret = _period_return(closes_stock, days)
		b_ret = _period_return(closes_bench, days)
		stock_returns[label] = s_ret if s_ret is not None else 0
		bench_returns[label] = b_ret if b_ret is not None else 0
		stock_weighted += (s_ret or 0) * weight
		bench_weighted += (b_ret or 0) * weight

	# Calculate ratio and map to 0-99 score
	if bench_weighted == 0:
		ratio = 1.0
	else:
		ratio = stock_weighted / bench_weighted if bench_weighted != 0 else 1.0

	# Map ratio to score: <0.5 -> ~1, 1.0 -> ~50, 2.0 -> ~90, 3.0+ -> ~99
	import math

	# 4-quadrant RS scoring for meaningful differentiation across all market conditions
	if stock_weighted < 0 and bench_weighted > 0:
		# Stock declining while benchmark rises: weakest RS, map to 1-25
		severity = min(abs(stock_weighted) / bench_weighted, 3.0)
		score = int(max(1, round(25 - 24 * severity / 3)))
	elif stock_weighted > 0 and bench_weighted < 0:
		# Stock rising while benchmark declines: strongest RS, map to 85-99
		strength = min(stock_weighted / abs(bench_weighted), 3.0)
		score = int(min(99, round(85 + 14 * strength / 3)))
	elif stock_weighted < 0 and bench_weighted < 0:
		# Both declining: proportional mapping, less bad = higher, map to 15-45
		ratio_abs = abs(stock_weighted) / abs(bench_weighted)
		clamped = min(ratio_abs, 3.0)
		score = int(max(1, min(45, round(45 - 30 * clamped / 3))))
	elif ratio <= 0:
		score = 1
	else:
		score = int(max(1, min(99, 50 * (1 + math.log(ratio, 2)))))

	return {
		"rs_score": score,
		"period_returns": stock_returns,
		"benchmark_returns": bench_returns,
		"weighted_composite_stock": round(stock_weighted, 2),
		"weighted_composite_benchmark": round(bench_weighted, 2),
		"vs_benchmark_ratio": round(ratio, 3),
	}


def compute_rs_score(symbol, benchmark="SPY", period="1y"):
	"""Public API: compute RS score (0-99) for use by other modules.

	Centralized RS engine using 4-quadrant weighted multi-period scoring.
	Called by trend_template.py criterion 8 and sepa_pipeline.py RS component.

	Args:
		symbol: Ticker symbol (e.g., "NVDA")
		benchmark: Benchmark symbol (default: "SPY")
		period: Data period for calculation (default: "1y")

	Returns:
		int or None: RS score 0-99, or None if data unavailable
	"""
	result = _compute_rs(symbol, benchmark, period)
	if result is None:
		return None
	return result["rs_score"]


@safe_run
def cmd_score(args):
	"""Calculate RS score for a single ticker."""
	symbol = args.symbol.upper()
	benchmark = args.benchmark.upper()

	result = _compute_rs(symbol, benchmark, args.period)
	if result is None:
		error_json(f"Unable to retrieve data for {symbol} or {benchmark}")

	output_json(
		{
			"symbol": symbol,
			"benchmark": benchmark,
			"date": str(yf.Ticker(symbol).history(period="1d").index[-1].date()),
			**result,
		}
	)


@safe_run
def cmd_screen(args):
	"""Screen for high-RS stocks using Finviz filters."""
	from finvizfinance.screener.overview import Overview

	# Build Finviz filters matching high-RS criteria
	# Per MEMO: Perf Year +20%, Perf Quarter +10%, 52W High 0-10% below
	# finvizfinance uses "Year +X%" and "Quarter +X%" format
	perf_year_map = {
		10: "Year +10%",
		20: "Year +20%",
		30: "Year +30%",
		50: "Year +50%",
		100: "Year +100%",
	}
	perf_quarter_map = {
		10: "Quarter +10%",
		20: "Quarter +20%",
		30: "Quarter +30%",
		50: "Quarter +50%",
	}

	# Find closest matching filter value
	year_key = max((k for k in perf_year_map if k <= args.min_year_perf), default=10)
	quarter_key = max((k for k in perf_quarter_map if k <= args.min_quarter_perf), default=10)

	filters_dict = {
		"Performance": perf_year_map[year_key],
		"Performance 2": perf_quarter_map[quarter_key],
		"52-Week High/Low": args.max_from_high,
	}

	foverview = Overview()
	foverview.set_filter(filters_dict=filters_dict)

	from datetime import datetime, timezone

	df = foverview.screener_view(limit=args.limit, verbose=0)

	if df is None or df.empty:
		output_json(
			{
				"data": [],
				"metadata": {
					"filters": filters_dict,
					"count": 0,
					"timestamp": datetime.now(timezone.utc).isoformat(),
				},
			}
		)
		return

	records = df.to_dict(orient="records")

	output_json(
		{
			"data": records,
			"metadata": {
				"description": "High-RS stocks screened via Finviz (approximates IBD RS 80+)",
				"filters": filters_dict,
				"count": len(records),
				"timestamp": datetime.now(timezone.utc).isoformat(),
			},
		}
	)


@safe_run
def cmd_compare(args):
	"""Compare RS scores across multiple tickers."""
	benchmark = args.benchmark.upper()
	results = []

	for symbol in args.symbols:
		symbol = symbol.upper()
		rs_data = _compute_rs(symbol, benchmark, "1y")
		if rs_data is not None:
			results.append(
				{
					"symbol": symbol,
					"rs_score": rs_data["rs_score"],
					"3m_return": rs_data["period_returns"]["3m"],
					"6m_return": rs_data["period_returns"]["6m"],
					"12m_return": rs_data["period_returns"]["12m"],
					"weighted_composite": rs_data["weighted_composite_stock"],
					"vs_benchmark_ratio": rs_data["vs_benchmark_ratio"],
				}
			)
		else:
			results.append(
				{
					"symbol": symbol,
					"rs_score": None,
					"error": "Data unavailable",
				}
			)

	# Sort by RS score descending
	results.sort(key=lambda x: x.get("rs_score") or 0, reverse=True)

	output_json(
		{
			"benchmark": benchmark,
			"rankings": results,
			"count": len(results),
		}
	)


def main():
	parser = argparse.ArgumentParser(description="RS (Relative Strength) Ranking")
	sub = parser.add_subparsers(dest="command", required=True)

	# score
	sp = sub.add_parser("score", help="Calculate RS score for a ticker")
	sp.add_argument("symbol", help="Ticker symbol")
	sp.add_argument("--benchmark", default="SPY", help="Benchmark symbol (default: SPY)")
	sp.add_argument("--period", default="1y", help="Data period (default: 1y)")
	sp.set_defaults(func=cmd_score)

	# screen
	sp = sub.add_parser("screen", help="Screen for high-RS stocks via Finviz")
	sp.add_argument("--min-year-perf", type=float, default=20, help="Min 1-year performance %% (default: 20)")
	sp.add_argument("--min-quarter-perf", type=float, default=10, help="Min quarterly performance %% (default: 10)")
	sp.add_argument("--max-from-high", default="0-10% below High", help="Max distance from 52w high")
	sp.add_argument("--limit", type=int, default=50, help="Max results (default: 50)")
	sp.set_defaults(func=cmd_screen)

	# compare
	sp = sub.add_parser("compare", help="Compare RS scores for multiple tickers")
	sp.add_argument("symbols", nargs="+", help="Ticker symbols to compare")
	sp.add_argument("--benchmark", default="SPY", help="Benchmark symbol (default: SPY)")
	sp.set_defaults(func=cmd_compare)

	args = parser.parse_args()
	args.func(args)


if __name__ == "__main__":
	main()
