#!/usr/bin/env python3
"""Find extreme events beyond threshold sigma to identify historical tail risk events.

Extreme event detection finds price or return observations exceeding a z-score threshold, indicating
statistically rare occurrences. Useful for tail risk analysis, stress testing, and identifying
historical outlier events for forward return analysis.

Args:
	symbol (str): Stock ticker symbol (e.g., "SPY", "AAPL", "^GSPC")
	--period (str): Historical data period for analysis (default: "10y" = 10 years)
	--interval (str): Data interval (default: "1d" = daily)
	--threshold (float): Sigma threshold for extreme detection (default: 3.0)
	--lookback (int): Lookback period for rolling z-score (default: 252 = 1 trading year)
	--use-returns (flag): Analyze returns instead of price levels
	--limit (int): Maximum extreme events to return (default: 50)

Returns:
	dict: {
		"analysis_date": str,           # Latest analysis date
		"symbol": str,                  # Ticker symbol
		"analysis_type": str,           # "price" or "returns"
		"threshold": str,               # Threshold (e.g., "±3.0σ")
		"lookback_for_zscore": int,     # Lookback period for z-score
		"total_extreme_events": int,    # Total extreme events detected
		"high_extremes": int,           # Count of high extremes (z > threshold)
		"low_extremes": int,            # Count of low extremes (z < -threshold)
		"extreme_events": [             # List of extreme events (limited by --limit)
			{
				"date": str,            # Event date
				"value": float,         # Price or return value
				"z_score": float,       # Z-score at event
				"type": str             # "high" or "low"
			},
			...
		]
	}

Example:
	>>> python extremes.py SPY --threshold 3.0 --lookback 252
	{
		"analysis_date": "2026-02-05",
		"symbol": "SPY",
		"analysis_type": "price",
		"threshold": "±3.0σ",
		"lookback_for_zscore": 252,
		"total_extreme_events": 12,
		"high_extremes": 7,
		"low_extremes": 5,
		"extreme_events": [
			{
				"date": "2020-03-16",
				"value": 238.45,
				"z_score": -3.42,
				"type": "low"
			},
			{
				"date": "2021-08-20",
				"value": 442.10,
				"z_score": 3.15,
				"type": "high"
			}
		]
	}

Use Cases:
	- Tail risk analysis: Identify and study historical extreme market events
	- Stress testing: Analyze portfolio behavior during extreme price moves
	- Crisis detection: Find market crash dates and magnitudes
	- Contrarian signals: Extreme events often precede mean reversion
	- Volatility analysis: Use --use-returns to find extreme volatility spikes
	- Forward return analysis: Study performance after extreme events

Notes:
	- 3σ threshold captures ~0.3% of observations (rare tail events)
	- 2σ threshold captures ~5% of observations (less rare extremes)
	- Lookback period affects z-score sensitivity: shorter = more extremes detected
	- Use --use-returns for volatility-adjusted extreme detection
	- Extreme high events may indicate euphoria or momentum exhaustion
	- Extreme low events may signal capitulation or buying opportunities
	- Events sorted by date (most recent first) for temporal analysis

See Also:
	- multi_extremes.py: Detect simultaneous extreme events across multiple assets
	- zscore.py: Calculate current z-score for real-time positioning
	- percentile.py: Alternative rank-based extreme detection without normality assumption
	- distribution.py: Analyze full return distribution including tail characteristics
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import yfinance as yf
from utils import output_json, safe_run


@safe_run
def cmd_extremes(args):
	"""Find extreme events (beyond threshold sigma) in historical data."""
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

	# Calculate rolling z-scores
	rolling_mean = series.rolling(window=args.lookback).mean()
	rolling_std = series.rolling(window=args.lookback).std()
	z_scores = (series - rolling_mean) / rolling_std

	# Find extreme events
	threshold = args.threshold
	extreme_high = z_scores[z_scores >= threshold]
	extreme_low = z_scores[z_scores <= -threshold]

	extreme_events = []
	for idx, z in extreme_high.items():
		extreme_events.append(
			{
				"date": str(idx.date()),
				"value": round(float(series.loc[idx]), 6 if args.use_returns else 2),
				"z_score": round(float(z), 2),
				"type": "high",
			}
		)
	for idx, z in extreme_low.items():
		extreme_events.append(
			{
				"date": str(idx.date()),
				"value": round(float(series.loc[idx]), 6 if args.use_returns else 2),
				"z_score": round(float(z), 2),
				"type": "low",
			}
		)

	# Sort by date
	extreme_events.sort(key=lambda x: x["date"], reverse=True)

	result = {
		"analysis_date": str(series.index[-1].date()),
		"symbol": args.symbol,
		"analysis_type": series_name,
		"threshold": f"±{threshold}σ",
		"lookback_for_zscore": args.lookback,
		"total_extreme_events": len(extreme_events),
		"high_extremes": len(extreme_high),
		"low_extremes": len(extreme_low),
		"extreme_events": extreme_events[: args.limit],  # Limit output
	}
	output_json(result)


if __name__ == "__main__":
	import argparse

	parser = argparse.ArgumentParser(description="Find extreme events beyond threshold sigma")
	parser.add_argument("symbol")
	parser.add_argument("--period", default="10y", help="Data period")
	parser.add_argument("--interval", default="1d", help="Data interval")
	parser.add_argument("--threshold", type=float, default=3.0, help="Sigma threshold")
	parser.add_argument("--lookback", type=int, default=252, help="Lookback for rolling z-score")
	parser.add_argument("--use-returns", action="store_true", help="Analyze returns instead of price")
	parser.add_argument("--limit", type=int, default=50, help="Max events to return")
	args = parser.parse_args()
	cmd_extremes(args)
