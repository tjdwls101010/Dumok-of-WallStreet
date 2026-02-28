#!/usr/bin/env python3
"""SEC data access - CLI dispatcher and shared utilities."""

import argparse
import os
import sys

import requests

# Add parent directory to sys.path for direct execution
if __name__ == "__main__":
	sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# SEC requires a User-Agent header with contact information
SEC_HEADERS = {
	"User-Agent": "MarketData/1.0 (contact@example.com)",
	"Accept-Encoding": "gzip, deflate",
}


def get_cik_from_symbol(symbol: str) -> str:
	"""Convert ticker symbol to CIK number."""
	url = "https://www.sec.gov/files/company_tickers.json"
	response = requests.get(url, headers=SEC_HEADERS, timeout=30)
	response.raise_for_status()
	data = response.json()

	symbol_upper = symbol.upper().replace(".", "-")
	for entry in data.values():
		if entry.get("ticker", "").upper() == symbol_upper:
			cik = str(entry.get("cik_str", entry.get("cik", "")))
			# Pad CIK to 10 digits
			return cik.zfill(10)

	raise ValueError(f"CIK not found for symbol: {symbol}")


def get_company_info(cik: str) -> dict:
	"""Get company submission data from SEC."""
	url = f"https://data.sec.gov/submissions/CIK{cik}.json"
	response = requests.get(url, headers=SEC_HEADERS, timeout=30)
	response.raise_for_status()
	return response.json()


# Import commands - use try/except for direct execution vs module import
if __name__ == "__main__":
	from data_advanced.sec.filings import cmd_filings, cmd_mda
	from data_advanced.sec.ftd import cmd_ftd, cmd_litigation
	from data_advanced.sec.insider import cmd_insider
	from data_advanced.sec.institutions import cmd_institutions
else:
	from .filings import cmd_filings, cmd_mda
	from .ftd import cmd_ftd, cmd_litigation
	from .insider import cmd_insider
	from .institutions import cmd_institutions


def main():
	"""Main CLI dispatcher."""
	parser = argparse.ArgumentParser(description="SEC EDGAR data retrieval")
	sub = parser.add_subparsers(dest="command", required=True)

	# filings
	sp = sub.add_parser("filings", help="Get company SEC filings (10-K, 10-Q, 8-K, etc.)")
	sp.add_argument("symbol", help="Ticker symbol")
	sp.add_argument("--form", default=None, help="Filter by form type (e.g., 10-K, 10-Q, 8-K)")
	sp.add_argument("--limit", type=int, default=20, help="Maximum number of filings to return")
	sp.set_defaults(func=cmd_filings)

	# mda
	sp = sub.add_parser("mda", help="Get Management Discussion and Analysis extraction")
	sp.add_argument("symbol", help="Ticker symbol")
	sp.add_argument("--form", default="10-K", help="Form type (10-K or 10-Q)")
	sp.set_defaults(func=cmd_mda)

	# insider
	sp = sub.add_parser("insider", help="Get Form 4 insider trading data")
	sp.add_argument("symbol", help="Ticker symbol")
	sp.add_argument("--limit", type=int, default=20, help="Maximum number of filings to return")
	sp.set_defaults(func=cmd_insider)

	# institutions
	sp = sub.add_parser("institutions", help="Get 13F filings submitted by the entity's CIK (investment managers only)")
	sp.add_argument("symbol", help="Ticker symbol")
	sp.set_defaults(func=cmd_institutions)

	# ftd
	sp = sub.add_parser("ftd", help="Get Fail-to-Deliver data")
	sp.add_argument("symbol", help="Ticker symbol")
	sp.add_argument("--start-date", default=None, help="Start date (YYYY-MM-DD)")
	sp.add_argument("--end-date", default=None, help="End date (YYYY-MM-DD)")
	sp.set_defaults(func=cmd_ftd)

	# litigation
	sp = sub.add_parser("litigation", help="Get SEC enforcement actions (RSS feed)")
	sp.add_argument("--limit", type=int, default=20, help="Maximum number of items to return")
	sp.set_defaults(func=cmd_litigation)

	args = parser.parse_args()
	args.func(args)


if __name__ == "__main__":
	main()
