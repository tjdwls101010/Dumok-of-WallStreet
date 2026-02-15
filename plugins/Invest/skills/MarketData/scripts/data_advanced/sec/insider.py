#!/usr/bin/env python3
"""SEC Form 4 insider trading activity tracking.

Provides access to Form 4 filings which disclose transactions by company insiders (officers,
directors, and 10%+ shareholders). Includes buy/sell transactions, option exercises, and
equity grants. Uses SEC EDGAR API with ticker to CIK mapping.

Args:
	symbol (str): Stock ticker symbol (e.g., "AAPL", "TSLA", "NVDA")
	--limit (int): Maximum number of Form 4 filings to return, most recent first (optional)

Returns:
	dict: {
		"data": [
			{
				"form": str,                     # Form type (always "4")
				"filing_date": str,              # Date filed with SEC (YYYY-MM-DD)
				"accession_number": str,         # SEC accession number (unique ID)
				"filing_url": str                # Direct URL to SEC EDGAR Form 4 document
			},
			...
		],
		"metadata": {
			"symbol": str,                       # Ticker symbol
			"cik": str,                          # SEC Central Index Key
			"company_name": str,                 # Official company name
			"total_results": int                 # Number of Form 4 filings returned
		}
	}

Example:
	>>> python insider.py TSLA --limit 10
	{
		"data": [
			{
				"form": "4",
				"filing_date": "2026-02-04",
				"accession_number": "0001494730-26-000352",
				"filing_url": "https://www.sec.gov/Archives/edgar/data/1318605/..."
			},
			{
				"form": "4",
				"filing_date": "2026-01-15",
				"accession_number": "0001494730-26-000128",
				"filing_url": "https://www.sec.gov/Archives/edgar/data/1318605/..."
			}
		],
		"metadata": {
			"symbol": "TSLA",
			"cik": "0001318605",
			"company_name": "Tesla, Inc.",
			"total_results": 10
		}
	}

	>>> python insider.py NVDA --limit 20
	>>> python insider.py AAPL --limit 50

Use Cases:
	- Track insider buying as bullish signal for undervalued stocks
	- Monitor insider selling for potential negative catalysts
	- Identify unusual insider activity patterns before earnings announcements
	- Build insider sentiment indicators using transaction clustering
	- Analyze CEO/CFO trading patterns for corporate governance assessment
	- Screen for stocks with recent cluster of insider purchases (value signal)

Notes:
	- No API key required (public SEC EDGAR access)
	- Rate limits: 10 requests per second per IP address (SEC enforced)
	- Data delays: Form 4 must be filed within 2 business days of transaction
	- Filing interpretation: Requires manual review of Form 4 XML/HTML for transaction details
	- Transaction types: Purchase, sale, option exercise, gift, equity award
	- Insider definition: Officers, directors, and 10%+ beneficial owners
	- Exemptions: Rule 10b5-1 plans (pre-scheduled sales) disclosed in footnotes
	- Form 4 vs Form 5: Form 4 is real-time (2-day deadline), Form 5 is annual catch-all
	- Empty results exit with code 1 and error JSON when no Form 4 filings found

See Also:
	- sec/filings.py: General SEC filings including 10-K/10-Q
	- sec/institutions.py: Form 13F institutional holdings
	- analysis/insider_sentiment.py: Insider trading sentiment scoring
	- statistics/correlation.py: Correlation between insider activity and stock returns
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from utils import error_json, output_json, safe_run

# Import shared utilities
from . import get_cik_from_symbol, get_company_info


@safe_run
def cmd_insider(args):
	"""Get Form 4 insider trading data."""
	cik = get_cik_from_symbol(args.symbol)
	data = get_company_info(cik)

	filings = data.get("filings", {}).get("recent", {})
	if not filings:
		error_json(f"No filings found for {args.symbol} (CIK: {cik})")

	# Filter for Form 4 filings
	results = []
	forms = filings.get("form", [])
	filing_dates = filings.get("filingDate", [])
	accession_numbers = filings.get("accessionNumber", [])
	primary_documents = filings.get("primaryDocument", [])

	for i in range(len(forms)):
		form_type = forms[i] if i < len(forms) else ""
		if form_type != "4":
			continue

		accession = accession_numbers[i] if i < len(accession_numbers) else ""
		primary_doc = primary_documents[i] if i < len(primary_documents) else ""
		cik_int = int(cik)

		filing_url = f"https://www.sec.gov/Archives/edgar/data/{cik_int}/{accession.replace('-', '')}/{primary_doc}"

		results.append(
			{
				"form": form_type,
				"filing_date": filing_dates[i] if i < len(filing_dates) else None,
				"accession_number": accession,
				"filing_url": filing_url,
			}
		)

		if args.limit and len(results) >= args.limit:
			break

	if not results:
		error_json(f"No Form 4 filings found for {args.symbol}")

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
