#!/usr/bin/env python3
"""Holder and insider transaction data.

Retrieve institutional ownership, mutual fund holdings, insider transactions, and major
shareholder information via Yahoo Finance API for ownership analysis and insider activity tracking.

Commands:
	get-major-holders: Major holder breakdown (percentage institutional/insider/public)
	get-institutional-holders: Top institutional investors with share counts
	get-mutualfund-holders: Top mutual fund holders with positions
	get-insider-transactions: Insider buying and selling activity
	get-insider-purchases: Insider purchase transactions only
	get-insider-roster-holders: Current insider ownership roster

Args:
	symbol (str): Ticker symbol (e.g., "AAPL", "MSFT", "SPY")
	--start (str): Start date (YYYY-MM-DD) for insider transactions — filter on or after this date
	--end (str): End date (YYYY-MM-DD) for insider transactions — filter on or before this date
	--exclude-grants (bool): Exclude grant/award transactions from insider transactions
	--min-value (int): Minimum transaction value filter for insider transactions

Returns:
	dict: {
		"Holder": str,                        # Institution or insider name
		"Shares": int,                        # Number of shares held
		"Date Reported": str,                 # Reporting date (YYYY-MM-DD)
		"% Out": float,                       # Percentage of shares outstanding
		"Value": int,                         # Position value in USD
		"Insider Name": str,                  # Insider name (insider transactions)
		"Title": str,                         # Insider title/position
		"Transaction Type": str,              # Buy/Sale/Option Exercise
		"Shares Traded": int,                 # Number of shares transacted
		"Price": float,                       # Transaction price per share
		"Shares Owned": int                   # Total shares owned after transaction
	}

Example:
	>>> python holders.py get-major-holders AAPL
	{
		"institutionsFloatPercentHeld": 0.6234,
		"institutionsPercentHeld": 0.6123,
		"institutionsCount": 5847
	}

	>>> python holders.py get-institutional-holders MSFT
	[
		{
			"Holder": "Vanguard Group Inc",
			"Shares": 789456123,
			"Date Reported": "2024-12-31",
			"% Out": 0.1048,
			"Value": 311234567890
		},
		{
			"Holder": "BlackRock Inc.",
			"Shares": 623789456,
			"% Out": 0.0828
		}
	]

	>>> python holders.py get-mutualfund-holders SPY
	[
		{
			"Holder": "Vanguard 500 Index Fund",
			"Shares": 125678901,
			"Date Reported": "2024-12-31",
			"% Out": 0.0134
		}
	]

	>>> python holders.py get-insider-transactions AAPL
	[
		{
			"Insider": "Tim Cook",
			"Title": "CEO",
			"Transaction": "Sale",
			"Shares": 50000,
			"Price": 175.50,
			"Value": 8775000,
			"Date": "2026-01-15",
			"Shares Owned": 3200000
		},
		{
			"Insider": "Luca Maestri",
			"Title": "CFO",
			"Transaction": "Purchase",
			"Shares": 10000,
			"Price": 174.20
		}
	]

	>>> python holders.py get-insider-transactions TSLA --start 2025-01-01 --exclude-grants
	[
		{
			"Insider": "Elon Musk",
			"Transaction": "Sale",
			"Shares": 100000,
			"Date": "2025-03-15"
		}
	]

	>>> python holders.py get-insider-purchases AAPL
	[
		{
			"Insider": "Board Member",
			"Transaction": "Purchase",
			"Shares": 5000,
			"Price": 173.80,
			"Date": "2026-01-10"
		}
	]

	>>> python holders.py get-insider-roster-holders MSFT
	[
		{
			"Name": "Satya Nadella",
			"Position": "CEO",
			"Shares": 1650000,
			"Value": 650000000,
			"% Ownership": 0.0022
		}
	]

Use Cases:
	- Institutional ownership tracking for sentiment analysis
	- Smart money following: Identify major fund accumulation/distribution
	- Insider buying as bullish signal (skin in the game)
	- Insider selling pattern detection (potential red flag)
	- Ownership concentration analysis for voting rights
	- 13F filing analysis and position change tracking

Notes:
	- Yahoo Finance API rate limits: ~2000 requests/hour
	- Institutional holdings data from quarterly 13F filings (45-day lag)
	- Insider transactions from SEC Form 4 filings (2-day lag)
	- Major holders percentages may not sum to 100% due to rounding
	- Mutual fund holdings updated quarterly
	- Insider transactions include stock options exercises
	- Some insider names may be redacted or anonymized
	- Position values calculated using report date prices

See Also:
	- info.py: Company metadata including shares outstanding
	- actions.py: Insider purchases may precede earnings announcements
	- price.py: Stock price for position value calculation
	- funds.py: Fund holdings when analyzing ETF/mutual fund ownership
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import yfinance as yf
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


@safe_run
def cmd_insider_transactions(args):
	import pandas as pd

	data = yf.Ticker(args.symbol).get_insider_transactions()

	if isinstance(data, pd.DataFrame) and not data.empty:
		# Identify date column
		date_col = None
		for col in data.columns:
			if "date" in col.lower() or "start date" in col.lower():
				date_col = col
				break
		# Also check index name
		if date_col is None and data.index.name and "date" in data.index.name.lower():
			data = data.reset_index()
			date_col = data.columns[0]

		# Apply --start filter
		if hasattr(args, "start") and args.start and date_col:
			data[date_col] = pd.to_datetime(data[date_col], errors="coerce")
			data = data[data[date_col] >= pd.Timestamp(args.start)]

		# Apply --end filter
		if hasattr(args, "end") and args.end and date_col:
			data[date_col] = pd.to_datetime(data[date_col], errors="coerce")
			data = data[data[date_col] <= pd.Timestamp(args.end)]

		# Apply --exclude-grants filter
		if hasattr(args, "exclude_grants") and args.exclude_grants:
			# Check Transaction column first, then Text column as fallback
			exclude_cols = []
			for col in data.columns:
				if col.lower() in ("transaction", "text"):
					exclude_cols.append(col)
			if exclude_cols:
				mask = pd.Series(False, index=data.index)
				for col in exclude_cols:
					mask = mask | data[col].astype(str).str.contains(r"grant|award|gift", case=False, na=False)
				data = data[~mask]

		# Apply --min-value filter
		if hasattr(args, "min_value") and args.min_value is not None:
			val_col = None
			for col in data.columns:
				if "value" in col.lower():
					val_col = col
					break
			if val_col:
				data[val_col] = pd.to_numeric(data[val_col], errors="coerce")
				data = data[data[val_col] >= args.min_value]

	output_json(data)


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

	# get-insider-transactions with filtering options
	sp = sub.add_parser("get-insider-transactions")
	sp.add_argument("symbol")
	sp.add_argument("--start", type=str, default=None, help="Start date (YYYY-MM-DD)")
	sp.add_argument("--end", type=str, default=None, help="End date (YYYY-MM-DD)")
	sp.add_argument("--exclude-grants", action="store_true", help="Exclude grant/award transactions")
	sp.add_argument("--min-value", type=int, default=None, help="Minimum transaction value")
	sp.set_defaults(func=cmd_insider_transactions)

	args = parser.parse_args()
	args.func(args)


if __name__ == "__main__":
	main()
