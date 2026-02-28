#!/usr/bin/env python3
"""Pattern analysis helper functions for DTW, correlation, and forward return calculations.

This module provides utility functions for pattern matching and analysis used across
similarity.py, fanchart.py, and other pattern detection scripts.

Functions include DTW distance calculation, pattern correlation, forward returns,
fan chart percentile generation, and slope-based pattern matching.

Args:
	For calculate_dtw_distance:
		series1 (np.ndarray): First normalized price series
		series2 (np.ndarray): Second normalized price series

	For calculate_slope:
		prices (pd.Series): Price series
		window (int): Rolling window for slope calculation (default: 20)

	For calculate_pattern_correlation:
		current_window (pd.Series): Current price window
		historical_window (pd.Series): Historical price window (must be same length)

	For find_similar_patterns:
		prices (pd.Series): Full price history
		window_size (int): Pattern window size in days (default: 140)
		top_n (int): Number of most similar patterns to return (default: 10)

	For calculate_forward_returns:
		prices (pd.Series): Full price history
		event_dates (list): List of pattern end dates
		forward_days (list): Forward periods in days (default: [30, 60, 90])

	For calculate_fan_chart:
		returns_data (dict): Forward returns by period from calculate_forward_returns

Returns:
	For calculate_dtw_distance:
		float: DTW distance (lower = more similar)

	For calculate_slope:
		pd.Series: Rolling slope values (NaN for initial periods)

	For calculate_pattern_correlation:
		float: Pearson correlation coefficient (-1 to 1)

	For find_similar_patterns:
		list: [
			{
				"window_start": str,
				"window_end": str,
				"correlation": float
			}
		]

	For calculate_forward_returns:
		dict: {
			"30d": [float, ...],  # List of 30-day returns
			"60d": [float, ...],
			"90d": [float, ...]
		}

	For calculate_fan_chart:
		dict: {
			"30d": {
				"p10": float,     # 10th percentile
				"p25": float,     # 25th percentile
				"p50": float,     # 50th percentile (median)
				"p75": float,     # 75th percentile
				"p90": float,     # 90th percentile
				"mean": float,    # Average return
				"count": int      # Sample size
			},
			"60d": {...},
			"90d": {...}
		}

Example:
	>>> import pandas as pd
	>>> import numpy as np
	>>> from analysis.analysis_utils import z_normalize
	>>>
	>>> # DTW distance calculation
	>>> series1 = z_normalize(prices.tail(60)).values
	>>> series2 = z_normalize(prices.iloc[-120:-60]).values
	>>> dtw_dist = calculate_dtw_distance(series1, series2)
	>>> print(f"DTW Distance: {dtw_dist:.4f}")
	DTW Distance: 0.2345
	>>>
	>>> # Pattern correlation
	>>> current = prices.tail(140)
	>>> historical = prices.iloc[-280:-140]
	>>> corr = calculate_pattern_correlation(current, historical)
	>>> print(f"Correlation: {corr:.4f}")
	Correlation: 0.8523
	>>>
	>>> # Find similar patterns
	>>> similar = find_similar_patterns(prices, window_size=140, top_n=5)
	>>> for p in similar:
	>>>     print(f"{p['window_end']}: {p['correlation']:.4f}")
	2020-09-01: 0.8523
	2019-06-10: 0.7892
	>>>
	>>> # Forward returns and fan chart
	>>> event_dates = ["2020-03-23", "2018-12-24"]
	>>> returns = calculate_forward_returns(prices, event_dates, [30, 60, 90])
	>>> fan_chart = calculate_fan_chart(returns)
	>>> print(fan_chart["30d"])
	{'p10': -5.2, 'p25': -1.8, 'p50': 2.5, 'p75': 6.8, 'p90': 11.3, 'mean': 3.1, 'count': 10}

Use Cases:
	- Build custom pattern matching workflows combining DTW and correlation
	- Create probabilistic forecasts using historical forward return distributions
	- Compare pattern similarity methods (correlation vs DTW vs slope-based)
	- Generate fan chart visualizations for risk/reward scenario planning
	- Develop backtesting frameworks using historical pattern matching

Notes:
	- DTW allows time-shifted matching; correlation requires aligned time series
	- Slope-based matching reduces noise and focuses on trend direction changes
	- Z-normalization is recommended before DTW to ensure scale invariance
	- Correlation threshold of 0.3+ filters weak matches (SidneyKim0 methodology)
	- Forward returns assume historical patterns repeat with similar outcomes
	- Fan chart percentiles provide distribution shape: symmetric = normal, skewed = tail risk
	- Larger sample sizes (count) produce more reliable percentile estimates

See Also:
	- pattern/similarity.py: Pattern matching using these helper functions
	- pattern/fanchart.py: Fan chart generation workflow
	- analysis/analysis_utils.py: Z-normalization and statistical utilities
"""

import numpy as np
import pandas as pd
from analysis.analysis_utils import z_normalize


def calculate_dtw_distance(series1: np.ndarray, series2: np.ndarray) -> float:
	"""Calculate Dynamic Time Warping distance between two normalized series.

	DTW measures similarity between two sequences that may vary in timing or speed.
	Unlike Euclidean distance, DTW allows time-shifted alignment for better matching.

	Algorithm:
	1. Create cost matrix of size (n+1) x (m+1)
	2. Initialize first row and column to infinity except [0,0] = 0
	3. Fill matrix using recurrence relation:
	   DTW[i,j] = cost[i,j] + min(DTW[i-1,j], DTW[i,j-1], DTW[i-1,j-1])
	4. Return DTW[n,m] as final distance

	Args:
		series1: First normalized price series (z-normalized recommended)
		series2: Second normalized price series (z-normalized recommended)

	Returns:
		float: DTW distance (lower = more similar; 0 = identical)
	"""
	n, m = len(series1), len(series2)

	# Create cost matrix
	dtw_matrix = np.full((n + 1, m + 1), np.inf)
	dtw_matrix[0, 0] = 0

	for i in range(1, n + 1):
		for j in range(1, m + 1):
			cost = abs(series1[i - 1] - series2[j - 1])
			dtw_matrix[i, j] = cost + min(
				dtw_matrix[i - 1, j],  # insertion
				dtw_matrix[i, j - 1],  # deletion
				dtw_matrix[i - 1, j - 1],  # match
			)

	return dtw_matrix[n, m]


def calculate_slope(prices: pd.Series, window: int = 20) -> pd.Series:
	"""Calculate rolling slope of price series using linear regression.

	Slope represents the rate of price change (trend direction and strength).
	Positive slope = uptrend, negative slope = downtrend, zero = sideways.

	Args:
		prices: Price series (typically Close prices)
		window: Rolling window for slope calculation (default: 20)

	Returns:
		pd.Series: Slope values (NaN for first window-1 periods)
	"""
	slopes = []
	for i in range(len(prices)):
		if i < window - 1:
			slopes.append(np.nan)
		else:
			window_prices = prices.iloc[i - window + 1 : i + 1].values
			x = np.arange(window)
			slope = np.polyfit(x, window_prices, 1)[0]
			slopes.append(slope)
	return pd.Series(slopes, index=prices.index)


def calculate_pattern_correlation(current_window: pd.Series, historical_window: pd.Series) -> float:
	"""Calculate Pearson correlation between two z-normalized price windows.

	Correlation measures linear similarity between patterns after normalization.
	+1 = perfect positive correlation, 0 = no correlation, -1 = perfect negative correlation.

	Args:
		current_window: Current price window (recent period)
		historical_window: Historical price window (must be same length as current)

	Returns:
		float: Correlation coefficient (0-1 range; 0 if lengths mismatch or calculation fails)
	"""
	if len(current_window) != len(historical_window):
		return 0.0
	# Z-normalize both windows, reset index to positional for alignment
	curr_norm = z_normalize(current_window).reset_index(drop=True)
	hist_norm = z_normalize(historical_window).reset_index(drop=True)
	# Calculate correlation (positional alignment, not DatetimeIndex)
	correlation = curr_norm.corr(hist_norm)
	return correlation if not pd.isna(correlation) else 0.0


def find_similar_patterns(prices: pd.Series, window_size: int = 140, top_n: int = 10) -> list:
	"""Find top N most similar historical patterns to current window using correlation.

	Slides a window through historical prices and compares each window to current period.
	Returns top matches sorted by correlation strength (highest first).

	Args:
		prices: Full price history
		window_size: Pattern window size in days (default: 140 = ~6 months)
		top_n: Number of most similar patterns to return (default: 10)

	Returns:
		list: [
			{
				"window_start": str,    # Pattern start date
				"window_end": str,      # Pattern end date
				"correlation": float    # Correlation coefficient (0.3-1.0)
			}
		]
		Sorted by correlation (descending)
	"""
	if len(prices) < window_size * 2:
		return []

	current_window = prices.tail(window_size)
	similar_patterns = []

	# Slide through history
	for i in range(len(prices) - window_size * 2):
		hist_start = i
		hist_end = i + window_size
		historical_window = prices.iloc[hist_start:hist_end]

		correlation = calculate_pattern_correlation(current_window, historical_window)

		if correlation > 0.3:  # Lower threshold for more pattern matches (SidneyKim0)
			similar_patterns.append(
				{
					"window_start": str(prices.index[hist_start].date()),
					"window_end": str(prices.index[hist_end - 1].date()),
					"correlation": round(correlation, 4),
				}
			)

	# Sort by correlation and return top N
	similar_patterns.sort(key=lambda x: x["correlation"], reverse=True)
	return similar_patterns[:top_n]


def calculate_forward_returns(prices: pd.Series, event_dates: list, forward_days: list = [30, 60, 90]) -> dict:
	"""Calculate forward returns after each event date for specified periods.

	For each event date, calculate percentage returns after 30, 60, 90 days (or custom periods).
	Used to build historical outcome distributions for fan charts.

	Args:
		prices: Full price history
		event_dates: List of pattern end dates (strings or Timestamps)
		forward_days: Forward periods in days (default: [30, 60, 90])

	Returns:
		dict: {
			"30d": [return1, return2, ...],  # List of 30-day returns
			"60d": [return1, return2, ...],
			"90d": [return1, return2, ...]
		}
	"""
	returns_data = {f"{d}d": [] for d in forward_days}

	for event_date in event_dates:
		try:
			event_idx = prices.index.get_loc(pd.Timestamp(event_date))
			event_price = prices.iloc[event_idx]

			for days in forward_days:
				if event_idx + days < len(prices):
					future_price = prices.iloc[event_idx + days]
					ret = (future_price - event_price) / event_price * 100
					returns_data[f"{days}d"].append(ret)
		except (KeyError, IndexError):
			continue

	return returns_data


def calculate_fan_chart(returns_data: dict) -> dict:
	"""Calculate percentile distribution for fan chart visualization.

	Generates 10th, 25th, 50th, 75th, 90th percentiles plus mean for each forward period.
	Percentiles represent probability ranges: p10-p90 = 80% confidence interval.

	Args:
		returns_data: Forward returns by period from calculate_forward_returns

	Returns:
		dict: {
			"30d": {
				"p10": float,     # 10th percentile (bearish tail)
				"p25": float,     # 25th percentile (bearish scenario)
				"p50": float,     # 50th percentile (median outcome)
				"p75": float,     # 75th percentile (bullish scenario)
				"p90": float,     # 90th percentile (bullish tail)
				"mean": float,    # Average return
				"count": int      # Sample size (number of historical analogues)
			},
			"60d": {...},
			"90d": {...}
		}
	"""
	fan_chart = {}
	percentiles = [10, 25, 50, 75, 90]

	for period, returns in returns_data.items():
		if len(returns) >= 3:
			fan_chart[period] = {f"p{p}": round(float(np.percentile(returns, p)), 2) for p in percentiles}
			fan_chart[period]["mean"] = round(float(np.mean(returns)), 2)
			fan_chart[period]["count"] = len(returns)

	return fan_chart
