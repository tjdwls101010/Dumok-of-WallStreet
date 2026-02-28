#!/usr/bin/env python3
"""Calculate correlation matrix for multiple symbols to identify relationship patterns and pair rankings.

Multi-symbol correlation analysis generates a full correlation matrix showing relationships between all
pairs of assets. Automatically ranks pairs by correlation strength for diversification or pairs trading.

Args:
	symbols (list): Space-separated ticker symbols (e.g., "SPY QQQ TLT GLD")
	--period (str): Historical data period for analysis (default: "2y" = 2 years)
	--interval (str): Data interval (default: "1d" = daily)

Returns:
	dict: {
		"date": str,                       # Analysis date
		"symbols": list,                   # List of symbols analyzed
		"period": str,                     # Data period used
		"data_points": int,                # Number of overlapping data points
		"correlation_matrix": {            # Full correlation matrix
			"SYMBOL1": {
				"SYMBOL1": float,          # Self-correlation (always 1.0)
				"SYMBOL2": float,          # Pairwise correlation
				...
			},
			...
		},
		"correlation_pairs_sorted": [      # All pairs sorted by correlation strength
			{
				"pair": str,               # "SYMBOL1-SYMBOL2"
				"correlation": float       # Correlation value
			},
			...
		],
		"strongest_positive": {            # Highest positive correlation pair
			"pair": str,
			"correlation": float
		},
		"strongest_negative": {            # Lowest (most negative) correlation pair
			"pair": str,
			"correlation": float
		}
	}

Example:
	>>> python multi_correlation.py SPY QQQ TLT GLD --period 2y
	{
		"date": "2026-02-05",
		"symbols": ["SPY", "QQQ", "TLT", "GLD"],
		"period": "2y",
		"data_points": 504,
		"correlation_matrix": {
			"SPY": {"SPY": 1.0, "QQQ": 0.89, "TLT": -0.35, "GLD": 0.12},
			"QQQ": {"SPY": 0.89, "QQQ": 1.0, "TLT": -0.28, "GLD": 0.08},
			"TLT": {"SPY": -0.35, "QQQ": -0.28, "TLT": 1.0, "GLD": 0.25},
			"GLD": {"SPY": 0.12, "QQQ": 0.08, "TLT": 0.25, "GLD": 1.0}
		},
		"correlation_pairs_sorted": [
			{"pair": "SPY-QQQ", "correlation": 0.89},
			{"pair": "SPY-TLT", "correlation": -0.35},
			...
		],
		"strongest_positive": {"pair": "SPY-QQQ", "correlation": 0.89},
		"strongest_negative": {"pair": "SPY-TLT", "correlation": -0.35}
	}

Use Cases:
	- Portfolio diversification: Identify negatively correlated assets for risk reduction
	- Sector rotation: Find correlated sectors for momentum strategies
	- Pairs trading: Discover highly correlated pairs (>0.7) for mean-reversion trades
	- Asset allocation: Build uncorrelated portfolios using weakly correlated assets
	- Risk management: Monitor correlation clustering during market stress

Notes:
	- Requires at least 30 overlapping data points for meaningful correlations
	- Self-correlation always equals 1.0 and is excluded from pair rankings
	- Correlation matrix is symmetric (corr(A,B) = corr(B,A))
	- Strong positive correlation (>0.7) useful for pairs trading
	- Strong negative correlation (<-0.7) useful for hedging and diversification
	- Market stress can cause all correlations to converge toward 1.0

See Also:
	- correlation.py: Detailed two-symbol correlation with rolling metrics and phase changes
	- cointegration.py: Test for long-term equilibrium relationship between pairs
	- zscore.py: Calculate spread z-scores for cointegrated pairs
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pandas as pd
import yfinance as yf
from utils import output_json, safe_run


@safe_run
def cmd_multi_correlation(args):
	"""Calculate correlation matrix for multiple symbols."""
	symbols = args.symbols
	if len(symbols) < 2:
		output_json({"error": "Need at least 2 symbols"})
		return

	# Download all data
	all_returns = {}
	for symbol in symbols:
		ticker = yf.Ticker(symbol)
		data = ticker.history(period=args.period, interval=args.interval)
		if data.empty:
			continue
		prices = data["Close"]
		returns = prices.pct_change().dropna()
		all_returns[symbol] = returns

	if len(all_returns) < 2:
		output_json({"error": "Not enough data for correlation matrix"})
		return

	# Create DataFrame
	df = pd.DataFrame(all_returns)
	df = df.dropna()

	if len(df) < 30:
		output_json({"error": f"Not enough overlapping data points: {len(df)}"})
		return

	# Calculate correlation matrix
	corr_matrix = df.corr()

	# Convert to JSON-friendly format
	matrix = {}
	for col in corr_matrix.columns:
		matrix[col] = {str(idx): round(float(val), 4) for idx, val in corr_matrix[col].items()}

	# Find strongest and weakest correlations (excluding self-correlation)
	corr_pairs = []
	for i, sym1 in enumerate(symbols):
		for j, sym2 in enumerate(symbols):
			if i < j and sym1 in corr_matrix.columns and sym2 in corr_matrix.columns:
				corr_val = corr_matrix.loc[sym1, sym2]
				if not pd.isna(corr_val):
					corr_pairs.append({"pair": f"{sym1}-{sym2}", "correlation": round(float(corr_val), 4)})

	corr_pairs.sort(key=lambda x: abs(x["correlation"]), reverse=True)

	result = {
		"date": str(df.index[-1].date()),
		"symbols": list(all_returns.keys()),
		"period": args.period,
		"data_points": len(df),
		"correlation_matrix": matrix,
		"correlation_pairs_sorted": corr_pairs,
		"strongest_positive": max(corr_pairs, key=lambda x: x["correlation"]) if corr_pairs else None,
		"strongest_negative": min(corr_pairs, key=lambda x: x["correlation"]) if corr_pairs else None,
	}
	output_json(result)


if __name__ == "__main__":
	import argparse

	parser = argparse.ArgumentParser(description="Calculate correlation matrix for multiple symbols")
	parser.add_argument("symbols", nargs="+", help="List of symbols")
	parser.add_argument("--period", default="2y", help="Data period")
	parser.add_argument("--interval", default="1d", help="Data interval")
	args = parser.parse_args()
	cmd_multi_correlation(args)
