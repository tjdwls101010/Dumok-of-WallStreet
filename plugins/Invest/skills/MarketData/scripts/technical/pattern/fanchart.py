#!/usr/bin/env python3
"""Generate fan chart probability distributions and analogue comparisons from similar historical patterns.

Fan charts visualize probability ranges for future price movements based on historical analogue outcomes.
Analogue analysis compares current period with specific historical periods to forecast potential paths.

Args:
	For fanchart:
		symbol (str): Stock ticker symbol (e.g., "AAPL", "SPY", "QQQ")
		--period (str): Historical data period (default: "5y" = 5 years for sufficient analogues)
		--interval (str): Data interval (default: "1d" = daily)
		--window (int): Pattern window size in days (default: 140 = ~6 months)
		--top-n (int): Number of similar patterns to base distribution on (default: 10)
		--forward-days (str): Comma-separated forward periods (default: "30,60,90,180")

	For analogue:
		symbol (str): Stock ticker symbol (e.g., "AAPL", "SPY")
		--period (str): Historical data period (default: "10y" for long-term analogues)
		--interval (str): Data interval (default: "1d")
		--window (int): Comparison window size in days (default: 140)
		--target-date (str): Historical analogue date to compare against (e.g., "2020-03-15")

Returns:
	For fanchart:
		dict: {
			"symbol": str,
			"window_days": int,
			"based_on_patterns": int,      # Number of similar patterns used
			"top_patterns": list,           # Top 5 patterns for reference
			"fan_chart": {
				"30d": {
					"p10": float,          # 10th percentile (bearish tail)
					"p25": float,          # 25th percentile (bearish scenario)
					"p50": float,          # 50th percentile (median outcome)
					"p75": float,          # 75th percentile (bullish scenario)
					"p90": float,          # 90th percentile (bullish tail)
					"mean": float,         # Average return
					"count": int           # Sample size
				},
				"60d": {...},
				"90d": {...}
			},
			"interpretation": dict         # Percentile descriptions
		}

	For analogue:
		dict: {
			"symbol": str,
			"current_period": {
				"start": str,
				"end": str
			},
			"analogue_period": {
				"target_date": str,
				"window_start": str,
				"window_end": str
			},
			"correlation": float,          # Similarity to historical period (0-1)
			"similarity_assessment": str,  # "Very High", "High", "Moderate", "Low"
			"analogue_forward_returns": {
				"30d": float,              # What happened 30 days after analogue
				"60d": float,
				"90d": float
			},
			"implication": str             # Expected outcome based on analogue
		}

Example:
	>>> python fanchart.py fanchart SPY --window 140 --top-n 10
	{
		"symbol": "SPY",
		"window_days": 140,
		"based_on_patterns": 10,
		"fan_chart": {
			"30d": {
				"p10": -5.2,
				"p25": -1.8,
				"p50": 2.5,
				"p75": 6.8,
				"p90": 11.3,
				"mean": 3.1,
				"count": 10
			},
			"90d": {
				"p10": -8.5,
				"p50": 7.2,
				"p90": 22.5,
				"mean": 8.3
			}
		}
	}

	>>> python fanchart.py analogue AAPL --target-date "2020-03-23" --window 140
	{
		"symbol": "AAPL",
		"current_period": {
			"start": "2025-08-01",
			"end": "2026-02-05"
		},
		"analogue_period": {
			"target_date": "2020-03-23",
			"window_start": "2019-10-01",
			"window_end": "2020-03-23"
		},
		"correlation": 0.8523,
		"similarity_assessment": "High",
		"analogue_forward_returns": {
			"30d": 28.5,
			"60d": 42.3,
			"90d": 55.8
		},
		"implication": "If current follows 2020-03-23 pattern, expected returns: {30d: 28.5%, 60d: 42.3%, 90d: 55.8%}"
	}

Use Cases:
	- Forecast probability ranges for future price movements using historical distributions
	- Compare current market conditions with specific historical events (e.g., 2020 COVID crash, 2008 financial crisis)
	- Assess risk/reward scenarios using percentile distributions (p10/p90 = tail risk)
	- Validate analogue-based forecasts with correlation metrics
	- Identify potential market outcomes based on similar historical precedents
	- Set profit targets and stop losses based on historical outcome distributions

Notes:
	- Fan chart percentiles represent historical outcome ranges (p10 = worst 10%, p90 = best 10%)
	- Sample size (count) affects distribution reliability; larger = more robust
	- Correlation >0.9 indicates very high analogue similarity; <0.6 indicates weak match
	- Historical analogues may not repeat exactly due to different market contexts
	- Forward-looking distributions assume similar market dynamics persist
	- Analogue method works best for regime-defining events (crashes, rallies, consolidations)
	- Use multiple forward periods to assess short-term vs long-term potential

See Also:
	- pattern/similarity.py: Find similar patterns that feed into fan chart generation
	- pattern/helpers.py: Core functions for forward return calculation and percentile generation
	- oscillators.py: RSI and MACD for momentum context around pattern matches
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

import pandas as pd
import yfinance as yf
from technical.pattern.helpers import (
	calculate_fan_chart,
	calculate_forward_returns,
	calculate_pattern_correlation,
	find_similar_patterns,
)
from utils import output_json, safe_run


@safe_run
def cmd_fanchart(args):
	"""Generate fan chart probability distribution based on similar patterns."""
	ticker = yf.Ticker(args.symbol)
	data = ticker.history(period=args.period, interval=args.interval)

	if data.empty:
		output_json({"error": f"No data for {args.symbol}"})
		return

	prices = data["Close"]
	similar = find_similar_patterns(prices, args.window, args.top_n)

	if not similar:
		output_json({"symbol": args.symbol, "message": "No similar patterns found for fan chart"})
		return

	# Get end dates of similar patterns
	event_dates = [p["window_end"] for p in similar]

	# Calculate forward returns
	forward_days = [int(d) for d in args.forward_days.split(",")]
	returns_data = calculate_forward_returns(prices, event_dates, forward_days)

	# Generate fan chart
	fan_chart = calculate_fan_chart(returns_data)

	result = {
		"symbol": args.symbol,
		"window_days": args.window,
		"based_on_patterns": len(similar),
		"top_patterns": similar[:5],  # Show top 5 for reference
		"fan_chart": fan_chart,
		"interpretation": {
			"p10": "Bearish tail (10% worst case)",
			"p25": "Bearish scenario",
			"p50": "Median outcome",
			"p75": "Bullish scenario",
			"p90": "Bullish tail (10% best case)",
		},
		"date": str(data.index[-1].date()),
	}
	output_json(result)


@safe_run
def cmd_analogue(args):
	"""Compare current period with a specific historical analogue."""
	ticker = yf.Ticker(args.symbol)
	data = ticker.history(period=args.period, interval=args.interval)

	if data.empty:
		output_json({"error": f"No data for {args.symbol}"})
		return

	prices = data["Close"]

	# Parse target date
	try:
		target_date = pd.Timestamp(args.target_date)
	except ValueError:
		output_json({"error": f"Invalid date format: {args.target_date}"})
		return

	# Find the target date in data - convert to same timezone/type as index
	try:
		# Normalize index to tz-naive for comparison
		prices_normalized = prices.copy()
		if prices_normalized.index.tz is not None:
			prices_normalized.index = prices_normalized.index.tz_localize(None)
		target_date_naive = target_date.tz_localize(None) if target_date.tz else target_date
		target_idx = prices_normalized.index.get_indexer([target_date_naive], method="nearest")[0]
	except (KeyError, IndexError):
		output_json({"error": f"Date {args.target_date} not found in data"})
		return

	# Get windows
	current_window = prices.tail(args.window)
	hist_start = max(0, target_idx - args.window + 1)
	hist_end = target_idx + 1
	historical_window = prices.iloc[hist_start:hist_end]

	if len(historical_window) < args.window:
		output_json({"error": "Insufficient data for historical window"})
		return

	# Calculate correlation
	correlation = calculate_pattern_correlation(current_window, historical_window.iloc[-len(current_window) :])

	# Calculate what happened after the analogue period
	forward_returns = {}
	for days in [30, 60, 90]:
		if target_idx + days < len(prices):
			future_price = prices.iloc[target_idx + days]
			target_price = prices.iloc[target_idx]
			ret = (future_price - target_price) / target_price * 100
			forward_returns[f"{days}d"] = round(ret, 2)

	result = {
		"symbol": args.symbol,
		"current_period": {"start": str(current_window.index[0].date()), "end": str(current_window.index[-1].date())},
		"analogue_period": {
			"target_date": str(target_date.date()),
			"window_start": str(prices.index[hist_start].date()),
			"window_end": str(prices.index[hist_end - 1].date()),
		},
		"correlation": round(correlation, 4),
		"similarity_assessment": (
			"Very High"
			if correlation > 0.9
			else "High"
			if correlation > 0.8
			else "Moderate"
			if correlation > 0.6
			else "Low"
		),
		"analogue_forward_returns": forward_returns,
		"implication": f"If current follows {args.target_date} pattern, expected returns: {forward_returns}",
	}
	output_json(result)
