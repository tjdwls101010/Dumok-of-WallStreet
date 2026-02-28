#!/usr/bin/env python3
"""Range Analysis: range expansion/contraction phase detection.

Detects whether a market is in a range contraction or expansion phase based on
Larry Williams' Range Axiom. Also computes a Close-as-Trend-Indicator showing
buying power versus selling pressure within each bar.

Commands:
		analyze: Detect range expansion/contraction phase for a ticker

Args:
		symbol (str): Ticker symbol (e.g., "AAPL", "ES=F", "EURUSD=X")
		--lookback (int): Number of bars for average range calculation (default: 20)

Returns:
		dict: {
				"symbol": str,
				"current_range_pct": float,
				"avg_range_pct": float,
				"range_ratio": float,
				"phase": str,
				"consecutive_small_ranges": int,
				"consecutive_large_ranges": int,
				"axiom_signal": str,
				"range_history": [{"date": str, "range_pct": float, "phase": str}],
				"close_position": {
						"buying_power": float,
						"selling_pressure": float,
						"close_pct": float,
						"recent_bias": str,
						"consecutive_upper_closes": int,
						"consecutive_lower_closes": int
				}
		}

Example:
		>>> python range_analysis.py analyze AAPL --lookback 20
		{
				"symbol": "AAPL",
				"current_range_pct": 1.234,
				"avg_range_pct": 1.567,
				"range_ratio": 0.79,
				"phase": "neutral",
				"consecutive_small_ranges": 0,
				"consecutive_large_ranges": 0,
				"axiom_signal": "neutral",
				"range_history": [
						{"date": "2025-12-15", "range_pct": 1.345, "phase": "neutral"}
				],
				"close_position": {
						"buying_power": 1.25,
						"selling_pressure": 0.75,
						"close_pct": 62.5,
						"recent_bias": "buying_dominant",
						"consecutive_upper_closes": 3,
						"consecutive_lower_closes": 0
				}
		}

Use Cases:
		- Anticipate breakouts by detecting contraction phases about to expand
		- Avoid chasing extended moves during expansion phases nearing exhaustion
		- Gauge intrabar sentiment via buying power vs selling pressure
		- Time entries when axiom signal indicates expansion is imminent

Notes:
		- Range Axiom: "Small ranges beget large ranges. Large ranges beget small ranges."
		- Phase thresholds: contraction (ratio < 0.7), expansion (ratio > 1.3)
		- Axiom signal triggers at 3+ consecutive small/large ranges
		- Close-as-Trend-Indicator: Buying Power = Close - Low, Selling Pressure = High - Close
		- Upper close threshold: >= 65% of range; Lower close threshold: <= 35%
		- Recent bias uses 1.2x ratio over 5-day window
		- Holds across all markets, all countries, all timeframes (5-minute through monthly)

See Also:
		- swing_points.py: Mechanical swing point identification
		- williams.py: Composite Williams methodology scoring
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import yfinance as yf
from utils import output_json, safe_run


def _fetch_ohlcv(symbol, period="1y", interval="1d"):
	"""Fetch OHLCV data via yfinance, return DataFrame."""
	ticker = yf.Ticker(symbol)
	df = ticker.history(period=period, interval=interval)
	if df.empty:
		raise ValueError(f"No data returned for {symbol}")
	return df


@safe_run
def cmd_analyze(args):
	"""Range expansion/contraction phase detection."""
	symbol = args.symbol.upper()
	df = _fetch_ohlcv(symbol, period="6mo")

	if len(df) < args.lookback + 5:
		raise ValueError(f"Insufficient data for range analysis ({len(df)} bars)")

	# Calculate daily range as percentage of close
	df["range_pct"] = (df["High"] - df["Low"]) / df["Close"] * 100

	# Recent window
	recent = df.tail(args.lookback)
	avg_range = float(recent["range_pct"].mean())
	current_range = float(df["range_pct"].iloc[-1])
	range_ratio = round(current_range / avg_range, 2) if avg_range > 0 else 1.0

	# Phase detection
	if range_ratio < 0.7:
		phase = "contraction"
	elif range_ratio > 1.3:
		phase = "expansion"
	else:
		phase = "neutral"

	# Count consecutive small/large ranges
	consecutive_small = 0
	consecutive_large = 0
	for i in range(len(df) - 1, max(len(df) - 20, 0) - 1, -1):
		r = float(df["range_pct"].iloc[i])
		if r < avg_range * 0.7:
			consecutive_small += 1
		else:
			break
	for i in range(len(df) - 1, max(len(df) - 20, 0) - 1, -1):
		r = float(df["range_pct"].iloc[i])
		if r > avg_range * 1.3:
			consecutive_large += 1
		else:
			break

	# Williams axiom signal
	if consecutive_small >= 3:
		axiom_signal = "expansion_imminent"
	elif consecutive_large >= 3:
		axiom_signal = "contraction_imminent"
	else:
		axiom_signal = "neutral"

	# Range history (last 10 bars)
	range_history = []
	for i in range(-min(10, len(recent)), 0):
		row = recent.iloc[i]
		r = float(row["range_pct"])
		p = "contraction" if r < avg_range * 0.7 else ("expansion" if r > avg_range * 1.3 else "neutral")
		range_history.append({
			"date": recent.index[i].strftime("%Y-%m-%d"),
			"range_pct": round(r, 3),
			"phase": p,
		})

	# Close-as-Trend-Indicator
	close = float(df["Close"].iloc[-1])
	high = float(df["High"].iloc[-1])
	low = float(df["Low"].iloc[-1])
	bar_range = high - low
	close_pct = round((close - low) / bar_range * 100, 1) if bar_range > 0 else 50.0
	buying_power = round(close - low, 2)
	selling_pressure = round(high - close, 2)

	# Recent bias: average buying power vs selling pressure over last 5 days
	recent_bp = []
	recent_sp = []
	for i in range(-min(5, len(df)), 0):
		row = df.iloc[i]
		bp = float(row["Close"]) - float(row["Low"])
		sp_val = float(row["High"]) - float(row["Close"])
		recent_bp.append(bp)
		recent_sp.append(sp_val)
	avg_bp = sum(recent_bp) / len(recent_bp)
	avg_sp = sum(recent_sp) / len(recent_sp)
	if avg_bp > avg_sp * 1.2:
		recent_bias = "buying_dominant"
	elif avg_sp > avg_bp * 1.2:
		recent_bias = "selling_dominant"
	else:
		recent_bias = "neutral"

	# Consecutive upper/lower closes
	consecutive_upper = 0
	consecutive_lower = 0
	for i in range(len(df) - 1, max(len(df) - 20, 0) - 1, -1):
		row = df.iloc[i]
		r = float(row["High"]) - float(row["Low"])
		if r > 0:
			cp = (float(row["Close"]) - float(row["Low"])) / r * 100
			if cp >= 65:
				consecutive_upper += 1
			else:
				break
	for i in range(len(df) - 1, max(len(df) - 20, 0) - 1, -1):
		row = df.iloc[i]
		r = float(row["High"]) - float(row["Low"])
		if r > 0:
			cp = (float(row["Close"]) - float(row["Low"])) / r * 100
			if cp <= 35:
				consecutive_lower += 1
			else:
				break

	output_json({
		"symbol": symbol,
		"current_range_pct": round(current_range, 3),
		"avg_range_pct": round(avg_range, 3),
		"range_ratio": range_ratio,
		"phase": phase,
		"consecutive_small_ranges": consecutive_small,
		"consecutive_large_ranges": consecutive_large,
		"axiom_signal": axiom_signal,
		"range_history": range_history,
		"close_position": {
			"buying_power": buying_power,
			"selling_pressure": selling_pressure,
			"close_pct": close_pct,
			"recent_bias": recent_bias,
			"consecutive_upper_closes": consecutive_upper,
			"consecutive_lower_closes": consecutive_lower,
		},
	})


def main():
	parser = argparse.ArgumentParser(description="Range Expansion/Contraction Analysis")
	sub = parser.add_subparsers(dest="command", required=True)

	sp = sub.add_parser("analyze", help="Detect range expansion/contraction phase")
	sp.add_argument("symbol", help="Ticker symbol")
	sp.add_argument("--lookback", type=int, default=20, help="Lookback period in bars (default: 20)")
	sp.set_defaults(func=cmd_analyze)

	args = parser.parse_args()
	args.func(args)


if __name__ == "__main__":
	main()
