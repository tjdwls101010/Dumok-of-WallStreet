#!/usr/bin/env python3
"""Multi-parameter macro inference model with residual Z-score analysis.

Builds a statistical model estimating a target asset's "fair value" based on
multiple macro input variables, then computes residual Z-scores to identify
statistical overextension or undervaluation relative to macro fundamentals.

SidneyKim0's signature analytical tool: when the residual Z-score exceeds
±2σ, the target asset is statistically extended vs what macro conditions
suggest. ±4σ indicates historically unprecedented deviation.

Commands:
    infer: Build macro inference model and compute residual Z-scores
    backtest: Backtest model signal accuracy over historical periods
    sensitivity: Analyze model sensitivity to each input variable

Args:
    target (str): Target asset ticker (e.g., "^GSPC", "^IXIC", "QQQ")
    --inputs (str): Comma-separated macro input tickers
                    (default: "DX-Y.NYB,^TNX,GC=F,^VIX")
    --period (str): Historical period for model fitting (default: "5y")
    --method (str): Model method - "ols", "ridge", "rolling" (default: "rolling")
    --window (int): Rolling window size in days (default: 252)

Returns:
    dict: {
        "target": str,
        "inputs": [str],
        "current_residual_zscore": float,
        "current_residual_sigma": float,
        "model_estimate": float,
        "actual_price": float,
        "deviation_pct": float,
        "r_squared": float,
        "historical_residuals": {
            "mean": float,
            "std": float,
            "current_percentile": float
        },
        "input_coefficients": {
            "variable": {"coef": float, "t_stat": float}
        },
        "extreme_episodes": [
            {"date": str, "zscore": float, "subsequent_30d_return": float}
        ]
    }

Example:
    >>> python macro_inference.py infer ^GSPC --inputs "DX-Y.NYB,^TNX,GC=F,^VIX"
    {
        "target": "^GSPC",
        "inputs": ["DX-Y.NYB", "^TNX", "GC=F", "^VIX"],
        "current_residual_zscore": 2.34,
        "current_residual_sigma": "2.3σ (above macro fair value) - Significant",
        "model_estimate": 5820.50,
        "actual_price": 5950.20,
        "deviation_pct": 2.23,
        "r_squared": 0.87,
        "historical_residuals": {
            "mean": 0.21,
            "std": 55.30,
            "current_percentile": 97.8
        },
        "input_coefficients": {
            "DX-Y.NYB": {"coef": -15.23, "t_stat": -4.12},
            "^TNX": {"coef": -85.40, "t_stat": -3.21},
            "GC=F": {"coef": 0.45, "t_stat": 2.87},
            "^VIX": {"coef": -12.30, "t_stat": -5.43}
        },
        "extreme_episodes": [
            {"date": "2021-11-19", "zscore": 2.51, "subsequent_30d_return": -5.21}
        ]
    }

Use Cases:
    - Identify when S&P 500 is statistically over/undervalued vs. macro inputs
    - Detect when equity market has "borrowed" too much from future macro conditions
    - Find historical episodes of similar Z-score extremes for scenario analysis
    - Quantify the sensitivity of the model to each macro variable

Notes:
    - Rolling OLS (default) updates coefficients over time; better handles regime changes
    - Ridge regularization available for high-multicollinearity input sets
    - R-squared > 0.70 indicates reliable macro inference model
    - Extreme episodes are defined as |Z-score| > threshold (default: 2.0)
    - T-statistics above ±2.0 indicate statistically significant factor relationships

See Also:
    - SKILL.md → Macro category for related macro analysis tools
    - SKILL.md → Statistics category for standalone Z-score tools
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import numpy as np
import pandas as pd
from macro.macro_utils import fetch_aligned_data, ols_regression
from utils import output_json, safe_run


def _rolling_ols(X_matrix, y_vector, window):
	"""Compute rolling OLS regression over a sliding window.

	Returns:
		betas: (n, k) array of coefficients at each time step (NaN before window filled)
		predictions: (n,) array of fitted values
		residuals: (n,) array of residuals
	"""
	n, k = X_matrix.shape
	betas = np.full((n, k), np.nan)
	predictions = np.full(n, np.nan)
	residuals = np.full(n, np.nan)

	for i in range(window, n):
		X_win = X_matrix[i - window:i]
		y_win = y_vector[i - window:i]
		try:
			XtX = X_win.T @ X_win
			XtX_inv = np.linalg.inv(XtX)
			beta = XtX_inv @ (X_win.T @ y_win)
			betas[i] = beta
			predictions[i] = X_matrix[i] @ beta
			residuals[i] = y_vector[i] - predictions[i]
		except np.linalg.LinAlgError:
			continue

	return betas, predictions, residuals


def _ridge_regression(X_matrix, y_vector, lam=0.01):
	"""Ridge regression: beta = (X'X + lambda*I)^-1 X'y."""
	k = X_matrix.shape[1]
	XtX = X_matrix.T @ X_matrix
	XtX_reg = XtX + lam * np.eye(k)
	XtX_inv = np.linalg.inv(XtX_reg)
	beta = XtX_inv @ (X_matrix.T @ y_vector)
	predictions = X_matrix @ beta
	residuals = y_vector - predictions
	return beta, predictions, residuals, XtX_inv


def _interpret_sigma(zscore):
	"""Interpret residual z-score in SidneyKim0 framework."""
	abs_z = abs(zscore)
	direction = "above" if zscore > 0 else "below"
	if abs_z >= 4:
		label = "Historically Unprecedented"
	elif abs_z >= 3:
		label = "Extreme"
	elif abs_z >= 2:
		label = "Significant"
	elif abs_z >= 1:
		label = "Moderate"
	else:
		label = "Normal"
	return f"{abs_z:.1f}σ ({direction} macro fair value) - {label}"


@safe_run
def cmd_infer(args):
	"""Build macro inference model and compute residual Z-scores."""
	input_symbols = [s.strip() for s in args.inputs.split(",")]
	all_symbols = [args.target] + input_symbols
	df = fetch_aligned_data(all_symbols, period=args.period)

	if df.empty or args.target not in df.columns:
		output_json({"error": f"Insufficient data for {args.target} with inputs {input_symbols}"})
		return

	available_inputs = [s for s in input_symbols if s in df.columns]
	if not available_inputs:
		output_json({"error": f"No input symbols available in data: {input_symbols}"})
		return

	X_df = df[available_inputs]
	y_series = df[args.target]

	# Add constant column
	X_with_const = X_df.copy()
	X_with_const["const"] = 1
	X_matrix = X_with_const.values
	y_vector = y_series.values
	col_names = list(X_with_const.columns)
	n, k = X_matrix.shape

	if args.method == "rolling":
		window = min(args.window, n - 1)
		if window < k + 1:
			output_json({"error": f"Insufficient data for rolling window {args.window}. Need at least {k + 2} data points."})
			return

		betas, predictions, residuals = _rolling_ols(X_matrix, y_vector, window)

		# Use the last valid beta for coefficient reporting
		last_valid_idx = -1
		for i in range(n - 1, -1, -1):
			if not np.isnan(betas[i, 0]):
				last_valid_idx = i
				break
		if last_valid_idx < 0:
			output_json({"error": "Rolling OLS produced no valid coefficients"})
			return

		final_beta = betas[last_valid_idx]

		# Compute XtX_inv for the last window for t-stats
		X_last_win = X_matrix[last_valid_idx - window:last_valid_idx]
		try:
			XtX = X_last_win.T @ X_last_win
			XtX_inv = np.linalg.inv(XtX)
		except np.linalg.LinAlgError:
			XtX_inv = np.eye(k)

		# R-squared for rolling: use valid predictions only
		valid_mask = ~np.isnan(predictions)
		if valid_mask.sum() < 2:
			output_json({"error": "Insufficient valid predictions from rolling OLS"})
			return
		y_valid = y_vector[valid_mask]
		pred_valid = predictions[valid_mask]
		ss_res = np.sum((y_valid - pred_valid) ** 2)
		ss_tot = np.sum((y_valid - np.mean(y_valid)) ** 2)
		r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0

	elif args.method == "ridge":
		if n < k + 1:
			output_json({"error": f"Insufficient data points ({n}) for ridge regression with {k} parameters"})
			return

		final_beta, predictions, residuals, XtX_inv = _ridge_regression(X_matrix, y_vector, lam=0.01)
		ss_res = np.sum(residuals ** 2)
		ss_tot = np.sum((y_vector - np.mean(y_vector)) ** 2)
		r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0

	else:  # ols
		result = ols_regression(X_df, y_series)
		if "error" in result:
			output_json(result)
			return

		predictions = result["predictions"]
		residuals = y_vector - predictions
		r_squared = result["r_squared"]

		# Reconstruct beta and XtX_inv for t-stats
		try:
			XtX = X_matrix.T @ X_matrix
			XtX_inv = np.linalg.inv(XtX)
			final_beta = XtX_inv @ (X_matrix.T @ y_vector)
		except np.linalg.LinAlgError:
			XtX_inv = np.eye(k)
			final_beta = np.zeros(k)

	# Compute residual statistics
	valid_residuals = residuals[~np.isnan(residuals)]
	if len(valid_residuals) < 2:
		output_json({"error": "Insufficient valid residuals for Z-score computation"})
		return

	residual_mean = float(np.mean(valid_residuals))
	residual_std = float(np.std(valid_residuals))
	current_residual = float(valid_residuals[-1])
	current_zscore = (current_residual - residual_mean) / residual_std if residual_std > 0 else 0.0

	# Percentile
	current_percentile = float(np.sum(valid_residuals < current_residual) / len(valid_residuals) * 100)

	# Model estimate and actual
	valid_pred = predictions[~np.isnan(predictions)]
	model_estimate = float(valid_pred[-1]) if len(valid_pred) > 0 else 0.0
	actual_price = float(y_vector[-1])
	deviation_pct = (actual_price - model_estimate) / model_estimate * 100 if model_estimate != 0 else 0.0

	# T-statistics for coefficients
	valid_mask = ~np.isnan(residuals)
	n_valid = int(valid_mask.sum())
	input_coefficients = {}
	if n_valid > k:
		mse = np.sum(valid_residuals ** 2) / (n_valid - k)
		se = np.sqrt(np.abs(mse * np.diag(XtX_inv)))
		for i, name in enumerate(col_names):
			if name == "const":
				continue
			coef_val = float(final_beta[i])
			t_stat = coef_val / se[i] if se[i] > 0 else 0.0
			input_coefficients[name] = {
				"coef": round(coef_val, 4),
				"t_stat": round(float(t_stat), 4),
			}
	else:
		for i, name in enumerate(col_names):
			if name == "const":
				continue
			input_coefficients[name] = {
				"coef": round(float(final_beta[i]), 4),
				"t_stat": 0.0,
			}

	# Extreme episodes
	extreme_episodes = []
	rolling_resid_mean = pd.Series(valid_residuals).rolling(window=min(args.window, len(valid_residuals) - 1)).mean()
	rolling_resid_std = pd.Series(valid_residuals).rolling(window=min(args.window, len(valid_residuals) - 1)).std()
	rolling_zscore = (pd.Series(valid_residuals) - rolling_resid_mean) / rolling_resid_std.replace(0, np.nan)

	# Map valid residuals back to original index
	valid_indices = np.where(valid_mask)[0]
	for j in range(len(rolling_zscore)):
		if pd.isna(rolling_zscore.iloc[j]):
			continue
		z = float(rolling_zscore.iloc[j])
		if abs(z) > args.threshold:
			orig_idx = valid_indices[j]
			date_val = df.index[orig_idx]
			date_str = str(date_val.date()) if hasattr(date_val, "date") else str(date_val)

			# Subsequent 30-day return
			future_idx = orig_idx + 30
			if future_idx < len(y_vector):
				ret_30d = (y_vector[future_idx] - y_vector[orig_idx]) / y_vector[orig_idx] * 100
			else:
				ret_30d = None

			extreme_episodes.append({
				"date": date_str,
				"zscore": round(z, 4),
				"subsequent_30d_return": round(float(ret_30d), 2) if ret_30d is not None else None,
			})

	output_json({
		"target": args.target,
		"inputs": available_inputs,
		"method": args.method,
		"period": args.period,
		"window": args.window,
		"data_points": len(df),
		"current_residual_zscore": round(current_zscore, 4),
		"current_residual_sigma": _interpret_sigma(current_zscore),
		"model_estimate": round(model_estimate, 2),
		"actual_price": round(actual_price, 2),
		"deviation_pct": round(deviation_pct, 2),
		"r_squared": round(r_squared, 4),
		"historical_residuals": {
			"mean": round(residual_mean, 4),
			"std": round(residual_std, 4),
			"current_percentile": round(current_percentile, 2),
		},
		"input_coefficients": input_coefficients,
		"extreme_episodes": extreme_episodes[-20:],
		"date": str(df.index[-1].date()) if hasattr(df.index[-1], "date") else str(df.index[-1]),
	})


@safe_run
def cmd_backtest(args):
	"""Backtest model signal accuracy over historical periods."""
	input_symbols = [s.strip() for s in args.inputs.split(",")]
	all_symbols = [args.target] + input_symbols
	df = fetch_aligned_data(all_symbols, period=args.period)

	if df.empty or args.target not in df.columns:
		output_json({"error": f"Insufficient data for {args.target}"})
		return

	available_inputs = [s for s in input_symbols if s in df.columns]
	if not available_inputs:
		output_json({"error": f"No input symbols available: {input_symbols}"})
		return

	X_df = df[available_inputs]
	y_series = df[args.target]

	X_with_const = X_df.copy()
	X_with_const["const"] = 1
	X_matrix = X_with_const.values
	y_vector = y_series.values
	n, k = X_matrix.shape

	window = min(args.window, n - 1)
	if window < k + 1:
		output_json({"error": f"Insufficient data for rolling window"})
		return

	_, predictions, residuals = _rolling_ols(X_matrix, y_vector, window)

	# Compute rolling z-scores on residuals
	valid_mask = ~np.isnan(residuals)
	valid_residuals = residuals[valid_mask]
	valid_indices = np.where(valid_mask)[0]

	if len(valid_residuals) < window:
		output_json({"error": "Insufficient valid residuals for backtest"})
		return

	resid_series = pd.Series(valid_residuals)
	roll_mean = resid_series.rolling(window=min(window, len(resid_series) - 1)).mean()
	roll_std = resid_series.rolling(window=min(window, len(resid_series) - 1)).std()
	zscore_series = (resid_series - roll_mean) / roll_std.replace(0, np.nan)

	signals = []
	for j in range(len(zscore_series)):
		if pd.isna(zscore_series.iloc[j]):
			continue
		z = float(zscore_series.iloc[j])
		if abs(z) > args.threshold:
			orig_idx = valid_indices[j]
			date_val = df.index[orig_idx]
			date_str = str(date_val.date()) if hasattr(date_val, "date") else str(date_val)

			signal_entry = {
				"date": date_str,
				"zscore": round(z, 4),
				"direction": "overvalued" if z > 0 else "undervalued",
			}

			# Subsequent returns at various horizons
			for horizon_name, horizon_days in [("5d", 5), ("10d", 10), ("20d", 20), ("30d", 30)]:
				future_idx = orig_idx + horizon_days
				if future_idx < len(y_vector):
					ret = (y_vector[future_idx] - y_vector[orig_idx]) / y_vector[orig_idx] * 100
					signal_entry[f"subsequent_{horizon_name}_return"] = round(float(ret), 2)
				else:
					signal_entry[f"subsequent_{horizon_name}_return"] = None

			signals.append(signal_entry)

	# Summary statistics
	signals_with_30d = [s for s in signals if s.get("subsequent_30d_return") is not None]
	if signals_with_30d:
		returns_30d = [s["subsequent_30d_return"] for s in signals_with_30d]
		avg_30d = float(np.mean(returns_30d))
		positive_count = sum(1 for r in returns_30d if r > 0)
		win_rate = positive_count / len(returns_30d) * 100
	else:
		avg_30d = 0.0
		positive_count = 0
		win_rate = 0.0

	output_json({
		"target": args.target,
		"inputs": available_inputs,
		"period": args.period,
		"window": args.window,
		"threshold": args.threshold,
		"signals": signals,
		"summary": {
			"total_signals": len(signals),
			"avg_30d_return": round(avg_30d, 4),
			"win_rate_pct": round(win_rate, 2),
			"positive_signals": positive_count,
		},
	})


@safe_run
def cmd_sensitivity(args):
	"""Analyze model sensitivity to each input variable."""
	input_symbols = [s.strip() for s in args.inputs.split(",")]
	all_symbols = [args.target] + input_symbols
	df = fetch_aligned_data(all_symbols, period=args.period)

	if df.empty or args.target not in df.columns:
		output_json({"error": f"Insufficient data for {args.target}"})
		return

	available_inputs = [s for s in input_symbols if s in df.columns]
	if not available_inputs:
		output_json({"error": f"No input symbols available: {input_symbols}"})
		return

	X_df = df[available_inputs]
	y_series = df[args.target]

	X_with_const = X_df.copy()
	X_with_const["const"] = 1
	X_matrix = X_with_const.values
	y_vector = y_series.values
	col_names = list(X_with_const.columns)
	n, k = X_matrix.shape

	# Full OLS for sensitivity analysis
	try:
		XtX = X_matrix.T @ X_matrix
		XtX_inv = np.linalg.inv(XtX)
		beta = XtX_inv @ (X_matrix.T @ y_vector)
		predictions = X_matrix @ beta
		residuals = y_vector - predictions
	except np.linalg.LinAlgError:
		output_json({"error": "Matrix inversion failed for sensitivity analysis"})
		return

	# MSE and standard errors
	mse = np.sum(residuals ** 2) / (n - k) if n > k else 0.0
	se = np.sqrt(np.abs(mse * np.diag(XtX_inv)))

	# Compute input standard deviations for contribution calculation
	input_stds = {}
	for name in available_inputs:
		input_stds[name] = float(X_df[name].std())

	# Absolute weighted contributions: |coef * input_std|
	contributions = {}
	total_contribution = 0.0
	for i, name in enumerate(col_names):
		if name == "const":
			continue
		coef_val = float(beta[i])
		input_std = input_stds.get(name, 1.0)
		abs_contribution = abs(coef_val * input_std)
		contributions[name] = abs_contribution
		total_contribution += abs_contribution

	# Build sensitivity results
	sensitivity_results = []
	for i, name in enumerate(col_names):
		if name == "const":
			continue
		coef_val = float(beta[i])
		t_stat = coef_val / se[i] if se[i] > 0 else 0.0
		pct_contribution = (contributions[name] / total_contribution * 100) if total_contribution > 0 else 0.0

		# Correlation of input with target residuals
		input_vals = X_df[name].values
		corr = float(np.corrcoef(input_vals, residuals)[0, 1]) if len(residuals) > 1 else 0.0

		sensitivity_results.append({
			"variable": name,
			"coefficient": round(coef_val, 4),
			"t_statistic": round(float(t_stat), 4),
			"pct_contribution": round(pct_contribution, 2),
			"input_std": round(input_stds.get(name, 0.0), 4),
			"residual_correlation": round(corr, 4),
		})

	# Sort by pct_contribution descending
	sensitivity_results.sort(key=lambda x: x["pct_contribution"], reverse=True)

	# R-squared
	ss_res = np.sum(residuals ** 2)
	ss_tot = np.sum((y_vector - np.mean(y_vector)) ** 2)
	r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0

	output_json({
		"target": args.target,
		"inputs": available_inputs,
		"period": args.period,
		"data_points": len(df),
		"r_squared": round(r_squared, 4),
		"sensitivity": sensitivity_results,
		"date": str(df.index[-1].date()) if hasattr(df.index[-1], "date") else str(df.index[-1]),
	})


def main():
	parser = argparse.ArgumentParser(description="Multi-parameter macro inference model")
	sub = parser.add_subparsers(dest="command", required=True)

	# infer
	sp = sub.add_parser("infer", help="Build macro inference model and compute residual Z-scores")
	sp.add_argument("target", help="Target asset ticker (e.g., ^GSPC)")
	sp.add_argument("--inputs", default="DX-Y.NYB,^TNX,GC=F,^VIX", help="Comma-separated macro input tickers")
	sp.add_argument("--period", default="5y", help="Historical period for model fitting")
	sp.add_argument("--method", default="rolling", choices=["ols", "ridge", "rolling"], help="Model method")
	sp.add_argument("--window", type=int, default=252, help="Rolling window size in days")
	sp.add_argument("--threshold", type=float, default=2.0, help="Z-score threshold for extreme episodes")
	sp.set_defaults(func=cmd_infer)

	# backtest
	sp = sub.add_parser("backtest", help="Backtest model signal accuracy over historical periods")
	sp.add_argument("target", help="Target asset ticker")
	sp.add_argument("--inputs", default="DX-Y.NYB,^TNX,GC=F,^VIX", help="Comma-separated macro input tickers")
	sp.add_argument("--period", default="5y", help="Historical period")
	sp.add_argument("--window", type=int, default=252, help="Rolling window size in days")
	sp.add_argument("--threshold", type=float, default=2.0, help="Z-score threshold for signals")
	sp.set_defaults(func=cmd_backtest)

	# sensitivity
	sp = sub.add_parser("sensitivity", help="Analyze model sensitivity to each input variable")
	sp.add_argument("target", help="Target asset ticker")
	sp.add_argument("--inputs", default="DX-Y.NYB,^TNX,GC=F,^VIX", help="Comma-separated macro input tickers")
	sp.add_argument("--period", default="5y", help="Historical period")
	sp.add_argument("--window", type=int, default=252, help="Rolling window size in days")
	sp.set_defaults(func=cmd_sensitivity)

	args = parser.parse_args()
	args.func(args)


if __name__ == "__main__":
	main()
