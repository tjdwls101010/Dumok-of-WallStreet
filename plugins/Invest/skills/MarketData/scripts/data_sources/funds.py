#!/usr/bin/env python3
"""YFinance funds data wrapper.

Retrieve comprehensive fund and ETF data including holdings, asset allocation, sector weightings,
bond characteristics, and operational details via Yahoo Finance API.

Commands:
	get-funds-data: Complete fund data in single response
	description: Fund description and investment objective
	fund-overview: Management company, inception date, category
	fund-operations: Expense ratios, minimum investments, legal structure
	asset-classes: Asset allocation breakdown (stocks, bonds, cash)
	top-holdings: Top 10-25 holdings with weights
	equity-holdings: Equity portfolio characteristics (P/E, P/B, median market cap)
	bond-holdings: Bond portfolio characteristics (duration, maturity, yield)
	bond-ratings: Credit quality distribution (AAA, AA, A, BBB, etc.)
	sector-weightings: Sector exposure percentages

Args:
	symbol (str): Fund/ETF ticker symbol (e.g., "SPY", "AGG", "VTI")

Returns:
	dict: {
		"description": str,                        # Investment objective
		"fund_overview": {
			"fundFamily": str,                     # Management company
			"legalType": str,                      # Legal structure (ETF, Mutual Fund)
			"category": str,                       # Morningstar category
			"totalAssets": int,                    # Assets under management
			"inceptionDate": str                   # Fund launch date
		},
		"fund_operations": {
			"expenseRatio": float,                 # Annual expense ratio (%)
			"minInitialInvestment": int,           # Minimum investment
			"minSubsequentInvestment": int,        # Minimum additional investment
			"projectedYield": float                # Estimated yield (%)
		},
		"asset_classes": {
			"stocks": float,                       # Stock allocation (%)
			"bonds": float,                        # Bond allocation (%)
			"cash": float,                         # Cash allocation (%)
			"other": float                         # Alternative allocation (%)
		},
		"top_holdings": {
			"symbol": str,                         # Holding ticker
			"holdingName": str,                    # Company name
			"holdingPercent": float                # Portfolio weight (%)
		},
		"equity_holdings": {
			"priceToEarnings": float,              # Weighted average P/E ratio
			"priceToBook": float,                  # Weighted average P/B ratio
			"medianMarketCap": int,                # Median market cap
			"threeYearEarningsGrowth": float       # 3-year earnings growth (%)
		},
		"bond_holdings": {
			"duration": float,                     # Effective duration (years)
			"maturity": float,                     # Average maturity (years)
			"creditQuality": float,                # Average credit rating
			"yieldToMaturity": float               # Yield to maturity (%)
		},
		"bond_ratings": {
			"AAA": float,                          # AAA-rated bonds (%)
			"AA": float,                           # AA-rated bonds (%)
			"BBB": float                           # BBB-rated bonds (%)
		},
		"sector_weightings": {
			"realestate": float,                   # Real Estate (%)
			"consumer_cyclical": float,            # Consumer Cyclical (%)
			"basic_materials": float,              # Basic Materials (%)
			"technology": float,                   # Technology (%)
			"financial_services": float            # Financial Services (%)
		}
	}

Example:
	>>> python funds.py get-funds-data SPY
	{
		"description": "The investment seeks to track the S&P 500 Index...",
		"fund_overview": {
			"fundFamily": "State Street Global Advisors",
			"legalType": "Exchange Traded Fund",
			"category": "Large Blend",
			"totalAssets": 445000000000,
			"inceptionDate": "1993-01-22"
		},
		"fund_operations": {
			"expenseRatio": 0.0945,
			"projectedYield": 1.35
		},
		"asset_classes": {
			"stocks": 99.8,
			"cash": 0.2
		}
	}

	>>> python funds.py top-holdings AGG
	{
		"holdings": [
			{"holdingName": "United States Treasury Note", "holdingPercent": 2.35},
			{"holdingName": "United States Treasury Bond", "holdingPercent": 1.89}
		]
	}

	>>> python funds.py equity-holdings VTI
	{
		"priceToEarnings": 24.5,
		"priceToBook": 4.2,
		"medianMarketCap": 52000000000,
		"threeYearEarningsGrowth": 12.5
	}

	>>> python funds.py bond-holdings AGG
	{
		"duration": 6.2,
		"maturity": 8.5,
		"yieldToMaturity": 4.35,
		"creditQuality": 2.1
	}

Use Cases:
	- ETF and mutual fund research for portfolio construction
	- Asset allocation analysis and rebalancing decisions
	- Expense ratio comparison for cost-efficient investing
	- Holdings overlap detection across multiple funds
	- Sector exposure analysis for diversification
	- Bond portfolio duration and credit quality assessment

Notes:
	- Yahoo Finance API rate limits: ~2000 requests/hour
	- Data only available for funds and ETFs (not individual stocks)
	- Holdings data typically updated monthly or quarterly
	- Some fields may be null for newly launched funds
	- Sector weightings use GICS classification system
	- Bond ratings based on average portfolio credit quality
	- Expense ratios expressed as annual percentage

See Also:
	- info.py: General ticker information including fund metadata
	- actions.py: Capital gains distributions for tax planning
	- price.py: Fund NAV history and performance data
	- holdings.py: Institutional ownership of fund shares
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import yfinance as yf
from utils import error_json, output_json, safe_run


def _get_funds_data(symbol):
	"""Return FundsData object or exit with error if not a fund."""
	ticker = yf.Ticker(symbol)
	fd = ticker.get_funds_data()
	if fd is None:
		error_json(f"{symbol} is not a fund/ETF or has no funds data")
	return fd


@safe_run
def cmd_get_funds_data(args):
	fd = _get_funds_data(args.symbol)
	output_json(
		{
			"description": fd.description,
			"fund_overview": fd.fund_overview,
			"fund_operations": fd.fund_operations,
			"asset_classes": fd.asset_classes,
			"top_holdings": fd.top_holdings,
			"equity_holdings": fd.equity_holdings,
			"bond_holdings": fd.bond_holdings,
			"bond_ratings": fd.bond_ratings,
			"sector_weightings": fd.sector_weightings,
			"quote_type": fd.quote_type if not callable(fd.quote_type) else fd.quote_type(),
		}
	)


@safe_run
def cmd_description(args):
	output_json(_get_funds_data(args.symbol).description)


@safe_run
def cmd_fund_overview(args):
	output_json(_get_funds_data(args.symbol).fund_overview)


@safe_run
def cmd_fund_operations(args):
	output_json(_get_funds_data(args.symbol).fund_operations)


@safe_run
def cmd_asset_classes(args):
	output_json(_get_funds_data(args.symbol).asset_classes)


@safe_run
def cmd_top_holdings(args):
	output_json(_get_funds_data(args.symbol).top_holdings)


@safe_run
def cmd_equity_holdings(args):
	output_json(_get_funds_data(args.symbol).equity_holdings)


@safe_run
def cmd_bond_holdings(args):
	output_json(_get_funds_data(args.symbol).bond_holdings)


@safe_run
def cmd_bond_ratings(args):
	output_json(_get_funds_data(args.symbol).bond_ratings)


@safe_run
def cmd_sector_weightings(args):
	output_json(_get_funds_data(args.symbol).sector_weightings)


def main():
	parser = argparse.ArgumentParser(description="YFinance funds data CLI")
	sub = parser.add_subparsers(dest="command", required=True)

	commands = [
		("get-funds-data", cmd_get_funds_data, "Get all fund data as JSON"),
		("description", cmd_description, "Fund description"),
		("fund-overview", cmd_fund_overview, "Fund overview"),
		("fund-operations", cmd_fund_operations, "Fund operations"),
		("asset-classes", cmd_asset_classes, "Asset class breakdown"),
		("top-holdings", cmd_top_holdings, "Top holdings"),
		("equity-holdings", cmd_equity_holdings, "Equity holdings"),
		("bond-holdings", cmd_bond_holdings, "Bond holdings"),
		("bond-ratings", cmd_bond_ratings, "Bond ratings"),
		("sector-weightings", cmd_sector_weightings, "Sector weightings"),
	]

	for name, func, help_text in commands:
		p = sub.add_parser(name, help=help_text)
		p.add_argument("symbol", help="Fund/ETF ticker symbol")
		p.set_defaults(func=func)

	args = parser.parse_args()
	args.func(args)


if __name__ == "__main__":
	main()
