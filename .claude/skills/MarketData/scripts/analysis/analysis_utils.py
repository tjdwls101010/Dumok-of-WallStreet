#!/usr/bin/env python3
"""Statistical Analysis Utilities providing reusable functions for multi-asset correlation, z-score, and percentile calculations.

Implements common statistical operations used across MarketData analysis scripts including z-score normalization
for regime detection, percentile ranking for relative valuation, rolling correlation for relationship tracking,
and series normalization for multi-asset comparison. Shared utility layer for convergence, divergence, and macro analysis.

Args:
	series (pd.Series): Time series data for analysis (prices, returns, indicators)
	lookback (int): Historical window size for rolling calculations (e.g., 252 trading days = 1 year)
	window (int): Rolling correlation window size (e.g., 60 days = 3 months)

Returns:
	Various types depending on function:
    
	calculate_z_score(series, lookback) -> tuple:
		(
			z_score: float,     # Standard deviations from mean (-3 to +3 typical range)
			mean: float,        # Historical average
			std: float          # Historical standard deviation
		)
    
	calculate_percentile(series, lookback) -> float:
		percentile: float       # 0-100, current value's historical rank
    
	calculate_rolling_correlation(series1, series2, window) -> pd.Series:
		rolling_corr: pd.Series # Time series of correlation values (-1 to +1)
    
	z_normalize(series) -> pd.Series:
		normalized: pd.Series   # Standardized series (mean=0, std=1)

Example:
	>>> import pandas as pd
	>>> from analysis_utils import calculate_z_score, calculate_percentile
	>>> prices = pd.Series([100, 102, 98, 105, 110, 108])
	>>> z_score, mean, std = calculate_z_score(prices, lookback=5)
	>>> print(f"Z-Score: {z_score:.2f}, Mean: {mean:.2f}")
	Z-Score: 0.31, Mean: 104.60
    
	>>> percentile = calculate_percentile(prices, lookback=5)
	>>> print(f"Current price is at {percentile:.0f}th percentile")
	Current price is at 80th percentile

Use Cases:
	- Z-score regime detection: Identify when assets deviate >2σ from historical norms (mean reversion signals)
	- Multi-asset correlation tracking: Monitor relationship breakdown between SPY, GLD, TLT for regime shifts
	- Percentile-based valuation: Rank CAPE ratio or P/E ratios vs historical distribution (cheap/expensive)
	- Series normalization: Compare assets with different scales (SPY $500 vs VIX $15) on equal footing
	- Rolling correlation divergence: Detect when traditional correlations break down (risk-off events)

Notes:
	- Z-scores >2 or <-2 indicate extreme deviations (2.5% probability assuming normality)
	- Z-scores >3 or <-3 are rare events (0.3% probability, potential reversal signals)
	- Lookback period affects sensitivity: shorter (20d) catches rapid moves, longer (252d) smooths noise
	- Percentile ranking is distribution-free (works for non-normal data unlike z-scores)
	- Rolling correlation with window=60 balances responsiveness vs stability for regime detection
	- Z-normalization enables cross-asset comparison (SPY returns vs VIX changes)

See Also:
	- convergence.py: Uses calculate_z_score for macro fair value residual analysis
	- divergence.py: Uses calculate_rolling_correlation for yield-equity relationship tracking
	- macro/macro.py: Uses z_normalize for multi-factor regression with different scales
	- cape.py: Uses calculate_percentile for CAPE ratio historical ranking
"""

import pandas as pd


def calculate_z_score(series: pd.Series, lookback: int) -> tuple:
	"""Calculate z-score for the latest value based on lookback period."""
	if len(series) < lookback:
		lookback = len(series)

	window_data = series.tail(lookback)
	mean = window_data.mean()
	std = window_data.std()

	if std == 0:
		return 0.0, mean, std

	current = series.iloc[-1]
	z_score = (current - mean) / std
	return z_score, mean, std


def calculate_percentile(series: pd.Series, lookback: int) -> float:
	"""Calculate percentile rank of the latest value."""
	if len(series) < lookback:
		lookback = len(series)

	window_data = series.tail(lookback)
	current = series.iloc[-1]

	# Calculate percentile rank
	rank = (window_data < current).sum() / len(window_data) * 100
	return rank


def calculate_rolling_correlation(series1: pd.Series, series2: pd.Series, window: int) -> pd.Series:
	"""Calculate rolling correlation between two series."""
	return series1.rolling(window=window).corr(series2)


def z_normalize(series: pd.Series) -> pd.Series:
	"""Z-normalize a series (mean=0, std=1)."""
	mean = series.mean()
	std = series.std()
	if std == 0:
		return series - mean
	return (series - mean) / std
