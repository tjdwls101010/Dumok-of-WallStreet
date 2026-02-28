#!/usr/bin/env python3
"""20-day rolling price slope normalization and RSI derivative momentum signals.

Provides three complementary momentum analysis tools based on SidneyKim0's methodology:
rolling price slope for trend strength quantification, RSI derivative with 9EMA crossover
for reversal detection, and combined momentum regime classification.

The 20-day rolling slope is computed via linear regression over a sliding window, then
normalized by current price to produce a percentage-based slope. This enables cross-asset
comparison and connects to thresholds.md rules: "20MA slope touches 1.0 then declines =
100% probability of turning negative (30-year data)".

RSI derivative analysis computes the rate of change of RSI and overlays a 9-period EMA
for crossover detection. This implements the "9-period EMA of RSI crossover = reversal
detection" signal from thresholds.md, and the "20-day RSI derivative double top = season
ending signal" pattern.

Args:
	Command: slope | rsi-derivative | momentum-regime

	slope:
		symbol (str): Stock ticker symbol (e.g., "SPY", "QQQ", "AAPL")
		--period (str): Historical data period (default: "2y")
		--interval (str): Data interval (default: "1d")
		--window (int): Rolling slope window in days (default: 20)

	rsi-derivative:
		symbol (str): Stock ticker symbol (e.g., "SPY", "QQQ")
		--period (str): Historical data period (default: "2y")
		--interval (str): Data interval (default: "1d")
		--rsi-period (int): RSI calculation period (default: 14)
		--ema-period (int): EMA period for RSI smoothing (default: 9)

	momentum-regime:
		symbol (str): Stock ticker symbol (e.g., "SPY", "QQQ")
		--period (str): Historical data period (default: "2y")
		--interval (str): Data interval (default: "1d")

Returns:
	For slope:
		dict: {
			"symbol": str,
			"date": str,
			"current_price": float,
			"slope": {
				"raw": float,              # Raw slope (price change per day)
				"normalized": float,       # Slope / price * 100 (percentage per day)
				"annualized": float,       # Normalized * 252 (annualized %)
				"z_score": float,          # Z-score vs 252-day history
				"percentile": float,       # Percentile vs history
				"direction": str           # "accelerating" | "decelerating" | "turning_negative" | "turning_positive"
			},
			"slope_history": {str: float}, # Last 20 days of normalized slope
			"thresholds_check": {
				"slope_touched_1_0": bool, # Whether slope reached 1.0 (danger signal)
				"slope_declining_from_peak": bool
			}
		}

	For rsi-derivative:
		dict: {
			"symbol": str,
			"date": str,
			"rsi": {
				"current": float,          # Current RSI value
				"ema9": float,             # 9-period EMA of RSI
				"derivative": float,       # RSI rate of change (1-day)
				"derivative_5d": float     # 5-day RSI rate of change
			},
			"signals": {
				"ema_crossover": str,      # "bullish_cross" | "bearish_cross" | "none"
				"crossover_bars_ago": int, # How many bars since last crossover
				"double_top_detected": bool,# RSI derivative double top pattern
				"rsi_divergence": str      # "bullish" | "bearish" | "none"
			},
			"rsi_history": {str: float}    # Last 20 RSI values
		}

	For momentum-regime:
		dict: {
			"symbol": str,
			"date": str,
			"regime": str,                 # "strong_uptrend" | "weakening_uptrend" | "transition" | "weakening_downtrend" | "strong_downtrend"
			"regime_score": float,         # -2 to +2 composite score
			"components": {
				"slope_signal": str,       # "bullish" | "neutral" | "bearish"
				"rsi_signal": str,         # "overbought" | "neutral" | "oversold"
				"rsi_derivative_signal": str, # "accelerating" | "decelerating" | "reversing"
				"ema_crossover_signal": str   # "bullish" | "bearish" | "neutral"
			},
			"interpretation": str
		}

Example:
	>>> python -m technical slope SPY --window 20 --period 2y
	{
		"symbol": "SPY",
		"date": "2026-02-06",
		"current_price": 602.45,
		"slope": {
			"raw": 0.85,
			"normalized": 0.141,
			"annualized": 35.5,
			"z_score": 1.23,
			"percentile": 89.2,
			"direction": "accelerating"
		}
	}

	>>> python -m technical rsi-derivative QQQ
	{
		"symbol": "QQQ",
		"date": "2026-02-06",
		"rsi": {"current": 62.3, "ema9": 58.1, "derivative": 2.1, "derivative_5d": 8.5},
		"signals": {"ema_crossover": "bullish_cross", "crossover_bars_ago": 3, "double_top_detected": false}
	}

	>>> python -m technical momentum-regime SPY
	{
		"symbol": "SPY",
		"regime": "weakening_uptrend",
		"regime_score": 0.5,
		"components": {
			"slope_signal": "bullish",
			"rsi_signal": "neutral",
			"rsi_derivative_signal": "decelerating",
			"ema_crossover_signal": "bearish"
		}
	}

Use Cases:
	- Detect momentum regime transitions before they become obvious in price
	- Identify "season ending signals" via RSI derivative double tops (07-08, 17-18, 20-21)
	- Quantify trend strength for cross-asset momentum comparison
	- Generate early reversal warnings via 9EMA of RSI crossovers
	- Validate pattern matching results with slope-based regime context

Notes:
	- Slope is computed via numpy.polyfit(degree=1) over rolling window
	- Normalized slope divides raw slope by current price for cross-asset comparability
	- RSI derivative uses calculate_rsi from indicators.py for consistency
	- 9EMA of RSI crossover is the primary reversal signal in SidneyKim0 methodology
	- "20MA slope touches 1.0 then declines = 100% turning negative" (30-year data)
	- "20-day RSI derivative double top = season ending signal" (thresholds.md)
	- Double top detection uses a simple peak-finding algorithm on RSI derivative

See Also:
	- technical/oscillators.py: RSI calculation and multi-timeframe analysis
	- technical/trend.py: Moving average trend indicators
	- technical/indicators.py: Core indicator calculation functions (calculate_rsi, calculate_ema)
	- technical/pattern/helpers.py: calculate_slope helper used in pattern analysis
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import numpy as np
import pandas as pd
import yfinance as yf
from technical.indicators import calculate_ema, calculate_rsi
from utils import output_json, safe_run


def compute_rolling_slope(prices: pd.Series, window: int = 20) -> pd.Series:
	"""Compute rolling linear regression slope over a window.

	Args:
		prices: Price series
		window: Rolling window size

	Returns:
		pd.Series: Raw slope values (price change per day)
	"""
	slopes = pd.Series(np.nan, index=prices.index)
	x = np.arange(window, dtype=float)
	for i in range(window - 1, len(prices)):
		y = prices.iloc[i - window + 1 : i + 1].values.astype(float)
		if len(y) == window and not np.any(np.isnan(y)):
			slope = np.polyfit(x, y, 1)[0]
			slopes.iloc[i] = slope
	return slopes


def detect_double_top(series: pd.Series, lookback: int = 60, min_separation: int = 10) -> bool:
	"""Detect double top pattern in a series (e.g., RSI derivative peaks).

	Args:
		series: Series to check for double top
		lookback: How far back to look
		min_separation: Minimum bars between peaks

	Returns:
		bool: True if double top detected
	"""
	recent = series.tail(lookback).dropna()
	if len(recent) < min_separation * 2:
		return False

	# Find local maxima
	values = recent.values
	peaks = []
	for i in range(1, len(values) - 1):
		if values[i] > values[i - 1] and values[i] > values[i + 1] and values[i] > 0:
			peaks.append((i, values[i]))

	if len(peaks) < 2:
		return False

	# Check last two peaks for double top pattern
	for j in range(len(peaks) - 1):
		p1_idx, p1_val = peaks[j]
		p2_idx, p2_val = peaks[j + 1]
		separation = p2_idx - p1_idx
		if separation >= min_separation:
			# Peaks should be similar magnitude (within 30%)
			if p1_val > 0 and p2_val > 0:
				ratio = min(p1_val, p2_val) / max(p1_val, p2_val)
				if ratio > 0.7:
					return True

	return False


@safe_run
def cmd_slope(args):
	"""Calculate 20-day rolling price slope with normalization and Z-score."""
	ticker = yf.Ticker(args.symbol)
	data = ticker.history(period=args.period, interval=args.interval)
	if data.empty:
		output_json({"error": f"No data for {args.symbol}"})
		return

	prices = data["Close"]
	current_price = float(prices.iloc[-1])

	# Compute rolling slope
	raw_slopes = compute_rolling_slope(prices, window=args.window)
	valid_slopes = raw_slopes.dropna()

	if len(valid_slopes) < 20:
		output_json({"error": "Insufficient data for slope calculation"})
		return

	current_raw_slope = float(raw_slopes.iloc[-1])
	normalized_slope = current_raw_slope / current_price * 100  # percentage per day
	annualized_slope = normalized_slope * 252

	# Normalized slope series for Z-score
	norm_slopes = raw_slopes / prices * 100
	valid_norm = norm_slopes.dropna()

	lookback = min(252, len(valid_norm))
	window_data = valid_norm.tail(lookback)
	slope_mean = float(window_data.mean())
	slope_std = float(window_data.std())
	z_score = (normalized_slope - slope_mean) / slope_std if slope_std > 0 else 0.0

	percentile = float((window_data < normalized_slope).sum() / len(window_data) * 100)

	# Direction detection
	recent_slopes = norm_slopes.tail(5).dropna()
	if len(recent_slopes) >= 3:
		slope_diff = float(recent_slopes.iloc[-1] - recent_slopes.iloc[-3])
		if normalized_slope > 0 and slope_diff > 0:
			direction = "accelerating"
		elif normalized_slope > 0 and slope_diff < 0:
			direction = "decelerating"
		elif normalized_slope <= 0 and slope_diff < 0:
			direction = "turning_negative" if recent_slopes.iloc[-3] > 0 else "accelerating"
		else:
			direction = "turning_positive" if recent_slopes.iloc[-3] < 0 else "decelerating"
	else:
		direction = "unknown"

	# Slope history (last 20 days)
	slope_history = {}
	for idx in norm_slopes.dropna().tail(20).index:
		date_str = str(idx.date()) if hasattr(idx, "date") else str(idx)
		slope_history[date_str] = round(float(norm_slopes.loc[idx]), 4)

	# Thresholds check (from thresholds.md)
	recent_60 = norm_slopes.tail(60).dropna()
	slope_touched_1_0 = bool((recent_60 >= 1.0).any()) if len(recent_60) > 0 else False
	slope_declining_from_peak = False
	if len(recent_60) >= 5 and slope_touched_1_0:
		peak_idx = recent_60.idxmax()
		peak_pos = recent_60.index.get_loc(peak_idx)
		if peak_pos < len(recent_60) - 1:
			slope_declining_from_peak = bool(recent_60.iloc[-1] < recent_60.iloc[peak_pos])

	result = {
		"symbol": args.symbol,
		"date": str(data.index[-1].date()),
		"current_price": round(current_price, 2),
		"slope": {
			"raw": round(current_raw_slope, 4),
			"normalized": round(normalized_slope, 4),
			"annualized": round(annualized_slope, 2),
			"z_score": round(z_score, 4),
			"percentile": round(percentile, 2),
			"direction": direction,
		},
		"slope_history": slope_history,
		"thresholds_check": {
			"slope_touched_1_0": slope_touched_1_0,
			"slope_declining_from_peak": slope_declining_from_peak,
		},
	}
	output_json(result)


@safe_run
def cmd_rsi_derivative(args):
	"""Calculate RSI derivative and 9EMA crossover signals."""
	ticker = yf.Ticker(args.symbol)
	data = ticker.history(period=args.period, interval=args.interval)
	if data.empty:
		output_json({"error": f"No data for {args.symbol}"})
		return

	prices = data["Close"]

	# Calculate RSI
	rsi = calculate_rsi(prices, period=args.rsi_period)
	rsi_valid = rsi.dropna()

	if len(rsi_valid) < 30:
		output_json({"error": "Insufficient data for RSI derivative calculation"})
		return

	# 9EMA of RSI
	rsi_ema = calculate_ema(rsi.dropna(), period=args.ema_period)

	# RSI derivative (1-day rate of change)
	rsi_deriv = rsi.diff()
	rsi_deriv_5d = rsi.diff(5)

	current_rsi = float(rsi.iloc[-1])
	current_ema9 = float(rsi_ema.iloc[-1]) if not pd.isna(rsi_ema.iloc[-1]) else None
	current_deriv = float(rsi_deriv.iloc[-1]) if not pd.isna(rsi_deriv.iloc[-1]) else None
	current_deriv_5d = float(rsi_deriv_5d.iloc[-1]) if not pd.isna(rsi_deriv_5d.iloc[-1]) else None

	# EMA crossover detection
	crossover = "none"
	crossover_bars_ago = -1

	if current_ema9 is not None:
		# Look back for most recent crossover
		for i in range(2, min(21, len(rsi_ema))):
			rsi_prev = rsi.iloc[-i]
			ema_prev = rsi_ema.iloc[-i]
			rsi_curr = rsi.iloc[-i + 1]
			ema_curr = rsi_ema.iloc[-i + 1]

			if pd.isna(rsi_prev) or pd.isna(ema_prev) or pd.isna(rsi_curr) or pd.isna(ema_curr):
				continue

			# Bullish cross: RSI crosses above EMA
			if rsi_prev <= ema_prev and rsi_curr > ema_curr:
				crossover = "bullish_cross"
				crossover_bars_ago = i - 1
				break
			# Bearish cross: RSI crosses below EMA
			elif rsi_prev >= ema_prev and rsi_curr < ema_curr:
				crossover = "bearish_cross"
				crossover_bars_ago = i - 1
				break

	# Double top detection on RSI derivative
	double_top = detect_double_top(rsi_deriv, lookback=60, min_separation=10)

	# RSI divergence (price making new high, RSI not)
	divergence = "none"
	if len(prices) >= 20 and len(rsi_valid) >= 20:
		price_high_20 = prices.tail(20).max()
		rsi_at_price_high = rsi.tail(20).max()
		price_high_5 = prices.tail(5).max()
		rsi_at_recent = rsi.tail(5).max()

		if price_high_5 >= price_high_20 * 0.998 and rsi_at_recent < rsi_at_price_high * 0.95:
			divergence = "bearish"
		elif price_high_5 <= prices.tail(20).min() * 1.002 and rsi_at_recent > rsi.tail(20).min() * 1.05:
			divergence = "bullish"

	# RSI history
	rsi_history = {}
	for idx in rsi.dropna().tail(20).index:
		date_str = str(idx.date()) if hasattr(idx, "date") else str(idx)
		rsi_history[date_str] = round(float(rsi.loc[idx]), 2)

	result = {
		"symbol": args.symbol,
		"date": str(data.index[-1].date()),
		"rsi": {
			"current": round(current_rsi, 2),
			"ema9": round(current_ema9, 2) if current_ema9 is not None else None,
			"derivative": round(current_deriv, 4) if current_deriv is not None else None,
			"derivative_5d": round(current_deriv_5d, 4) if current_deriv_5d is not None else None,
		},
		"signals": {
			"ema_crossover": crossover,
			"crossover_bars_ago": crossover_bars_ago,
			"double_top_detected": double_top,
			"rsi_divergence": divergence,
		},
		"rsi_history": rsi_history,
	}
	output_json(result)


@safe_run
def cmd_momentum_regime(args):
	"""Combined slope + RSI derivative momentum regime classification."""
	ticker = yf.Ticker(args.symbol)
	data = ticker.history(period=args.period, interval=args.interval)
	if data.empty:
		output_json({"error": f"No data for {args.symbol}"})
		return

	prices = data["Close"]

	# Slope analysis
	raw_slopes = compute_rolling_slope(prices, window=20)
	norm_slopes = raw_slopes / prices * 100
	current_norm_slope = float(norm_slopes.iloc[-1]) if not pd.isna(norm_slopes.iloc[-1]) else 0.0

	# RSI analysis
	rsi = calculate_rsi(prices, 14)
	current_rsi = float(rsi.iloc[-1]) if not pd.isna(rsi.iloc[-1]) else 50.0

	# RSI derivative
	rsi_deriv = rsi.diff()
	current_deriv = float(rsi_deriv.iloc[-1]) if not pd.isna(rsi_deriv.iloc[-1]) else 0.0

	# RSI 9EMA crossover
	rsi_ema9 = calculate_ema(rsi.dropna(), 9)
	rsi_above_ema = bool(current_rsi > float(rsi_ema9.iloc[-1])) if not pd.isna(rsi_ema9.iloc[-1]) else True

	# Component signals
	if current_norm_slope > 0.1:
		slope_signal = "bullish"
	elif current_norm_slope < -0.1:
		slope_signal = "bearish"
	else:
		slope_signal = "neutral"

	if current_rsi >= 70:
		rsi_signal = "overbought"
	elif current_rsi <= 30:
		rsi_signal = "oversold"
	else:
		rsi_signal = "neutral"

	if current_deriv > 1.0:
		rsi_deriv_signal = "accelerating"
	elif current_deriv < -1.0:
		rsi_deriv_signal = "reversing"
	else:
		rsi_deriv_signal = "decelerating"

	ema_cross_signal = "bullish" if rsi_above_ema else "bearish"

	# Composite regime score: -2 to +2
	score = 0.0
	if slope_signal == "bullish":
		score += 0.5
	elif slope_signal == "bearish":
		score -= 0.5

	if rsi_signal == "overbought":
		score += 0.25  # overbought in uptrend is still uptrend
	elif rsi_signal == "oversold":
		score -= 0.25

	if rsi_deriv_signal == "accelerating":
		score += 0.5
	elif rsi_deriv_signal == "reversing":
		score -= 0.5

	if ema_cross_signal == "bullish":
		score += 0.25
	else:
		score -= 0.25

	# Regime classification
	if score >= 1.0:
		regime = "strong_uptrend"
	elif score >= 0.25:
		regime = "weakening_uptrend"
	elif score > -0.25:
		regime = "transition"
	elif score > -1.0:
		regime = "weakening_downtrend"
	else:
		regime = "strong_downtrend"

	# Interpretation
	interpretations = {
		"strong_uptrend": "Strong bullish momentum: positive slope + accelerating RSI + bullish EMA cross",
		"weakening_uptrend": "Uptrend intact but momentum fading: watch for RSI derivative double top",
		"transition": "Momentum regime transitioning: mixed signals across slope, RSI, and EMA",
		"weakening_downtrend": "Downtrend weakening: slope still negative but RSI stabilizing",
		"strong_downtrend": "Strong bearish momentum: negative slope + declining RSI + bearish EMA cross",
	}

	result = {
		"symbol": args.symbol,
		"date": str(data.index[-1].date()),
		"regime": regime,
		"regime_score": round(score, 2),
		"components": {
			"slope_signal": slope_signal,
			"rsi_signal": rsi_signal,
			"rsi_derivative_signal": rsi_deriv_signal,
			"ema_crossover_signal": ema_cross_signal,
		},
		"raw_values": {
			"normalized_slope": round(current_norm_slope, 4),
			"rsi": round(current_rsi, 2),
			"rsi_derivative": round(current_deriv, 4),
			"rsi_above_ema9": rsi_above_ema,
		},
		"interpretation": interpretations.get(regime, "Unknown regime"),
	}
	output_json(result)
