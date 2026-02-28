#!/usr/bin/env python3
"""Core helper functions for backtest analysis.

Provides reusable components for condition detection and probability calculation
used across backtest scripts. Implements pivot point methodology (SidneyKim0)
for identifying meaningful reversal events rather than simple threshold crossings.

Functions:
	find_condition_events: Detect dates where technical conditions are met
	calculate_target_probability: Calculate probability of reaching target after events

Args (find_condition_events):
	data (pd.DataFrame): Price data with OHLCV columns
	condition_type (str): Condition to detect
		- "rsi_above": RSI exceeds threshold then pivots down
		- "rsi_below": RSI falls below threshold then pivots up
		- "zscore_above": Z-score crosses above threshold
		- "zscore_below": Z-score crosses below threshold
	threshold (float): Threshold value for condition
	use_pivot (bool): If True, detect pivot points (default: True)
					 If False, detect initial crossing only

Returns (find_condition_events):
	list: [
		{
			"date": str,      # Event date (YYYY-MM-DD)
			"value": float,   # Indicator value at event
			"price": float    # Close price at event
		}
	]

Args (calculate_target_probability):
	data (pd.DataFrame): Price data with OHLCV columns
	events (list): List of event dictionaries from find_condition_events
	target_type (str): Target outcome type
		- "rsi_below": RSI falls below target_value
		- "rsi_above": RSI rises above target_value
		- "return_below": Price return falls below target_value %
		- "return_above": Price return rises above target_value %
	target_value (float): Threshold for target achievement
	max_days (int): Maximum forward lookback period (default: 30)

Returns (calculate_target_probability):
	dict: {
		"total_events": int,        # Total events analyzed
		"successes": int,            # Events that reached target
		"probability": float,        # Success rate as percentage
		"avg_days_to_target": float, # Average days to reach target
		"min_days": int,             # Fastest target achievement
		"max_days": int              # Slowest target achievement
	}

Example (find_condition_events):
	>>> import yfinance as yf
	>>> data = yf.Ticker("AAPL").history(period="1y")
	>>> events = find_condition_events(data, "rsi_above", 70, use_pivot=True)
	>>> events[0]
	{
		"date": "2025-06-15",
		"value": 72.5,
		"price": 185.20
	}

Example (calculate_target_probability):
	>>> prob = calculate_target_probability(data, events, "return_below", -5, max_days=30)
	>>> prob
	{
		"total_events": 15,
		"successes": 11,
		"probability": 73.3,
		"avg_days_to_target": 12.4,
		"min_days": 3,
		"max_days": 28
	}

Use Cases:
	- Reusable condition detection across multiple backtest scripts
	- Pivot point methodology for cleaner signal generation
	- Probability calculation for conditional analysis
	- Event-based backtesting infrastructure

Notes:
	- Pivot detection (default): Identifies reversal points after threshold breach
		- RSI above 70 + pivot down = overbought reversal signal
		- RSI below 30 + pivot up = oversold reversal signal
	- Simple crossing (use_pivot=False): Detects first threshold breach only
	- Z-score lookback: Uses 252-day rolling window (1 trading year)
	- RSI period: Fixed at 14 periods (standard default)
	- Forward-looking bias: Ensure target calculation doesn't peek into future
	- Sample size: Probability estimates unreliable with <20 events

See Also:
	- conditional.py: Uses these helpers for probability analysis
	- event_returns.py: Uses find_condition_events for return calculations
	- indicators.py: Provides calculate_rsi function used internally
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pandas as pd
from indicators import calculate_rsi


def find_condition_events(data: pd.DataFrame, condition_type: str, threshold: float, use_pivot: bool = True) -> list:
	"""Find all dates where condition is met.

	Args:
		data: Price data
		condition_type: Type of condition (rsi_above, rsi_below, etc.)
		threshold: Threshold value
		use_pivot: If True, detect pivot points (reversal after crossing threshold)
				   If False, detect initial crossing only
	"""
	events = []
	prices = data["Close"]

	if condition_type == "rsi_above":
		rsi = calculate_rsi(prices, 14)

		if use_pivot:
			# SidneyKim0 methodology: "RSI 80+ break then pivot"
			# Find points where RSI was above threshold and started declining
			above_threshold = rsi > threshold
			declining = rsi < rsi.shift(1)
			# Pivot = was above threshold, now declining, and previous point was not declining
			pivot = above_threshold & declining & ~declining.shift(1).fillna(False)
			event_indices = data.index[pivot]
		else:
			# Original behavior: first crossing above threshold
			mask = rsi > threshold
			crossed = mask & ~mask.shift(1).fillna(False)
			event_indices = data.index[crossed]

		for idx in event_indices:
			loc = data.index.get_loc(idx)
			events.append(
				{
					"date": str(idx.date()),
					"value": round(float(rsi.iloc[loc]), 2),
					"price": round(float(prices.iloc[loc]), 2),
				}
			)

	elif condition_type == "rsi_below":
		rsi = calculate_rsi(prices, 14)

		if use_pivot:
			# SidneyKim0 methodology: "RSI 30- break then pivot"
			# Find points where RSI was below threshold and started rising
			below_threshold = rsi < threshold
			rising = rsi > rsi.shift(1)
			# Pivot = was below threshold, now rising, and previous point was not rising
			pivot = below_threshold & rising & ~rising.shift(1).fillna(False)
			event_indices = data.index[pivot]
		else:
			# Original behavior: first crossing below threshold
			mask = rsi < threshold
			crossed = mask & ~mask.shift(1).fillna(False)
			event_indices = data.index[crossed]

		for idx in event_indices:
			loc = data.index.get_loc(idx)
			events.append(
				{
					"date": str(idx.date()),
					"value": round(float(rsi.iloc[loc]), 2),
					"price": round(float(prices.iloc[loc]), 2),
				}
			)

	elif condition_type == "zscore_above":
		lookback = 252
		rolling_mean = prices.rolling(lookback).mean()
		rolling_std = prices.rolling(lookback).std()
		zscore = (prices - rolling_mean) / rolling_std
		mask = zscore > threshold
		crossed = mask & ~mask.shift(1).fillna(False)
		event_indices = data.index[crossed]
		for idx in event_indices:
			loc = data.index.get_loc(idx)
			events.append(
				{
					"date": str(idx.date()),
					"value": round(float(zscore.iloc[loc]), 2),
					"price": round(float(prices.iloc[loc]), 2),
				}
			)

	elif condition_type == "zscore_below":
		lookback = 252
		rolling_mean = prices.rolling(lookback).mean()
		rolling_std = prices.rolling(lookback).std()
		zscore = (prices - rolling_mean) / rolling_std
		mask = zscore < threshold
		crossed = mask & ~mask.shift(1).fillna(False)
		event_indices = data.index[crossed]
		for idx in event_indices:
			loc = data.index.get_loc(idx)
			events.append(
				{
					"date": str(idx.date()),
					"value": round(float(zscore.iloc[loc]), 2),
					"price": round(float(prices.iloc[loc]), 2),
				}
			)

	return events


def calculate_target_probability(
	data: pd.DataFrame, events: list, target_type: str, target_value: float, max_days: int = 30
) -> dict:
	"""Calculate probability of hitting target after event."""
	prices = data["Close"]
	successes = 0
	days_to_target = []

	for event in events:
		event_date = pd.Timestamp(event["date"])
		try:
			event_idx = data.index.get_loc(event_date)
		except KeyError:
			continue

		# Look forward up to max_days
		for days in range(1, min(max_days + 1, len(prices) - event_idx)):
			future_idx = event_idx + days

			if target_type == "rsi_below":
				rsi = calculate_rsi(prices, 14)
				if rsi.iloc[future_idx] < target_value:
					successes += 1
					days_to_target.append(days)
					break
			elif target_type == "rsi_above":
				rsi = calculate_rsi(prices, 14)
				if rsi.iloc[future_idx] > target_value:
					successes += 1
					days_to_target.append(days)
					break
			elif target_type == "return_below":
				ret = (prices.iloc[future_idx] - prices.iloc[event_idx]) / prices.iloc[event_idx] * 100
				if ret < target_value:
					successes += 1
					days_to_target.append(days)
					break
			elif target_type == "return_above":
				ret = (prices.iloc[future_idx] - prices.iloc[event_idx]) / prices.iloc[event_idx] * 100
				if ret > target_value:
					successes += 1
					days_to_target.append(days)
					break

	total = len(events)
	probability = successes / total if total > 0 else 0

	return {
		"total_events": total,
		"successes": successes,
		"probability": round(probability * 100, 1),
		"avg_days_to_target": round(sum(days_to_target) / len(days_to_target), 1) if days_to_target else None,
		"min_days": min(days_to_target) if days_to_target else None,
		"max_days": max(days_to_target) if days_to_target else None,
	}
