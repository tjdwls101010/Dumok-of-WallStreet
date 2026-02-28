#!/usr/bin/env python3
"""Corporate actions, earnings dates, calendar, and news.

Retrieve dividend payments, stock splits, capital gains distributions, earnings data,
earnings calendar, corporate event calendar, and company news via Yahoo Finance API.

Commands:
	get-dividends: Historical dividend payments with ex-dates
	get-splits: Stock split history and ratios
	get-capital-gains: Capital gains distributions (mutual funds/ETFs)
	get-actions: Combined dividends and splits
	get-earnings: Annual or quarterly earnings summary
	get-earnings-dates: Future and past earnings announcement dates
	get-calendar: Upcoming earnings, ex-dividend, and other corporate events
	get-news: Company news and press releases

Args:
	symbol (str): Ticker symbol (e.g., "AAPL", "MSFT", "SPY")
	--start (str): Start date for dividend filter (YYYY-MM-DD)
	--end (str): End date for dividend filter (YYYY-MM-DD)
	--freq (str): Earnings frequency (yearly/quarterly, default: yearly)
	--limit (int): Number of earnings dates to retrieve (default: 12)
	--count (int): Number of news articles (default: 10)
	--tab (str): News tab filter (news/all/press_releases, default: news)

Returns:
	dict: {
		"Date": str,              # Action date or announcement date
		"Dividends": float,       # Dividend amount per share
		"Stock Splits": str,      # Split ratio (e.g., "2:1")
		"Capital Gains": float,   # Capital gains per share
		"Revenue": float,         # Earnings revenue (for get-earnings)
		"Earnings": float,        # Earnings per share
		"title": str,             # News headline (for get-news)
		"publisher": str,         # News source
		"link": str               # News article URL
	}

Example:
	>>> python actions.py get-dividends AAPL --start 2024-01-01 --end 2024-12-31
	{
		"2024-02-09": {"Dividends": 0.24},
		"2024-05-10": {"Dividends": 0.24},
		"2024-08-12": {"Dividends": 0.25},
		"2024-11-08": {"Dividends": 0.25}
	}

	>>> python actions.py get-splits AAPL
	{
		"2014-06-09": {"Stock Splits": "7:1"},
		"2020-08-31": {"Stock Splits": "4:1"}
	}

	>>> python actions.py get-earnings MSFT --freq quarterly
	{
		"2025Q4": {"Revenue": 62026000000, "Earnings": 3.13},
		"2025Q3": {"Revenue": 65585000000, "Earnings": 3.30},
		"2025Q2": {"Revenue": 64727000000, "Earnings": 2.99}
	}

	>>> python actions.py get-earnings-dates AAPL --limit 4
	{
		"2026-01-29": {"Earnings Date": "2026-01-29", "EPS Estimate": 2.35},
		"2025-10-31": {"Earnings Date": "2025-10-31", "EPS Estimate": 1.59}
	}

	>>> python actions.py get-calendar SPY
	{
		"Earnings Date": "N/A",
		"Ex-Dividend Date": "2026-03-21",
		"Dividend Date": "2026-04-30"
	}

	>>> python actions.py get-news AAPL --count 5
	[
		{
			"title": "Apple announces new product line",
			"publisher": "Reuters",
			"link": "https://...",
			"providerPublishTime": 1704153600
		}
	]

Use Cases:
	- Dividend tracking for income portfolio management
	- Ex-dividend date calendar for dividend capture strategies
	- Earnings calendar integration for event-driven trading
	- News sentiment analysis and event detection
	- Corporate action adjustments for backtesting
	- Stock split history for price normalization

Notes:
	- Yahoo Finance API rate limits: ~2000 requests/hour
	- Dividend dates are ex-dividend dates (not payment dates)
	- Earnings dates may be estimates subject to change
	- News articles limited to recent 30-60 days
	- get-calendar returns next upcoming events only
	- Capital gains primarily applicable to mutual funds and ETFs
	- Earnings estimates may be null if not available

See Also:
	- price.py: Historical price data (use with --actions flag)
	- financials.py: Detailed earnings statements and metrics
	- info.py: Company metadata and business information
	- funds.py: Fund-specific distribution data
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import pandas as pd
import yfinance as yf
from utils import output_json, safe_run


@safe_run
def cmd_dividends(args):
	data = yf.Ticker(args.symbol).get_dividends()
	if args.start:
		start = pd.Timestamp(args.start)
		if data.index.tz is not None:
			start = start.tz_localize(data.index.tz)
		data = data[data.index >= start]
	if args.end:
		end = pd.Timestamp(args.end)
		if data.index.tz is not None:
			end = end.tz_localize(data.index.tz)
		data = data[data.index <= end]
	output_json(data)


@safe_run
def cmd_splits(args):
	output_json(yf.Ticker(args.symbol).get_splits())


@safe_run
def cmd_capital_gains(args):
	output_json(yf.Ticker(args.symbol).get_capital_gains())


@safe_run
def cmd_actions(args):
	output_json(yf.Ticker(args.symbol).get_actions())


@safe_run
def cmd_earnings(args):
	output_json(yf.Ticker(args.symbol).get_earnings(freq=args.freq))


@safe_run
def cmd_earnings_dates(args):
	output_json(yf.Ticker(args.symbol).get_earnings_dates(limit=args.limit))


@safe_run
def cmd_calendar(args):
	output_json(yf.Ticker(args.symbol).get_calendar())


@safe_run
def cmd_news(args):
	output_json(yf.Ticker(args.symbol).get_news(count=args.count, tab=args.tab))


def main():
	parser = argparse.ArgumentParser(description="Corporate actions, earnings, and news")
	sub = parser.add_subparsers(dest="command", required=True)

	# get-dividends
	sp = sub.add_parser("get-dividends")
	sp.add_argument("symbol")
	sp.add_argument("--start", default=None, help="Start date (YYYY-MM-DD)")
	sp.add_argument("--end", default=None, help="End date (YYYY-MM-DD)")
	sp.set_defaults(func=cmd_dividends)

	# get-splits
	sp = sub.add_parser("get-splits")
	sp.add_argument("symbol")
	sp.set_defaults(func=cmd_splits)

	# get-capital-gains
	sp = sub.add_parser("get-capital-gains")
	sp.add_argument("symbol")
	sp.set_defaults(func=cmd_capital_gains)

	# get-actions
	sp = sub.add_parser("get-actions")
	sp.add_argument("symbol")
	sp.set_defaults(func=cmd_actions)

	# get-earnings
	sp = sub.add_parser("get-earnings")
	sp.add_argument("symbol")
	sp.add_argument("--freq", choices=["yearly", "quarterly"], default="yearly")
	sp.set_defaults(func=cmd_earnings)

	# get-earnings-dates
	sp = sub.add_parser("get-earnings-dates")
	sp.add_argument("symbol")
	sp.add_argument("--limit", type=int, default=12)
	sp.set_defaults(func=cmd_earnings_dates)

	# get-calendar
	sp = sub.add_parser("get-calendar")
	sp.add_argument("symbol")
	sp.set_defaults(func=cmd_calendar)

	# get-news
	sp = sub.add_parser("get-news")
	sp.add_argument("symbol")
	sp.add_argument("--count", type=int, default=10)
	sp.add_argument("--tab", choices=["news", "all", "press_releases"], default="news")
	sp.set_defaults(func=cmd_news)

	args = parser.parse_args()
	args.func(args)


if __name__ == "__main__":
	main()
