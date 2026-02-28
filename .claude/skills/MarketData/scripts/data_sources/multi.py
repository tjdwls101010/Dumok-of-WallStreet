#!/usr/bin/env python3
"""Multi-ticker operations: compare, download, and news.

Batch operations for comparing metrics, downloading historical data, and
retrieving news across multiple ticker symbols simultaneously.

Args:
	command (str): Operation - compare, download, or news
	symbols (list): List of ticker symbols to process
	--fields (list): Info fields to compare (compare command)
	--period (str): Historical period for download (default: 1y)
	--interval (str): Data interval (default: 1d)
	--start (str): Start date in YYYY-MM-DD format
	--end (str): End date in YYYY-MM-DD format
	--group-by (str): Group by ticker or column for download output

Returns:
	dict: Command-specific results:
		compare: {
			"AAPL": {"shortName": str, "currentPrice": float, ...},
			"MSFT": {"shortName": str, "currentPrice": float, ...}
		}
		download: DataFrame with multi-index columns (ticker, field) or rows
		news: list of news articles across all tickers sorted by date

Example:
	>>> python multi.py compare AAPL MSFT GOOGL --fields currentPrice marketCap trailingPE
	{
		"AAPL": {"currentPrice": 175.43, "marketCap": 2750000000000, "trailingPE": 28.5},
		"MSFT": {"currentPrice": 380.12, "marketCap": 2820000000000, "trailingPE": 35.2}
	}

	>>> python multi.py download SPY QQQ --period 1mo --interval 1d
	{
		"Date": ["2026-01-06", "2026-01-07", ...],
		"SPY": {"Close": [475.20, 478.30, ...], "Volume": [...]},
		"QQQ": {"Close": [395.50, 398.20, ...], "Volume": [...]}
	}

	>>> python multi.py news AAPL TSLA NVDA
	[
		{
			"title": "Apple announces new AI features",
			"publisher": "Reuters",
			"link": "https://...",
			"providerPublishTime": 1738771200,
			"relatedTickers": ["AAPL"]
		}
	]

Use Cases:
	- Side-by-side fundamental comparison for stock screening
	- Batch historical data download for backtesting strategies
	- Multi-asset correlation analysis using aligned time series
	- Sector performance comparison across top constituents
	- News aggregation for portfolio monitoring and sentiment analysis

Notes:
	- Default comparison fields: shortName, currentPrice, marketCap, trailingPE, forwardPE, dividendYield
	- Download supports date range (start/end) or period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
	- Interval options: 1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo
	- Group by ticker (default): columns = (ticker, field), group by column: columns = field with ticker rows
	- News results include related tickers for cross-symbol filtering
	- Data aligned by date for download command (missing dates handled automatically)

See Also:
	- ticker.py: Single-symbol detailed information
	- search.py: Symbol discovery and screening
	- correlate.py: Statistical correlation analysis for multi-ticker datasets
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import yfinance as yf
from utils import output_json, safe_run

DEFAULT_FIELDS = [
	"shortName",
	"currentPrice",
	"marketCap",
	"trailingPE",
	"forwardPE",
	"dividendYield",
]


@safe_run
def cmd_compare(args):
	symbols = args.symbols
	fields = args.fields or DEFAULT_FIELDS
	tickers = yf.Tickers(" ".join(symbols))
	result = {}
	for sym, ticker in tickers.tickers.items():
		info = ticker.info
		result[sym] = {f: info.get(f) for f in fields}
	output_json(result)


@safe_run
def cmd_download(args):
	kwargs = {
		"tickers": args.symbols,
		"group_by": args.group_by,
	}
	if args.start:
		kwargs["start"] = args.start
		if args.end:
			kwargs["end"] = args.end
	else:
		kwargs["period"] = args.period
	kwargs["interval"] = args.interval

	df = yf.download(**kwargs)
	output_json(df)


@safe_run
def cmd_news(args):
	tickers = yf.Tickers(" ".join(args.symbols))
	output_json(tickers.news())


def main():
	parser = argparse.ArgumentParser(description="Multi-ticker operations")
	sub = parser.add_subparsers(dest="command", required=True)

	# compare
	p_compare = sub.add_parser("compare", help="Compare ticker info fields")
	p_compare.add_argument("symbols", nargs="+", help="Ticker symbols")
	p_compare.add_argument("--fields", nargs="+", default=None, help="Info fields to extract")
	p_compare.set_defaults(func=cmd_compare)

	# download
	p_download = sub.add_parser("download", help="Download historical data")
	p_download.add_argument("symbols", nargs="+", help="Ticker symbols")
	p_download.add_argument("--period", default="1y", help="Period (default: 1y)")
	p_download.add_argument("--interval", default="1d", help="Interval (default: 1d)")
	p_download.add_argument("--start", default=None, help="Start date (YYYY-MM-DD)")
	p_download.add_argument("--end", default=None, help="End date (YYYY-MM-DD)")
	p_download.add_argument(
		"--group-by",
		default="ticker",
		choices=["ticker", "column"],
		help="Group by (default: ticker)",
	)
	p_download.set_defaults(func=cmd_download)

	# news
	p_news = sub.add_parser("news", help="Get news for multiple tickers")
	p_news.add_argument("symbols", nargs="+", help="Ticker symbols")
	p_news.set_defaults(func=cmd_news)

	args = parser.parse_args()
	args.func(args)


if __name__ == "__main__":
	main()
