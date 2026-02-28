#!/usr/bin/env python3
"""Williams %R: momentum oscillator measuring overbought/oversold conditions.

Calculates the Williams %R oscillator, which measures the level of the close
relative to the highest high over a lookback period. Values range from 0 to -100,
where readings above -20 indicate overbought conditions and below -80 indicate
oversold conditions.

Commands:
	calculate: Calculate Williams %R and generate signal for a ticker

Args:
	symbol (str): Ticker symbol (e.g., "AAPL", "SPY", "QQQ")
	--period (int): Lookback period for %R calculation (default: 14)
	--history (int): Number of recent %R values to include in output (default: 10)

Returns:
	dict: {
		"symbol": str,
		"current_wr": float,
		"signal": str,
		"period": int,
		"wr_history": {date: wr_value},
		"statistics": {
			"mean": float,
			"std": float,
			"pct_time_overbought": float,
			"pct_time_oversold": float
		}
	}

Example:
	>>> python williams_r.py calculate SPY --period 14 --history 5
	{
		"symbol": "SPY",
		"current_wr": -45.32,
		"signal": "neutral",
		"period": 14,
		"wr_history": {"2026-02-24": -52.1, "2026-02-25": -48.3, ...},
		"statistics": {
			"mean": -50.2,
			"std": 22.4,
			"pct_time_overbought": 15.3,
			"pct_time_oversold": 12.8
		}
	}

Use Cases:
	- Identify overbought/oversold conditions for entry/exit timing
	- Confirm momentum divergences with price action
	- Filter breakout entries by requiring %R confirmation
	- Monitor oscillator extremes for mean-reversion setups

Notes:
	- Formula: Williams %R = -100 * (Highest High - Close) / (Highest High - Lowest Low)
	- Scale: 0 to -100 (0 = overbought, -100 = oversold)
	- Standard period is 14 (Wilder's default), but Williams uses various periods
	- Overbought threshold: > -20; Oversold threshold: < -80

See Also:
	- oscillators.py: RSI and MACD oscillator analysis
	- atr_breakout.py: ATR-based volatility breakout levels
	- calendar_bias.py: TDW/TDM calendar bias
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import numpy as np
import yfinance as yf
from utils import output_json, safe_run


def _williams_pct_r(df, period=14):
	"""Calculate Williams %R oscillator.

	Williams %R = -100 * (Highest High - Close) / (Highest High - Lowest Low)

	Args:
		df: DataFrame with High, Low, Close columns
		period: Lookback period for highest high / lowest low

	Returns:
		pd.Series: Williams %R values (0 to -100)
	"""
	highest_high = df["High"].rolling(period).max()
	lowest_low = df["Low"].rolling(period).min()
	wr = -100 * (highest_high - df["Close"]) / (highest_high - lowest_low)
	return wr


def _determine_signal(wr_value):
	"""Determine signal based on Williams %R value.

	Args:
		wr_value: Current Williams %R reading

	Returns:
		str: "overbought" (> -20), "oversold" (< -80), or "neutral"
	"""
	if wr_value > -20:
		return "overbought"
	elif wr_value < -80:
		return "oversold"
	return "neutral"


@safe_run
def cmd_calculate(args):
	"""Calculate Williams %R and generate signal."""
	symbol = args.symbol.upper()
	ticker = yf.Ticker(symbol)
	data = ticker.history(period="1y", interval="1d")

	if data.empty or len(data) < args.period:
		output_json({
			"error": f"Insufficient data for {symbol}. Need at least {args.period} trading days.",
			"data_points": len(data),
		})
		return

	# Calculate Williams %R
	wr = _williams_pct_r(data, period=args.period)

	# Drop NaN values for clean statistics
	wr_clean = wr.dropna()

	if wr_clean.empty:
		output_json({
			"error": f"Could not calculate Williams %R for {symbol}.",
		})
		return

	current_wr = float(wr_clean.iloc[-1])
	signal = _determine_signal(current_wr)

	# Build history dict (last N values)
	history_count = min(args.history, len(wr_clean))
	wr_tail = wr_clean.tail(history_count)
	wr_history = {
		str(idx.date()): round(float(val), 2)
		for idx, val in wr_tail.items()
	}

	# Compute statistics
	wr_values = wr_clean.values.astype(float)
	total_count = len(wr_values)
	overbought_count = int(np.sum(wr_values > -20))
	oversold_count = int(np.sum(wr_values < -80))

	statistics = {
		"mean": round(float(np.nanmean(wr_values)), 2),
		"std": round(float(np.nanstd(wr_values)), 2),
		"pct_time_overbought": round(overbought_count / total_count * 100, 1),
		"pct_time_oversold": round(oversold_count / total_count * 100, 1),
	}

	output_json({
		"symbol": symbol,
		"current_wr": round(current_wr, 2),
		"signal": signal,
		"period": args.period,
		"wr_history": wr_history,
		"statistics": statistics,
	})


def main():
	parser = argparse.ArgumentParser(description="Williams %%R Momentum Oscillator")
	sub = parser.add_subparsers(dest="command", required=True)

	sp = sub.add_parser("calculate", help="Calculate Williams %%R and signal")
	sp.add_argument("symbol", help="Ticker symbol")
	sp.add_argument("--period", type=int, default=14, help="Lookback period (default: 14)")
	sp.add_argument("--history", type=int, default=10, help="Number of historical values (default: 10)")
	sp.set_defaults(func=cmd_calculate)

	args = parser.parse_args()
	args.func(args)


if __name__ == "__main__":
	main()
