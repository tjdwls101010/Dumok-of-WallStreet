#!/usr/bin/env python3
"""Calculate percentile rank for stock price or returns to identify relative positioning without distribution assumptions.

Percentile rank shows where the current price sits in its historical distribution using rank-based
statistics. Unlike z-score, it makes no assumptions about normal distribution and is robust to outliers.

Args:
	symbol (str): Stock ticker symbol (e.g., "AAPL", "SPY", "^GSPC")
	--period (str): Historical data period for analysis (default: "5y" = 5 years)
	--interval (str): Data interval (default: "1d" = daily)
	--lookback (int): Number of periods for percentile calculation (default: 252 = 1 trading year)
	--use-returns (flag): Calculate percentile on returns instead of price levels

Returns:
	dict: {
		"symbol": str,              # Ticker symbol
		"analysis_type": str,       # "price" or "returns"
		"current_value": float,     # Current price or return value
		"percentile_rank": float,   # Percentile rank (0-100)
		"interpretation": str,      # Category (Top 5%, Bottom 25%, etc.)
		"lookback_days": int,       # Lookback period used
		"date": str,                # Analysis date
		"distribution": {           # Historical distribution quartiles
			"min": float,
			"q25": float,
			"median": float,
			"q75": float,
			"max": float
		}
	}

Example:
	>>> python percentile.py AAPL --lookback 252
	{
		"symbol": "AAPL",
		"analysis_type": "price",
		"current_value": 175.43,
		"percentile_rank": 72.5,
		"interpretation": "Top 25%",
		"lookback_days": 252,
		"date": "2026-02-05",
		"distribution": {
			"min": 125.30,
			"q25": 152.10,
			"median": 165.80,
			"q75": 178.20,
			"max": 195.45
		}
	}

Use Cases:
	- Identify overbought/oversold levels without normality assumptions
	- Track relative positioning over time with robust non-parametric metric
	- Compare multiple stocks using percentile ranks for screener construction
	- Detect extreme conditions (>95th or <5th percentile) for entry/exit signals
	- Use with --use-returns flag for volatility-normalized positioning

Notes:
	- Percentile rank is robust to outliers and fat-tailed distributions
	- Lookback period affects granularity: shorter = more responsive, longer = more stable
	- Top 5% and Bottom 5% thresholds useful for extreme condition detection
	- For volatile or non-normal distributions, percentile is preferred over z-score
	- Market holidays may slightly affect lookback calculation accuracy

See Also:
	- zscore.py: Normal distribution-based positioning metric (requires normality)
	- extremes.py: Historical extreme event detection with z-score thresholds
	- distribution.py: Full distribution analysis including skewness and kurtosis
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import yfinance as yf
from analysis.analysis_utils import calculate_percentile
from utils import output_json, safe_run


@safe_run
def cmd_percentile(args):
	"""Calculate historical percentile rank for a symbol."""
	ticker = yf.Ticker(args.symbol)
	data = ticker.history(period=args.period, interval=args.interval)
	if data.empty:
		output_json({"error": f"No data for {args.symbol}"})
		return

	prices = data["Close"]

	if args.use_returns:
		series = prices.pct_change().dropna()
		series_name = "returns"
	else:
		series = prices
		series_name = "price"

	percentile = calculate_percentile(series, args.lookback)
	current_value = series.iloc[-1]

	# Get historical stats
	window_data = series.tail(args.lookback)
	min_val = window_data.min()
	max_val = window_data.max()
	q25 = window_data.quantile(0.25)
	q50 = window_data.quantile(0.50)
	q75 = window_data.quantile(0.75)

	result = {
		"symbol": args.symbol,
		"analysis_type": series_name,
		"current_value": round(float(current_value), 6 if args.use_returns else 2),
		"percentile_rank": round(float(percentile), 2),
		"interpretation": "Top 5%"
		if percentile >= 95
		else "Top 10%"
		if percentile >= 90
		else "Top 25%"
		if percentile >= 75
		else "Bottom 25%"
		if percentile <= 25
		else "Bottom 10%"
		if percentile <= 10
		else "Bottom 5%"
		if percentile <= 5
		else "Middle 50%",
		"lookback_days": args.lookback,
		"date": str(data.index[-1].date()),
		"distribution": {
			"min": round(float(min_val), 6 if args.use_returns else 2),
			"q25": round(float(q25), 6 if args.use_returns else 2),
			"median": round(float(q50), 6 if args.use_returns else 2),
			"q75": round(float(q75), 6 if args.use_returns else 2),
			"max": round(float(max_val), 6 if args.use_returns else 2),
		},
	}
	output_json(result)


if __name__ == "__main__":
	import argparse

	parser = argparse.ArgumentParser(description="Calculate percentile rank")
	parser.add_argument("symbol")
	parser.add_argument("--period", default="5y", help="Data period")
	parser.add_argument("--interval", default="1d", help="Data interval")
	parser.add_argument("--lookback", type=int, default=252, help="Lookback period")
	parser.add_argument("--use-returns", action="store_true", help="Calculate percentile for returns")
	args = parser.parse_args()
	cmd_percentile(args)
