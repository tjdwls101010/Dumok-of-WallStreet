#!/usr/bin/env python3
"""Detect extreme price events and measure mean reversion characteristics.

Identifies statistically extreme price movements (defined by z-score thresholds) and
analyzes their reversal patterns - how long it takes for prices to normalize and the
magnitude of the reversal. Useful for tail risk assessment and mean reversion strategies.

Args:
	symbol (str): Stock ticker symbol (e.g., "AAPL", "SPY", "^GSPC")
	--threshold (float): Sigma threshold for extreme event detection (default: 3.0)
		- Values >= 3.0 capture ~0.3% probability tail events
		- Higher values (3.5, 4.0) focus on rarer extreme moves
	--lookback (int): Lookback period for z-score calculation (default: 252 = 1 year)
	--period (str): Historical data period for analysis (default: "10y")
	--interval (str): Data interval (default: "1d")

Returns:
	dict: {
		"symbol": str,
		"period": str,
		"threshold": str,           # Threshold expressed as ±Nσ
		"lookback_days": int,       # Z-score calculation window
		"total_extreme_events": int, # Count of extreme events found
		"above_threshold": {         # Statistics for positive extremes
			"count": int,            # Number of upside extremes
			"with_reversal": int,    # Events that reversed to normal
			"avg_reversal_days": float,  # Average days to revert to ±1σ
			"avg_reversal_pct": float    # Average price change during reversal
		},
		"below_threshold": {         # Statistics for negative extremes
			"count": int,
			"with_reversal": int,
			"avg_reversal_days": float,
			"avg_reversal_pct": float
		},
		"recent_events": list,       # Last 10 extreme events with details
		"date": str                  # Analysis date
	}

Example:
	>>> python extreme_reversals.py SPY --threshold 3 --lookback 252
	{
		"symbol": "SPY",
		"period": "10y",
		"threshold": "±3σ",
		"lookback_days": 252,
		"total_extreme_events": 12,
		"above_threshold": {
			"count": 5,
			"with_reversal": 4,
			"avg_reversal_days": 28.5,
			"avg_reversal_pct": -4.2
		},
		"below_threshold": {
			"count": 7,
			"with_reversal": 6,
			"avg_reversal_days": 22.3,
			"avg_reversal_pct": 6.8
		},
		"recent_events": [
			{
				"date": "2024-10-15",
				"zscore": -3.24,
				"price": 420.50,
				"type": "below",
				"reversal_days": 18,
				"reversal_pct": 7.5
			}
		],
		"date": "2026-02-05"
	}

Use Cases:
	- Tail risk assessment: Identify and study extreme market events
	- Mean reversion strategies: Quantify reversal probabilities and timing
	- Risk management: Estimate recovery periods after extreme moves
	- Volatility regime analysis: Compare reversal patterns across periods
	- Contrarian entry timing: Determine optimal entry after extremes

Notes:
	- Survivorship bias: Analysis excludes permanently impaired securities
	- Overfitting risk: Thresholds optimized on historical data may not hold
	- Sample size: Extreme events are rare by definition (few data points)
	- Distribution assumptions: Z-score assumes normal distribution (fat tails underestimated)
	- Reversal definition: Uses ±1σ as "normal" threshold (configurable in code)
	- Market structure changes: Reversal patterns may differ across regimes
	- Black swan events: Unprecedented extremes may not follow historical patterns

See Also:
	- conditional.py: Calculate probability of specific reversal targets
	- event_returns.py: Analyze return distributions after extreme events
	- zscore.py: Calculate current z-score position for real-time signals
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import numpy as np
import pandas as pd
import yfinance as yf
from utils import output_json, safe_run


@safe_run
def cmd_extreme_reversals(args):
	"""Find extreme events and measure their reversal characteristics."""
	ticker = yf.Ticker(args.symbol)
	data = ticker.history(period=args.period, interval=args.interval)

	if data.empty:
		output_json({"error": f"No data for {args.symbol}"})
		return

	prices = data["Close"]
	lookback = args.lookback

	# Calculate z-score
	rolling_mean = prices.rolling(lookback).mean()
	rolling_std = prices.rolling(lookback).std()
	zscore = (prices - rolling_mean) / rolling_std

	# Find extreme events (above threshold sigma)
	extreme_events = []

	for i in range(lookback, len(zscore)):
		z = zscore.iloc[i]
		if abs(z) >= args.threshold:
			event_date = data.index[i]
			event_price = prices.iloc[i]

			# Find reversal (when z-score returns to ±1)
			reversal_days = None
			reversal_magnitude = None

			for j in range(i + 1, min(i + 252, len(zscore))):  # Look up to 1 year
				if abs(zscore.iloc[j]) <= 1:
					reversal_days = j - i
					reversal_price = prices.iloc[j]
					reversal_magnitude = (reversal_price - event_price) / event_price * 100
					break

			extreme_events.append(
				{
					"date": str(event_date.date()),
					"zscore": round(float(z), 2),
					"price": round(float(event_price), 2),
					"type": "above" if z > 0 else "below",
					"reversal_days": reversal_days,
					"reversal_pct": round(reversal_magnitude, 2) if reversal_magnitude else None,
				}
			)

	# Remove consecutive events (keep only the most extreme in a cluster)
	filtered_events = []
	min_gap = 20  # Minimum 20 days between events

	for event in extreme_events:
		if not filtered_events:
			filtered_events.append(event)
		else:
			last_date = pd.Timestamp(filtered_events[-1]["date"])
			curr_date = pd.Timestamp(event["date"])
			if (curr_date - last_date).days >= min_gap:
				filtered_events.append(event)

	# Calculate statistics
	above_events = [e for e in filtered_events if e["type"] == "above"]
	below_events = [e for e in filtered_events if e["type"] == "below"]

	def calc_reversal_stats(events):
		reversals = [e["reversal_days"] for e in events if e["reversal_days"]]
		magnitudes = [e["reversal_pct"] for e in events if e["reversal_pct"]]
		return {
			"count": len(events),
			"with_reversal": len(reversals),
			"avg_reversal_days": round(np.mean(reversals), 1) if reversals else None,
			"avg_reversal_pct": round(np.mean(magnitudes), 2) if magnitudes else None,
		}

	result = {
		"symbol": args.symbol,
		"period": args.period,
		"threshold": f"±{args.threshold}σ",
		"lookback_days": lookback,
		"total_extreme_events": len(filtered_events),
		"above_threshold": calc_reversal_stats(above_events),
		"below_threshold": calc_reversal_stats(below_events),
		"recent_events": filtered_events[-10:],
		"date": str(data.index[-1].date()),
	}
	output_json(result)


if __name__ == "__main__":
	import argparse

	parser = argparse.ArgumentParser(description="Analyze extreme events and reversals")
	parser.add_argument("symbol")
	parser.add_argument("--threshold", type=float, default=3, help="Sigma threshold for extreme")
	parser.add_argument("--lookback", type=int, default=252, help="Lookback for z-score")
	parser.add_argument("--period", default="10y", help="Data period")
	parser.add_argument("--interval", default="1d", help="Data interval")
	args = parser.parse_args()
	cmd_extreme_reversals(args)
