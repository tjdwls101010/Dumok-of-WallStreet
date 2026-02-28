#!/usr/bin/env python3
"""Calculate forward return statistics after condition trigger events.

Analyzes the distribution of forward returns at multiple time horizons (e.g., 30/60/90 days)
following condition events such as RSI extremes or z-score thresholds. Provides statistical
measures including mean, standard deviation, and positive/negative rates for strategy backtesting.

Args:
	symbol (str): Stock ticker symbol (e.g., "AAPL", "SPY", "^GSPC")
	--condition (str): Condition trigger type
		- "rsi_above": RSI exceeds threshold
		- "rsi_below": RSI falls below threshold
		- "zscore_above": Z-score exceeds threshold
		- "zscore_below": Z-score falls below threshold
	--threshold (float): Threshold value for condition detection
	--forward-days (str): Comma-separated forward periods to measure (default: "30,60,90")
	--period (str): Historical data period for analysis (default: "10y")
	--interval (str): Data interval (default: "1d")
	--no-pivot (flag): Use initial crossing instead of pivot point detection

Returns:
	dict: {
		"symbol": str,
		"period": str,
		"condition": {
			"type": str,        # Condition type
			"threshold": float  # Threshold value
		},
		"total_events": int,    # Number of events detected
		"return_statistics": {
			"30d": {            # Statistics for each forward period
				"count": int,           # Number of valid returns
				"mean": float,          # Average return percentage
				"std": float,           # Standard deviation of returns
				"min": float,           # Worst return
				"max": float,           # Best return
				"positive_rate": float, # Percentage of positive returns
				"negative_rate": float  # Percentage of negative returns
			},
			"60d": {...},       # 60-day forward statistics
			"90d": {...}        # 90-day forward statistics
		},
		"event_details": list,  # First 10 events with dates and indicator values
		"date": str             # Analysis date
	}

Example:
	>>> python event_returns.py SPY --condition rsi_below --threshold 30 --forward-days 30,60,90
	{
		"symbol": "SPY",
		"period": "10y",
		"condition": {"type": "rsi_below", "threshold": 30},
		"total_events": 28,
		"return_statistics": {
			"30d": {
				"count": 28,
				"mean": 4.85,
				"std": 6.23,
				"min": -8.50,
				"max": 18.75,
				"positive_rate": 78.6,
				"negative_rate": 21.4
			},
			"60d": {
				"count": 27,
				"mean": 7.12,
				"std": 9.45,
				"positive_rate": 81.5,
				"negative_rate": 18.5
			}
		},
		"date": "2026-02-05"
	}

Use Cases:
	- Strategy validation: Quantify expected returns from technical signals
	- Parameter tuning: Compare return distributions across different thresholds
	- Risk/reward assessment: Evaluate win rates and average gains vs losses
	- Holding period optimization: Determine optimal exit timing (30d vs 60d vs 90d)
	- Performance benchmarking: Compare signal efficacy across different assets

Notes:
	- Survivorship bias: Historical returns exclude delisted/bankrupt stocks
	- Overfitting risk: In-sample statistics may overestimate future performance
	- Sample size: Require minimum 20+ events per period for reliable statistics
	- Forward-looking bias: Ensure event detection doesn't peek into future data
	- Market regime dependency: Return patterns vary across market conditions
	- Distribution assumptions: Returns may not be normally distributed (check skew/kurtosis)

See Also:
	- conditional.py: Calculate probability of specific target outcomes
	- extreme_reversals.py: Analyze mean reversion after extreme events
	- helpers.py: Core event detection and return calculation functions
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import numpy as np
import pandas as pd
import yfinance as yf
from utils import output_json, safe_run

# Handle both relative and absolute imports
try:
	from .helpers import find_condition_events
except ImportError:
	from helpers import find_condition_events


@safe_run
def cmd_event_returns(args):
	"""Calculate returns after condition events."""
	ticker = yf.Ticker(args.symbol)
	data = ticker.history(period=args.period, interval=args.interval)

	if data.empty:
		output_json({"error": f"No data for {args.symbol}"})
		return

	prices = data["Close"]
	use_pivot = not args.no_pivot if hasattr(args, "no_pivot") else True
	events = find_condition_events(data, args.condition, args.threshold, use_pivot=use_pivot)

	if not events:
		output_json(
			{"symbol": args.symbol, "condition": f"{args.condition} {args.threshold}", "message": "No events found"}
		)
		return

	# Calculate forward returns for each event
	forward_days = [int(d) for d in args.forward_days.split(",")]
	returns_by_period = {f"{d}d": [] for d in forward_days}

	for event in events:
		event_date = pd.Timestamp(event["date"])
		try:
			event_idx = data.index.get_loc(event_date)
			event_price = prices.iloc[event_idx]

			for days in forward_days:
				if event_idx + days < len(prices):
					future_price = prices.iloc[event_idx + days]
					ret = (future_price - event_price) / event_price * 100
					returns_by_period[f"{days}d"].append({"event_date": event["date"], "return": round(ret, 2)})
		except KeyError:
			continue

	# Calculate statistics
	stats = {}
	for period, returns in returns_by_period.items():
		if returns:
			ret_values = [r["return"] for r in returns]
			stats[period] = {
				"count": len(ret_values),
				"mean": round(np.mean(ret_values), 2),
				"std": round(np.std(ret_values), 2),
				"min": round(min(ret_values), 2),
				"max": round(max(ret_values), 2),
				"positive_rate": round(sum(1 for r in ret_values if r > 0) / len(ret_values) * 100, 1),
				"negative_rate": round(sum(1 for r in ret_values if r < 0) / len(ret_values) * 100, 1),
			}

	result = {
		"symbol": args.symbol,
		"period": args.period,
		"condition": {"type": args.condition, "threshold": args.threshold},
		"total_events": len(events),
		"return_statistics": stats,
		"event_details": events[:10],
		"date": str(data.index[-1].date()),
	}
	output_json(result)


if __name__ == "__main__":
	import argparse

	parser = argparse.ArgumentParser(description="Calculate returns after events")
	parser.add_argument("symbol")
	parser.add_argument(
		"--condition", required=True, choices=["rsi_above", "rsi_below", "zscore_above", "zscore_below"]
	)
	parser.add_argument("--threshold", type=float, required=True)
	parser.add_argument("--forward-days", default="30,60,90", help="Forward days to measure")
	parser.add_argument("--period", default="10y", help="Data period")
	parser.add_argument("--interval", default="1d", help="Data interval")
	parser.add_argument(
		"--no-pivot",
		action="store_true",
		help="Use initial crossing instead of pivot points",
	)
	args = parser.parse_args()
	cmd_event_returns(args)
