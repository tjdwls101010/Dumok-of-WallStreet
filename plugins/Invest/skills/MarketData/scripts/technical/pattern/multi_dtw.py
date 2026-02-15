#!/usr/bin/env python3
"""Multi-feature DTW pattern matching using price+RSI+slope+volatility+D2H vectors.

Extends single-feature DTW similarity (similarity.py) to multi-dimensional pattern
matching per SidneyKim0's methodology Step 4: "Z-normalized price + weekly RSI +
slope + volatility + D2H (distance to high)" for historical case search.

For each sliding window, the script computes 5 feature vectors, Z-normalizes each
independently, then calculates a weighted DTW distance across all features. This
reduces false positives compared to price-only matching by requiring that momentum
(RSI), trend strength (slope), risk (volatility), and drawdown depth (D2H) all
match the current pattern.

Features:
- price: Z-normalized closing prices (standard DTW baseline)
- rsi: 14-period RSI series over the window
- slope: 20-day rolling linear regression slope (normalized by price)
- vol: 20-day rolling volatility (standard deviation of daily returns)
- d2h: Distance-to-high = (price - rolling_max) / rolling_max (drawdown depth)

Args:
	Command: multi-dtw

	multi-dtw:
		symbol (str): Stock ticker symbol (e.g., "SPY", "QQQ", "AAPL")
		--features (str): Comma-separated feature selection (default: "price,rsi,slope,vol,d2h")
		--weights (str): Comma-separated feature weights matching feature order (default: "1.0,0.5,0.3,0.3,0.3")
		--window (int): Pattern window size in days (default: 60)
		--period (str): Historical data period (default: "15y")
		--interval (str): Data interval (default: "1d")
		--top-n (int): Number of top matches to return (default: 5)
		--threshold (float): Maximum weighted DTW distance (default: 3.0)

Returns:
	dict: {
		"symbol": str,
		"date": str,
		"window_days": int,
		"method": "Multi-Feature DTW",
		"features_used": [str],            # List of features used
		"feature_weights": {str: float},   # Feature name -> weight mapping
		"threshold": float,
		"current_window": {
			"start": str,
			"end": str
		},
		"top_similar_patterns": [
			{
				"window_start": str,
				"window_end": str,
				"weighted_dtw_distance": float,    # Combined weighted distance
				"similarity_score": float,         # 1/(1+distance)
				"per_feature_distance": {          # Individual feature distances
					"price": float,
					"rsi": float,
					"slope": float,
					"vol": float,
					"d2h": float
				},
				"forward_returns": {
					"30d": float,
					"60d": float,
					"90d": float
				}
			}
		],
		"forward_return_summary": {
			"30d": {"mean": float, "median": float, "min": float, "max": float, "count": int},
			"60d": {...},
			"90d": {...}
		},
		"interpretation": str
	}

Example:
	>>> python -m technical.pattern multi-dtw SPY --window 60 --period 15y --top-n 5
	{
		"symbol": "SPY",
		"window_days": 60,
		"method": "Multi-Feature DTW",
		"features_used": ["price", "rsi", "slope", "vol", "d2h"],
		"top_similar_patterns": [
			{
				"window_start": "2018-10-01",
				"window_end": "2018-12-20",
				"weighted_dtw_distance": 1.23,
				"similarity_score": 0.4484,
				"per_feature_distance": {"price": 0.8, "rsi": 1.2, "slope": 0.5, "vol": 0.9, "d2h": 0.7},
				"forward_returns": {"30d": 8.5, "60d": 12.3, "90d": 15.1}
			}
		]
	}

	>>> python -m technical.pattern multi-dtw QQQ --features price,rsi,vol --weights 1.0,0.7,0.5 --window 90
	# Uses only 3 features with custom weights

Use Cases:
	- Verify "necessary conditions" for historical analogies (Step 4 methodology)
	- Reduce false positive pattern matches by requiring multi-dimensional similarity
	- Compare current drawdown structure (D2H) with historical episodes
	- Identify periods where momentum (RSI) AND trend (slope) both match current regime
	- Generate forward return distributions from multi-feature matched historical periods

Notes:
	- Computational cost increases with number of features and history length
	- Price-only DTW: O(n*w^2) per window; multi-feature: O(n*w^2*f) where f = feature count
	- For 15y daily data with 5 features and 60-day window: ~30-60 seconds
	- Feature weights default: price=1.0 (anchor), rsi=0.5, slope=0.3, vol=0.3, d2h=0.3
	- Each feature is Z-normalized independently before DTW computation
	- D2H (distance-to-high) uses 60-day rolling max for drawdown measurement
	- Minimum overlap of 30 valid data points required per feature per window
	- Forward returns calculated same as similarity.py:cmd_dtw_similarity

See Also:
	- technical/pattern/similarity.py: Single-feature DTW and correlation-based matching
	- technical/pattern/helpers.py: calculate_dtw_distance, z_normalize, calculate_slope
	- technical/slope.py: Standalone slope analysis with regime classification
	- technical/indicators.py: calculate_rsi for RSI computation
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

import numpy as np
import pandas as pd
import yfinance as yf
from analysis.analysis_utils import z_normalize
from technical.indicators import calculate_rsi
from technical.pattern.helpers import calculate_dtw_distance
from utils import output_json, safe_run


def compute_features(prices: pd.Series, feature_names: list, window_slice: slice = None) -> dict:
	"""Compute feature vectors for a price series.

	Args:
		prices: Full price series (need extra data before window for indicators)
		feature_names: List of feature names to compute
		window_slice: Slice to extract the final window after computation

	Returns:
		dict: {feature_name: np.ndarray} of Z-normalized feature vectors
	"""
	features = {}

	for name in feature_names:
		if name == "price":
			series = prices
		elif name == "rsi":
			series = calculate_rsi(prices, 14)
		elif name == "slope":
			# 20-day rolling slope normalized by price
			slopes = pd.Series(np.nan, index=prices.index)
			x = np.arange(20, dtype=float)
			for i in range(19, len(prices)):
				y = prices.iloc[i - 19 : i + 1].values.astype(float)
				if not np.any(np.isnan(y)):
					slope = np.polyfit(x, y, 1)[0]
					slopes.iloc[i] = slope / prices.iloc[i] * 100 if prices.iloc[i] != 0 else 0
			series = slopes
		elif name == "vol":
			# 20-day rolling volatility of returns
			returns = prices.pct_change()
			series = returns.rolling(window=20).std() * np.sqrt(252)  # annualized
		elif name == "d2h":
			# Distance to 60-day rolling high
			rolling_max = prices.rolling(window=60, min_periods=1).max()
			series = (prices - rolling_max) / rolling_max * 100  # percentage drawdown
		else:
			continue

		if window_slice is not None:
			series = series.iloc[window_slice]

		# Drop NaN and Z-normalize
		valid = series.dropna()
		if len(valid) < 20:
			features[name] = None
			continue

		normalized = z_normalize(valid).values
		features[name] = normalized

	return features


def weighted_dtw_distance(features_current: dict, features_historical: dict, weights: dict) -> tuple:
	"""Compute weighted DTW distance across multiple features.

	Args:
		features_current: {name: np.ndarray} current window features
		features_historical: {name: np.ndarray} historical window features
		weights: {name: float} feature weights

	Returns:
		tuple: (weighted_distance, per_feature_distances)
	"""
	total_weight = 0.0
	weighted_sum = 0.0
	per_feature = {}

	for name in features_current:
		curr = features_current.get(name)
		hist = features_historical.get(name)

		if curr is None or hist is None:
			continue

		# Align lengths
		min_len = min(len(curr), len(hist))
		if min_len < 20:
			continue

		dist = calculate_dtw_distance(curr[:min_len], hist[:min_len])
		normalized_dist = dist / min_len  # normalize by length

		w = weights.get(name, 0.3)
		weighted_sum += normalized_dist * w
		total_weight += w
		per_feature[name] = round(normalized_dist, 4)

	if total_weight == 0:
		return float("inf"), {}

	weighted_distance = weighted_sum / total_weight
	return weighted_distance, per_feature


@safe_run
def cmd_multi_dtw(args):
	"""Multi-feature DTW pattern matching."""
	# Parse features and weights
	feature_names = [f.strip() for f in args.features.split(",")]
	weight_values = [float(w.strip()) for w in args.weights.split(",")]

	# Pad weights if fewer than features
	while len(weight_values) < len(feature_names):
		weight_values.append(0.3)

	weights = dict(zip(feature_names, weight_values))

	# Fetch data
	ticker = yf.Ticker(args.symbol)
	data = ticker.history(period=args.period, interval=args.interval)
	if data.empty:
		output_json({"error": f"No data for {args.symbol}"})
		return

	prices = data["Close"]

	# Need extra buffer for indicator computation (RSI=14, slope=20, vol=20, d2h=60)
	buffer = 80  # max lookback needed for any feature
	min_required = args.window * 2 + buffer

	if len(prices) < min_required:
		output_json({"error": f"Insufficient data: need {min_required} bars, have {len(prices)}"})
		return

	# Compute current window features
	current_start = len(prices) - args.window
	current_features = compute_features(prices, feature_names, slice(current_start, None))

	# Check we have valid features
	valid_features = {k: v for k, v in current_features.items() if v is not None}
	if not valid_features:
		output_json({"error": "Could not compute any valid features for current window"})
		return

	# Slide through history
	similar_patterns = []
	scan_end = len(prices) - args.window * 2  # don't overlap with current window

	for i in range(buffer, scan_end):
		hist_start = i
		hist_end = i + args.window

		# Compute features for this historical window
		# Need buffer before the window for indicator warm-up
		pre_buffer_start = max(0, hist_start - buffer)
		hist_prices = prices.iloc[pre_buffer_start:hist_end]

		# Window slice relative to hist_prices
		window_offset = hist_start - pre_buffer_start
		hist_features = compute_features(hist_prices, feature_names, slice(window_offset, window_offset + args.window))

		# Check valid features
		hist_valid = {k: v for k, v in hist_features.items() if v is not None}
		if len(hist_valid) < len(valid_features) * 0.5:
			continue

		# Compute weighted DTW distance
		dist, per_feature = weighted_dtw_distance(valid_features, hist_valid, weights)

		if dist < args.threshold:
			similar_patterns.append(
				{
					"window_start": str(prices.index[hist_start].date()),
					"window_end": str(prices.index[hist_end - 1].date()),
					"weighted_dtw_distance": round(dist, 4),
					"similarity_score": round(1 / (1 + dist), 4),
					"per_feature_distance": per_feature,
				}
			)

	# Sort by distance (most similar first)
	similar_patterns.sort(key=lambda x: x["weighted_dtw_distance"])
	similar_patterns = similar_patterns[: args.top_n]

	if not similar_patterns:
		output_json(
			{
				"symbol": args.symbol,
				"window_days": args.window,
				"method": "Multi-Feature DTW",
				"features_used": list(valid_features.keys()),
				"message": f"No patterns found below threshold {args.threshold}",
				"suggestion": "Try increasing --threshold or decreasing --window",
			}
		)
		return

	# Calculate forward returns for matched patterns
	for pattern in similar_patterns:
		end_date = pd.Timestamp(pattern["window_end"])
		try:
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

	# Forward return summary
	fwd_summary = {}
	for period in ["30d", "60d", "90d"]:
		returns = [p["forward_returns"].get(period) for p in similar_patterns if period in p.get("forward_returns", {})]
		returns = [r for r in returns if r is not None]
		if returns:
			fwd_summary[period] = {
				"mean": round(float(np.mean(returns)), 2),
				"median": round(float(np.median(returns)), 2),
				"min": round(float(np.min(returns)), 2),
				"max": round(float(np.max(returns)), 2),
				"count": len(returns),
			}

	result = {
		"symbol": args.symbol,
		"date": str(data.index[-1].date()),
		"window_days": args.window,
		"method": "Multi-Feature DTW",
		"features_used": list(valid_features.keys()),
		"feature_weights": {k: round(v, 2) for k, v in weights.items() if k in valid_features},
		"threshold": args.threshold,
		"current_window": {
			"start": str(prices.index[current_start].date()),
			"end": str(prices.index[-1].date()),
		},
		"top_similar_patterns": similar_patterns,
		"forward_return_summary": fwd_summary,
		"interpretation": (
			f"Multi-feature DTW matched {len(similar_patterns)} historical patterns "
			f"using {len(valid_features)} features: {', '.join(valid_features.keys())}. "
			f"Lower weighted distance = more similar across all dimensions."
		),
	}
	output_json(result)
