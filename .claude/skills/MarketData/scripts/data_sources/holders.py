#!/usr/bin/env python3
"""Holder and insider transaction data.

Retrieve institutional ownership, mutual fund holdings, insider transactions, and major
shareholder information for ownership analysis and insider activity tracking.
Holder data from Yahoo Finance API; insider transactions from Finviz.

Commands:
	get-major-holders: Major holder breakdown (percentage institutional/insider/public)
	get-institutional-holders: Top institutional investors with share counts
	get-mutualfund-holders: Top mutual fund holders with positions
	get-insider-transactions: Insider buying and selling activity (via Finviz)
	get-insider-purchases: Insider purchase transactions only
	get-insider-roster-holders: Current insider ownership roster

Args:
	symbol (str): Ticker symbol (e.g., "AAPL", "MSFT", "NVDA")

Returns:
	get-insider-transactions returns list of dicts:
	[
		{
			"date": str,              # Transaction date (YYYY-MM-DD)
			"insider": str,           # Insider name
			"relationship": str,      # Role/title (e.g., "Chief Executive Officer", "Director")
			"transaction": str,       # Transaction type: Sale, Buy, Option Exercise, Proposed Sale
			"cost": float,            # Price per share
			"shares": int,            # Number of shares transacted
			"value": int,             # Total transaction value in USD
			"shares_total": int|null  # Remaining shares after transaction (null if unavailable)
		}
	]

Example:
	>>> python holders.py get-insider-transactions NVDA
	[
		{
			"date": "2026-03-10",
			"insider": "Puri Ajay K",
			"relationship": "EVP, Worldwide Field Ops",
			"transaction": "Sale",
			"cost": 182.52,
			"shares": 300000,
			"value": 54756044,
			"shares_total": 3318547
		}
	]

Use Cases:
	- Institutional ownership tracking for sentiment analysis
	- Smart money following: Identify major fund accumulation/distribution
	- Insider buying as bullish signal (skin in the game)
	- Insider selling pattern detection (potential red flag)
	- Ownership concentration analysis for voting rights

Notes:
	- Insider transactions sourced from Finviz (scrapes SEC Form 4 filings)
	- Returns ~100 most recent transactions (~12 months)
	- Transaction types: Sale, Buy, Option Exercise, Proposed Sale
	- Holder data (institutional, mutual fund, major) from Yahoo Finance API
	- Institutional holdings from quarterly 13F filings (45-day lag)

See Also:
	- info.py: Company metadata including shares outstanding
	- actions.py: Insider purchases may precede earnings announcements
	- price.py: Stock price for position value calculation
	- funds.py: Fund holdings when analyzing ETF/mutual fund ownership
"""

import argparse
import os
import re
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import yfinance as yf
from finviz import get_insider
from utils import output_json, safe_run


@safe_run
def cmd_major_holders(args):
	output_json(yf.Ticker(args.symbol).get_major_holders())


@safe_run
def cmd_institutional_holders(args):
	output_json(yf.Ticker(args.symbol).get_institutional_holders())


@safe_run
def cmd_mutualfund_holders(args):
	output_json(yf.Ticker(args.symbol).get_mutualfund_holders())


def _parse_int(s):
	"""Parse comma-separated integer string, return None for empty/invalid."""
	if not s or not s.strip():
		return None
	try:
		return int(s.replace(",", ""))
	except (ValueError, TypeError):
		return None


def _parse_float(s):
	"""Parse float string, return None for empty/invalid."""
	if not s or not s.strip():
		return None
	try:
		return float(s.replace(",", ""))
	except (ValueError, TypeError):
		return None


def _parse_finviz_date(s):
	"""Parse finviz date format (e.g., "Mar 10 '26") to ISO format."""
	if not s:
		return None
	try:
		dt = datetime.strptime(s.strip(), "%b %d '%y")
		return dt.strftime("%Y-%m-%d")
	except ValueError:
		return s


@safe_run
def cmd_insider_transactions(args):
	raw = get_insider(args.symbol)
	results = []
	for record in raw:
		results.append({
			"date": _parse_finviz_date(record.get("Date", "")),
			"insider": record.get("Insider Trading", ""),
			"relationship": record.get("Relationship", ""),
			"transaction": record.get("Transaction", ""),
			"cost": _parse_float(record.get("Cost", "")),
			"shares": _parse_int(record.get("#Shares", "")),
			"value": _parse_int(record.get("Value ($)", "")),
			"shares_total": _parse_int(record.get("#Shares Total", "")),
		})
	output_json(results)


@safe_run
def cmd_insider_purchases(args):
	output_json(yf.Ticker(args.symbol).get_insider_purchases())


@safe_run
def cmd_insider_roster_holders(args):
	output_json(yf.Ticker(args.symbol).get_insider_roster_holders())


def main():
	parser = argparse.ArgumentParser(description="Holder and insider data")
	sub = parser.add_subparsers(dest="command", required=True)

	for name, func in [
		("get-major-holders", cmd_major_holders),
		("get-institutional-holders", cmd_institutional_holders),
		("get-mutualfund-holders", cmd_mutualfund_holders),
		("get-insider-purchases", cmd_insider_purchases),
		("get-insider-roster-holders", cmd_insider_roster_holders),
	]:
		sp = sub.add_parser(name)
		sp.add_argument("symbol")
		sp.set_defaults(func=func)

	sp = sub.add_parser("get-insider-transactions")
	sp.add_argument("symbol")
	sp.set_defaults(func=cmd_insider_transactions)

	args = parser.parse_args()
	args.func(args)


if __name__ == "__main__":
	main()
