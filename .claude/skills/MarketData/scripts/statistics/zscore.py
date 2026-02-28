#!/usr/bin/env python3
"""Calculate z-score for stock price or returns to identify statistical overbought/oversold levels.

Z-score measures how many standard deviations the current price is from its historical mean.
Higher absolute z-scores indicate more extreme deviations from average.

Args:
	symbol (str): Stock ticker symbol (e.g., "AAPL", "SPY", "^GSPC")
	--period (str): Historical data period (default: "5y" = 5 years)
	--interval (str): Data interval (default: "1d" = daily)
	--lookback (int): Number of periods for mean/std calculation (default: 252 = 1 trading year)
	--use-returns (flag): Calculate z-score for returns instead of price levels

Returns:
	dict: {
		"symbol": str,                    # Ticker symbol
		"analysis_type": str,             # "price" or "returns"
		"current_value": float,           # Current price or return
		"mean": float,                    # Historical mean
		"std": float,                     # Historical standard deviation
		"z_score": float,                 # Z-score value
		"sigma_level": str,               # Interpretation (±2σ, ±3σ, EXTREME)
		"lookback_days": int,             # Lookback period used
		"date": str,                      # Analysis date
		"probability_above": float | None # Probability price exceeds current (if z > 0)
		"probability_below": float | None # Probability price below current (if z < 0)
	}

Example:
	>>> python zscore.py AAPL --lookback 252
	{
		"symbol": "AAPL",
		"z_score": 0.67,
		"sigma_level": "0.7σ (above mean) - Normal",
		"probability_above": 25.14
	}

Use Cases:
	- Identify mean-reversion opportunities when z-score exceeds ±2σ
	- Detect extreme market conditions (z-score > 3σ indicates 99.7th percentile)
	- Statistical arbitrage pairs trading (compare z-scores of correlated assets)
	- Risk management (extreme z-scores signal elevated volatility)

Notes:
	- Z-score assumes normal distribution (may not hold during crises)
	- Lookback period affects sensitivity (shorter = more reactive, longer = smoother)
	- Use returns-based z-score for non-stationary price series
	- Probability calculations use cumulative normal distribution

See Also:
	- percentile.py: Alternative rank-based metric without distribution assumption
	- extremes.py: Detect extreme z-score events in historical data
	- correlation.py: Analyze z-score relationships between assets
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import yfinance as yf
from analysis.analysis_utils import calculate_z_score
from utils import output_json, safe_run


@safe_run
def cmd_zscore(args):
	"""Calculate z-score for a symbol's price or returns."""
	ticker = yf.Ticker(args.symbol)
	data = ticker.history(period=args.period, interval=args.interval)
	if data.empty:
		output_json({"error": f"No data for {args.symbol}"})
		return

	prices = data["Close"]

	if args.use_returns:
		# Calculate returns
		series = prices.pct_change().dropna()
		series_name = "returns"
	else:
		series = prices
		series_name = "price"

	z_score, mean, std = calculate_z_score(series, args.lookback)
	current_value = series.iloc[-1]

	# Determine sigma level
	abs_z = abs(z_score)
	if abs_z >= 4:
		sigma_level = f"{z_score:.1f}σ ({'above' if z_score > 0 else 'below'} mean) - EXTREME"
	elif abs_z >= 3:
		sigma_level = f"{z_score:.1f}σ ({'above' if z_score > 0 else 'below'} mean) - Very High"
	elif abs_z >= 2:
		sigma_level = f"{z_score:.1f}σ ({'above' if z_score > 0 else 'below'} mean) - High"
	else:
		sigma_level = f"{z_score:.1f}σ ({'above' if z_score > 0 else 'below'} mean) - Normal"

	result = {
		"symbol": args.symbol,
		"analysis_type": series_name,
		"current_value": round(float(current_value), 6 if args.use_returns else 2),
		"mean": round(float(mean), 6 if args.use_returns else 2),
		"std": round(float(std), 6 if args.use_returns else 2),
		"z_score": round(float(z_score), 2),
		"sigma_level": sigma_level,
		"lookback_days": args.lookback,
		"date": str(data.index[-1].date()),
		"probability_above": round(float((1 - 0.5 * (1 + math.erf(z_score / math.sqrt(2)))) * 100), 4)
		if z_score > 0
		else None,
		"probability_below": round(float(0.5 * (1 + math.erf(z_score / math.sqrt(2))) * 100), 4)
		if z_score < 0
		else None,
	}
	output_json(result)


if __name__ == "__main__":
	import argparse

	parser = argparse.ArgumentParser(description="Calculate z-score for price or returns")
	parser.add_argument("symbol")
	parser.add_argument("--period", default="5y", help="Data period")
	parser.add_argument("--interval", default="1d", help="Data interval")
	parser.add_argument("--lookback", type=int, default=252, help="Lookback period for mean/std calculation")
	parser.add_argument("--use-returns", action="store_true", help="Calculate z-score for returns instead of price")
	args = parser.parse_args()
	cmd_zscore(args)
