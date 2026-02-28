#!/usr/bin/env python3
"""Calculate distribution statistics for returns to analyze risk, reward, and tail characteristics.

Distribution analysis provides comprehensive statistics on return distributions including moments (mean,
standard deviation, skewness, kurtosis), annualized metrics (return, volatility, Sharpe ratio), and
percentile thresholds for VaR-style risk assessment.

Args:
	symbol (str): Stock ticker symbol (e.g., "AAPL", "SPY", "^GSPC")
	--period (str): Historical data period for analysis (default: "5y" = 5 years)
	--interval (str): Data interval (default: "1d" = daily)
	--lookback (int): Lookback period for analysis (default: 252 = 1 trading year)

Returns:
	dict: {
		"symbol": str,                  # Ticker symbol
		"lookback_days": int,           # Lookback period used
		"data_points": int,             # Number of return observations
		"date": str,                    # Latest data date
		"daily_returns": {              # Daily return statistics (in %)
			"mean": float,              # Average daily return
			"std": float,               # Daily volatility
			"min": float,               # Worst daily return
			"max": float,               # Best daily return
			"skewness": float,          # Return asymmetry (-/+ for left/right skew)
			"kurtosis": float           # Tail thickness (>3 = fat tails)
		},
		"annualized": {                 # Annualized metrics (in %)
			"return": float,            # Annualized return (mean * 252)
			"volatility": float,        # Annualized volatility (std * sqrt(252))
			"sharpe_ratio": float       # Risk-adjusted return (return/volatility)
		},
		"percentiles_daily_return_pct": {  # Return distribution percentiles
			"p5": float,                # 5th percentile (VaR 95% confidence)
			"p10": float,               # 10th percentile
			"p25": float,               # 25th percentile (Q1)
			"p50": float,               # 50th percentile (median)
			"p75": float,               # 75th percentile (Q3)
			"p90": float,               # 90th percentile
			"p95": float                # 95th percentile (CVaR threshold)
		},
		"distribution_shape": str       # Shape classification
	}

Example:
	>>> python distribution.py SPY --lookback 252
	{
		"symbol": "SPY",
		"lookback_days": 252,
		"data_points": 252,
		"date": "2026-02-05",
		"daily_returns": {
			"mean": 0.0512,
			"std": 1.0234,
			"min": -3.87,
			"max": 4.12,
			"skewness": -0.1523,
			"kurtosis": 4.2341
		},
		"annualized": {
			"return": 12.90,
			"volatility": 16.25,
			"sharpe_ratio": 0.79
		},
		"percentiles_daily_return_pct": {
			"p5": -1.58,
			"p10": -1.12,
			"p25": -0.52,
			"p50": 0.06,
			"p75": 0.68,
			"p90": 1.35,
			"p95": 1.82
		},
		"distribution_shape": "Fat tails"
	}

Use Cases:
	- Risk assessment: Use p5 percentile as Value-at-Risk (VaR) estimate
	- Volatility analysis: Track daily and annualized volatility for risk budgeting
	- Tail risk measurement: High kurtosis (>3) indicates fat tails and extreme events
	- Skewness detection: Negative skewness signals more frequent large losses
	- Sharpe ratio optimization: Compare risk-adjusted returns across assets
	- Performance attribution: Decompose returns into mean and volatility components

Notes:
	- Assumes 252 trading days per year for annualization
	- Skewness: Negative = left tail (more losses), Positive = right tail (more gains)
	- Kurtosis: >3 = fat tails (more extreme events), <3 = thin tails (fewer extremes)
	- Sharpe ratio: >1 is good, >2 is excellent (risk-adjusted performance)
	- p5 percentile approximates 95% VaR (expected worst 5% daily loss)
	- Fat tails invalidate normal distribution assumptions used in z-score analysis
	- Lookback period should match investment horizon (252 for 1-year, 63 for quarterly)

See Also:
	- zscore.py: Assumes normal distribution (may fail for fat-tailed returns)
	- percentile.py: Rank-based positioning robust to distribution shape
	- extremes.py: Identify extreme tail events exceeding threshold
	- correlation.py: Measure co-movement with other assets
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import numpy as np
import yfinance as yf
from utils import output_json, safe_run


@safe_run
def cmd_distribution(args):
	"""Calculate distribution statistics for returns."""
	ticker = yf.Ticker(args.symbol)
	data = ticker.history(period=args.period, interval=args.interval)
	if data.empty:
		output_json({"error": f"No data for {args.symbol}"})
		return

	prices = data["Close"]
	returns = prices.pct_change().dropna()

	if len(returns) < args.lookback:
		lookback = len(returns)
	else:
		lookback = args.lookback

	window_returns = returns.tail(lookback)

	# Calculate statistics
	mean = window_returns.mean()
	std = window_returns.std()
	skew = window_returns.skew()
	kurt = window_returns.kurtosis()
	min_ret = window_returns.min()
	max_ret = window_returns.max()

	# Calculate annualized metrics (assuming daily data)
	trading_days = 252
	annualized_return = mean * trading_days
	annualized_vol = std * np.sqrt(trading_days)
	sharpe = annualized_return / annualized_vol if annualized_vol > 0 else 0

	# Percentile thresholds
	percentiles = {
		"p5": round(float(window_returns.quantile(0.05)) * 100, 2),
		"p10": round(float(window_returns.quantile(0.10)) * 100, 2),
		"p25": round(float(window_returns.quantile(0.25)) * 100, 2),
		"p50": round(float(window_returns.quantile(0.50)) * 100, 2),
		"p75": round(float(window_returns.quantile(0.75)) * 100, 2),
		"p90": round(float(window_returns.quantile(0.90)) * 100, 2),
		"p95": round(float(window_returns.quantile(0.95)) * 100, 2),
	}

	result = {
		"symbol": args.symbol,
		"lookback_days": lookback,
		"data_points": len(window_returns),
		"date": str(data.index[-1].date()),
		"daily_returns": {
			"mean": round(float(mean) * 100, 4),  # in percentage
			"std": round(float(std) * 100, 4),
			"min": round(float(min_ret) * 100, 2),
			"max": round(float(max_ret) * 100, 2),
			"skewness": round(float(skew), 4),
			"kurtosis": round(float(kurt), 4),
		},
		"annualized": {
			"return": round(float(annualized_return) * 100, 2),  # in percentage
			"volatility": round(float(annualized_vol) * 100, 2),
			"sharpe_ratio": round(float(sharpe), 2),
		},
		"percentiles_daily_return_pct": percentiles,
		"distribution_shape": "Fat tails" if kurt > 3 else "Normal-like" if abs(kurt) <= 1 else "Thin tails",
	}
	output_json(result)


if __name__ == "__main__":
	import argparse

	parser = argparse.ArgumentParser(description="Calculate distribution statistics for returns")
	parser.add_argument("symbol")
	parser.add_argument("--period", default="5y", help="Data period")
	parser.add_argument("--interval", default="1d", help="Data interval")
	parser.add_argument("--lookback", type=int, default=252, help="Lookback period")
	args = parser.parse_args()
	cmd_distribution(args)
