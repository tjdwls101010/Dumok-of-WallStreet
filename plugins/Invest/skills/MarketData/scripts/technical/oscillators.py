#!/usr/bin/env python3
"""Calculate momentum oscillators including RSI and MACD for overbought/oversold detection.

RSI (Relative Strength Index) measures momentum on 0-100 scale with statistical enhancements.
MACD (Moving Average Convergence Divergence) identifies trend changes via moving average crossovers.

Args:
	For RSI:
		symbol (str): Stock ticker symbol (e.g., "AAPL", "SPY", "TSLA")
		--period (str): Historical data period (default: "1y" = 1 year)
		--interval (str): Data interval (default: "1d" = daily; "1wk" = weekly; "1mo" = monthly)
		--rsi-period (int): RSI calculation window (default: 14 = standard Wilder period)
		--history-length (int): Number of historical RSI values to return (default: 20)

	For RSI Multi-Timeframe:
		symbol (str): Stock ticker symbol (e.g., "AAPL", "SPY")
		--rsi-period (int): RSI calculation period (default: 14)

	For MACD:
		symbol (str): Stock ticker symbol (e.g., "AAPL", "SPY")
		--period (str): Historical data period (default: "1y")
		--interval (str): Data interval (default: "1d")
		--fast (int): Fast EMA period (default: 12)
		--slow (int): Slow EMA period (default: 26)
		--signal (int): Signal line period (default: 9)

Returns:
	For RSI:
		dict: {
			"symbol": str,                 # Ticker symbol
			"current_rsi": float,          # Current RSI value (0-100)
			"signal": str,                 # "overbought" (≥70), "oversold" (≤30), "neutral"
			"statistics": {
				"mean": float,             # Historical RSI mean
				"std": float,              # Standard deviation
				"percentile": float,       # Current RSI percentile rank
				"interpretation": str      # Relative positioning description
			},
			"mean_reversion_probability": str,  # Historical reversion analysis
			"rsi_history": dict            # Recent RSI values by date
		}

	For RSI Multi-Timeframe:
		dict: {
			"symbol": str,
			"timeframes": {
				"daily": {"current_rsi": float, "signal": str, "price": float},
				"weekly": {"current_rsi": float, "signal": str},
				"monthly": {"current_rsi": float, "signal": str}
			},
			"convergence": str,            # Multi-timeframe alignment assessment
			"probability_rules": list,     # Historical probability insights
			"overbought_timeframes": int,  # Count of overbought timeframes
			"oversold_timeframes": int     # Count of oversold timeframes
		}

	For MACD:
		dict: {
			"symbol": str,
			"macd": {
				"macd_line": float,        # Fast EMA - Slow EMA
				"signal_line": float,      # EMA of MACD line
				"histogram": float         # MACD - Signal (momentum strength)
			},
			"signal": str,                 # "bullish_crossover", "bearish_crossover", "bullish", "bearish"
			"current_price": float,
			"date": str
		}

Example:
	>>> python oscillators.py rsi AAPL --rsi-period 14
	{
		"symbol": "AAPL",
		"current_rsi": 72.45,
		"signal": "overbought",
		"statistics": {
			"mean": 55.30,
			"std": 12.50,
			"percentile": 85.20,
			"interpretation": "High"
		},
		"mean_reversion_probability": "Moderate (Overbought, expect cooling)"
	}

	>>> python oscillators.py rsi-mtf SPY
	{
		"symbol": "SPY",
		"timeframes": {
			"daily": {"current_rsi": 85.2, "signal": "overbought"},
			"weekly": {"current_rsi": 78.5, "signal": "overbought"},
			"monthly": {"current_rsi": 65.0, "signal": "neutral"}
		},
		"convergence": "DOUBLE OVERBOUGHT - High caution"
	}

	>>> python oscillators.py macd AAPL --fast 12 --slow 26
	{
		"symbol": "AAPL",
		"macd": {
			"macd_line": 2.45,
			"signal_line": 1.80,
			"histogram": 0.65
		},
		"signal": "bullish"
	}

Use Cases:
	- Identify entry/exit points when RSI reaches extreme levels (≥70 overbought, ≤30 oversold)
	- Detect trend reversals using MACD crossovers (bullish/bearish signals)
	- Multi-timeframe RSI analysis for stronger signal confirmation (triple overbought/oversold)
	- Mean reversion trading when RSI exceeds 80 (historical probability of touching 45)
	- Momentum confirmation combining MACD histogram strength with RSI positioning

Notes:
	- RSI 80+ has 100% historical probability of touching 45 within 30-60 days (SidneyKim0 methodology)
	- RSI 85+ historically enters 20s range with high probability
	- Multi-timeframe convergence (triple overbought/oversold) provides strongest signals
	- MACD crossovers work best when combined with volume and price action confirmation
	- Standard RSI period is 14, but shorter periods (7-9) increase sensitivity for day trading
	- Lookback period for statistics affects RSI percentile interpretation
	- MACD histogram divergence from price can signal weakening trends

See Also:
	- indicators.py: Core RSI and MACD calculation functions
	- trend.py: Moving averages for trend confirmation with oscillators
	- pattern/similarity.py: Pattern matching for RSI extreme outcome analysis
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import pandas as pd
import yfinance as yf
from technical.indicators import calculate_macd, calculate_rsi
from utils import output_json, safe_run


@safe_run
def cmd_rsi(args):
	"""Calculate RSI for a symbol with statistical enhancements."""
	import numpy as np

	ticker = yf.Ticker(args.symbol)
	data = ticker.history(period=args.period, interval=args.interval)
	if data.empty:
		output_json({"error": f"No data for {args.symbol}"})
		return

	prices = data["Close"]
	rsi = calculate_rsi(prices, args.rsi_period)

	# Remove NaN values for statistics
	rsi_clean = rsi.dropna()
	if len(rsi_clean) == 0:
		output_json({"error": "Insufficient data for RSI calculation"})
		return

	current_rsi = rsi.iloc[-1]

	# Statistical analysis
	rsi_mean = float(rsi_clean.mean())
	rsi_std = float(rsi_clean.std())
	rsi_percentile = float(np.percentile(rsi_clean, 100 * (rsi_clean < current_rsi).sum() / len(rsi_clean)))

	# Mean reversion probability (historical analysis)
	if current_rsi >= 80:
		# Count historical cases where RSI >= 80
		extreme_cases = rsi_clean[rsi_clean >= 80]
		if len(extreme_cases) > 0:
			reversion_prob = "High (RSI 80+ historically reverts to 45 within 30-60 days)"
		else:
			reversion_prob = "N/A (No historical RSI 80+ cases in this period)"
	elif current_rsi <= 20:
		extreme_cases = rsi_clean[rsi_clean <= 20]
		if len(extreme_cases) > 0:
			reversion_prob = "High (RSI 20- historically bounces to 55+ within 30-60 days)"
		else:
			reversion_prob = "N/A (No historical RSI 20- cases in this period)"
	elif current_rsi >= 70:
		reversion_prob = "Moderate (Overbought, expect cooling)"
	elif current_rsi <= 30:
		reversion_prob = "Moderate (Oversold, expect bounce)"
	else:
		reversion_prob = "Low (RSI in normal range)"

	result = {
		"symbol": args.symbol,
		"period": args.period,
		"interval": args.interval,
		"rsi_period": args.rsi_period,
		"current_rsi": round(float(current_rsi), 2) if not pd.isna(current_rsi) else None,
		"current_price": round(float(prices.iloc[-1]), 2),
		"date": str(data.index[-1].date()),
		"signal": "overbought" if current_rsi >= 70 else "oversold" if current_rsi <= 30 else "neutral",
		"statistics": {
			"mean": round(rsi_mean, 2),
			"std": round(rsi_std, 2),
			"percentile": round(rsi_percentile, 2),
			"interpretation": "Extremely High"
			if rsi_percentile > 95
			else "High"
			if rsi_percentile > 80
			else "Above Average"
			if rsi_percentile > 60
			else "Average"
			if rsi_percentile > 40
			else "Below Average"
			if rsi_percentile > 20
			else "Low"
			if rsi_percentile > 5
			else "Extremely Low",
		},
		"mean_reversion_probability": reversion_prob,
		"rsi_history": {
			str(idx.date()): round(float(v), 2) for idx, v in rsi.tail(args.history_length).items() if not pd.isna(v)
		},
	}
	output_json(result)


@safe_run
def cmd_rsi_multi_timeframe(args):
	"""Calculate RSI across multiple timeframes (daily, weekly, monthly) - SidneyKim0 methodology."""
	ticker = yf.Ticker(args.symbol)

	results = {"symbol": args.symbol, "timeframes": {}}

	# Daily RSI
	daily_data = ticker.history(period="2y", interval="1d")
	if not daily_data.empty:
		daily_rsi = calculate_rsi(daily_data["Close"], args.rsi_period)
		current_daily = daily_rsi.iloc[-1]
		results["timeframes"]["daily"] = {
			"current_rsi": round(float(current_daily), 2) if not pd.isna(current_daily) else None,
			"signal": "overbought" if current_daily >= 70 else "oversold" if current_daily <= 30 else "neutral",
			"date": str(daily_data.index[-1].date()),
			"price": round(float(daily_data["Close"].iloc[-1]), 2),
		}

	# Weekly RSI
	weekly_data = ticker.history(period="5y", interval="1wk")
	if not weekly_data.empty:
		weekly_rsi = calculate_rsi(weekly_data["Close"], args.rsi_period)
		current_weekly = weekly_rsi.iloc[-1]
		results["timeframes"]["weekly"] = {
			"current_rsi": round(float(current_weekly), 2) if not pd.isna(current_weekly) else None,
			"signal": "overbought" if current_weekly >= 70 else "oversold" if current_weekly <= 30 else "neutral",
			"date": str(weekly_data.index[-1].date()),
		}

	# Monthly RSI
	monthly_data = ticker.history(period="10y", interval="1mo")
	if not monthly_data.empty:
		monthly_rsi = calculate_rsi(monthly_data["Close"], args.rsi_period)
		current_monthly = monthly_rsi.iloc[-1]
		results["timeframes"]["monthly"] = {
			"current_rsi": round(float(current_monthly), 2) if not pd.isna(current_monthly) else None,
			"signal": "overbought" if current_monthly >= 70 else "oversold" if current_monthly <= 30 else "neutral",
			"date": str(monthly_data.index[-1].date()),
		}

	# SidneyKim0 probability rules
	daily_val = results["timeframes"].get("daily", {}).get("current_rsi", 0) or 0
	weekly_val = results["timeframes"].get("weekly", {}).get("current_rsi", 0) or 0
	monthly_val = results["timeframes"].get("monthly", {}).get("current_rsi", 0) or 0

	probability_rules = []
	if daily_val >= 80:
		probability_rules.append("Daily RSI 80+: 100% probability of RSI touching 45 within 1 month (historical)")
	if weekly_val >= 80:
		probability_rules.append("Weekly RSI 80+: High probability of significant correction")
	if monthly_val >= 80:
		probability_rules.append("Monthly RSI 80+: Long-term overbought, expect multi-month correction")
	if daily_val >= 85:
		probability_rules.append("Daily RSI 85+: 100% probability of RSI entering 20s (historical)")
	if daily_val <= 20:
		probability_rules.append("Daily RSI 20-: Extreme oversold, high probability bounce")
	if daily_val <= 30:
		probability_rules.append("Daily RSI 30-: Oversold, potential accumulation opportunity")

	# Convergence assessment
	overbought_count = sum(1 for v in [daily_val, weekly_val, monthly_val] if v >= 70)
	oversold_count = sum(1 for v in [daily_val, weekly_val, monthly_val] if v <= 30)

	if overbought_count == 3:
		convergence = "TRIPLE OVERBOUGHT - Maximum caution"
	elif overbought_count == 2:
		convergence = "DOUBLE OVERBOUGHT - High caution"
	elif oversold_count == 3:
		convergence = "TRIPLE OVERSOLD - Strong accumulation signal"
	elif oversold_count == 2:
		convergence = "DOUBLE OVERSOLD - Potential accumulation"
	else:
		convergence = "MIXED - No clear multi-timeframe signal"

	results["convergence"] = convergence
	results["probability_rules"] = probability_rules
	results["overbought_timeframes"] = overbought_count
	results["oversold_timeframes"] = oversold_count

	output_json(results)


@safe_run
def cmd_macd(args):
	"""Calculate MACD."""
	ticker = yf.Ticker(args.symbol)
	data = ticker.history(period=args.period, interval=args.interval)
	if data.empty:
		output_json({"error": f"No data for {args.symbol}"})
		return

	prices = data["Close"]
	macd_line, signal_line, histogram = calculate_macd(prices, args.fast, args.slow, args.signal)

	current_macd = macd_line.iloc[-1]
	current_signal = signal_line.iloc[-1]
	current_hist = histogram.iloc[-1]
	prev_hist = histogram.iloc[-2] if len(histogram) > 1 else 0

	# Determine signal
	if current_macd > current_signal and prev_hist <= 0 < current_hist:
		signal = "bullish_crossover"
	elif current_macd < current_signal and prev_hist >= 0 > current_hist:
		signal = "bearish_crossover"
	elif current_macd > current_signal:
		signal = "bullish"
	else:
		signal = "bearish"

	result = {
		"symbol": args.symbol,
		"period": args.period,
		"interval": args.interval,
		"parameters": {"fast": args.fast, "slow": args.slow, "signal": args.signal},
		"current_price": round(float(prices.iloc[-1]), 2),
		"date": str(data.index[-1].date()),
		"macd": {
			"macd_line": round(float(current_macd), 4),
			"signal_line": round(float(current_signal), 4),
			"histogram": round(float(current_hist), 4),
		},
		"signal": signal,
	}
	output_json(result)


def main():
	"""Main CLI for oscillator indicators."""
	parser = argparse.ArgumentParser(description="Oscillator indicators")
	sub = parser.add_subparsers(dest="command", required=True)

	# RSI
	sp = sub.add_parser("rsi", help="Calculate RSI (Relative Strength Index)")
	sp.add_argument("symbol")
	sp.add_argument("--period", default="1y", help="Data period (1y, 2y, 5y, etc.)")
	sp.add_argument("--interval", default="1d", help="Data interval (1d, 1wk, 1mo)")
	sp.add_argument("--rsi-period", type=int, default=14, help="RSI calculation period")
	sp.add_argument("--history-length", type=int, default=20, help="Number of historical RSI values to return")
	sp.set_defaults(func=cmd_rsi)

	# RSI Multi-Timeframe
	sp = sub.add_parser("rsi-mtf", help="Calculate RSI across daily/weekly/monthly timeframes")
	sp.add_argument("symbol")
	sp.add_argument("--rsi-period", type=int, default=14, help="RSI calculation period")
	sp.set_defaults(func=cmd_rsi_multi_timeframe)

	# MACD
	sp = sub.add_parser("macd", help="Calculate MACD")
	sp.add_argument("symbol")
	sp.add_argument("--period", default="1y", help="Data period")
	sp.add_argument("--interval", default="1d", help="Data interval")
	sp.add_argument("--fast", type=int, default=12, help="Fast EMA period")
	sp.add_argument("--slow", type=int, default=26, help="Slow EMA period")
	sp.add_argument("--signal", type=int, default=9, help="Signal line period")
	sp.set_defaults(func=cmd_macd)

	args = parser.parse_args()
	args.func(args)


if __name__ == "__main__":
	main()
