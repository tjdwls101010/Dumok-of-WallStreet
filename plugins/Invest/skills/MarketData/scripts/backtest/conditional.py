#!/usr/bin/env python3
"""Calculate conditional probability of reaching a target given a condition event.

Analyzes historical patterns to determine P(target | condition) - the probability
that a target outcome occurs within a specified timeframe after a condition is met.
Uses pivot point detection (SidneyKim0 methodology) to identify meaningful reversals.

Args:
	symbol (str): Stock ticker symbol (e.g., "AAPL", "SPY", "^GSPC")
	--condition (str): Condition trigger type
		- "rsi_above": RSI crosses above threshold
		- "rsi_below": RSI crosses below threshold
		- "zscore_above": Z-score crosses above threshold
		- "zscore_below": Z-score crosses below threshold
	--threshold (float): Threshold value for condition trigger
	--target-type (str): Target outcome to measure probability for
		- "rsi_below": RSI falls below target value
		- "rsi_above": RSI rises above target value
		- "return_below": Price return falls below target percentage
		- "return_above": Price return rises above target percentage
	--target-value (float): Target threshold value
	--max-days (int): Maximum days to wait for target (default: 30)
	--period (str): Historical data period (default: "10y")
	--interval (str): Data interval (default: "1d")
	--no-pivot (flag): Use initial crossing instead of pivot points

Returns:
	dict: {
		"symbol": str,
		"period": str,
		"condition": {
			"type": str,        # Condition type used
			"threshold": float  # Threshold value
		},
		"target": {
			"type": str,        # Target type measured
			"value": float,     # Target threshold
			"max_days": int     # Maximum lookforward period
		},
		"result": {
			"total_events": int,        # Number of condition events found
			"successes": int,            # Events that reached target
			"probability": float,        # Success rate as percentage (0-100)
			"avg_days_to_target": float, # Average days to reach target
			"min_days": int,             # Fastest target achievement
			"max_days": int              # Slowest target achievement
		},
		"probability_statement": str,  # Human-readable interpretation
		"events": list,                # First 10 condition events with details
		"date": str                    # Analysis date
	}

Example:
	>>> python conditional.py AAPL --condition rsi_above --threshold 70 --target-type return_below --target-value -5 --max-days 30
	{
		"symbol": "AAPL",
		"period": "10y",
		"condition": {"type": "rsi_above", "threshold": 70},
		"target": {"type": "return_below", "value": -5, "max_days": 30},
		"result": {
			"total_events": 45,
			"successes": 33,
			"probability": 73.3,
			"avg_days_to_target": 12.4,
			"min_days": 3,
			"max_days": 28
		},
		"probability_statement": "When rsi_above crosses 70, probability of return_below -5 within 30 days: 73.3%",
		"date": "2026-02-05"
	}

Use Cases:
	- Strategy validation: Test if technical signals predict future outcomes
	- Parameter tuning: Optimize threshold values for entry/exit rules
	- Risk assessment: Quantify probability of adverse price movements
	- Mean reversion testing: Measure oversold/overbought reversal rates
	- Conditional timing: Determine optimal holding periods after signals

Notes:
	- Survivorship bias: Historical probabilities may not reflect future outcomes
	- Overfitting risk: Optimized thresholds may not generalize to new data
	- Sample size: Require minimum 30+ events for statistical significance
	- Pivot detection (default): Uses reversal points for more meaningful signals
	- Market regime changes: Probabilities vary across bull/bear/volatile periods
	- Look-ahead bias: Ensure condition detection doesn't use future data

See Also:
	- event_returns.py: Analyze return distributions after condition events
	- extreme_reversals.py: Study extreme events and mean reversion patterns
	- helpers.py: Core functions for condition detection and probability calculation
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import yfinance as yf
from utils import output_json, safe_run

# Handle both relative and absolute imports
try:
	from .helpers import calculate_target_probability, find_condition_events
except ImportError:
	from helpers import calculate_target_probability, find_condition_events


@safe_run
def cmd_conditional(args):
	"""Calculate conditional probability: P(target | condition)."""
	ticker = yf.Ticker(args.symbol)
	data = ticker.history(period=args.period, interval=args.interval)

	if data.empty:
		output_json({"error": f"No data for {args.symbol}"})
		return

	# Find events matching condition (use pivot detection by default for SidneyKim0 methodology)
	use_pivot = not args.no_pivot if hasattr(args, "no_pivot") else True
	events = find_condition_events(data, args.condition, args.threshold, use_pivot=use_pivot)

	if not events:
		output_json(
			{
				"symbol": args.symbol,
				"condition": f"{args.condition} {args.threshold}",
				"message": "No events found matching condition",
			}
		)
		return

	# Calculate target probability
	prob_result = calculate_target_probability(data, events, args.target_type, args.target_value, args.max_days)

	result = {
		"symbol": args.symbol,
		"period": args.period,
		"condition": {"type": args.condition, "threshold": args.threshold},
		"target": {"type": args.target_type, "value": args.target_value, "max_days": args.max_days},
		"result": prob_result,
		"probability_statement": (
			f"When {args.condition} crosses {args.threshold}, "
			f"probability of {args.target_type} {args.target_value} within {args.max_days} days: "
			f"{prob_result['probability']}%"
		),
		"events": events[:10],  # Show first 10 events
		"date": str(data.index[-1].date()),
	}
	output_json(result)


if __name__ == "__main__":
	import argparse

	parser = argparse.ArgumentParser(description="Calculate conditional probability")
	parser.add_argument("symbol")
	parser.add_argument(
		"--condition",
		required=True,
		choices=["rsi_above", "rsi_below", "zscore_above", "zscore_below"],
		help="Condition type",
	)
	parser.add_argument("--threshold", type=float, required=True, help="Condition threshold")
	parser.add_argument(
		"--target-type",
		required=True,
		choices=["rsi_below", "rsi_above", "return_below", "return_above"],
		help="Target type",
	)
	parser.add_argument("--target-value", type=float, required=True, help="Target value")
	parser.add_argument("--max-days", type=int, default=30, help="Max days to reach target")
	parser.add_argument("--period", default="10y", help="Data period")
	parser.add_argument("--interval", default="1d", help="Data interval")
	parser.add_argument(
		"--no-pivot",
		action="store_true",
		help="Use initial crossing instead of pivot points",
	)
	args = parser.parse_args()
	cmd_conditional(args)
