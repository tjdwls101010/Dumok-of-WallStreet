#!/usr/bin/env python3
"""SEC 13F filing lookup by company CIK.

Searches for Form 13F filings submitted by the entity matching the given ticker's CIK.
This is useful for investment managers (hedge funds, mutual funds, pension funds) that
file 13F to disclose their quarterly equity holdings. Most operating companies (AAPL,
TSLA, GOOGL) do NOT file 13F — only institutional investment managers with >$100M AUM do.

To find which institutions hold a given stock, use holders.py get-institutional-holders instead.

Args:
	symbol (str): Stock ticker symbol (e.g., "BRK-B", "GS", "JPM")
	No additional command-line arguments

Returns:
	dict: {
		"data": [
			{
				"form": str,                     # Form type (e.g., "13F-HR", "13F-HR/A")
				"filing_date": str,              # Date filed with SEC (YYYY-MM-DD)
				"report_date": str,              # Quarter end date (YYYY-MM-DD)
				"accession_number": str,         # SEC accession number (unique ID)
				"filing_url": str                # Direct URL to SEC EDGAR 13F document
			},
			...
		],
		"metadata": {
			"symbol": str,                       # Ticker symbol
			"cik": str,                          # SEC Central Index Key
			"company_name": str,                 # Official company name
			"total_results": int                 # Number of 13F filings returned
		}
	}

Example:
	>>> python -m data_advanced.sec institutions BRK-B
	{
		"data": [
			{
				"form": "13F-HR",
				"filing_date": "2025-11-14",
				"report_date": "2025-09-30",
				"accession_number": "0001067983-25-000089",
				"filing_url": "https://www.sec.gov/Archives/edgar/data/1067983/..."
			}
		],
		"metadata": {
			"symbol": "BRK-B",
			"cik": "0001067983",
			"company_name": "BERKSHIRE HATHAWAY INC",
			"total_results": 4
		}
	}

	>>> python -m data_advanced.sec institutions GS
	>>> python -m data_advanced.sec institutions JPM

Use Cases:
	- Look up 13F filings for known investment managers (BRK-B, GS, JPM)
	- Retrieve quarterly portfolio snapshots from hedge fund 13F disclosures
	- Track filing dates and accession numbers for 13F document analysis

Notes:
	- This searches 13F filings filed BY the entity with the given CIK
	- Most operating companies (AAPL, TSLA) will return empty results
	- Only investment managers with >$100M AUM are required to file 13F
	- To find which institutions hold a stock, use: holders.py get-institutional-holders
	- No API key required (public SEC EDGAR access)
	- Rate limits: 10 requests per second per IP address (SEC enforced)
	- Data delays: 13F must be filed within 45 days of quarter end
	- Filing schedule: Q1 (May 15), Q2 (Aug 15), Q3 (Nov 15), Q4 (Feb 15) deadlines
	- Form types: 13F-HR (initial filing), 13F-HR/A (amendment)
	- Empty results with exit 1 when no 13F filings found for the given CIK

See Also:
	- holders.py get-institutional-holders: Which institutions hold a given stock
	- sec/filings.py: General SEC filings including 10-K/10-Q
	- sec/insider.py: Form 4 insider trading activity
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from utils import error_json, output_json, safe_run

# Import shared utilities
from . import get_cik_from_symbol, get_company_info


@safe_run
def cmd_institutions(args):
	"""Get Form 13F institutional holdings for a company."""
	cik = get_cik_from_symbol(args.symbol)
	data = get_company_info(cik)

	filings = data.get("filings", {}).get("recent", {})
	if not filings:
		error_json(f"No filings found for {args.symbol} (CIK: {cik})")

	# Filter for 13F-HR filings
	results = []
	forms = filings.get("form", [])
	filing_dates = filings.get("filingDate", [])
	accession_numbers = filings.get("accessionNumber", [])
	primary_documents = filings.get("primaryDocument", [])
	report_dates = filings.get("reportDate", [])

	for i in range(len(forms)):
		form_type = forms[i] if i < len(forms) else ""
		if "13F" not in form_type.upper():
			continue

		accession = accession_numbers[i] if i < len(accession_numbers) else ""
		primary_doc = primary_documents[i] if i < len(primary_documents) else ""
		cik_int = int(cik)

		filing_url = f"https://www.sec.gov/Archives/edgar/data/{cik_int}/{accession.replace('-', '')}/{primary_doc}"

		results.append(
			{
				"form": form_type,
				"filing_date": filing_dates[i] if i < len(filing_dates) else None,
				"report_date": report_dates[i] if i < len(report_dates) else None,
				"accession_number": accession,
				"filing_url": filing_url,
			}
		)

	if not results:
		error_json(f"No 13F filings found for {args.symbol} (CIK: {cik})")

	output_json(
		{
			"data": results,
			"metadata": {
				"symbol": args.symbol,
				"cik": cik,
				"company_name": data.get("name", ""),
				"total_results": len(results),
			},
		}
	)
