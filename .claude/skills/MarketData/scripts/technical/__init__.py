#!/usr/bin/env python3
"""Technical analysis indicators CLI dispatcher.

This module provides a unified command-line interface for all technical indicators:
- Oscillators: RSI, MACD (oscillators.py)
- Trend: SMA, EMA, Bollinger Bands (trend.py)
- All: Comprehensive indicator summary
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import pandas as pd
import yfinance as yf
from technical.indicators import (
	calculate_bollinger_bands,
	calculate_macd,
	calculate_rsi,
	calculate_sma,
)
from technical.oscillators import cmd_macd, cmd_rsi, cmd_rsi_multi_timeframe
from technical.slope import cmd_momentum_regime, cmd_rsi_derivative, cmd_slope
from technical.trend import cmd_bollinger, cmd_ema, cmd_sma
from utils import output_json, safe_run


@safe_run
def cmd_all(args):
	"""Calculate all technical indicators at once."""
	ticker = yf.Ticker(args.symbol)
	data = ticker.history(period=args.period, interval=args.interval)
	if data.empty:
		output_json({"error": f"No data for {args.symbol}"})
		return

	prices = data["Close"]
	current_price = prices.iloc[-1]

	# RSI
	rsi = calculate_rsi(prices, 14)
	current_rsi = rsi.iloc[-1]

	# SMAs
	sma20 = calculate_sma(prices, 20).iloc[-1]
	sma50 = calculate_sma(prices, 50).iloc[-1]
	sma200 = calculate_sma(prices, 200).iloc[-1]

	# Bollinger Bands
	bb_sma, bb_upper, bb_lower = calculate_bollinger_bands(prices, 20, 2.0)

	# MACD
	macd_line, signal_line, histogram = calculate_macd(prices, 12, 26, 9)

	result = {
		"symbol": args.symbol,
		"period": args.period,
		"interval": args.interval,
		"current_price": round(float(current_price), 2),
		"date": str(data.index[-1].date()),
		"rsi": {
			"value": round(float(current_rsi), 2) if not pd.isna(current_rsi) else None,
			"signal": "overbought" if current_rsi >= 70 else "oversold" if current_rsi <= 30 else "neutral",
		},
		"moving_averages": {
			"sma20": round(float(sma20), 2) if not pd.isna(sma20) else None,
			"sma50": round(float(sma50), 2) if not pd.isna(sma50) else None,
			"sma200": round(float(sma200), 2) if not pd.isna(sma200) else None,
			"above_sma20": bool(current_price > sma20) if not pd.isna(sma20) else None,
			"above_sma50": bool(current_price > sma50) if not pd.isna(sma50) else None,
			"above_sma200": bool(current_price > sma200) if not pd.isna(sma200) else None,
		},
		"bollinger_bands": {
			"upper": round(float(bb_upper.iloc[-1]), 2),
			"middle": round(float(bb_sma.iloc[-1]), 2),
			"lower": round(float(bb_lower.iloc[-1]), 2),
		},
		"macd": {
			"macd_line": round(float(macd_line.iloc[-1]), 4),
			"signal_line": round(float(signal_line.iloc[-1]), 4),
			"histogram": round(float(histogram.iloc[-1]), 4),
		},
	}
	output_json(result)


def main():
	"""Main CLI entry point for technical indicators."""
	parser = argparse.ArgumentParser(description="Technical analysis indicators")
	sub = parser.add_subparsers(dest="command", required=True)

	# RSI
	sp = sub.add_parser("rsi", help="Calculate RSI (Relative Strength Index)")
	sp.add_argument("symbol")
	sp.add_argument("--period", default="1y", help="Data period (1y, 2y, 5y, etc.)")
	sp.add_argument("--interval", default="1d", help="Data interval (1d, 1wk, 1mo)")
	sp.add_argument("--rsi-period", type=int, default=14, help="RSI calculation period")
	sp.add_argument("--history-length", type=int, default=20, help="Number of historical RSI values to return")
	sp.set_defaults(func=cmd_rsi)

	# RSI Multi-Timeframe (SidneyKim0 methodology)
	sp = sub.add_parser("rsi-mtf", help="Calculate RSI across daily/weekly/monthly timeframes")
	sp.add_argument("symbol")
	sp.add_argument("--rsi-period", type=int, default=14, help="RSI calculation period")
	sp.set_defaults(func=cmd_rsi_multi_timeframe)

	# SMA
	sp = sub.add_parser("sma", help="Calculate Simple Moving Averages")
	sp.add_argument("symbol")
	sp.add_argument("--period", default="2y", help="Data period")
	sp.add_argument("--interval", default="1d", help="Data interval")
	sp.add_argument("--periods", default="20,50,200", help="SMA periods (comma-separated)")
	sp.set_defaults(func=cmd_sma)

	# EMA
	sp = sub.add_parser("ema", help="Calculate Exponential Moving Averages")
	sp.add_argument("symbol")
	sp.add_argument("--period", default="1y", help="Data period")
	sp.add_argument("--interval", default="1d", help="Data interval")
	sp.add_argument("--periods", default="12,26,50", help="EMA periods (comma-separated)")
	sp.set_defaults(func=cmd_ema)

	# Bollinger Bands
	sp = sub.add_parser("bollinger", help="Calculate Bollinger Bands")
	sp.add_argument("symbol")
	sp.add_argument("--period", default="1y", help="Data period")
	sp.add_argument("--interval", default="1d", help="Data interval")
	sp.add_argument("--bb-period", type=int, default=20, help="Bollinger Band period")
	sp.add_argument("--std-dev", type=float, default=2.0, help="Standard deviation multiplier")
	sp.set_defaults(func=cmd_bollinger)

	# MACD
	sp = sub.add_parser("macd", help="Calculate MACD")
	sp.add_argument("symbol")
	sp.add_argument("--period", default="1y", help="Data period")
	sp.add_argument("--interval", default="1d", help="Data interval")
	sp.add_argument("--fast", type=int, default=12, help="Fast EMA period")
	sp.add_argument("--slow", type=int, default=26, help="Slow EMA period")
	sp.add_argument("--signal", type=int, default=9, help="Signal line period")
	sp.set_defaults(func=cmd_macd)

	# Slope (SidneyKim0 methodology)
	sp = sub.add_parser("slope", help="Calculate 20-day rolling price slope")
	sp.add_argument("symbol")
	sp.add_argument("--period", default="2y", help="Data period")
	sp.add_argument("--interval", default="1d", help="Data interval")
	sp.add_argument("--window", type=int, default=20, help="Rolling slope window")
	sp.set_defaults(func=cmd_slope)

	# RSI Derivative (SidneyKim0 methodology)
	sp = sub.add_parser("rsi-derivative", help="RSI derivative and 9EMA crossover signals")
	sp.add_argument("symbol")
	sp.add_argument("--period", default="2y", help="Data period")
	sp.add_argument("--interval", default="1d", help="Data interval")
	sp.add_argument("--rsi-period", type=int, default=14, help="RSI calculation period")
	sp.add_argument("--ema-period", type=int, default=9, help="EMA period for RSI smoothing")
	sp.set_defaults(func=cmd_rsi_derivative)

	# Momentum Regime (SidneyKim0 methodology)
	sp = sub.add_parser("momentum-regime", help="Combined slope + RSI momentum regime")
	sp.add_argument("symbol")
	sp.add_argument("--period", default="2y", help="Data period")
	sp.add_argument("--interval", default="1d", help="Data interval")
	sp.set_defaults(func=cmd_momentum_regime)

	# All indicators
	sp = sub.add_parser("all", help="Calculate all technical indicators")
	sp.add_argument("symbol")
	sp.add_argument("--period", default="2y", help="Data period")
	sp.add_argument("--interval", default="1d", help="Data interval")
	sp.set_defaults(func=cmd_all)

	args = parser.parse_args()
	args.func(args)


if __name__ == "__main__":
	main()
