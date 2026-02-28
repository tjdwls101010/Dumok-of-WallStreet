#!/usr/bin/env python3
"""Greatest Swing Value (GSV): failure swing measurement for entry/stop levels.

Computes Larry Williams' Greatest Swing Value from "Long-Term Secrets to
Short-Term Trading" (2011 edition). Measures the average failure swing on
down-close and up-close days to derive entry and stop levels based on
historical swing exhaustion thresholds.

Commands:
	analyze: Calculate GSV entry/stop levels for a ticker

Args:
	symbol (str): Ticker symbol (e.g., "AAPL", "SPY", "ES=F")

Returns:
	dict: {
		"symbol": str,
		"avg_buy_swing": float,
		"avg_sell_swing": float,
		"buy_entry_level": float,
		"buy_stop_level": float,
		"sell_entry_level": float,
		"sell_stop_level": float,
		"swing_period_days": int,
		"recent_gsv_exceeded": bool,
		"swing_history": [{"date": str, "type": str, "value": float}]
	}

Example:
	>>> python gsv.py analyze SPY
	{
		"symbol": "SPY",
		"avg_buy_swing": 3.45,
		"avg_sell_swing": 2.89,
		"buy_entry_level": 518.30,
		"buy_stop_level": 516.00,
		"sell_entry_level": 529.21,
		"sell_stop_level": 530.76,
		"swing_period_days": 4,
		"recent_gsv_exceeded": false,
		"swing_history": [
			{"date": "2026-02-20", "type": "buy_swing", "value": 3.12},
			{"date": "2026-02-21", "type": "sell_swing", "value": 2.45}
		]
	}

Use Cases:
	- Determine intraday entry thresholds for buy/sell setups
	- Set stop-loss levels based on swing exhaustion multiples
	- Detect recent exhaustion events (recent_gsv_exceeded = True)
	- Combine with TDW bias for day-specific swing filtering

Notes:
	- GSV Formula: Buy Swing = High - Open (on down-close days),
	  Sell Swing = Open - Low (on up-close days)
	- Entry threshold: 180% of 4-day average failure swing
	- Stop threshold: 225% of 4-day average failure swing
	- Bond GSV with TDW filter: 90% accuracy in pit-era testing
	- S&P GSV with Bond filter (Bond close > 15 days ago): $105,675 profit,
	  67% accuracy, 247 trades
	- Electronic Era Status: Opening-based GSV greatly diminished (open ~= prior
	  close in electronic markets)
	- TDW data within GSV framework still holds: Fridays for Bonds, Tuesdays
	  for stocks
	- recent_gsv_exceeded = True means 225% threshold hit recently (exhaustion
	  signal)

See Also:
	- bar_patterns.py: Williams bar pattern detection
	- williams.py: Consolidated Williams tools (legacy)
	- range_analysis.py: Range expansion/contraction context
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import yfinance as yf
from utils import output_json, safe_run

# ── Command ────────────────────────────────────────────────────────────────


@safe_run
def cmd_gsv(args):
	"""Calculate Greatest Swing Value entry and stop levels."""
	symbol = args.symbol.upper()

	ticker = yf.Ticker(symbol)
	df = ticker.history(period="3mo", interval="1d")

	if len(df) < 15:
		raise ValueError(f"Insufficient data for GSV calculation ({len(df)} bars)")

	# Classify each bar and compute its swing value
	buy_swings = []
	sell_swings = []
	for i in range(len(df)):
		row = df.iloc[i]
		if row["Close"] < row["Open"]:
			buy_swings.append(float(row["High"] - row["Open"]))
		else:
			sell_swings.append(float(row["Open"] - row["Low"]))

	# Use last 4 swings of each type for the average
	recent_buy_swings = buy_swings[-4:] if len(buy_swings) >= 4 else buy_swings
	recent_sell_swings = sell_swings[-4:] if len(sell_swings) >= 4 else sell_swings

	avg_buy_swing = round(sum(recent_buy_swings) / len(recent_buy_swings), 2) if recent_buy_swings else 0.0
	avg_sell_swing = round(sum(recent_sell_swings) / len(recent_sell_swings), 2) if recent_sell_swings else 0.0

	# Derive entry/stop levels from today's open
	current_open = float(df["Open"].iloc[-1])
	buy_entry_level = round(current_open - (avg_sell_swing * 1.80), 2)
	buy_stop_level = round(current_open - (avg_sell_swing * 2.25), 2)
	sell_entry_level = round(current_open + (avg_buy_swing * 1.80), 2)
	sell_stop_level = round(current_open + (avg_buy_swing * 2.25), 2)

	# Check if GSV 225% threshold was exceeded in last 5 bars
	recent_gsv_exceeded = False
	for i in range(-min(5, len(df)), 0):
		row = df.iloc[i]
		if row["Close"] < row["Open"]:
			swing = float(row["High"] - row["Open"])
			if avg_buy_swing > 0 and swing > avg_buy_swing * 2.25:
				recent_gsv_exceeded = True
				break
		else:
			swing = float(row["Open"] - row["Low"])
			if avg_sell_swing > 0 and swing > avg_sell_swing * 2.25:
				recent_gsv_exceeded = True
				break

	# Build swing history for last 10 bars
	swing_history = []
	for i in range(-min(10, len(df)), 0):
		row = df.iloc[i]
		date_str = df.index[i].strftime("%Y-%m-%d")
		if row["Close"] < row["Open"]:
			swing_history.append({"date": date_str, "type": "buy_swing", "value": round(float(row["High"] - row["Open"]), 2)})
		else:
			swing_history.append({"date": date_str, "type": "sell_swing", "value": round(float(row["Open"] - row["Low"]), 2)})

	output_json({
		"symbol": symbol,
		"avg_buy_swing": avg_buy_swing,
		"avg_sell_swing": avg_sell_swing,
		"buy_entry_level": buy_entry_level,
		"buy_stop_level": buy_stop_level,
		"sell_entry_level": sell_entry_level,
		"sell_stop_level": sell_stop_level,
		"swing_period_days": 4,
		"recent_gsv_exceeded": recent_gsv_exceeded,
		"swing_history": swing_history,
	})


# ── CLI entry point ───────────────────────────────────────────────────────


def main():
	parser = argparse.ArgumentParser(description="Greatest Swing Value Analysis")
	sub = parser.add_subparsers(dest="command", required=True)

	sp = sub.add_parser("analyze", help="Calculate GSV entry and stop levels")
	sp.add_argument("symbol", help="Ticker symbol")
	sp.set_defaults(func=cmd_gsv)

	args = parser.parse_args()
	args.func(args)


if __name__ == "__main__":
	main()
