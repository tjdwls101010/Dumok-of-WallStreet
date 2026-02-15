#!/usr/bin/env python3
"""Calculate and analyze asset price ratios for relative value assessment.

Computes the ratio between two assets (e.g., Gold/Silver, SPY/TLT) and evaluates
its current position relative to historical distribution. Provides percentile ranking,
z-score, and statistical extremes to identify relative value opportunities.

Args:
	symbol1 (str): Numerator ticker symbol (e.g., "GLD" for Gold ETF)
	symbol2 (str): Denominator ticker symbol (e.g., "SLV" for Silver ETF)
	--lookback (int): Lookback period for statistics calculation (default: 252 = 1 year)
	--period (str): Historical data period for analysis (default: "5y")
	--interval (str): Data interval (default: "1d")

Returns:
	dict: {
		"ratio": str,           # Ratio description (symbol1/symbol2)
		"period": str,          # Data period analyzed
		"lookback_days": int,   # Lookback window for statistics
		"current": {
			"ratio": float,         # Current ratio value
			"percentile": float,    # Historical percentile rank (0-100)
			"zscore": float         # Z-score relative to lookback period
		},
		"statistics": {
			"mean": float,          # Average ratio over lookback
			"std": float,           # Standard deviation of ratio
			"max": float,           # Maximum ratio value
			"max_date": str,        # Date of maximum ratio
			"min": float,           # Minimum ratio value
			"min_date": str         # Date of minimum ratio
		},
		"interpretation": str,  # Qualitative assessment
							   # (Historically Low/Below Average/Normal/Above Average/Historically High)
		"date": str            # Analysis date
	}

Example:
	>>> python ratio.py GLD SLV --lookback 252
	{
		"ratio": "GLD/SLV",
		"period": "5y",
		"lookback_days": 252,
		"current": {
			"ratio": 78.25,
			"percentile": 92.3,
			"zscore": 1.65
		},
		"statistics": {
			"mean": 72.50,
			"std": 3.48,
			"max": 82.15,
			"max_date": "2024-08-12",
			"min": 65.30,
			"min_date": "2023-11-05"
		},
		"interpretation": "Historically High",
		"date": "2026-02-05"
	}

Use Cases:
	- Pairs trading: Identify mean reversion opportunities in correlated assets
	- Relative value analysis: Compare valuation across asset classes
	- Portfolio rebalancing: Determine which asset is relatively cheaper
	- Market regime detection: Track ratio shifts across economic cycles
	- Spread trading: Quantify current positioning for long/short strategies

Notes:
	- Survivorship bias: Ratios assume both assets remain liquid
	- Overfitting risk: Historical extremes may be exceeded in future
	- Sample size: Require sufficient data points (minimum 252 days recommended)
	- Stationarity assumption: Ratio mean may drift over long periods
	- Correlation breakdown: Ratios can diverge during regime changes
	- Dividend adjustments: Use total return series for dividend-paying assets
	- Outlier sensitivity: Single extreme events can distort statistics

See Also:
	- zscore.py: Z-score calculation for single assets
	- correlation.py: Correlation analysis for asset pair relationships
	- percentile.py: Percentile ranking for distribution-free analysis
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pandas as pd
import yfinance as yf
from utils import output_json, safe_run


@safe_run
def cmd_ratio(args):
	"""Calculate and analyze asset ratio (e.g., Gold/Silver)."""
	ticker1 = yf.Ticker(args.symbol1)
	ticker2 = yf.Ticker(args.symbol2)

	data1 = ticker1.history(period=args.period, interval=args.interval)
	data2 = ticker2.history(period=args.period, interval=args.interval)

	if data1.empty or data2.empty:
		output_json({"error": "Could not fetch data for one or both symbols"})
		return

	# Align data
	prices1 = data1["Close"]
	prices2 = data2["Close"]

	# Create aligned DataFrame
	df = pd.DataFrame({args.symbol1: prices1, args.symbol2: prices2})
	df = df.dropna()

	if len(df) < 50:
		output_json({"error": "Insufficient overlapping data"})
		return

	# Calculate ratio
	ratio = df[args.symbol1] / df[args.symbol2]
	current_ratio = ratio.iloc[-1]

	# Calculate statistics
	lookback = min(args.lookback, len(ratio))
	recent_ratio = ratio.tail(lookback)

	percentile = (recent_ratio < current_ratio).sum() / len(recent_ratio) * 100
	mean_ratio = recent_ratio.mean()
	std_ratio = recent_ratio.std()
	zscore = (current_ratio - mean_ratio) / std_ratio if std_ratio > 0 else 0

	# Historical extremes
	max_ratio = recent_ratio.max()
	min_ratio = recent_ratio.min()
	max_date = str(recent_ratio.idxmax().date())
	min_date = str(recent_ratio.idxmin().date())

	result = {
		"ratio": f"{args.symbol1}/{args.symbol2}",
		"period": args.period,
		"lookback_days": lookback,
		"current": {
			"ratio": round(float(current_ratio), 4),
			"percentile": round(percentile, 1),
			"zscore": round(float(zscore), 2),
		},
		"statistics": {
			"mean": round(float(mean_ratio), 4),
			"std": round(float(std_ratio), 4),
			"max": round(float(max_ratio), 4),
			"max_date": max_date,
			"min": round(float(min_ratio), 4),
			"min_date": min_date,
		},
		"interpretation": (
			"Historically High"
			if percentile > 90
			else "Above Average"
			if percentile > 70
			else "Normal"
			if percentile > 30
			else "Below Average"
			if percentile > 10
			else "Historically Low"
		),
		"date": str(df.index[-1].date()),
	}
	output_json(result)


if __name__ == "__main__":
	import argparse

	parser = argparse.ArgumentParser(description="Analyze asset ratio")
	parser.add_argument("symbol1", help="Numerator symbol")
	parser.add_argument("symbol2", help="Denominator symbol")
	parser.add_argument("--lookback", type=int, default=252, help="Lookback period")
	parser.add_argument("--period", default="5y", help="Data period")
	parser.add_argument("--interval", default="1d", help="Data interval")
	args = parser.parse_args()
	cmd_ratio(args)
