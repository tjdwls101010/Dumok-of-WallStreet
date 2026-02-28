#!/usr/bin/env python3
"""Options data retrieval via yfinance.

Retrieve options expiration dates and option chain data (calls and puts) for listed options
on stocks and ETFs via Yahoo Finance API.

Commands:
	get-options: List all available expiration dates for a ticker
	option-chain: Retrieve full option chain (calls/puts) for specific expiration

Args:
	symbol (str): Ticker symbol (e.g., "AAPL", "SPY", "MSFT")
	--date (str): Expiration date (YYYY-MM-DD format, optional)
		- If omitted, uses nearest expiration date
		- Must match exact expiration from get-options list
	--type (str): Option type filter (calls/puts/both, default: both)
		- calls: Call options only
		- puts: Put options only
		- both: Both calls and puts

Returns:
	list: Available expiration dates (get-options)
	dict: Option chain data (option-chain)
		{
			"contractSymbol": str,           # Options contract identifier
			"strike": float,                 # Strike price
			"currency": str,                 # Currency (USD, EUR, etc.)
			"lastPrice": float,              # Last traded price
			"bid": float,                    # Current bid price
			"ask": float,                    # Current ask price
			"volume": int,                   # Trading volume
			"openInterest": int,             # Open interest (contracts outstanding)
			"impliedVolatility": float,      # Implied volatility (annualized)
			"inTheMoney": bool,              # ITM/OTM status
			"lastTradeDate": str,            # Last trade timestamp
			"change": float,                 # Price change from previous close
			"percentChange": float           # Percentage change
		}

Example:
	>>> python options.py get-options AAPL
	[
		"2026-02-13",
		"2026-02-20",
		"2026-02-27",
		"2026-03-20",
		"2026-06-19",
		"2027-01-15"
	]

	>>> python options.py option-chain AAPL --date 2026-03-20 --type calls
	{
		"calls": [
			{
				"contractSymbol": "AAPL260320C00150000",
				"strike": 150.0,
				"lastPrice": 26.50,
				"bid": 26.30,
				"ask": 26.70,
				"volume": 523,
				"openInterest": 1245,
				"impliedVolatility": 0.2345,
				"inTheMoney": true
			},
			{
				"strike": 155.0,
				"lastPrice": 22.10,
				"impliedVolatility": 0.2289
			}
		]
	}

	>>> python options.py option-chain SPY --date 2026-02-20 --type both
	{
		"calls": [...],
		"puts": [
			{
				"contractSymbol": "SPY260220P00470000",
				"strike": 470.0,
				"lastPrice": 3.85,
				"impliedVolatility": 0.1523,
				"inTheMoney": false
			}
		]
	}

Use Cases:
	- Options strategy analysis (covered calls, protective puts, spreads)
	- Implied volatility surface construction and analysis
	- Open interest tracking for support/resistance levels
	- Expiration calendar monitoring for position management
	- Unusual options activity detection via volume/OI
	- Greeks calculation input data (IV, strike, expiration)

Notes:
	- Yahoo Finance API rate limits: ~2000 requests/hour
	- Options data delayed 15 minutes for most exchanges
	- Expiration dates are third Friday of month (standard)
	- Weekly options available for liquid tickers (SPY, QQQ, AAPL)
	- Bid/ask spread indicates liquidity (tighter = more liquid)
	- Open interest updated once daily after market close
	- Implied volatility calculated using Black-Scholes model
	- Some strikes may have zero volume/open interest

See Also:
	- price.py: Underlying stock price for options valuation
	- info.py: Stock metadata including trading hours
	- actions.py: Dividend calendar for options adjustment events
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import yfinance as yf
from utils import output_json, safe_run


@safe_run
def cmd_get_options(args):
	ticker = yf.Ticker(args.symbol)
	output_json(list(ticker.options))


@safe_run
def cmd_option_chain(args):
	ticker = yf.Ticker(args.symbol)
	chain = ticker.option_chain(args.date)
	if args.type == "calls":
		output_json(chain.calls)
	elif args.type == "puts":
		output_json(chain.puts)
	else:
		output_json({"calls": chain.calls, "puts": chain.puts})


def main():
	parser = argparse.ArgumentParser(description="Options data via yfinance")
	sub = parser.add_subparsers(dest="command", required=True)

	p_get = sub.add_parser("get-options", help="List expiration dates")
	p_get.add_argument("symbol")
	p_get.set_defaults(func=cmd_get_options)

	p_chain = sub.add_parser("option-chain", help="Get option chain")
	p_chain.add_argument("symbol")
	p_chain.add_argument("--date", default=None, help="Expiration date")
	p_chain.add_argument("--type", choices=["calls", "puts", "both"], default="both")
	p_chain.set_defaults(func=cmd_option_chain)

	args = parser.parse_args()
	args.func(args)


if __name__ == "__main__":
	main()
