#!/usr/bin/env python3
"""Geometric Brownian Motion (GBM) Fair Value Model for asset price valuation.

Models asset prices as a stochastic process to estimate fair value based on historical drift
and volatility parameters. GBM assumes log-normal distribution of prices and provides statistical
confidence intervals for valuation assessment.

Args:
	symbol (str): Ticker symbol to analyze (e.g., "SPY", "AAPL", "^GSPC")
	--period (str): Historical data period for parameter estimation (default: "5y")
		- Longer periods (5y, 10y) provide more stable parameter estimates
		- Shorter periods (1y, 2y) reflect recent market regime
	--forecast-days (int): Forward-looking horizon in days (default: 252 = 1 year)
		- Common values: 30 (1 month), 90 (1 quarter), 252 (1 year)

Returns:
	dict: {
		"symbol": str,
		"date": str,
		"current_price": float,
		"fair_value": float,             # Expected value under GBM: s0 * exp(μ*t)
		"deviation_pct": float,          # (Current - Fair) / Fair * 100
		"valuation": str,                # Significantly Overvalued/Moderately Overvalued/Fair Valued/etc.
		"confidence_interval_68": {
			"lower": float,              # s0 * exp((μ - σ)*t)
			"upper": float,              # s0 * exp((μ + σ)*t)
			"range_pct": float           # Width of confidence interval
		},
		"gbm_parameters": {
			"drift_annual": float,       # Annualized mean return (μ)
			"volatility_annual": float,  # Annualized standard deviation (σ)
			"risk_adjusted_return": float # Sharpe-like ratio: μ/σ
		},
		"forecast_horizon": {
			"days": int,
			"years": float
		},
		"historical_period": {
			"period": str,
			"data_points": int
		},
		"interpretation": str            # Human-readable valuation summary
	}

Example:
	>>> python gbm.py SPY --period 5y --forecast-days 252
	{
		"symbol": "SPY",
		"current_price": 475.50,
		"fair_value": 480.25,
		"deviation_pct": -0.99,
		"valuation": "Fair Valued",
		"confidence_interval_68": {
			"lower": 420.30,
			"upper": 548.75,
			"range_pct": 27.02
		},
		"gbm_parameters": {
			"drift_annual": 0.0850,
			"volatility_annual": 0.1850,
			"risk_adjusted_return": 0.4595
		},
		"forecast_horizon": {"days": 252, "years": 1.0},
		"interpretation": "Fair Valued: Current price $475.50 vs Fair value $480.25 (-0.99%)"
	}

Use Cases:
	- Fair value estimation based on stochastic price dynamics
	- Valuation assessment using statistical confidence intervals
	- Risk-adjusted return analysis via drift/volatility ratio
	- Parameter sensitivity testing across different time horizons
	- Probabilistic price range forecasting for options pricing

Notes:
	- Assumes log-normal distribution of prices (may not hold during crises)
	- Drift (μ) and volatility (σ) estimated from historical returns
	- Fair value represents expected value, not most likely outcome
	- Confidence intervals assume constant drift and volatility (rare in practice)
	- Model does not account for dividends (use total return index for accuracy)
	- Parameter stability: shorter estimation periods may produce unstable parameters
	- Black swan events: GBM underestimates tail risk (fat tails not modeled)
	- Mean reversion not captured: GBM assumes constant drift
	- Forecast accuracy degrades with longer time horizons

See Also:
	- macro.py fairvalue: Alternative regression-based fair value model
	- macro.py residual: Residual analysis for regression models
	- zscore.py: Z-score based statistical valuation
	- percentile.py: Distribution-free valuation approach
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import numpy as np
import yfinance as yf
from utils import output_json, safe_run


@safe_run
def cmd_gbm_fairvalue(args):
	"""Calculate fair value using Geometric Brownian Motion model.

	GBM models asset prices as a stochastic process:
	dS = μ*S*dt + σ*S*dW

	Where:
	- μ (drift): Expected return rate
	- σ (volatility): Standard deviation of returns
	- dW: Wiener process (random walk)

	Fair value is calculated as:
	S_fair = s0 * exp(μ*t)

	With confidence intervals using volatility:
	Upper = s0 * exp((μ + σ)*t)
	Lower = s0 * exp((μ - σ)*t)

	Args:
		symbol: Ticker symbol (e.g., SPY, AAPL)
		period: Historical data period for parameter estimation (default: 5y)
		forecast_days: Forward-looking horizon in days (default: 252, 1 year)
	"""
	ticker = yf.Ticker(args.symbol)
	data = ticker.history(period=args.period, interval="1d")

	if data.empty or len(data) < 100:
		output_json({"error": f"Insufficient data for {args.symbol} (minimum 100 days required)"})
		return

	# Calculate log returns
	prices = data["Close"]
	returns = np.log(prices / prices.shift(1)).dropna()

	# Estimate GBM parameters
	# Drift (μ): annualized mean return
	# Volatility (σ): annualized standard deviation of returns
	mu = returns.mean() * 252  # Annualized drift
	sigma = returns.std() * np.sqrt(252)  # Annualized volatility

	# Current price
	s0 = float(prices.iloc[-1])

	# Time horizon (in years)
	t = args.forecast_days / 252

	# Fair value: expected value under GBM
	# E[S_t] = s0 * exp(μ*t)
	fair_value = s0 * np.exp(mu * t)

	# Confidence intervals (1 standard deviation)
	# Using drift-diffusion: μ ± σ
	upper_bound = s0 * np.exp((mu + sigma) * t)
	lower_bound = s0 * np.exp((mu - sigma) * t)

	# Deviation from fair value
	# Positive: Current > Fair (Overvalued)
	# Negative: Current < Fair (Undervalued)
	deviation = ((s0 - fair_value) / fair_value) * 100

	# Interpretation
	if deviation > 10:
		valuation = "Significantly Overvalued"
	elif deviation > 5:
		valuation = "Moderately Overvalued"
	elif deviation < -10:
		valuation = "Significantly Undervalued"
	elif deviation < -5:
		valuation = "Moderately Undervalued"
	else:
		valuation = "Fair Valued"

	# Risk-adjusted metrics
	# Sharpe-like metric (drift/volatility)
	risk_adjusted_return = mu / sigma if sigma > 0 else 0

	result = {
		"symbol": args.symbol,
		"date": str(data.index[-1].date()),
		"current_price": round(s0, 2),
		"fair_value": round(fair_value, 2),
		"deviation_pct": round(deviation, 2),
		"valuation": valuation,
		"confidence_interval_68": {
			"lower": round(lower_bound, 2),
			"upper": round(upper_bound, 2),
			"range_pct": round(((upper_bound - lower_bound) / s0) * 100, 2),  # Width of CI
		},
		"gbm_parameters": {
			"drift_annual": round(mu, 4),
			"volatility_annual": round(sigma, 4),
			"risk_adjusted_return": round(risk_adjusted_return, 4),
		},
		"forecast_horizon": {
			"days": args.forecast_days,
			"years": round(t, 2),
		},
		"historical_period": {
			"period": args.period,
			"data_points": len(returns),
		},
		"interpretation": f"{valuation}: Current price ${s0:.2f} vs Fair value ${fair_value:.2f} ({deviation:+.2f}%)",
	}

	output_json(result)


if __name__ == "__main__":
	parser = argparse.ArgumentParser(description="GBM Fair Value Model - Geometric Brownian Motion valuation")
	parser.add_argument("symbol", help="Ticker symbol (e.g., SPY, QQQ, AAPL)")
	parser.add_argument(
		"--period",
		default="5y",
		help="Historical period for parameter estimation (default: 5y)",
	)
	parser.add_argument(
		"--forecast-days",
		type=int,
		default=252,
		help="Forward-looking horizon in days (default: 252, 1 year)",
	)

	args = parser.parse_args()
	cmd_gbm_fairvalue(args)
