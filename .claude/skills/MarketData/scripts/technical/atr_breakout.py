#!/usr/bin/env python3
"""ATR Breakout: volatility-based entry and exit level calculation.

Calculates ATR-based breakout levels using both the classical pit-trading-era
formula and the electronic-era adaptation. Uses short-term ATR (default 3-day)
to capture recent volatility for intraday breakout setups.

Commands:
	breakout: Calculate ATR-based breakout entry/exit levels for a ticker

Args:
	symbol (str): Ticker symbol (e.g., "AAPL", "SPY", "ES=F")
	--atr-period (int): ATR calculation period (default: 3)
	--pct (float): Breakout percentage multiplier (default: 0.6)

Returns:
	dict: {
		"symbol": str,
		"date": str,
		"open": float,
		"previous_close": float,
		"atr_3day": float,
		"classic_buy_level": float,
		"classic_sell_level": float,
		"electronic_buy_level": float,
		"electronic_sell_level": float,
		"yesterday_close_direction": str,
		"active_signal": str,
		"current_price": float,
		"breakout_triggered": bool
	}

Example:
	>>> python atr_breakout.py breakout SPY --atr-period 3 --pct 0.6
	{
		"symbol": "SPY",
		"date": "2026-02-28",
		"open": 502.50,
		"previous_close": 500.10,
		"atr_3day": 8.45,
		"classic_buy_level": 507.57,
		"classic_sell_level": 497.43,
		"electronic_buy_level": 507.57,
		"electronic_sell_level": 497.43,
		"yesterday_close_direction": "up",
		"active_signal": "watching_for_breakout",
		"current_price": 504.30,
		"breakout_triggered": false
	}

Use Cases:
	- Set intraday breakout entry levels before market open
	- Calculate stop-loss levels based on volatility
	- Combine with TDW/TDM bias for filtered entry signals
	- Adjust position sizing based on ATR distance

Notes:
	- Classical Formula (Pit Trading Era): Buy = Open + (Pct * Yesterday's Range),
	  Sell = Open - (Pct * Yesterday's Range)
	- Electronic Era Adaptation: Primary Reference = Prior Day's Low + 20% of 3-day ATR
	  (after down close)
	- Secondary Reference = Open + 60% of 3-day ATR (after up close)
	- Williams uses 3-day ATR (not standard 14-day) for short-term volatility measurement
	- ATR% optimization: range % increases -> fewer trades, higher accuracy, larger
	  average profit
	- Bond Market Evidence (1990-1998): 100% of range = 80% accuracy on 651 trades,
	  $173 avg profit/trade
	- S&P 500 Evidence (1982-1998): 50% volatility expansion = $227,822 profit,
	  74% accuracy, 1,333 trades
	- Optimized 40% buy / 200% sell with TDW filter: 83% accuracy, $251 avg/trade
	- Electronic Era Testing (S&P E-Mini, 2000-2011): Prior Day's Low + 20% ATR =
	  most consistent equity line
	- Monday and Tuesday are strongest buy days; Wednesday should be excluded

See Also:
	- williams_r.py: Williams %R momentum oscillator
	- calendar_bias.py: TDW/TDM calendar bias for day filtering
	- indicators.py: calculate_atr function used internally
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import yfinance as yf
from technical.indicators import calculate_atr
from utils import output_json, safe_run


@safe_run
def cmd_breakout(args):
	"""Calculate ATR-based volatility breakout entry/exit levels."""
	symbol = args.symbol.upper()
	ticker = yf.Ticker(symbol)
	data = ticker.history(period="3mo", interval="1d")

	if data.empty or len(data) < args.atr_period + 2:
		output_json({
			"error": f"Insufficient data for {symbol}. Need at least {args.atr_period + 2} trading days.",
			"data_points": len(data),
		})
		return

	# Calculate ATR
	atr_series = calculate_atr(data["High"], data["Low"], data["Close"], period=args.atr_period)
	atr_value = float(atr_series.iloc[-1])

	# Today's data (latest bar)
	today = data.iloc[-1]
	today_open = float(today["Open"])
	today_close = float(today["Close"])
	today_date = str(data.index[-1].date())

	# Yesterday's data
	yesterday = data.iloc[-2]
	yesterday_open = float(yesterday["Open"])
	yesterday_close = float(yesterday["Close"])
	yesterday_low = float(yesterday["Low"])
	yesterday_high = float(yesterday["High"])

	# Determine yesterday's close direction
	yesterday_direction = "down" if yesterday_close < yesterday_open else "up"

	# Classic breakout levels: Buy = Open + pct * ATR, Sell = Open - pct * ATR
	pct = args.pct
	classic_buy = today_open + pct * atr_value
	classic_sell = today_open - pct * atr_value

	# Electronic era breakout levels
	if yesterday_direction == "down":
		# After down close: buy from prior day's low + small ATR offset
		electronic_buy = yesterday_low + 0.20 * atr_value
		electronic_sell = yesterday_high - 0.60 * atr_value
	else:
		# After up close: buy from open + larger ATR offset
		electronic_buy = today_open + 0.60 * atr_value
		electronic_sell = today_open - 0.60 * atr_value

	# Current price and breakout status
	current_price = float(today_close)
	breakout_triggered = current_price >= classic_buy

	# Determine active signal
	if breakout_triggered:
		active_signal = "breakout_long"
	elif current_price <= classic_sell:
		active_signal = "breakout_short"
	else:
		active_signal = "watching_for_breakout"

	output_json({
		"symbol": symbol,
		"date": today_date,
		"open": round(today_open, 2),
		"previous_close": round(yesterday_close, 2),
		"atr_3day": round(atr_value, 2),
		"classic_buy_level": round(classic_buy, 2),
		"classic_sell_level": round(classic_sell, 2),
		"electronic_buy_level": round(electronic_buy, 2),
		"electronic_sell_level": round(electronic_sell, 2),
		"yesterday_close_direction": yesterday_direction,
		"active_signal": active_signal,
		"current_price": round(current_price, 2),
		"breakout_triggered": breakout_triggered,
	})


def main():
	parser = argparse.ArgumentParser(description="ATR-Based Volatility Breakout Levels")
	sub = parser.add_subparsers(dest="command", required=True)

	sp = sub.add_parser("breakout", help="Calculate ATR breakout entry/exit levels")
	sp.add_argument("symbol", help="Ticker symbol")
	sp.add_argument("--atr-period", type=int, default=3, help="ATR calculation period (default: 3)")
	sp.add_argument("--pct", type=float, default=0.6, help="Breakout percentage multiplier (default: 0.6)")
	sp.set_defaults(func=cmd_breakout)

	args = parser.parse_args()
	args.func(args)


if __name__ == "__main__":
	main()
