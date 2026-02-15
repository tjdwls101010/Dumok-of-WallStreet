#!/usr/bin/env python3
"""Financial calendars: earnings, IPO, economic events, and stock splits.

Real-time and upcoming financial event calendars including corporate earnings
reports, initial public offerings, economic data releases, and stock split
announcements with filtering and pagination support.

Args:
	command (str): Calendar type - get-earnings-calendar, get-ipo-info-calendar,
				   get-economic-events-calendar, or get-splits-calendar
	--start (str): Start date filter in YYYY-MM-DD format
	--end (str): End date filter in YYYY-MM-DD format
	--market-cap (float): Minimum market cap filter for earnings (in billions)
	--no-filter-active (flag): Disable most active filter for earnings
	--limit (int): Maximum rows to return (default: 12)
	--offset (int): Rows to skip for pagination (default: 0)

Returns:
	DataFrame: Calendar-specific event data:
		earnings: {
			"ticker": str,             # Stock symbol
			"companyshortname": str,   # Company name
			"startdatetime": str,      # Event datetime (ISO 8601)
			"epsestimate": float,      # Consensus EPS estimate
			"epsactual": float,        # Actual EPS (if reported)
			"epssurprisepct": float    # Surprise percentage
		}
		ipo: {
			"symbol": str,             # IPO ticker
			"companyName": str,        # Company name
			"exchange": str,           # Listing exchange
			"actions": str,            # IPO or Direct Listing
			"shares": int,             # Shares offered
			"priceLow": float,         # Price range low
			"priceHigh": float,        # Price range high
			"expectedDate": str        # Expected listing date
		}
		economic: {
			"ticker": str,             # Economic indicator code
			"description": str,        # Event description
			"gmtTime": str,            # Event time (GMT)
			"actual": float,           # Actual value (if released)
			"consensus": float,        # Consensus forecast
			"previous": float,         # Previous value
			"importance": str          # HIGH, MEDIUM, LOW
		}
		splits: {
			"ticker": str,             # Stock symbol
			"companyshortname": str,   # Company name
			"splitDate": str,          # Split effective date
			"splitRatio": str,         # Ratio (e.g., "2:1", "3:2")
			"splitType": str           # Forward or Reverse
		}

Example:
	>>> python calendars.py get-earnings-calendar --start 2026-02-05 --limit 5
	[
		{
			"ticker": "AAPL",
			"companyshortname": "Apple Inc.",
			"startdatetime": "2026-02-05T16:30:00",
			"epsestimate": 2.15,
			"epsactual": 2.23,
			"epssurprisepct": 3.72
		}
	]

	>>> python calendars.py get-ipo-info-calendar --start 2026-02-01 --end 2026-02-28
	[
		{
			"symbol": "NEWCO",
			"companyName": "New Company Inc.",
			"priceLow": 18.00,
			"priceHigh": 20.00,
			"expectedDate": "2026-02-15"
		}
	]

	>>> python calendars.py get-economic-events-calendar --limit 10
	[
		{
			"ticker": "UNEMPLOYMENT",
			"description": "U.S. Unemployment Rate",
			"actual": 3.7,
			"consensus": 3.8,
			"importance": "HIGH"
		}
	]

Use Cases:
	- Earnings season tracking for volatility trading strategies
	- Pre-earnings position adjustment using consensus estimates
	- IPO calendar monitoring for allocation opportunities
	- Economic event calendar for macro-driven trading decisions
	- Stock split tracking for corporate action adjustments

Notes:
	- Earnings calendar updated in real-time during market hours
	- Market cap filter applies only to earnings (removes small-cap by default)
	- IPO data includes expected pricing and share count (subject to change)
	- Economic events sorted by importance (HIGH > MEDIUM > LOW)
	- Stock splits include forward (2:1) and reverse (1:2) splits
	- Pagination via --limit and --offset for large result sets
	- Default date range is next 7 days if no start/end specified

See Also:
	- ticker.py: Company-specific earnings history and guidance
	- market.py: Market-wide status during earnings releases
	- news.py: Event-driven news correlation with calendar dates
"""

import argparse
import os
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import yfinance as yf
from utils import output_json, safe_run


def _apply_slice(data, args):
	"""Apply --limit and --offset slicing to DataFrame results."""
	if isinstance(data, pd.DataFrame) and not data.empty:
		offset = args.offset
		limit = args.limit
		data = data.iloc[offset : offset + limit]
	return data


def _add_pagination(parser):
	"""Add --limit and --offset arguments to a subparser."""
	parser.add_argument("--limit", type=int, default=12, help="Max rows to return")
	parser.add_argument("--offset", type=int, default=0, help="Rows to skip")


def _add_date_range(parser):
	"""Add --start and --end date arguments to a subparser."""
	parser.add_argument("--start", default=None, help="Start date (YYYY-MM-DD)")
	parser.add_argument("--end", default=None, help="End date (YYYY-MM-DD)")


@safe_run
def cmd_earnings(args):
	kwargs = {}
	if args.start:
		kwargs["start"] = args.start
	if args.end:
		kwargs["end"] = args.end
	if args.market_cap is not None:
		kwargs["market_cap"] = args.market_cap
	kwargs["filter_most_active"] = not args.no_filter_active
	result = yf.Calendars().get_earnings_calendar(**kwargs)
	output_json(_apply_slice(result, args))


@safe_run
def cmd_ipo(args):
	kwargs = {}
	if args.start:
		kwargs["start"] = args.start
	if args.end:
		kwargs["end"] = args.end
	result = yf.Calendars().get_ipo_info_calendar(**kwargs)
	output_json(_apply_slice(result, args))


@safe_run
def cmd_economic(args):
	kwargs = {}
	if args.start:
		kwargs["start"] = args.start
	if args.end:
		kwargs["end"] = args.end
	result = yf.Calendars().get_economic_events_calendar(**kwargs)
	output_json(_apply_slice(result, args))


@safe_run
def cmd_splits(args):
	kwargs = {}
	if args.start:
		kwargs["start"] = args.start
	if args.end:
		kwargs["end"] = args.end
	result = yf.Calendars().get_splits_calendar(**kwargs)
	output_json(_apply_slice(result, args))


def main():
	parser = argparse.ArgumentParser(description="yfinance Calendars data")
	sub = parser.add_subparsers(dest="command", required=True)

	p_earn = sub.add_parser("get-earnings-calendar", help="Earnings calendar")
	_add_date_range(p_earn)
	p_earn.add_argument("--market-cap", type=float, default=None, help="Min market cap filter")
	p_earn.add_argument("--no-filter-active", action="store_true", help="Disable active filter")
	_add_pagination(p_earn)
	p_earn.set_defaults(func=cmd_earnings)

	p_ipo = sub.add_parser("get-ipo-info-calendar", help="IPO info calendar")
	_add_date_range(p_ipo)
	_add_pagination(p_ipo)
	p_ipo.set_defaults(func=cmd_ipo)

	p_econ = sub.add_parser("get-economic-events-calendar", help="Economic events calendar")
	_add_date_range(p_econ)
	_add_pagination(p_econ)
	p_econ.set_defaults(func=cmd_economic)

	p_splits = sub.add_parser("get-splits-calendar", help="Splits calendar")
	_add_date_range(p_splits)
	_add_pagination(p_splits)
	p_splits.set_defaults(func=cmd_splits)

	args = parser.parse_args()
	args.func(args)


if __name__ == "__main__":
	main()
