#!/usr/bin/env python3
"""Market status and summary data via yfinance.

Real-time market status and summary information for major global markets
including US, UK, Asia, Europe, rates, commodities, currencies, and crypto.

Args:
	command (str): Operation - status or summary
	market (str): Market identifier from: us, gb, asia, europe, rates, commodities, currencies, crypto

Returns:
	dict: Market-specific data:
		status: {
			"region": str,           # Market region name
			"gmtoffset": int,        # GMT offset in seconds
			"state": str,            # Current market state (PRE, OPEN, POST, CLOSED)
			"tradingHours": str,     # Trading hours in local time
			"currentTime": str       # Current time in market timezone
		}
		summary: {
			"marketSummaryResponse": {
				"result": list,      # Market indices and their values
				"error": None
			}
		}

Example:
	>>> python market.py status us
	{
		"region": "US",
		"state": "OPEN",
		"tradingHours": "09:30 - 16:00 EST",
		"currentTime": "2026-02-05T14:30:00-05:00"
	}

	>>> python market.py summary us
	{
		"marketSummaryResponse": {
			"result": [
				{
					"symbol": "^GSPC",
					"shortName": "S&P 500",
					"regularMarketPrice": 5285.34,
					"regularMarketChange": 12.45,
					"regularMarketChangePercent": 0.24
				}
			]
		}
	}

Use Cases:
	- Monitor global market hours for after-hours trading strategies
	- Check pre-market and post-market status before placing orders
	- Track major indices across regions for correlation analysis
	- Determine optimal trading windows for international markets
	- Real-time market state verification before automated trading

Notes:
	- Market states: PRE (pre-market), OPEN (regular hours), POST (after-hours), CLOSED
	- US market includes NYSE and NASDAQ (09:30-16:00 EST regular hours)
	- Summary data refreshed every 15 minutes during market hours
	- Crypto markets operate 24/7 with state always OPEN
	- Rates market includes bond yields and treasury data
	- Commodity markets follow futures exchange hours

See Also:
	- ticker.py: Individual symbol status and trading hours
	- calendars.py: Market holidays and special events
	- multi.py: Batch market data for multiple symbols
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import yfinance as yf
from utils import output_json, safe_run

MARKETS = ["us", "gb", "asia", "europe", "rates", "commodities", "currencies", "crypto"]


@safe_run
def cmd_status(args):
	market = yf.Market(args.market)
	output_json(market.status)


@safe_run
def cmd_summary(args):
	market = yf.Market(args.market)
	output_json(market.summary)


def main():
	parser = argparse.ArgumentParser(description="yfinance Market data")
	sub = parser.add_subparsers(dest="command", required=True)

	p_status = sub.add_parser("status", help="Get market status")
	p_status.add_argument("market", choices=MARKETS, help="Market identifier")
	p_status.set_defaults(func=cmd_status)

	p_summary = sub.add_parser("summary", help="Get market summary")
	p_summary.add_argument("market", choices=MARKETS, help="Market identifier")
	p_summary.set_defaults(func=cmd_summary)

	args = parser.parse_args()
	args.func(args)


if __name__ == "__main__":
	main()
