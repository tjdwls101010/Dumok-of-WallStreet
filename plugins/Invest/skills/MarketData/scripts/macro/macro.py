#!/usr/bin/env python3
"""Macro model and fair value analysis for SidneyKim0 methodology.

Provides comprehensive macro-economic analysis tools including multi-factor regression models,
residual analysis, spread calculations, and multi-model signal convergence. Combines technical,
statistical, and fundamental approaches for robust market analysis.

Args:
	Command: fairvalue | residual | spread | convergence

	fairvalue:
		target (str): Target symbol to predict (e.g., "SPY")
		--inputs (str): Comma-separated macro factor symbols (e.g., "DX-Y.NYB,GC=F,^TNX")
		--period (str): Historical data period (default: "5y")
		--interval (str): Data interval (default: "1d")

	residual:
		target (str): Target symbol to analyze
		--inputs (str): Comma-separated macro factor symbols
		--lookback (int): Rolling window for z-score (default: 252)
		--threshold (float): Sigma threshold for extremes (default: 3.0)
		--period (str): Historical data period (default: "5y")
		--interval (str): Data interval (default: "1d")

	spread:
		symbol1 (str): First symbol (e.g., "^TYX")
		symbol2 (str): Second symbol (e.g., "^TNX")
		--spread-type (str): "difference" or "ratio" (default: "difference")
		--lookback (int): Statistics window (default: 252)
		--period (str): Historical data period (default: "5y")
		--interval (str): Data interval (default: "1d")

	convergence:
		target (str): Target symbol to analyze (e.g., "SPY")
		--symbols (str): Comma-separated symbols for macro model
		--period (str): Historical data period (default: "2y")
		--interval (str): Data interval (default: "1d")

Returns:
	dict: Command-specific output structure (see individual function docstrings)

See Also:
	- macro_utils.py: Core regression and data alignment utilities
	- gbm.py: Alternative stochastic fair value model
	- convergence.py: Standalone multi-model convergence analysis
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import numpy as np
import pandas as pd
import yfinance as yf
from macro.macro_utils import fetch_aligned_data, ols_regression
from utils import output_json, safe_run


@safe_run
def cmd_fairvalue(args):
	"""Multi-factor OLS fair value model."""
	input_symbols = [s.strip() for s in args.inputs.split(",")]
	all_symbols = [args.target] + input_symbols
	df = fetch_aligned_data(all_symbols, period=args.period, interval=args.interval)

	if df.empty or args.target not in df.columns:
		output_json({"error": f"Insufficient data for {args.target} with inputs {input_symbols}"})
		return

	available_inputs = [s for s in input_symbols if s in df.columns]
	if not available_inputs:
		output_json({"error": f"No input symbols available in data: {input_symbols}"})
		return

	X = df[available_inputs]
	y = df[args.target]
	result = ols_regression(X, y)

	if "error" in result:
		output_json(result)
		return

	predictions = result["predictions"]
	residuals = y.values - predictions
	current_actual = float(y.iloc[-1])
	current_predicted = float(predictions[-1])
	current_residual = current_actual - current_predicted

	# Residual z-score over full period
	residual_mean = float(np.mean(residuals))
	residual_std = float(np.std(residuals))
	residual_zscore = (current_residual - residual_mean) / residual_std if residual_std > 0 else 0.0

	output_json({
		"target": args.target,
		"inputs": available_inputs,
		"period": args.period,
		"data_points": len(df),
		"model": {
			"r_squared": result["r_squared"],
			"coefficients": result["coefficients"],
		},
		"current_analysis": {
			"actual": round(current_actual, 2),
			"predicted": round(current_predicted, 2),
			"residual": round(current_residual, 2),
			"residual_zscore": round(residual_zscore, 4),
			"residual_pct": round(current_residual / current_predicted * 100, 2) if current_predicted != 0 else 0,
		},
		"interpretation": _interpret_residual(residual_zscore),
		"date": str(df.index[-1].date()) if hasattr(df.index[-1], "date") else str(df.index[-1]),
	})


@safe_run
def cmd_residual(args):
	"""Rolling residual Z-score with extreme event detection."""
	input_symbols = [s.strip() for s in args.inputs.split(",")]
	all_symbols = [args.target] + input_symbols
	df = fetch_aligned_data(all_symbols, period=args.period, interval=args.interval)

	if df.empty or args.target not in df.columns:
		output_json({"error": f"Insufficient data for {args.target}"})
		return

	available_inputs = [s for s in input_symbols if s in df.columns]
	if not available_inputs:
		output_json({"error": f"No input symbols available: {input_symbols}"})
		return

	X = df[available_inputs]
	y = df[args.target]
	result = ols_regression(X, y)

	if "error" in result:
		output_json(result)
		return

	predictions = result["predictions"]
	residuals = pd.Series(y.values - predictions, index=df.index)

	# Rolling z-score
	lookback = min(args.lookback, len(residuals) - 1)
	rolling_mean = residuals.rolling(window=lookback).mean()
	rolling_std = residuals.rolling(window=lookback).std()
	zscore_series = (residuals - rolling_mean) / rolling_std.replace(0, np.nan)

	# Detect extremes
	extreme_mask = zscore_series.abs() > args.threshold
	extreme_events = []
	for idx in zscore_series[extreme_mask].dropna().index:
		extreme_events.append({
			"date": str(idx.date()) if hasattr(idx, "date") else str(idx),
			"zscore": round(float(zscore_series.loc[idx]), 4),
			"residual": round(float(residuals.loc[idx]), 2),
			"actual": round(float(y.loc[idx]), 2),
			"predicted": round(float(predictions[df.index.get_loc(idx)]), 2),
		})

	current_zscore = float(zscore_series.iloc[-1]) if not pd.isna(zscore_series.iloc[-1]) else 0.0
	current_residual = float(residuals.iloc[-1])

	# Recent z-score history (last 20 trading days)
	recent_zscores = {}
	for idx in zscore_series.dropna().tail(20).index:
		date_str = str(idx.date()) if hasattr(idx, "date") else str(idx)
		recent_zscores[date_str] = round(float(zscore_series.loc[idx]), 4)

	output_json({
		"target": args.target,
		"inputs": available_inputs,
		"period": args.period,
		"lookback": lookback,
		"threshold": args.threshold,
		"model_r_squared": result["r_squared"],
		"current_status": {
			"residual": round(current_residual, 2),
			"zscore": round(current_zscore, 4),
			"is_extreme": abs(current_zscore) > args.threshold,
			"sigma_level": f"{abs(current_zscore):.1f}σ ({'above' if current_zscore > 0 else 'below'} fair value)",
		},
		"extreme_events_count": len(extreme_events),
		"extreme_events_recent": extreme_events[-10:],
		"recent_zscores": recent_zscores,
		"interpretation": _interpret_residual(current_zscore),
		"date": str(df.index[-1].date()) if hasattr(df.index[-1], "date") else str(df.index[-1]),
	})


@safe_run
def cmd_spread(args):
	"""Two-symbol spread analysis with regime classification."""
	df = fetch_aligned_data([args.symbol1, args.symbol2], period=args.period, interval=args.interval)

	if df.empty or args.symbol1 not in df.columns or args.symbol2 not in df.columns:
		output_json({"error": f"Insufficient data for {args.symbol1} and {args.symbol2}"})
		return

	s1 = df[args.symbol1]
	s2 = df[args.symbol2]

	if args.spread_type == "ratio":
		spread = s1 / s2
		spread_label = f"{args.symbol1} / {args.symbol2}"
	else:
		spread = s1 - s2
		spread_label = f"{args.symbol1} - {args.symbol2}"

	lookback = min(args.lookback, len(spread) - 1)
	rolling_mean = spread.rolling(window=lookback).mean()
	rolling_std = spread.rolling(window=lookback).std()

	current_spread = float(spread.iloc[-1])
	current_mean = float(rolling_mean.iloc[-1]) if not pd.isna(rolling_mean.iloc[-1]) else current_spread
	current_std = float(rolling_std.iloc[-1]) if not pd.isna(rolling_std.iloc[-1]) else 1.0
	current_zscore = (current_spread - current_mean) / current_std if current_std > 0 else 0.0

	# Percentile
	valid_spread = spread.dropna()
	percentile = float((valid_spread < current_spread).sum() / len(valid_spread) * 100)

	# Regime classification for yield spreads
	regime = _classify_spread_regime(args.symbol1, args.symbol2, s1, s2, spread)

	# Recent spread history
	recent = {}
	for idx in spread.tail(20).index:
		date_str = str(idx.date()) if hasattr(idx, "date") else str(idx)
		recent[date_str] = round(float(spread.loc[idx]), 4)

	output_json({
		"spread": spread_label,
		"spread_type": args.spread_type,
		"period": args.period,
		"data_points": len(df),
		"current": {
			"value": round(current_spread, 4),
			"mean": round(current_mean, 4),
			"std": round(current_std, 4),
			"zscore": round(current_zscore, 4),
			"percentile": round(percentile, 2),
		},
		"statistics": {
			"min": round(float(valid_spread.min()), 4),
			"max": round(float(valid_spread.max()), 4),
			"median": round(float(valid_spread.median()), 4),
		},
		"regime": regime,
		"recent_spread": recent,
		"date": str(df.index[-1].date()) if hasattr(df.index[-1], "date") else str(df.index[-1]),
	})


@safe_run
def cmd_convergence(args):
	"""Multi-model signal convergence assessment."""
	input_symbols = [s.strip() for s in args.symbols.split(",")]
	all_symbols = [args.target] + input_symbols

	# Fetch data
	ticker = yf.Ticker(args.target)
	data = ticker.history(period=args.period, interval=args.interval)
	if data.empty:
		output_json({"error": f"No data for {args.target}"})
		return

	prices = data["Close"]

	# Technical signal: RSI
	delta = prices.diff()
	gain = delta.where(delta > 0, 0).rolling(14).mean()
	loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
	rs = gain / loss.replace(0, np.nan)
	rsi = 100 - (100 / (1 + rs))
	current_rsi = float(rsi.iloc[-1]) if not pd.isna(rsi.iloc[-1]) else 50.0
	tech_signal = "BEARISH" if current_rsi > 70 else ("BULLISH" if current_rsi < 30 else "NEUTRAL")

	# Statistical signal: Z-score
	lookback = min(252, len(prices) - 1)
	price_mean = float(prices.tail(lookback).mean())
	price_std = float(prices.tail(lookback).std())
	price_zscore = (float(prices.iloc[-1]) - price_mean) / price_std if price_std > 0 else 0.0
	stat_signal = "BEARISH" if price_zscore > 2 else ("BULLISH" if price_zscore < -2 else "NEUTRAL")

	# Macro signal: residual from regression
	macro_signal = "NEUTRAL"
	macro_zscore = 0.0
	df = fetch_aligned_data(all_symbols, period=args.period, interval=args.interval)
	if not df.empty and args.target in df.columns:
		available_inputs = [s for s in input_symbols if s in df.columns]
		if available_inputs:
			X = df[available_inputs]
			y = df[args.target]
			reg_result = ols_regression(X, y)
			if "error" not in reg_result:
				predictions = reg_result["predictions"]
				residuals = y.values - predictions
				residual_std = float(np.std(residuals))
				current_residual = float(y.iloc[-1]) - float(predictions[-1])
				macro_zscore = current_residual / residual_std if residual_std > 0 else 0.0
				macro_signal = "BEARISH" if macro_zscore > 2 else ("BULLISH" if macro_zscore < -2 else "NEUTRAL")

	# Convergence assessment
	signals = [tech_signal, stat_signal, macro_signal]
	bearish_count = signals.count("BEARISH")
	bullish_count = signals.count("BULLISH")

	if bearish_count == 3:
		assessment = "STRONG BEARISH (All signals agree)"
		confidence = "HIGH"
	elif bullish_count == 3:
		assessment = "STRONG BULLISH (All signals agree)"
		confidence = "HIGH"
	elif bearish_count == 2:
		assessment = "MODERATE BEARISH (2/3 signals)"
		confidence = "MEDIUM"
	elif bullish_count == 2:
		assessment = "MODERATE BULLISH (2/3 signals)"
		confidence = "MEDIUM"
	else:
		assessment = "MIXED (No convergence)"
		confidence = "LOW"

	output_json({
		"target": args.target,
		"inputs": input_symbols,
		"period": args.period,
		"signals": {
			"technical": {"type": "RSI", "value": round(current_rsi, 2), "signal": tech_signal},
			"statistical": {"type": "Z-score", "value": round(price_zscore, 4), "signal": stat_signal},
			"macro": {"type": "Residual Z-score", "value": round(macro_zscore, 4), "signal": macro_signal},
		},
		"convergence": {"assessment": assessment, "confidence": confidence},
		"date": str(data.index[-1].date()) if hasattr(data.index[-1], "date") else str(data.index[-1]),
	})


def _interpret_residual(zscore: float) -> str:
	"""Interpret residual z-score in SidneyKim0 framework."""
	abs_z = abs(zscore)
	direction = "overvalued" if zscore > 0 else "undervalued"
	if abs_z >= 3:
		return f"EXTREME {direction} ({abs_z:.1f}σ) - Historical anomaly level"
	elif abs_z >= 2:
		return f"SIGNIFICANT {direction} ({abs_z:.1f}σ) - Mean reversion signal"
	elif abs_z >= 1:
		return f"MODERATE {direction} ({abs_z:.1f}σ) - Monitoring zone"
	else:
		return f"NORMAL ({abs_z:.1f}σ) - Within fair value range"


def _classify_spread_regime(sym1: str, sym2: str, s1: pd.Series, s2: pd.Series, spread: pd.Series) -> str:
	"""Classify yield curve or spread regime."""
	# Check if both are increasing or decreasing (last 20 days trend)
	s1_trend = float(s1.iloc[-1] - s1.iloc[-20]) if len(s1) >= 20 else 0
	s2_trend = float(s2.iloc[-1] - s2.iloc[-20]) if len(s2) >= 20 else 0
	spread_trend = float(spread.iloc[-1] - spread.iloc[-20]) if len(spread) >= 20 else 0
	current_spread = float(spread.iloc[-1])

	if current_spread > 0:
		if spread_trend > 0 and s1_trend > 0:
			return "Bear Steepening (rates rising, long > short)"
		elif spread_trend > 0 and s1_trend <= 0:
			return "Bull Steepening (short rates falling faster)"
		elif spread_trend <= 0 and s1_trend > 0:
			return "Bear Flattening (long rates rising slower)"
		else:
			return "Bull Flattening (rates falling, converging)"
	else:
		return f"Inverted ({sym2} > {sym1})"


def main():
	parser = argparse.ArgumentParser(description="Macro model and fair value analysis")
	sub = parser.add_subparsers(dest="command", required=True)

	# fairvalue
	sp = sub.add_parser("fairvalue", help="Multi-factor OLS fair value model")
	sp.add_argument("target", help="Target symbol (e.g., SPY)")
	sp.add_argument("--inputs", required=True, help="Comma-separated macro factor symbols")
	sp.add_argument("--period", default="5y", help="Data period")
	sp.add_argument("--interval", default="1d", help="Data interval")
	sp.set_defaults(func=cmd_fairvalue)

	# residual
	sp = sub.add_parser("residual", help="Rolling residual Z-score with extreme detection")
	sp.add_argument("target", help="Target symbol")
	sp.add_argument("--inputs", required=True, help="Comma-separated macro factor symbols")
	sp.add_argument("--lookback", type=int, default=252, help="Rolling window for z-score")
	sp.add_argument("--threshold", type=float, default=3.0, help="Sigma threshold for extremes")
	sp.add_argument("--period", default="5y", help="Data period")
	sp.add_argument("--interval", default="1d", help="Data interval")
	sp.set_defaults(func=cmd_residual)

	# spread
	sp = sub.add_parser("spread", help="Two-symbol spread analysis")
	sp.add_argument("symbol1", help="First symbol")
	sp.add_argument("symbol2", help="Second symbol")
	sp.add_argument("--spread-type", default="difference", choices=["difference", "ratio"])
	sp.add_argument("--lookback", type=int, default=252, help="Statistics window")
	sp.add_argument("--period", default="5y", help="Data period")
	sp.add_argument("--interval", default="1d", help="Data interval")
	sp.set_defaults(func=cmd_spread)

	# convergence
	sp = sub.add_parser("convergence", help="Multi-model signal convergence")
	sp.add_argument("target", help="Target symbol")
	sp.add_argument("--symbols", required=True, help="Comma-separated symbols for macro model")
	sp.add_argument("--period", default="2y", help="Data period")
	sp.add_argument("--interval", default="1d", help="Data interval")
	sp.set_defaults(func=cmd_convergence)

	args = parser.parse_args()
	args.func(args)


if __name__ == "__main__":
	main()
