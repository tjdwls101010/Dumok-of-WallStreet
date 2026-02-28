#!/usr/bin/env python3
"""Search, screening, sector and industry data via yfinance.

Comprehensive symbol search, lookup, screening, and sector/industry analysis
using Yahoo Finance API. Supports fuzzy search, custom screening queries,
and detailed sector/industry breakdowns.

Args:
	command (str): Operation to perform - search, lookup, screen, screen-custom, sector, or industry
	query (str): Search query string for search and lookup commands
	preset (str): Screening preset name (e.g., most_actives, day_gainers) for screen command
	query_json (str): Custom JSON query for screen-custom command with type and operators
	key (str): Sector or industry key for sector/industry commands

Returns:
	dict: Command-specific results:
		search: {
			"quotes": list,       # Matching quote results
			"news": list,         # Related news articles
			"lists": list,        # Curated lists
			"research": list,     # Research reports (if enabled)
			"nav": list          # Navigation links (if enabled)
		}
		lookup: list of matching symbols filtered by type
		screen: DataFrame of screened securities
		sector/industry: {
			"name": str,                    # Sector/industry name
			"symbol": str,                  # Identifier
			"overview": dict,               # Market summary
			"top_companies": list,          # Leading companies
			"research_reports": list,       # Available reports
			"top_etfs": list,              # Related ETFs
			"top_mutual_funds": list       # Related funds
		}

Example:
	>>> python search.py search AAPL --quotes-count 5 --news-count 3
	{
		"quotes": [{"symbol": "AAPL", "shortname": "Apple Inc.", ...}],
		"news": [{"title": "Apple announces...", ...}]
	}

	>>> python search.py lookup tech --type stock --count 10
	[{"symbol": "AAPL", "name": "Apple Inc.", ...}]

	>>> python search.py screen most_actives
	{"count": 25, "quotes": [...], ...}

	>>> python search.py sector technology
	{"name": "Technology", "top_companies": [...], ...}

Use Cases:
	- Multi-symbol discovery across asset classes (stocks, ETFs, funds, futures)
	- Custom screening with complex criteria using EquityQuery/FundQuery
	- Sector rotation analysis with top performers and ETF tracking
	- Industry-specific research and company comparison
	- Fuzzy search for approximate ticker matching

Notes:
	- Search results limited by quotes_count (default 8) and news_count (default 8)
	- Lookup supports filtering by type: stock, etf, mutualfund, index, future, currency, cryptocurrency
	- Screen presets include: most_actives, day_gainers, day_losers, growth_technology_stocks
	- Custom screening requires JSON query with nested operator/operand structure
	- Sector keys available: technology, healthcare, financial-services, consumer-cyclical, etc.
	- Industry data includes performance metrics and growth rankings

See Also:
	- ticker.py: Single-symbol detailed information and metadata
	- multi.py: Batch operations on multiple symbols
	- market.py: Market-wide status and summary data
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import yfinance as yf
from utils import error_json, output_json, safe_run


@safe_run
def cmd_search(args):
	s = yf.Search(
		args.query,
		max_results=args.quotes_count,
		news_count=args.news_count,
		enable_fuzzy_query=args.enable_fuzzy,
		include_research=args.include_research,
		include_nav_links=args.include_nav,
	)
	output_json(
		{
			"quotes": s.quotes,
			"news": s.news,
			"lists": s.lists,
			"research": s.research,
			"nav": s.nav,
		}
	)


@safe_run
def cmd_lookup(args):
	lk = yf.Lookup(args.query)
	type_map = {
		"all": "get_all",
		"stock": "get_stock",
		"mutualfund": "get_mutualfund",
		"etf": "get_etf",
		"index": "get_index",
		"future": "get_future",
		"currency": "get_currency",
		"cryptocurrency": "get_cryptocurrency",
	}
	method_name = type_map.get(args.type)
	if method_name is None:
		error_json(f"Unknown type: {args.type}")
	method = getattr(lk, method_name)
	output_json(method(count=args.count))


@safe_run
def cmd_screen(args):
	output_json(yf.screen(args.preset))


def _build_query(data, query_cls):
	"""Recursively build EquityQuery/FundQuery from nested dict."""
	operator = data.get("operator")
	operand = data.get("operand")
	if operator and operand:
		sub_queries = [_build_query(op, query_cls) if isinstance(op, dict) else op for op in operand]
		return query_cls(operator, sub_queries)
	return query_cls(**data)


@safe_run
def cmd_screen_custom(args):
	from yfinance import EquityQuery, FundQuery

	data = json.loads(args.query_json)
	query_type = data.pop("type", "equity")
	if query_type == "equity":
		query = _build_query(data, EquityQuery)
	elif query_type == "fund":
		query = _build_query(data, FundQuery)
	else:
		error_json(f"Unknown query type: {query_type}. Use 'equity' or 'fund'.")
	output_json(yf.screen(query))


@safe_run
def cmd_sector(args):
	s = yf.Sector(args.key)
	output_json(
		{
			"name": s.name,
			"symbol": s.symbol,
			"overview": s.overview,
			"top_companies": s.top_companies,
			"research_reports": s.research_reports,
			"top_etfs": s.top_etfs,
			"top_mutual_funds": s.top_mutual_funds,
			"industries": s.industries,
		}
	)


@safe_run
def cmd_industry(args):
	i = yf.Industry(args.key)
	output_json(
		{
			"name": i.name,
			"symbol": i.symbol,
			"overview": i.overview,
			"top_companies": i.top_companies,
			"research_reports": i.research_reports,
			"sector_key": i.sector_key,
			"sector_name": i.sector_name,
			"top_performing_companies": i.top_performing_companies,
			"top_growth_companies": i.top_growth_companies,
		}
	)


def main():
	parser = argparse.ArgumentParser(description="Search and screening via yfinance")
	sub = parser.add_subparsers(dest="command", required=True)

	# search
	p_search = sub.add_parser("search", help="Search quotes and news")
	p_search.add_argument("query")
	p_search.add_argument("--quotes-count", type=int, default=8)
	p_search.add_argument("--news-count", type=int, default=8)
	p_search.add_argument("--enable-fuzzy", action="store_true")
	p_search.add_argument("--include-research", action="store_true")
	p_search.add_argument("--include-nav", action="store_true")
	p_search.set_defaults(func=cmd_search)

	# lookup
	p_lookup = sub.add_parser("lookup", help="Lookup symbols by type")
	p_lookup.add_argument("query")
	p_lookup.add_argument(
		"--type",
		default="all",
		choices=["all", "stock", "mutualfund", "etf", "index", "future", "currency", "cryptocurrency"],
	)
	p_lookup.add_argument("--count", type=int, default=25)
	p_lookup.set_defaults(func=cmd_lookup)

	# screen
	p_screen = sub.add_parser("screen", help="Screen with preset")
	p_screen.add_argument("preset", help="e.g. most_actives, day_gainers")
	p_screen.set_defaults(func=cmd_screen)

	# screen-custom
	p_custom = sub.add_parser("screen-custom", help="Screen with custom query JSON")
	p_custom.add_argument("query_json", help='JSON string with "type" and query operators')
	p_custom.set_defaults(func=cmd_screen_custom)

	# sector
	p_sector = sub.add_parser("sector", help="Sector information")
	p_sector.add_argument("key", help="Sector key")
	p_sector.set_defaults(func=cmd_sector)

	# industry
	p_industry = sub.add_parser("industry", help="Industry information")
	p_industry.add_argument("key", help="Industry key")
	p_industry.set_defaults(func=cmd_industry)

	args = parser.parse_args()
	args.func(args)


if __name__ == "__main__":
	main()
