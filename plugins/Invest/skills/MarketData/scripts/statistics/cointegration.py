#!/usr/bin/env python3
"""Test cointegration between two symbols using Engle-Granger method for pairs trading.

Cointegration tests whether two non-stationary price series maintain a stationary long-term relationship.
Unlike correlation which measures co-movement, cointegration identifies pairs that revert to equilibrium,
making it ideal for statistical arbitrage and pairs trading strategies.

Args:
	symbol1 (str): First symbol (dependent variable, e.g., "AAPL")
	symbol2 (str): Second symbol (independent variable, e.g., "MSFT")
	--period (str): Historical data period for analysis (default: "5y" = 5 years)
	--interval (str): Data interval (default: "1d" = daily)

Returns:
	dict: {
		"symbol1": str,                    # First symbol (dependent variable)
		"symbol2": str,                    # Second symbol (independent variable)
		"period": str,                     # Data period used
		"data_points": int,                # Number of overlapping data points
		"regression": {                    # OLS regression results
			"alpha": float,                # Intercept coefficient
			"beta": float,                 # Slope coefficient (hedge ratio)
			"interpretation": str          # Equation: Y = alpha + beta * X
		},
		"adf_test": {                      # Augmented Dickey-Fuller test on residuals
			"t_statistic": float,          # ADF test statistic
			"critical_values": {           # Critical values for significance levels
				"1%": float,
				"5%": float,
				"10%": float
			},
			"is_cointegrated_1pct": bool,  # Significant at 1% level
			"is_cointegrated_5pct": bool,  # Significant at 5% level
			"is_cointegrated_10pct": bool  # Significant at 10% level
		},
		"spread_analysis": {               # Current spread statistics
			"current_spread": float,       # Current spread value
			"spread_mean": float,          # Historical mean spread
			"spread_std": float,           # Spread standard deviation
			"spread_zscore": float,        # Current spread z-score
			"half_life_days": float        # Mean-reversion half-life (if cointegrated)
		},
		"conclusion": str,                 # Cointegration test result
		"trading_signal": str              # Signal based on spread z-score
	}

Example:
	>>> python cointegration.py AAPL MSFT --period 5y
	{
		"symbol1": "AAPL",
		"symbol2": "MSFT",
		"period": "5y",
		"data_points": 1258,
		"regression": {
			"alpha": 12.34,
			"beta": 0.8765,
			"interpretation": "AAPL = 12.34 + 0.8765 * MSFT"
		},
		"adf_test": {
			"t_statistic": -4.12,
			"critical_values": {"1%": -3.96, "5%": -3.37, "10%": -3.07},
			"is_cointegrated_1pct": true,
			"is_cointegrated_5pct": true,
			"is_cointegrated_10pct": true
		},
		"spread_analysis": {
			"current_spread": 2.45,
			"spread_mean": 0.15,
			"spread_std": 1.05,
			"spread_zscore": 2.19,
			"half_life_days": 12.3
		},
		"conclusion": "COINTEGRATED (statistically significant long-term relationship)",
		"trading_signal": "Spread is WIDE - potential mean reversion opportunity"
	}

Use Cases:
	- Pairs trading: Identify cointegrated pairs for mean-reversion strategies
	- Statistical arbitrage: Exploit spread deviations from equilibrium
	- Hedge ratio calculation: Beta coefficient provides optimal hedge ratio
	- Entry/exit signals: Trade when spread z-score exceeds ±2σ threshold
	- Portfolio construction: Build market-neutral strategies with cointegrated pairs

Notes:
	- Cointegration requires long history (5y recommended) for reliable test results
	- Beta coefficient (hedge ratio) indicates units of symbol2 to hedge symbol1
	- Half-life estimates mean-reversion speed (shorter = faster reversion)
	- ADF test checks if spread is stationary (mean-reverting)
	- Spread z-score >2 or <-2 signals potential mean-reversion opportunities
	- Cointegration can break down during regime changes or market stress
	- Minimum 30 data points required for meaningful test results

See Also:
	- correlation.py: Measure short-term relationship strength (different from cointegration)
	- zscore.py: Calculate spread z-scores for entry/exit timing
	- extremes.py: Identify historical extreme spread events
	- multi_correlation.py: Screen multiple pairs for cointegration candidates
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import numpy as np
import yfinance as yf
from utils import output_json, safe_run


@safe_run
def cmd_cointegration(args):
	"""Test cointegration between two symbols using Engle-Granger method."""
	ticker1 = yf.Ticker(args.symbol1)
	ticker2 = yf.Ticker(args.symbol2)

	data1 = ticker1.history(period=args.period, interval=args.interval)
	data2 = ticker2.history(period=args.period, interval=args.interval)

	if data1.empty or data2.empty:
		output_json({"error": "No data for one or both symbols"})
		return

	prices1 = data1["Close"]
	prices2 = data2["Close"]

	# Align by index
	common_idx = prices1.index.intersection(prices2.index)
	prices1 = prices1.loc[common_idx]
	prices2 = prices2.loc[common_idx]

	if len(prices1) < 30:
		output_json({"error": "Insufficient overlapping data for cointegration test"})
		return

	# Simple Engle-Granger cointegration test implementation
	# Step 1: OLS regression y = a + b*x + e
	x = prices2.values
	y = prices1.values
	n = len(x)

	x_mean = np.mean(x)
	y_mean = np.mean(y)

	# Calculate regression coefficients
	beta = np.sum((x - x_mean) * (y - y_mean)) / np.sum((x - x_mean) ** 2)
	alpha = y_mean - beta * x_mean

	# Calculate residuals
	residuals = y - (alpha + beta * x)

	# Step 2: ADF test on residuals (simplified)
	# Calculate first differences of residuals
	resid_diff = np.diff(residuals)
	resid_lag = residuals[:-1]

	# Simple ADF regression: delta_resid = gamma * resid_lag + error
	gamma = np.sum(resid_lag * resid_diff) / np.sum(resid_lag**2)
	se_gamma = np.sqrt(np.var(resid_diff - gamma * resid_lag) / np.sum(resid_lag**2))
	t_stat = gamma / se_gamma if se_gamma > 0 else 0

	# Critical values for cointegration test (Engle-Granger)
	# Approximate critical values at 1%, 5%, 10% significance levels
	critical_values = {"1%": -3.96, "5%": -3.37, "10%": -3.07}

	# Determine cointegration
	is_cointegrated_1pct = t_stat < critical_values["1%"]
	is_cointegrated_5pct = t_stat < critical_values["5%"]
	is_cointegrated_10pct = t_stat < critical_values["10%"]

	# Calculate spread statistics
	spread_mean = np.mean(residuals)
	spread_std = np.std(residuals)
	current_spread = residuals[-1]
	spread_zscore = (current_spread - spread_mean) / spread_std if spread_std > 0 else 0

	# Half-life of mean reversion (if cointegrated)
	half_life = -np.log(2) / gamma if gamma < 0 else None

	result = {
		"symbol1": args.symbol1,
		"symbol2": args.symbol2,
		"period": args.period,
		"data_points": n,
		"regression": {
			"alpha": round(float(alpha), 4),
			"beta": round(float(beta), 4),
			"interpretation": f"{args.symbol1} = {round(alpha, 2)} + {round(beta, 4)} * {args.symbol2}",
		},
		"adf_test": {
			"t_statistic": round(float(t_stat), 4),
			"critical_values": critical_values,
			"is_cointegrated_1pct": is_cointegrated_1pct,
			"is_cointegrated_5pct": is_cointegrated_5pct,
			"is_cointegrated_10pct": is_cointegrated_10pct,
		},
		"spread_analysis": {
			"current_spread": round(float(current_spread), 4),
			"spread_mean": round(float(spread_mean), 4),
			"spread_std": round(float(spread_std), 4),
			"spread_zscore": round(float(spread_zscore), 2),
			"half_life_days": round(float(half_life), 1) if half_life and half_life > 0 else None,
		},
		"conclusion": "COINTEGRATED (statistically significant long-term relationship)"
		if is_cointegrated_5pct
		else "NOT COINTEGRATED (no statistically significant relationship)",
		"trading_signal": "Spread is WIDE - potential mean reversion opportunity"
		if abs(spread_zscore) > 2
		else "Spread is NORMAL - no clear signal"
		if abs(spread_zscore) < 1
		else "Spread is ELEVATED - monitor for entry",
	}
	output_json(result)


if __name__ == "__main__":
	import argparse

	parser = argparse.ArgumentParser(description="Test cointegration between two symbols")
	parser.add_argument("symbol1", help="First symbol (dependent variable)")
	parser.add_argument("symbol2", help="Second symbol (independent variable)")
	parser.add_argument("--period", default="5y", help="Data period")
	parser.add_argument("--interval", default="1d", help="Data interval")
	args = parser.parse_args()
	cmd_cointegration(args)
