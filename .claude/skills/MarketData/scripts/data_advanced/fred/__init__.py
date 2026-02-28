#!/usr/bin/env python3
"""FRED data access - CLI dispatcher."""

import argparse
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# Try relative imports first, fall back to absolute imports
try:
	from .inflation import cmd_breakeven_inflation, cmd_cpi, cmd_michigan, cmd_pce
	from .policy import cmd_credit_spreads, cmd_policy, cmd_tga
	from .rates import (
		cmd_fed_funds,
		cmd_international_yield,
		cmd_mortgage,
		cmd_sofr,
		cmd_tips,
		cmd_yield_curve,
		cmd_yield_spread,
	)
	from .series import cmd_series
except ImportError:
	from data_advanced.fred.inflation import cmd_breakeven_inflation, cmd_cpi, cmd_michigan, cmd_pce
	from data_advanced.fred.policy import cmd_credit_spreads, cmd_policy, cmd_tga
	from data_advanced.fred.rates import (
		cmd_fed_funds,
		cmd_international_yield,
		cmd_mortgage,
		cmd_sofr,
		cmd_tips,
		cmd_yield_curve,
		cmd_yield_spread,
	)
	from data_advanced.fred.series import cmd_series


def add_common_args(parser):
	"""Add common arguments to a subparser."""
	parser.add_argument("--start-date", default=None, help="Start date (YYYY-MM-DD format)")
	parser.add_argument("--end-date", default=None, help="End date (YYYY-MM-DD format)")
	parser.add_argument("--limit", type=int, default=None, help="Number of observations to return (most recent)")


def main():
	"""Main CLI dispatcher."""
	parser = argparse.ArgumentParser(description="FRED economic data")
	subparsers = parser.add_subparsers(dest="command", help="Available commands")

	# Rates commands
	sp_fed_funds = subparsers.add_parser("fed-funds", help="Federal Funds Rate")
	sp_fed_funds.add_argument(
		"--series-type",
		default="all",
		choices=["all", "effective_rate", "target_upper", "target_lower", "monthly_avg"],
		help="Type of fed funds data",
	)
	add_common_args(sp_fed_funds)

	sp_yield = subparsers.add_parser("yield-curve", help="Treasury Yield Curve")
	sp_yield.add_argument(
		"--maturities", default=None, help="Comma-separated maturities (1m,3m,6m,1y,2y,3y,5y,7y,10y,20y,30y)"
	)
	add_common_args(sp_yield)

	sp_sofr = subparsers.add_parser("sofr", help="Secured Overnight Financing Rate")
	sp_sofr.add_argument(
		"--series-type",
		default="all",
		choices=["all", "rate", "avg_30d", "avg_90d", "avg_180d", "index"],
		help="Type of SOFR data",
	)
	add_common_args(sp_sofr)

	sp_tips = subparsers.add_parser("tips", help="TIPS yields")
	sp_tips.add_argument(
		"--maturity", default="all", choices=["all", "5y", "7y", "10y", "20y", "30y"], help="TIPS maturity"
	)
	add_common_args(sp_tips)

	sp_mortgage = subparsers.add_parser("mortgage", help="Mortgage rates")
	sp_mortgage.add_argument(
		"--rate-type", default="all", choices=["all", "30y_fixed", "15y_fixed", "5y_arm"], help="Type of mortgage rate"
	)
	add_common_args(sp_mortgage)

	sp_intl_yield = subparsers.add_parser("international-yield", help="International Government Bond Yields")
	sp_intl_yield.add_argument("--country", default="korea", choices=["korea"], help="Country")
	sp_intl_yield.add_argument("--maturity", default="10y", choices=["10y", "3m", "all"], help="Maturity")
	add_common_args(sp_intl_yield)

	sp_yield_spread = subparsers.add_parser("yield-spread", help="Yield spread between countries/maturities")
	sp_yield_spread.add_argument("--country1", default="us", choices=["us", "korea"], help="First country")
	sp_yield_spread.add_argument("--maturity1", default="10y", choices=["10y", "2y", "3m"], help="First maturity")
	sp_yield_spread.add_argument("--country2", default="korea", choices=["us", "korea"], help="Second country")
	sp_yield_spread.add_argument("--maturity2", default="10y", choices=["10y", "2y", "3m"], help="Second maturity")
	add_common_args(sp_yield_spread)

	# Inflation commands
	sp_cpi = subparsers.add_parser("cpi", help="Consumer Price Index")
	sp_cpi.add_argument(
		"--series-type", default="all", choices=["all", "headline", "core", "headline_yoy"], help="Type of CPI data"
	)
	add_common_args(sp_cpi)

	sp_pce = subparsers.add_parser("pce", help="Personal Consumption Expenditures")
	sp_pce.add_argument(
		"--series-type",
		default="all",
		choices=["all", "headline", "core", "headline_yoy", "core_yoy"],
		help="Type of PCE data",
	)
	add_common_args(sp_pce)

	sp_breakeven = subparsers.add_parser("breakeven-inflation", help="Breakeven Inflation")
	sp_breakeven.add_argument(
		"--maturity", default="all", choices=["all", "5y", "10y", "5y_fwd_5y"], help="Breakeven inflation maturity"
	)
	add_common_args(sp_breakeven)

	sp_michigan = subparsers.add_parser("michigan", help="Michigan Inflation Expectations")
	sp_michigan.add_argument(
		"--indicator",
		default="all",
		choices=["all", "consumer_sentiment", "inflation_expectation", "current_conditions", "expectations"],
		help="Michigan survey indicator",
	)
	add_common_args(sp_michigan)

	# Policy commands
	sp_policy = subparsers.add_parser("policy", help="Fed Policy Rate")
	sp_policy.add_argument(
		"--indicator",
		default="all",
		choices=["all", "fed_balance_sheet", "policy_uncertainty", "tga_balance", "reverse_repo"],
		help="Policy indicator type",
	)
	add_common_args(sp_policy)

	sp_credit = subparsers.add_parser("credit-spreads", help="Credit Spreads")
	sp_credit.add_argument(
		"--spread-type",
		default="all",
		choices=["all", "hy_spread", "ig_spread", "bbb_spread"],
		help="Type of credit spread",
	)
	add_common_args(sp_credit)

	sp_tga = subparsers.add_parser("tga", help="Treasury General Account (TGA) balance with liquidity analysis")
	sp_tga.add_argument(
		"--series-type",
		default="weekly_avg",
		choices=["weekly_avg", "wednesday", "daily"],
		help="TGA series type",
	)
	add_common_args(sp_tga)

	# Series command
	sp_series = subparsers.add_parser("series", help="Generic FRED series")
	sp_series.add_argument(
		"--series-id", required=True, help="FRED series ID(s), comma-separated (e.g., GDP,UNRATE,GDPC1)"
	)
	add_common_args(sp_series)

	args = parser.parse_args()

	# Dispatch
	command_map = {
		"fed-funds": cmd_fed_funds,
		"yield-curve": cmd_yield_curve,
		"sofr": cmd_sofr,
		"tips": cmd_tips,
		"mortgage": cmd_mortgage,
		"international-yield": cmd_international_yield,
		"yield-spread": cmd_yield_spread,
		"cpi": cmd_cpi,
		"pce": cmd_pce,
		"breakeven-inflation": cmd_breakeven_inflation,
		"michigan": cmd_michigan,
		"policy": cmd_policy,
		"credit-spreads": cmd_credit_spreads,
		"tga": cmd_tga,
		"series": cmd_series,
	}

	if args.command in command_map:
		command_map[args.command](args)
	else:
		parser.print_help()
		sys.exit(1)


if __name__ == "__main__":
	main()
