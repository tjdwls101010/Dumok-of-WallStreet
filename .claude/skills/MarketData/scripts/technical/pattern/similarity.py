#!/usr/bin/env python3
"""Find similar historical price patterns using correlation and DTW (Dynamic Time Warping).

Pattern similarity analysis identifies historical periods with similar price movements to the current window.
Two methods: correlation-based (linear similarity) and DTW (shape similarity with time warping).

Args:
	For similarity (correlation-based):
		symbol (str): Stock ticker symbol (e.g., "AAPL", "SPY", "QQQ")
		--period (str): Historical data period (default: "5y" = 5 years for sufficient history)
		--interval (str): Data interval (default: "1d" = daily)
		--window (int): Pattern window size in days (default: 140 = ~6 months)
		--top-n (int): Number of most similar patterns to return (default: 10)

	For dtw-similarity (DTW-based):
		symbol (str): Stock ticker symbol (e.g., "AAPL", "SPY")
		--period (str): Historical data period (default: "5y")
		--interval (str): Data interval (default: "1d")
		--window (int): Pattern window size in days (default: 140)
		--top-n (int): Number of most similar patterns to return (default: 10)
		--threshold (float): DTW distance threshold (default: 0.5; lower = more similar)
		--use-slope (flag): Match on price slopes instead of raw prices

Returns:
	For similarity:
		dict: {
			"symbol": str,
			"window_days": int,
			"current_window": {
				"start": str,              # Start date of current pattern
				"end": str                 # End date (today)
			},
			"top_similar_patterns": [
				{
					"window_start": str,   # Historical pattern start date
					"window_end": str,     # Historical pattern end date
					"correlation": float   # Correlation coefficient (0.3-1.0)
				}
			]
		}

	For dtw-similarity:
		dict: {
			"symbol": str,
			"window_days": int,
			"method": str,                 # "DTW" or "DTW + Slope"
			"threshold": float,
			"top_similar_patterns": [
				{
					"window_start": str,
					"window_end": str,
					"dtw_distance": float,      # Lower = more similar
					"similarity_score": float,  # 1/(1+distance), higher = more similar
					"forward_returns": {
						"30d": float,           # Return 30 days after pattern end
						"60d": float,
						"90d": float
					}
				}
			],
			"interpretation": str
		}

Example:
	>>> python similarity.py similarity AAPL --window 140 --top-n 5
	{
		"symbol": "AAPL",
		"window_days": 140,
		"current_window": {
			"start": "2025-08-01",
			"end": "2026-02-05"
		},
		"top_similar_patterns": [
			{
				"window_start": "2020-03-15",
				"window_end": "2020-09-01",
				"correlation": 0.8523
			},
			{
				"window_start": "2018-12-20",
				"window_end": "2019-06-10",
				"correlation": 0.7892
			}
		]
	}

	>>> python similarity.py dtw-similarity SPY --window 60 --threshold 0.3 --use-slope
	{
		"symbol": "SPY",
		"window_days": 60,
		"method": "DTW + Slope",
		"top_similar_patterns": [
			{
				"window_start": "2023-10-01",
				"window_end": "2023-12-15",
				"dtw_distance": 0.1523,
				"similarity_score": 0.8682,
				"forward_returns": {
					"30d": 5.2,
					"60d": 8.7,
					"90d": 12.3
				}
			}
		],
		"interpretation": "Lower DTW distance = more similar pattern shape"
	}

Use Cases:
	- Predict future price movements based on historical analogue outcomes
	- Validate current market conditions against past similar periods
	- Identify potential turning points when current pattern matches historical reversals
	- Compare different pattern matching methods (correlation vs DTW)
	- Backtest strategy performance on historically similar market conditions

Notes:
	- Correlation method captures linear similarity; DTW captures shape similarity regardless of timing
	- DTW with --use-slope flag reduces noise and focuses on trend direction changes
	- Window size affects pattern granularity: smaller windows = short-term patterns, larger = long-term trends
	- Correlation threshold set at 0.3+ to filter weak matches (SidneyKim0 methodology)
	- DTW distance is normalized by window length for comparability across different windows
	- Forward returns show actual outcomes after historical pattern completion
	- Larger historical periods (5y+) provide more pattern candidates for matching

See Also:
	- pattern/fanchart.py: Generate probability distributions from similar patterns
	- pattern/helpers.py: Core pattern matching helper functions (DTW, correlation)
	- oscillators.py: RSI extremes combined with pattern matching for entry signals
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

import pandas as pd
import yfinance as yf
from analysis.analysis_utils import z_normalize
from technical.pattern.helpers import (
	calculate_dtw_distance,
	calculate_slope,
	find_similar_patterns,
)
from utils import output_json, safe_run


@safe_run
def cmd_similarity(args):
	"""Find similar historical patterns."""
	ticker = yf.Ticker(args.symbol)
	data = ticker.history(period=args.period, interval=args.interval)

	if data.empty:
		output_json({"error": f"No data for {args.symbol}"})
		return

	prices = data["Close"]
	similar = find_similar_patterns(prices, args.window, args.top_n)

	if not similar:
		output_json(
			{
				"symbol": args.symbol,
				"window": args.window,
				"message": "No similar patterns found (insufficient data or no correlations > 0.3)",
				"suggestion": "Try decreasing --window or increasing --period for more historical data",
			}
		)
		return

	result = {
		"symbol": args.symbol,
		"period": args.period,
		"window_days": args.window,
		"current_window": {"start": str(prices.index[-args.window].date()), "end": str(prices.index[-1].date())},
		"top_similar_patterns": similar,
		"date": str(data.index[-1].date()),
	}
	output_json(result)


@safe_run
def cmd_dtw_similarity(args):
	"""Find similar historical patterns using DTW (Dynamic Time Warping) - SidneyKim0 methodology."""
	ticker = yf.Ticker(args.symbol)
	data = ticker.history(period=args.period, interval=args.interval)

	if data.empty:
		output_json({"error": f"No data for {args.symbol}"})
		return

	prices = data["Close"]

	if len(prices) < args.window * 2:
		output_json({"error": "Insufficient data for DTW pattern matching"})
		return

	# Get current window and z-normalize
	current_window = prices.tail(args.window)
	current_normalized = z_normalize(current_window).values

	# Calculate slope if requested
	if args.use_slope:
		slopes = calculate_slope(prices, window=20)
		current_slope = slopes.tail(args.window)
		if current_slope.isna().sum() < len(current_slope) * 0.5:
			current_normalized = z_normalize(current_slope.dropna()).values

	similar_patterns = []

	# Slide through history
	for i in range(len(prices) - args.window * 2):
		hist_start = i
		hist_end = i + args.window
		historical_window = prices.iloc[hist_start:hist_end]

		if args.use_slope:
			hist_slopes = calculate_slope(historical_window, window=20)
			if hist_slopes.isna().sum() < len(hist_slopes) * 0.5:
				hist_normalized = z_normalize(hist_slopes.dropna()).values
			else:
				continue
		else:
			hist_normalized = z_normalize(historical_window).values

		# Ensure same length for DTW
		min_len = min(len(current_normalized), len(hist_normalized))
		if min_len < 20:
			continue

		dtw_dist = calculate_dtw_distance(current_normalized[:min_len], hist_normalized[:min_len])

		# Normalize DTW distance by window length
		normalized_dist = dtw_dist / min_len

		# Lower distance = more similar (threshold based on experience)
		if normalized_dist < args.threshold:
			similar_patterns.append(
				{
					"window_start": str(prices.index[hist_start].date()),
					"window_end": str(prices.index[hist_end - 1].date()),
					"dtw_distance": round(normalized_dist, 4),
					"similarity_score": round(1 / (1 + normalized_dist), 4),  # Convert to similarity
				}
			)

	# Sort by DTW distance (ascending = most similar first)
	similar_patterns.sort(key=lambda x: x["dtw_distance"])
	similar_patterns = similar_patterns[: args.top_n]

	if not similar_patterns:
		output_json(
			{
				"symbol": args.symbol,
				"window": args.window,
				"method": "DTW" + (" + Slope" if args.use_slope else ""),
				"message": f"No similar patterns found (DTW distance threshold: {args.threshold})",
				"suggestion": "Try increasing --threshold or decreasing --window",
			}
		)
		return

	# Calculate forward returns for matched patterns
	for pattern in similar_patterns:
		end_date = pd.Timestamp(pattern["window_end"])
		try:
			# Handle timezone-aware vs naive index comparison
			if prices.index.tz is not None:
				end_date = end_date.tz_localize(prices.index.tz)
			end_idx = prices.index.get_indexer([end_date], method="nearest")[0]
			forward_returns = {}
			for days in [30, 60, 90]:
				if end_idx + days < len(prices):
					future_price = prices.iloc[end_idx + days]
					end_price = prices.iloc[end_idx]
					ret = (future_price - end_price) / end_price * 100
					forward_returns[f"{days}d"] = round(ret, 2)
			pattern["forward_returns"] = forward_returns
		except (KeyError, IndexError):
			pattern["forward_returns"] = {}

	result = {
		"symbol": args.symbol,
		"period": args.period,
		"window_days": args.window,
		"method": "DTW" + (" + Slope" if args.use_slope else ""),
		"threshold": args.threshold,
		"current_window": {"start": str(prices.index[-args.window].date()), "end": str(prices.index[-1].date())},
		"top_similar_patterns": similar_patterns,
		"date": str(data.index[-1].date()),
		"interpretation": "Lower DTW distance = more similar pattern shape",
	}
	output_json(result)
