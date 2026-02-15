#!/usr/bin/env python3
"""Calculate trend-following indicators including SMA, EMA, and Bollinger Bands.

Moving averages smooth price data to identify trends and support/resistance levels.
Bollinger Bands measure volatility and detect price extremes relative to moving average.

Args:
	For SMA/EMA:
		symbol (str): Stock ticker symbol (e.g., "AAPL", "SPY", "TSLA")
		--period (str): Historical data period (default: "1y" = 1 year)
		--interval (str): Data interval (default: "1d" = daily)
		--periods (str): Comma-separated MA periods (default: "20,50,200" for SMA; "9,21,50" for EMA)

	For Bollinger Bands:
		symbol (str): Stock ticker symbol (e.g., "AAPL", "SPY")
		--period (str): Historical data period (default: "1y")
		--interval (str): Data interval (default: "1d")
		--bb-period (int): Bollinger Band calculation period (default: 20)
		--std-dev (float): Standard deviation multiplier (default: 2.0)

Returns:
	For SMA:
		dict: {
			"symbol": str,
			"current_price": float,
			"sma": {
				"SMA20": {
					"value": float,          # 20-day simple moving average
					"distance_pct": float    # % distance from current price
				},
				"SMA50": {...},
				"SMA200": {...}
			}
		}

	For EMA:
		dict: {
			"symbol": str,
			"current_price": float,
			"ema": {
				"EMA9": {
					"value": float,          # 9-day exponential moving average
					"distance_pct": float    # % distance from current price
				},
				"EMA21": {...},
				"EMA50": {...}
			}
		}

	For Bollinger Bands:
		dict: {
			"symbol": str,
			"current_price": float,
			"bollinger": {
				"upper": float,              # Upper band (SMA + 2σ)
				"middle": float,             # Middle band (SMA)
				"lower": float,              # Lower band (SMA - 2σ)
				"pct_b": float,              # %B indicator (0-1 position within bands)
				"bandwidth": float           # Band width as % of middle band
			},
			"signal": str                    # "above_upper", "below_lower", "within_bands"
		}

Example:
	>>> python trend.py sma AAPL --periods "20,50,200"
	{
		"symbol": "AAPL",
		"current_price": 175.50,
		"sma": {
			"SMA20": {"value": 173.20, "distance_pct": 1.33},
			"SMA50": {"value": 168.40, "distance_pct": 4.22},
			"SMA200": {"value": 155.80, "distance_pct": 12.64}
		}
	}

	>>> python trend.py ema SPY --periods "9,21,50"
	{
		"symbol": "SPY",
		"current_price": 475.50,
		"ema": {
			"EMA9": {"value": 474.80, "distance_pct": 0.15},
			"EMA21": {"value": 472.30, "distance_pct": 0.68}
		}
	}

	>>> python trend.py bollinger TSLA --bb-period 20 --std-dev 2.0
	{
		"symbol": "TSLA",
		"current_price": 242.80,
		"bollinger": {
			"upper": 255.30,
			"middle": 240.00,
			"lower": 224.70,
			"pct_b": 0.42,
			"bandwidth": 12.75
		},
		"signal": "within_bands"
	}

Use Cases:
	- Identify trend direction using moving average slopes (rising = uptrend, falling = downtrend)
	- Detect support/resistance levels at major MAs (20-day, 50-day, 200-day)
	- Confirm breakouts when price crosses above/below key moving averages
	- Mean reversion trading when price touches Bollinger Band extremes
	- Volatility assessment using Bollinger Band width (narrow = low volatility, wide = high volatility)
	- Entry/exit signals combining MA crossovers with Bollinger %B positioning

Notes:
	- SMA gives equal weight to all prices; EMA gives more weight to recent prices
	- Golden cross (50-day MA crosses above 200-day MA) signals long-term bullish trend
	- Death cross (50-day MA crosses below 200-day MA) signals long-term bearish trend
	- Bollinger %B above 1.0 indicates price above upper band (extreme overbought)
	- Bollinger %B below 0.0 indicates price below lower band (extreme oversold)
	- Narrow Bollinger Bands often precede significant price moves (volatility expansion)
	- Standard deviation multiplier affects band sensitivity (2.0 = 95% confidence interval)

See Also:
	- indicators.py: Core moving average and Bollinger Band calculation functions
	- oscillators.py: RSI and MACD for momentum confirmation with trend
	- pattern/regime.py: Market regime detection combining multiple indicators
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import pandas as pd
import yfinance as yf
from technical.indicators import calculate_bollinger_bands, calculate_ema, calculate_sma
from utils import output_json, safe_run


@safe_run
def cmd_sma(args):
	"""Calculate Simple Moving Averages."""
	ticker = yf.Ticker(args.symbol)
	data = ticker.history(period=args.period, interval=args.interval)
	if data.empty:
		output_json({"error": f"No data for {args.symbol}"})
		return

	prices = data["Close"]
	periods = [int(p) for p in args.periods.split(",")]

	result = {
		"symbol": args.symbol,
		"period": args.period,
		"interval": args.interval,
		"current_price": round(float(prices.iloc[-1]), 2),
		"date": str(data.index[-1].date()),
		"sma": {},
	}

	for p in periods:
		sma = calculate_sma(prices, p)
		current_sma = sma.iloc[-1]
		if not pd.isna(current_sma):
			result["sma"][f"SMA{p}"] = {
				"value": round(float(current_sma), 2),
				"distance_pct": round((prices.iloc[-1] - current_sma) / current_sma * 100, 2),
			}

	output_json(result)


@safe_run
def cmd_ema(args):
	"""Calculate Exponential Moving Averages."""
	ticker = yf.Ticker(args.symbol)
	data = ticker.history(period=args.period, interval=args.interval)
	if data.empty:
		output_json({"error": f"No data for {args.symbol}"})
		return

	prices = data["Close"]
	periods = [int(p) for p in args.periods.split(",")]

	result = {
		"symbol": args.symbol,
		"period": args.period,
		"interval": args.interval,
		"current_price": round(float(prices.iloc[-1]), 2),
		"date": str(data.index[-1].date()),
		"ema": {},
	}

	for p in periods:
		ema = calculate_ema(prices, p)
		current_ema = ema.iloc[-1]
		if not pd.isna(current_ema):
			result["ema"][f"EMA{p}"] = {
				"value": round(float(current_ema), 2),
				"distance_pct": round((prices.iloc[-1] - current_ema) / current_ema * 100, 2),
			}

	output_json(result)


@safe_run
def cmd_bollinger(args):
	"""Calculate Bollinger Bands."""
	ticker = yf.Ticker(args.symbol)
	data = ticker.history(period=args.period, interval=args.interval)
	if data.empty:
		output_json({"error": f"No data for {args.symbol}"})
		return

	prices = data["Close"]
	sma, upper, lower = calculate_bollinger_bands(prices, args.bb_period, args.std_dev)

	current_price = prices.iloc[-1]
	current_upper = upper.iloc[-1]
	current_lower = lower.iloc[-1]
	current_sma = sma.iloc[-1]

	# Calculate %B (position within bands)
	pct_b = (
		(current_price - current_lower) / (current_upper - current_lower)
		if (current_upper - current_lower) > 0
		else 0.5
	)

	# Calculate bandwidth
	bandwidth = (current_upper - current_lower) / current_sma * 100 if current_sma > 0 else 0

	result = {
		"symbol": args.symbol,
		"period": args.period,
		"interval": args.interval,
		"bb_period": args.bb_period,
		"std_dev": args.std_dev,
		"current_price": round(float(current_price), 2),
		"date": str(data.index[-1].date()),
		"bollinger": {
			"upper": round(float(current_upper), 2),
			"middle": round(float(current_sma), 2),
			"lower": round(float(current_lower), 2),
			"pct_b": round(float(pct_b), 4),
			"bandwidth": round(float(bandwidth), 2),
		},
		"signal": "above_upper"
		if current_price > current_upper
		else "below_lower"
		if current_price < current_lower
		else "within_bands",
	}
	output_json(result)
