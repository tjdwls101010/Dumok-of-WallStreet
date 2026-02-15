#!/usr/bin/env python3
"""Multi-Asset Extreme Detection - Identify simultaneous extreme z-scores across multiple assets.

Extreme events occur when multiple assets reach statistically unusual levels (|z-score| > threshold)
simultaneously, indicating systemic market stress, regime shifts, or broad-based opportunities.
Useful for detecting market-wide dislocations and risk-on/risk-off transitions.

Args:
	symbols (str): Comma-separated ticker symbols (e.g., "SPY,QQQ,TLT,GLD")
	--threshold (float): Z-score threshold for extreme detection (default: 2.0)
	--lookback (int): Lookback period for mean/std calculation (default: 252 days)
	--period (str): Historical data period (default: "5y" = 5 years)
	--interval (str): Data interval (default: "1d" = daily)
	--use-returns (flag): Calculate z-score for returns instead of price

Returns:
	dict: {
		"date": str,                    # Analysis date
		"threshold": float,             # Z-score threshold used
		"lookback_days": int,           # Lookback period for z-score
		"total_extremes": int,          # Number of assets at extreme levels
		"total_assets": int,            # Total assets analyzed (excluding errors)
		"extreme_percentage": float,    # Percentage of assets at extremes
		"interpretation": str,          # Event classification (systemic/partial/single/none)
		"extreme_assets": [             # Assets currently at extremes
			{
				"symbol": str,
				"z_score": float,
				"current_value": float,
				"mean": float,
				"std": float,
				"direction": str,       # "overbought" | "oversold" | "neutral"
				"analysis_type": str,   # "price" or "returns"
				"is_extreme": bool
			},
			...
		],
		"all_assets": [                 # All assets with z-scores
			{
				"symbol": str,
				"z_score": float,
				"current_value": float,
				"mean": float,
				"std": float,
				"direction": str,
				"analysis_type": str,
				"is_extreme": bool
			},
			...
		]
	}

Example:
	>>> python multi_extremes.py "SPY,QQQ,TLT,GLD" --threshold 2.0 --lookback 252
	{
		"date": "2026-02-05",
		"threshold": 2.0,
		"lookback_days": 252,
		"total_extremes": 2,
		"total_assets": 4,
		"extreme_percentage": 50.0,
		"interpretation": "Partial stress: 2/4 assets at extremes",
		"extreme_assets": [
			{
				"symbol": "SPY",
				"z_score": -2.15,
				"current_value": 485.23,
				"mean": 512.45,
				"std": 12.67,
				"direction": "oversold",
				"analysis_type": "price",
				"is_extreme": true
			},
			{
				"symbol": "TLT",
				"z_score": 2.34,
				"current_value": 96.78,
				"mean": 89.12,
				"std": 3.27,
				"direction": "overbought",
				"analysis_type": "price",
				"is_extreme": true
			}
		],
		"all_assets": [...]
	}

Use Cases:
	- Systemic risk detection: Identify market-wide stress when 50%+ assets at extremes
	- Flight-to-quality events: Detect risk-off moves (SPY down, TLT/GLD up simultaneously)
	- Regime shift detection: Monitor transition from low to high volatility regimes
	- Portfolio rebalancing: Identify opportunistic entry points during broad selloffs
	- Correlation breakdown: Detect when normally uncorrelated assets move together
	- Multi-asset mean reversion: Find opportunities when multiple assets deviate from mean

Notes:
	- Threshold 2.0σ captures ~5% of observations (moderately rare events)
	- Threshold 3.0σ captures ~0.3% of observations (very rare tail events)
	- Systemic stress defined as ≥50% of assets at extremes simultaneously
	- Use --use-returns for volatility-normalized analysis across different asset classes
	- Flight-to-quality pattern: SPY/QQQ oversold while TLT/GLD overbought
	- Risk-on pattern: SPY/QQQ overbought while TLT oversold
	- Lookback period affects sensitivity to extremes (shorter = more extremes detected)

See Also:
	- extremes.py: Single-asset extreme event detection with historical event list
	- zscore.py: Real-time z-score calculation for current positioning
	- correlation.py: Correlation analysis to understand asset relationships during stress
	- multi_correlation.py: Multi-asset correlation matrix for relationship mapping
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import yfinance as yf
from analysis.analysis_utils import calculate_z_score
from utils import output_json, safe_run


@safe_run
def cmd_multi_extremes(args):
	"""Detect simultaneous extreme z-scores across multiple assets."""
	symbols = [s.strip() for s in args.symbols.split(",")]

	if len(symbols) < 2:
		output_json({"error": "At least 2 symbols required for multi-asset analysis"})
		return

	extreme_assets = []
	all_assets = []

	for symbol in symbols:
		try:
			ticker = yf.Ticker(symbol)
			data = ticker.history(period=args.period, interval=args.interval)

			if data.empty:
				all_assets.append(
					{
						"symbol": symbol,
						"error": "No data available",
						"is_extreme": False,
					}
				)
				continue

			prices = data["Close"]

			if args.use_returns:
				series = prices.pct_change().dropna()
				analysis_type = "returns"
			else:
				series = prices
				analysis_type = "price"

			z_score, mean, std = calculate_z_score(series, args.lookback)
			current_value = float(series.iloc[-1])
			abs_z = abs(z_score)

			# Determine direction
			if z_score > 0:
				direction = "overbought"
			elif z_score < 0:
				direction = "oversold"
			else:
				direction = "neutral"

			asset_data = {
				"symbol": symbol,
				"z_score": round(float(z_score), 4),
				"current_value": round(current_value, 6 if args.use_returns else 2),
				"mean": round(float(mean), 6 if args.use_returns else 2),
				"std": round(float(std), 6 if args.use_returns else 2),
				"direction": direction,
				"analysis_type": analysis_type,
				"is_extreme": abs_z >= args.threshold,
			}

			all_assets.append(asset_data)

			if abs_z >= args.threshold:
				extreme_assets.append(asset_data)

		except Exception as e:
			all_assets.append({"symbol": symbol, "error": str(e), "is_extreme": False})

	# Interpretation
	total_extremes = len(extreme_assets)
	total_assets = len([a for a in all_assets if "error" not in a])

	if total_extremes == 0:
		interpretation = "No extreme conditions detected"
	elif total_extremes == 1:
		interpretation = f"Single extreme: {extreme_assets[0]['symbol']} ({extreme_assets[0]['direction']})"
	elif total_extremes >= total_assets * 0.5:
		interpretation = f"Systemic stress: {total_extremes}/{total_assets} assets at extremes"
	else:
		interpretation = f"Partial stress: {total_extremes}/{total_assets} assets at extremes"

	result = {
		"date": str(data.index[-1].date()) if not data.empty else None,
		"threshold": args.threshold,
		"lookback_days": args.lookback,
		"total_extremes": total_extremes,
		"total_assets": total_assets,
		"extreme_percentage": round((total_extremes / total_assets * 100) if total_assets > 0 else 0, 2),
		"interpretation": interpretation,
		"extreme_assets": extreme_assets,
		"all_assets": all_assets,
	}

	output_json(result)


if __name__ == "__main__":
	parser = argparse.ArgumentParser(description="Multi-Asset Extreme Detection - Simultaneous extreme z-scores")
	parser.add_argument("symbols", help="Comma-separated ticker symbols (e.g., SPY,GLD,TLT,DXY)")
	parser.add_argument(
		"--threshold",
		type=float,
		default=2.0,
		help="Z-score threshold for extreme detection (default: 2.0)",
	)
	parser.add_argument(
		"--lookback",
		type=int,
		default=252,
		help="Lookback period for mean/std calculation (default: 252 days)",
	)
	parser.add_argument("--period", default="5y", help="Historical data period (default: 5y)")
	parser.add_argument("--interval", default="1d", help="Data interval (default: 1d)")
	parser.add_argument(
		"--use-returns",
		action="store_true",
		help="Calculate z-score for returns instead of price",
	)

	args = parser.parse_args()
	cmd_multi_extremes(args)
