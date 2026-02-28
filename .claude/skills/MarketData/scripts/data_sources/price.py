#!/usr/bin/env python3
"""Price data retrieval: history, download, and quote.

Retrieve historical OHLCV (Open, High, Low, Close, Volume) data and current quote information
for stocks, ETFs, indices, and other financial instruments via Yahoo Finance API.

Commands:
	history: Retrieve historical price data for a single ticker
	download: Batch download historical data for multiple tickers
	quote: Get current quote and fast info for real-time price data

Args:
	symbol (str): Ticker symbol (e.g., "AAPL", "SPY", "MSFT")
	--period (str): Data period (default: "1y"). Options: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max
	--interval (str): Data interval (default: "1d"). Options: 1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo
	--start (str): Start date (YYYY-MM-DD) for custom date range
	--end (str): End date (YYYY-MM-DD) for custom date range
	--prepost (flag): Include pre-market and post-market data
	--actions (flag): Include dividends and stock splits in history
	--auto-adjust (flag): Automatically adjust all OHLC data
	--repair (flag): Repair missing data using Yahoo Finance's repair algorithm
	--group-by (str): Group multi-ticker data by 'ticker' or 'column' (download only)

Returns:
	dict: {
		"Date": str,           # Trading date (YYYY-MM-DD)
		"Open": float,         # Opening price
		"High": float,         # Highest price during period
		"Low": float,          # Lowest price during period
		"Close": float,        # Closing price
		"Volume": int,         # Trading volume
		"Dividends": float,    # Dividend amount (if --actions enabled)
		"Stock Splits": float  # Split ratio (if --actions enabled)
	}

Example:
	>>> python price.py history AAPL --period 1mo --interval 1d
	{
		"2026-01-06": {"Open": 175.23, "High": 176.50, "Low": 174.80, "Close": 176.12, "Volume": 52341000},
		"2026-01-07": {"Open": 176.50, "High": 177.25, "Low": 175.90, "Close": 176.85, "Volume": 48932000}
	}

	>>> python price.py download AAPL MSFT GOOGL --period 5d --interval 1d
	{
		"AAPL": {"2026-01-06": {"Open": 175.23, "Close": 176.12}},
		"MSFT": {"2026-01-06": {"Open": 389.45, "Close": 392.10}},
		"GOOGL": {"2026-01-06": {"Open": 142.30, "Close": 143.55}}
	}

	>>> python price.py quote SPY
	{
		"symbol": "SPY",
		"last_price": 475.50,
		"last_volume": 78234000,
		"market_cap": 445000000000,
		"day_high": 476.80,
		"day_low": 474.20,
		"open": 475.00,
		"previous_close": 474.90,
		"year_high": 480.50,
		"year_low": 410.30
	}

Use Cases:
	- Historical price analysis for backtesting trading strategies
	- Batch data collection for portfolio analysis across multiple tickers
	- Real-time price monitoring using quote command
	- Technical analysis requiring OHLCV data
	- Data pipeline integration for quantitative research
	- Corporate action tracking with dividends and splits

Notes:
	- Yahoo Finance API has rate limits: ~2000 requests/hour per IP
	- Intraday intervals (1m, 5m) limited to last 7-60 days depending on interval
	- Data freshness: 15-minute delay for real-time quotes (varies by exchange)
	- Market hours: Data availability depends on exchange trading hours
	- Use --repair flag to fix missing or corrupt data points
	- Pre/post-market data (--prepost) only available for US equities
	- Auto-adjust (--auto-adjust) applies dividend and split adjustments to OHLC

See Also:
	- info.py: Company metadata and ticker information
	- actions.py: Detailed dividend and split history with dates
	- financials.py: Fundamental data for valuation analysis
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import yfinance as yf
from utils import output_json, safe_run


@safe_run
def cmd_history(args):
	ticker = yf.Ticker(args.symbol)
	kwargs = {"period": args.period, "interval": args.interval}
	if args.start:
		kwargs["start"] = args.start
	if args.end:
		kwargs["end"] = args.end
	if args.prepost:
		kwargs["prepost"] = True
	if args.actions:
		kwargs["actions"] = True
	if args.auto_adjust:
		kwargs["auto_adjust"] = True
	if args.repair:
		kwargs["repair"] = True
	data = ticker.history(**kwargs)
	output_json(data)


@safe_run
def cmd_download(args):
	kwargs = {"period": args.period, "interval": args.interval}
	if args.start:
		kwargs["start"] = args.start
	if args.end:
		kwargs["end"] = args.end
	if args.group_by:
		kwargs["group_by"] = args.group_by
	data = yf.download(args.symbols, **kwargs)
	output_json(data)


@safe_run
def cmd_quote(args):
	ticker = yf.Ticker(args.symbol)
	fi = ticker.fast_info
	result = {}
	for attr in dir(fi):
		if attr.startswith("_"):
			continue
		try:
			val = getattr(fi, attr)
			if not callable(val):
				result[attr] = val
		except Exception:
			pass
	output_json(result)


def main():
	parser = argparse.ArgumentParser(description="Price data retrieval")
	sub = parser.add_subparsers(dest="command", required=True)

	# history
	sp = sub.add_parser("history", help="Get price history for a symbol")
	sp.add_argument("symbol")
	sp.add_argument("--period", default="1y")
	sp.add_argument("--interval", default="1d")
	sp.add_argument("--start", default=None)
	sp.add_argument("--end", default=None)
	sp.add_argument("--prepost", action="store_true")
	sp.add_argument("--actions", action="store_true")
	sp.add_argument("--auto-adjust", action="store_true")
	sp.add_argument("--repair", action="store_true")
	sp.set_defaults(func=cmd_history)

	# download
	sp = sub.add_parser("download", help="Download price data for multiple symbols")
	sp.add_argument("symbols", nargs="+")
	sp.add_argument("--period", default="1y")
	sp.add_argument("--interval", default="1d")
	sp.add_argument("--start", default=None)
	sp.add_argument("--end", default=None)
	sp.add_argument("--group-by", default="ticker")
	sp.set_defaults(func=cmd_download)

	# quote
	sp = sub.add_parser("quote", help="Get current quote info")
	sp.add_argument("symbol")
	sp.set_defaults(func=cmd_quote)

	args = parser.parse_args()
	args.func(args)


if __name__ == "__main__":
	main()
