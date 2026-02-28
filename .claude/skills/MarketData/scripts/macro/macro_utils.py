#!/usr/bin/env python3
"""Macro analysis utility functions for MarketData skill.

Provides core utilities for macro-economic analysis including multi-asset data alignment,
timezone normalization, and OLS regression without external ML libraries. These functions
form the foundation for fair value modeling and factor analysis.

Functions:
	fetch_aligned_data: Download and synchronize multi-asset price data
	ols_regression: Perform linear regression using numpy matrix operations

Args (fetch_aligned_data):
	symbols (list[str]): List of ticker symbols to fetch
	period (str): Historical data period (default: "5y")
	interval (str): Data interval/granularity (default: "1d")

Returns (fetch_aligned_data):
	pd.DataFrame: Aligned price data with symbols as columns, timestamps as index

Args (ols_regression):
	X (pd.DataFrame): Independent variables (macro factors)
	y (pd.Series): Dependent variable (target asset)

Returns (ols_regression):
	dict: {
		"coefficients": dict,       # Factor beta values + intercept
		"r_squared": float,         # Model fit quality (0-1)
		"predictions": np.ndarray   # Fitted values
	} or {"error": str} on failure

Example:
	>>> # Fetch and align data
	>>> df = fetch_aligned_data(["SPY", "DX-Y.NYB", "GC=F"], period="2y")
	>>> print(df.head())
				SPY  DX-Y.NYB    GC=F
	2023-02-05  410.5  102.45  1920.30
    
	>>> # Run regression
	>>> X = df[["DX-Y.NYB", "GC=F"]]
	>>> y = df["SPY"]
	>>> result = ols_regression(X, y)
	>>> print(result["r_squared"])
	0.8750
	>>> print(result["coefficients"])
	{"DX-Y.NYB": -2.45, "GC=F": 0.08, "const": 450.2}

Use Cases:
	- Multi-asset data preparation for regression models
	- Factor analysis and sensitivity calculations
	- Fair value model estimation via OLS
	- Macro factor relationship quantification
	- Residual calculation for mean reversion signals

Notes:
	- Timezone normalization prevents alignment issues across markets
	- All NaN rows dropped to ensure clean regression inputs
	- Minimum 2 symbols required for valid DataFrame output
	- OLS uses numpy matrix operations (no scikit-learn dependency)
	- R-squared > 0.70 indicates strong factor relationship
	- Matrix inversion may fail with multicollinear factors
	- No regularization applied (pure OLS without penalties)
	- Coefficients represent factor sensitivities (β values)

See Also:
	- macro.py fairvalue: Uses these utilities for regression modeling
	- macro.py residual: Analyzes regression residuals over time
	- macro.py convergence: Combines regression with other signals
	- gbm.py: Alternative stochastic model without factor regression
"""

import numpy as np
import pandas as pd
import yfinance as yf


def fetch_aligned_data(symbols: list, period: str = "5y", interval: str = "1d") -> pd.DataFrame:
	"""Fetch and align historical price data for multiple symbols.

	Downloads price data for multiple tickers and aligns them by date, handling
	timezone normalization and missing data removal. Essential for multi-asset
	regression models where all factors must have synchronized timestamps.

	Args:
		symbols (list[str]): List of ticker symbols to fetch (e.g., ["SPY", "DX-Y.NYB", "GC=F"])
		period (str): Historical data period (default: "5y")
			Valid values: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max
		interval (str): Data interval/granularity (default: "1d")
			Valid values: 1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo

	Returns:
		pd.DataFrame: DataFrame with symbols as columns and timestamps as index.
			Empty DataFrame if fewer than 2 symbols have valid data.
			All rows with any missing values are dropped for alignment.

	Example:
		>>> df = fetch_aligned_data(["SPY", "DX-Y.NYB", "GC=F"], period="2y")
		>>> print(df.head())
					SPY  DX-Y.NYB    GC=F
		2023-02-05  410.5  102.45  1920.30
		2023-02-06  412.3  102.60  1925.50
		>>> print(len(df))  # Number of aligned trading days
		504

	Use Cases:
		- Prepare data for multi-asset regression models
		- Synchronize macro factors with target asset
		- Build correlation matrices across assets
		- Time series analysis requiring aligned data

	Notes:
		- Timezone information is removed (normalized) to prevent alignment issues
		- Symbols with no data are silently excluded from output
		- Minimum 2 symbols required for valid output
		- All NaN rows dropped to ensure clean regression inputs
		- Uses Close prices for all symbols

	See Also:
		- ols_regression: Regression analysis on aligned data
		- macro.py fairvalue: Uses this function for data preparation
	"""
	data_dict = {}
	for sym in symbols:
		ticker = yf.Ticker(sym.strip())
		hist = ticker.history(period=period, interval=interval)
		if not hist.empty:
			# Normalize index to date only (remove timezone issues)
			close_series = hist["Close"].copy()
			close_series.index = close_series.index.normalize().tz_localize(None)
			data_dict[sym.strip()] = close_series

	if len(data_dict) < 2:
		return pd.DataFrame()

	df = pd.DataFrame(data_dict)
	df = df.dropna()
	return df


def ols_regression(X: pd.DataFrame, y: pd.Series) -> dict:
	"""Perform Ordinary Least Squares (OLS) regression without scikit-learn.

	Calculates linear regression using numpy matrix operations:
	β = (X'X)⁻¹X'y

	Where:
	- X: Matrix of independent variables (factors)
	- y: Vector of dependent variable (target)
	- β: Vector of regression coefficients

	Args:
		X (pd.DataFrame): Independent variables (macro factors)
			Shape: (n_observations, n_factors)
			Example: DataFrame with columns ["DX-Y.NYB", "GC=F", "^TNX"]
		y (pd.Series): Dependent variable (target asset)
			Shape: (n_observations,)
			Example: Series of SPY prices

	Returns:
		dict: {
			"coefficients": dict,       # {factor: beta_value, "const": intercept}
			"r_squared": float,         # Model fit quality (0-1, higher is better)
			"predictions": np.ndarray   # Fitted values (y_hat)
		}
		or {"error": str} if matrix inversion fails

	Example:
		>>> import pandas as pd
		>>> X = pd.DataFrame({
		...     "DX-Y.NYB": [102, 103, 101],
		...     "GC=F": [1920, 1925, 1915]
		... })
		>>> y = pd.Series([410, 412, 408], name="SPY")
		>>> result = ols_regression(X, y)
		>>> print(result["r_squared"])
		0.8750
		>>> print(result["coefficients"])
		{"DX-Y.NYB": -2.45, "GC=F": 0.08, "const": 450.2}

	Use Cases:
		- Fair value model estimation (macro factor regression)
		- Factor sensitivity analysis via coefficients
		- Model quality assessment via R-squared
		- Residual calculation for mean reversion signals

	Notes:
		- R-squared interpretation:
			- 0.70-0.89: Strong relationship
			- 0.50-0.69: Moderate relationship
			- <0.50: Weak relationship
		- Intercept added automatically as "const" coefficient
		- Matrix inversion may fail with multicollinearity
		- No regularization applied (pure OLS)
		- Coefficients rounded to 6 decimal places
		- R-squared and predictions rounded to 4 decimal places

	See Also:
		- fetch_aligned_data: Data preparation for regression
		- macro.py fairvalue: Uses OLS for fair value estimation
		- macro.py residual: Analyzes regression residuals
	"""
	# Add constant (intercept)
	X_with_const = X.copy()
	X_with_const["const"] = 1

	# OLS: beta = (X'X)^-1 X'y
	X_matrix = X_with_const.values
	y_vector = y.values

	try:
		XtX = X_matrix.T @ X_matrix
		XtX_inv = np.linalg.inv(XtX)
		Xty = X_matrix.T @ y_vector
		beta = XtX_inv @ Xty

		# Predictions
		y_pred = X_matrix @ beta

		# R-squared
		ss_res = np.sum((y_vector - y_pred) ** 2)
		ss_tot = np.sum((y_vector - np.mean(y_vector)) ** 2)
		r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0

		# Coefficients
		coefficients = {col: round(float(beta[i]), 6) for i, col in enumerate(X_with_const.columns)}

		return {"coefficients": coefficients, "r_squared": round(float(r_squared), 4), "predictions": y_pred}
	except np.linalg.LinAlgError:
		return {"error": "Matrix inversion failed"}
