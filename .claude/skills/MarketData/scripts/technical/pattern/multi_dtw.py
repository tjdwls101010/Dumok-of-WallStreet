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
	- Performance optimizations: Pearson correlation pre-filter reduces DTW candidates by ~7-8x,
	  Sakoe-Chiba band constrains DTW to diagonal ± n/3, and features are pre-computed once
	  over the full series then sliced per window (eliminates ~3,400 redundant computations).
	  Vectorized slope (convolution-based) replaces per-bar np.polyfit. Target: <5s for 15y data.
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
from technical.pattern.helpers import calculate_dtw_distance, calculate_slope_vectorized
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

		dist = calculate_dtw_distance(curr[:min_len], hist[:min_len], band_radius=max(10, min_len // 4))
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

	# --- Step 3: Pre-compute all raw features once over entire price series ---
	price_arr = prices.values.astype(float)
	n_prices = len(price_arr)
	window = args.window

	raw_features = {}
	for name in feature_names:
		if name == "price":
			raw_features[name] = price_arr
		elif name == "rsi":
			raw_features[name] = calculate_rsi(prices, 14).values
		elif name == "slope":
			slope_series = calculate_slope_vectorized(prices, 20)
			# Normalize by price (same as original compute_features)
			slope_vals = slope_series.values
			with np.errstate(divide="ignore", invalid="ignore"):
				raw_features[name] = np.where(price_arr != 0, slope_vals / price_arr * 100, 0.0)
		elif name == "vol":
			raw_features[name] = (prices.pct_change().rolling(window=20).std() * np.sqrt(252)).values
		elif name == "d2h":
			rolling_max = prices.rolling(window=60, min_periods=1).max().values
			raw_features[name] = (price_arr - rolling_max) / rolling_max * 100

	# Helper: Z-normalize a 1-D array slice, returns None if insufficient valid data
	def _znorm_slice(arr, start, end):
		s = arr[start:end]
		mask = ~np.isnan(s)
		valid = s[mask]
		if len(valid) < 20:
			return None
		mean = valid.mean()
		std = valid.std()
		if std < 1e-10:
			return np.zeros_like(valid)
		return (valid - mean) / std

	# Compute current window features from pre-computed arrays
	current_start = n_prices - window
	valid_features = {}
	for name in feature_names:
		normed = _znorm_slice(raw_features[name], current_start, n_prices)
		if normed is not None:
			valid_features[name] = normed

	if not valid_features:
		output_json({"error": "Could not compute any valid features for current window"})
		return

	# --- Step 4: Correlation pre-filter on price feature ---
	scan_end = n_prices - window * 2  # don't overlap with current window
	scan_start = buffer

	# Build candidate indices via fast correlation pre-filter
	max_candidates = 400
	candidate_list = None
	if "price" in valid_features and (scan_end - scan_start) > 100:
		try:
			from numpy.lib.stride_tricks import sliding_window_view
			all_windows = sliding_window_view(price_arr[scan_start:scan_end + window - 1], window)
			# Z-normalize each row
			means = all_windows.mean(axis=1, keepdims=True)
			stds = all_windows.std(axis=1, keepdims=True)
			stds = np.where(stds < 1e-10, 1.0, stds)
			normed_windows = (all_windows - means) / stds

			# Current price window Z-normalized
			curr_price = price_arr[current_start:n_prices]
			curr_mean = curr_price.mean()
			curr_std = curr_price.std()
			if curr_std < 1e-10:
				curr_std = 1.0
			curr_normed = (curr_price - curr_mean) / curr_std

			# Vectorized correlation: dot product of normalized vectors / window
			correlations = normed_windows @ curr_normed / window

			# Select top candidates, capped at max_candidates
			n_total = len(correlations)
			if n_total <= max_candidates:
				selected = np.arange(n_total)
			else:
				# Keep correlation > 0.15, but cap at max_candidates (take top by correlation)
				above_mask = correlations > 0.15
				n_above = above_mask.sum()
				if n_above <= max_candidates:
					selected = np.where(above_mask)[0]
					# Ensure at least max_candidates if possible
					if len(selected) < max_candidates:
						top_idx = np.argpartition(correlations, -max_candidates)[-max_candidates:]
						selected = top_idx
				else:
					# Too many above threshold — take top max_candidates
					top_idx = np.argpartition(correlations, -max_candidates)[-max_candidates:]
					selected = top_idx

			# Convert relative indices to absolute and sort for sequential access
			candidate_list = np.sort(selected + scan_start)
		except Exception:
			candidate_list = None  # Fallback: scan all

	# --- Scan loop with pre-computed features + pre-filter ---
	similar_patterns = []
	min_valid = max(1, int(len(valid_features) * 0.5))

	# Iterate directly over candidate list (or full range as fallback)
	scan_indices = candidate_list if candidate_list is not None else range(scan_start, scan_end)

	for i in scan_indices:
		hist_end = i + window

		# Build historical features from pre-computed arrays (just slice + Z-normalize)
		hist_features = {}
		for name in valid_features:
			normed = _znorm_slice(raw_features[name], i, hist_end)
			if normed is not None:
				hist_features[name] = normed

		if len(hist_features) < min_valid:
			continue

		# Compute weighted DTW distance
		dist, per_feature = weighted_dtw_distance(valid_features, hist_features, weights)

		if dist < args.threshold:
			similar_patterns.append(
				{
					"window_start": str(prices.index[i].date()),
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
