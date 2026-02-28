#!/usr/bin/env python3
"""Calculate correlation between two symbols to identify relationship strength and regime changes.

Correlation analysis measures the linear relationship between two assets' returns using both overall and
rolling correlation metrics. Detects phase changes (positive to negative correlation shifts) useful for
pairs trading, diversification analysis, and regime detection.

Args:
	symbol1 (str): First ticker symbol (e.g., "SPY", "AAPL")
	symbol2 (str): Second ticker symbol (e.g., "TLT", "MSFT")
	--period (str): Historical data period for analysis (default: "2y" = 2 years)
	--interval (str): Data interval (default: "1d" = daily)
	--rolling-window (int): Rolling correlation window (default: 45 = ~2 months)
	--force-align (flag): Force datetime alignment for FX/international pairs

Returns:
	dict: {
		"date": str,                            # Analysis date
		"symbol1": str,                         # First symbol
		"symbol2": str,                         # Second symbol
		"period": str,                          # Data period used
		"overall_correlation": float,           # Overall correlation (-1 to 1)
		"rolling_window": int,                  # Rolling window size
		"current_rolling_correlation": float,   # Current rolling correlation
		"current_regime": str,                  # Positive/Negative/Neutral
		"correlation_interpretation": str,       # Strength category
		"phase_changes": {                      # Phase change detection
			"total_detected": int,
			"recent_changes": [                 # Last 3 phase changes
				{
					"date": str,
					"change": str,              # "positive_to_negative" or "negative_to_positive"
					"from": float,
					"to": float
				}
			]
		},
		"data_points": int,                     # Number of data points
		"recent_rolling_correlation": dict      # Last 20 days of rolling correlation
	}

Example:
	>>> python correlation.py SPY TLT --rolling-window 45
	{
		"date": "2026-02-05",
		"symbol1": "SPY",
		"symbol2": "TLT",
		"period": "2y",
		"overall_correlation": -0.3542,
		"rolling_window": 45,
		"current_rolling_correlation": -0.4123,
		"current_regime": "Negative Correlation",
		"correlation_interpretation": "Moderate Negative",
		"phase_changes": {
			"total_detected": 3,
			"recent_changes": [
				{
					"date": "2025-11-15",
					"change": "positive_to_negative",
					"from": 0.25,
					"to": -0.15
				}
			]
		},
		"data_points": 504,
		"recent_rolling_correlation": {"2026-02-04": -0.3987, "2026-02-05": -0.4123}
	}

Use Cases:
	- Pairs trading: Identify cointegrated pairs with high positive correlation
	- Diversification: Find negatively correlated assets for portfolio balance
	- Regime detection: Track correlation phase changes for market state identification
	- Risk management: Monitor correlation breakdown during market stress
	- FX analysis: Use --force-align for currency pairs with timezone mismatches

Notes:
	- Rolling window affects responsiveness: shorter = more reactive, longer = more stable
	- Phase changes with threshold >0.1 avoid noise around zero correlation
	- Strong positive (>0.7) useful for pairs trading, strong negative (<-0.7) for hedging
	- Use --force-align for FX pairs or international symbols with timezone issues
	- Correlation can break down during market crises (correlations go to 1)

See Also:
	- multi_correlation.py: Correlation matrix for multiple symbols with pair rankings
	- cointegration.py: Statistical test for long-term relationship and pairs trading
	- zscore.py: Spread z-score calculation for mean-reversion signals
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pandas as pd
import yfinance as yf
from analysis.analysis_utils import calculate_rolling_correlation
from utils import output_json, safe_run


@safe_run
def cmd_correlation(args):
	"""Calculate correlation between two symbols."""
	ticker1 = yf.Ticker(args.symbol1)
	ticker2 = yf.Ticker(args.symbol2)

	data1 = ticker1.history(period=args.period, interval=args.interval)
	data2 = ticker2.history(period=args.period, interval=args.interval)

	if data1.empty or data2.empty:
		output_json({"error": "No data for one or both symbols"})
		return

	# Align dates
	prices1 = data1["Close"]
	prices2 = data2["Close"]

	# Calculate returns
	returns1 = prices1.pct_change().dropna()
	returns2 = prices2.pct_change().dropna()

	# Align by index
	common_idx = returns1.index.intersection(returns2.index)
	returns1 = returns1.loc[common_idx]
	returns2 = returns2.loc[common_idx]

	if len(returns1) < args.rolling_window:
		output_json({"error": f"Not enough data for rolling window of {args.rolling_window}"})
		return

	# Overall correlation
	overall_corr = returns1.corr(returns2)

	# Rolling correlation
	rolling_corr = calculate_rolling_correlation(returns1, returns2, args.rolling_window)
	current_rolling = rolling_corr.iloc[-1]

	# Phase change detection (positive → negative or vice versa)
	rolling_clean = rolling_corr.dropna()
	phase_changes = []
	if len(rolling_clean) > 1:
		for i in range(1, len(rolling_clean)):
			prev_val = rolling_clean.iloc[i - 1]
			curr_val = rolling_clean.iloc[i]
			# Detect sign change with threshold (avoid noise around zero)
			if prev_val > 0.1 and curr_val < -0.1:
				phase_changes.append(
					{
						"date": str(rolling_clean.index[i].date()),
						"change": "positive_to_negative",
						"from": round(float(prev_val), 4),
						"to": round(float(curr_val), 4),
					}
				)
			elif prev_val < -0.1 and curr_val > 0.1:
				phase_changes.append(
					{
						"date": str(rolling_clean.index[i].date()),
						"change": "negative_to_positive",
						"from": round(float(prev_val), 4),
						"to": round(float(curr_val), 4),
					}
				)

	# Get recent phase changes (last 3)
	recent_phase_changes = phase_changes[-3:] if len(phase_changes) > 0 else []

	# Current regime
	if current_rolling > 0.3:
		current_regime = "Positive Correlation"
	elif current_rolling < -0.3:
		current_regime = "Negative Correlation"
	else:
		current_regime = "Neutral / Decoupled"

	# Get recent rolling correlations
	recent_rolling = {str(idx.date()): round(float(v), 4) for idx, v in rolling_corr.tail(20).items() if not pd.isna(v)}

	result = {
		"date": str(returns1.index[-1].date()),
		"symbol1": args.symbol1,
		"symbol2": args.symbol2,
		"period": args.period,
		"overall_correlation": round(float(overall_corr), 4),
		"rolling_window": args.rolling_window,
		"current_rolling_correlation": round(float(current_rolling), 4) if not pd.isna(current_rolling) else None,
		"current_regime": current_regime,
		"correlation_interpretation": "Strong Positive"
		if overall_corr > 0.7
		else "Moderate Positive"
		if overall_corr > 0.3
		else "Weak"
		if abs(overall_corr) <= 0.3
		else "Moderate Negative"
		if overall_corr > -0.7
		else "Strong Negative",
		"phase_changes": {"total_detected": len(phase_changes), "recent_changes": recent_phase_changes},
		"data_points": len(returns1),
		"recent_rolling_correlation": recent_rolling,
	}
	output_json(result)


@safe_run
def cmd_correlation_fx(args):
	"""Calculate correlation between FX pairs with manual datetime alignment.

	FX data often has timezone mismatches or different trading hours, causing
	intersection to fail. This command forces alignment by normalizing datetime
	indices to date-only for matching.
	"""
	ticker1 = yf.Ticker(args.symbol1)
	ticker2 = yf.Ticker(args.symbol2)

	data1 = ticker1.history(period=args.period, interval=args.interval)
	data2 = ticker2.history(period=args.period, interval=args.interval)

	if data1.empty or data2.empty:
		output_json({"error": "No data for one or both symbols"})
		return

	# Get close prices
	prices1 = data1["Close"]
	prices2 = data2["Close"]

	# Force datetime alignment: Convert timezone-aware to timezone-naive dates
	if prices1.index.tz is not None:
		prices1.index = prices1.index.tz_localize(None)
	if prices2.index.tz is not None:
		prices2.index = prices2.index.tz_localize(None)

	# Normalize to date only (removes time component)
	prices1.index = prices1.index.normalize()
	prices2.index = prices2.index.normalize()

	# Remove duplicate dates (keep first occurrence)
	prices1 = prices1[~prices1.index.duplicated(keep="first")]
	prices2 = prices2[~prices2.index.duplicated(keep="first")]

	# Calculate returns
	returns1 = prices1.pct_change().dropna()
	returns2 = prices2.pct_change().dropna()

	# Manual alignment by date intersection
	common_dates = returns1.index.intersection(returns2.index)

	if len(common_dates) == 0:
		output_json({"error": "No overlapping dates after alignment"})
		return

	returns1_aligned = returns1.loc[common_dates]
	returns2_aligned = returns2.loc[common_dates]

	if len(returns1_aligned) < args.rolling_window:
		output_json({"error": f"Not enough data for rolling window of {args.rolling_window}"})
		return

	# Overall correlation
	overall_corr = returns1_aligned.corr(returns2_aligned)

	# Rolling correlation
	rolling_corr = calculate_rolling_correlation(returns1_aligned, returns2_aligned, args.rolling_window)
	current_rolling = rolling_corr.iloc[-1]

	# Get recent rolling correlations
	recent_rolling = {str(idx.date()): round(float(v), 4) for idx, v in rolling_corr.tail(20).items() if not pd.isna(v)}

	result = {
		"date": str(returns1_aligned.index[-1].date()),
		"symbol1": args.symbol1,
		"symbol2": args.symbol2,
		"period": args.period,
		"alignment_method": "force_align (timezone-naive date matching)",
		"overall_correlation": round(float(overall_corr), 4),
		"rolling_window": args.rolling_window,
		"current_rolling_correlation": round(float(current_rolling), 4) if not pd.isna(current_rolling) else None,
		"correlation_interpretation": "Strong Positive"
		if overall_corr > 0.7
		else "Moderate Positive"
		if overall_corr > 0.3
		else "Weak"
		if abs(overall_corr) <= 0.3
		else "Moderate Negative"
		if overall_corr > -0.7
		else "Strong Negative",
		"data_points": len(returns1_aligned),
		"recent_rolling_correlation": recent_rolling,
	}
	output_json(result)


if __name__ == "__main__":
	import argparse

	parser = argparse.ArgumentParser(description="Calculate correlation between symbols")
	parser.add_argument("symbol1")
	parser.add_argument("symbol2")
	parser.add_argument("--period", default="2y", help="Data period")
	parser.add_argument("--interval", default="1d", help="Data interval")
	parser.add_argument("--rolling-window", type=int, default=45, help="Rolling correlation window (default: 45)")
	parser.add_argument(
		"--force-align",
		action="store_true",
		help="Force datetime alignment for FX/international pairs (timezone-naive date matching)",
	)
	args = parser.parse_args()

	# Route to appropriate function based on --force-align flag
	if args.force_align:
		cmd_correlation_fx(args)
	else:
		cmd_correlation(args)
