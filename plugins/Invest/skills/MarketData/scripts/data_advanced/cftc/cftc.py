#!/usr/bin/env python3
"""CFTC Commitment of Traders (COT) data retrieval.

Fetches weekly Commitment of Traders (COT) reports from the CFTC Socrata API.
COT data shows how commercial hedgers, large speculators, and small traders are
positioned in futures markets. This is a key sentiment and positioning indicator
in SidneyKim0's methodology for detecting crowded trades and potential reversals.

Supports multiple report types (legacy, disaggregated, financial, supplemental)
with both futures-only and combined (futures + options) variants. Includes a
symbol mapping for common futures tickers (ES, GC, CL, etc.) to CFTC contract
names.

Args:
	Command: cot | search

	cot:
		symbol (str): Futures symbol (e.g., ES, GC, CL) or search term (required)
		--report-type (str): "legacy" | "disaggregated" | "financial" | "supplemental"
							 (default: "legacy")
		--futures-only (flag): Return futures-only report (default: combined)
		--start (str): Start date (YYYY-MM-DD, default: last Tuesday)
		--end (str): End date (YYYY-MM-DD, default: today)
		--limit (int): Maximum records to return (default: 100)

	search:
		query (str): Search term for contract names (e.g., "gold", "crude", "s&p")

Returns:
	cot -> dict: {
		"data": [{
			"date": str,
			"market_and_exchange_names": str,
			"open_interest_all": int,
			"noncomm_positions_long_all": int,   # Large speculators long
			"noncomm_positions_short_all": int,  # Large speculators short
			"comm_positions_long_all": int,      # Commercials long
			"comm_positions_short_all": int,     # Commercials short
			"nonrept_positions_long_all": int,   # Small traders long
			"nonrept_positions_short_all": int,  # Small traders short
			"pct_of_oi_noncomm_long_all": float, # % of OI
			...
		}],
		"metadata": {
			"source": "CFTC",
			"symbol": str,
			"report_type": str,
			"count": int
		}
	}

	search -> dict: {
		"data": [{"code": str, "name": str, "category": str, ...}],
		"metadata": {"query": str, "count": int}
	}

Example:
	>>> python data_advanced/cftc/cftc.py cot GC
	{"data": [{"date": "2026-02-04", "open_interest_all": 532000, ...}]}

	>>> python data_advanced/cftc/cftc.py cot ES --report-type financial --start 2025-01-01
	{"data": [...], "metadata": {"count": 52}}

	>>> python data_advanced/cftc/cftc.py search gold
	{"data": [{"code": "088691", "name": "GOLD - COMMODITY EXCHANGE INC.", ...}]}

Use Cases:
	- Monitor large speculator net positioning for crowded trade detection
	- Track commercial hedger positioning for smart money signals
	- Detect extreme positioning: when net long/short reaches historical extremes
	- Cross-validate with price action: if price rises but spec longs decrease = divergence
	- SidneyKim0 Step 1: Flow Data (foreign/institutional/individual positioning)

Notes:
	- Data is released weekly (Friday) for positions as of Tuesday
	- CFTC Socrata API is free, no API key required
	- Common symbol mappings included: ES, NQ, GC, SI, CL, ZN, 6E, BTC, etc.
	- Legacy report: commercials vs non-commercials (simplest)
	- Disaggregated: producer/merchant, swap dealer, managed money, other
	- Financial: dealer, asset manager, leveraged funds, other
	- Percentage fields (pct_*) are automatically converted to decimal (0-1 range)

See Also:
	- analysis/putcall_ratio.py: Options sentiment (complementary positioning data)
	- Personas/Sidneykim0/methodology.md: Step 1 flow data cascade
	- Personas/Sidneykim0/thresholds.md: Positioning extremes interpretation
"""

import argparse
import os
import sys
from datetime import datetime, timedelta
from urllib.parse import quote

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
import requests
from utils import output_json, safe_run

# CFTC Socrata API report codes
REPORT_CODES = {
	"legacy_futures_only": "6dca-aqww",
	"legacy_combined": "jun7-fc8e",
	"disaggregated_futures_only": "72hh-3qpy",
	"disaggregated_combined": "kh3c-gbw2",
	"financial_futures_only": "gpe5-46if",
	"financial_combined": "yw9f-hn96",
	"supplemental": "4zgm-a668",
}

# Common futures symbol to contract name mappings
SYMBOL_MAPPINGS = {
	"ES": "E-MINI S&P 500",
	"NQ": "E-MINI NASDAQ 100",
	"YM": "MINI DOW JONES",
	"RTY": "E-MINI RUSSELL 2000",
	"GC": "GOLD",
	"SI": "SILVER",
	"HG": "COPPER",
	"PL": "PLATINUM",
	"CL": "CRUDE OIL",
	"NG": "NATURAL GAS",
	"RB": "RBOB GASOLINE",
	"HO": "HEATING OIL",
	"ZB": "30-YEAR TREASURY",
	"ZN": "10-YEAR TREASURY",
	"ZF": "5-YEAR TREASURY",
	"ZT": "2-YEAR TREASURY",
	"ZC": "CORN",
	"ZS": "SOYBEANS",
	"ZW": "WHEAT",
	"ZL": "SOYBEAN OIL",
	"ZM": "SOYBEAN MEAL",
	"LE": "LIVE CATTLE",
	"HE": "LEAN HOGS",
	"6E": "EURO FX",
	"6J": "JAPANESE YEN",
	"6B": "BRITISH POUND",
	"6A": "AUSTRALIAN DOLLAR",
	"6C": "CANADIAN DOLLAR",
	"6S": "SWISS FRANC",
	"BTC": "BITCOIN",
	"ETH": "ETHER",
	"VX": "VIX",
}


def get_report_key(report_type: str, futures_only: bool) -> str:
	"""Get the report key for CFTC API."""
	if report_type == "supplemental":
		return "supplemental"
	suffix = "futures_only" if futures_only else "combined"
	return f"{report_type}_{suffix}"


def parse_cot_response(data: list) -> list:
	"""Parse and clean COT response data."""
	results = []
	string_cols = {
		"market_and_exchange_names",
		"cftc_contract_market_code",
		"cftc_market_code",
		"cftc_region_code",
		"cftc_commodity_code",
		"commodity_group_name",
		"commodity",
		"commodity_name",
		"commodity_subgroup_name",
		"contract_units",
		"report_date_as_yyyy_mm_dd",
		"yyyy_report_week_ww",
		"futonly_or_combined",
	}

	for row in data:
		parsed = {}
		for key, value in row.items():
			key_lower = key.lower().replace("__", "_")
			if value is None or value == "":
				continue
			if key.lower() in string_cols:
				parsed[key_lower] = str(value)
			elif key.lower() == "report_date_as_yyyy_mm_dd":
				parsed["date"] = str(value).split("T")[0]
			elif key_lower.startswith("pct_") and value:
				try:
					parsed[key_lower] = float(value) / 100
				except (ValueError, TypeError):
					parsed[key_lower] = value
			elif key_lower.startswith("conc_") and value:
				try:
					parsed[key_lower] = float(value)
				except (ValueError, TypeError):
					parsed[key_lower] = value
			else:
				try:
					parsed[key_lower] = int(value)
				except (ValueError, TypeError):
					try:
						parsed[key_lower] = float(value)
					except (ValueError, TypeError):
						parsed[key_lower] = value
		if parsed:
			results.append(parsed)
	return results


@safe_run
def cmd_cot(args):
	"""Get Commitment of Traders report data."""
	# Resolve symbol to search term
	search_term = args.symbol.upper()
	if search_term in SYMBOL_MAPPINGS:
		search_term = SYMBOL_MAPPINGS[search_term]

	# Add wildcards for LIKE search and URL-encode special characters
	if not search_term[:3].isdigit():
		search_term = f"%{search_term}%"
	# URL encode the search term (safe='' encodes everything including &)
	search_term_encoded = quote(search_term, safe="")

	# Build date range
	today = datetime.now()
	if args.start:
		start_date = args.start
	else:
		# Default to last week's report (Tuesday)
		last_tuesday = today - timedelta(days=(today.weekday() - 1) % 7 + 7)
		start_date = last_tuesday.strftime("%Y-%m-%d")

	end_date = args.end if args.end else today.strftime("%Y-%m-%d")

	# Get report code
	report_key = get_report_key(args.report_type, args.futures_only)
	report_code = REPORT_CODES.get(report_key)
	if not report_code:
		raise ValueError(f"Unknown report type: {args.report_type}")

	# Build URL
	base_url = f"https://publicreporting.cftc.gov/resource/{report_code}.json"
	date_range = f"$where=Report_Date_as_YYYY_MM_DD between '{start_date}' AND '{end_date}'"
	search_clause = (
		f" AND (UPPER(contract_market_name) like UPPER('{search_term_encoded}') "
		f"OR UPPER(commodity) like UPPER('{search_term_encoded}') "
		f"OR UPPER(cftc_contract_market_code) like UPPER('{search_term_encoded}') "
		f"OR UPPER(commodity_group_name) like UPPER('{search_term_encoded}') "
		f"OR UPPER(commodity_subgroup_name) like UPPER('{search_term_encoded}'))"
	)
	order = "&$order=Report_Date_as_YYYY_MM_DD DESC"
	limit = f"&$limit={args.limit}"

	url = f"{base_url}?{date_range}{search_clause}{order}{limit}"

	resp = requests.get(url, timeout=60)
	resp.raise_for_status()
	raw = resp.json()

	if not raw:
		result = {
			"data": [],
			"metadata": {
				"source": "CFTC",
				"symbol": args.symbol,
				"search_term": search_term.replace("%", ""),
				"report_type": args.report_type,
				"futures_only": args.futures_only,
				"message": "No data found for the specified criteria",
			},
		}
	else:
		data = parse_cot_response(raw)
		result = {
			"data": data,
			"metadata": {
				"source": "CFTC",
				"symbol": args.symbol,
				"search_term": search_term.replace("%", ""),
				"report_type": args.report_type,
				"futures_only": args.futures_only,
				"start_date": start_date,
				"end_date": end_date,
				"count": len(data),
			},
		}

	output_json(result)


@safe_run
def cmd_search(args):
	"""Search for COT contract names and codes."""
	query = args.query.upper()

	# Use legacy combined report to search for contracts
	report_code = REPORT_CODES["legacy_combined"]
	base_url = f"https://publicreporting.cftc.gov/resource/{report_code}.json"

	# Get distinct contract market names
	url = (
		f"{base_url}?"
		f"$select=distinct cftc_contract_market_code,contract_market_name,"
		f"commodity_group_name,commodity_subgroup_name,commodity"
		f"&$where=UPPER(contract_market_name) like UPPER('%{query}%') "
		f"OR UPPER(commodity) like UPPER('%{query}%') "
		f"OR UPPER(cftc_contract_market_code) like UPPER('%{query}%') "
		f"OR UPPER(commodity_group_name) like UPPER('%{query}%')"
		f"&$limit=100"
		f"&$order=contract_market_name"
	)

	resp = requests.get(url, timeout=60)
	resp.raise_for_status()
	raw = resp.json()

	# Deduplicate and format results
	seen = set()
	data = []
	for item in raw:
		code = item.get("cftc_contract_market_code")
		if code and code not in seen:
			seen.add(code)
			data.append(
				{
					"code": code,
					"name": item.get("contract_market_name"),
					"category": item.get("commodity_group_name"),
					"subcategory": item.get("commodity_subgroup_name"),
					"commodity": item.get("commodity"),
				}
			)

	result = {
		"data": data,
		"metadata": {
			"source": "CFTC",
			"query": args.query,
			"count": len(data),
		},
	}
	output_json(result)


def main():
	parser = argparse.ArgumentParser(description="CFTC Commitment of Traders data")
	sub = parser.add_subparsers(dest="command", required=True)

	# cot
	sp = sub.add_parser("cot", help="Get Commitment of Traders report")
	sp.add_argument("symbol", help="Futures symbol (e.g., ES, GC, CL) or search term")
	sp.add_argument(
		"--report-type",
		choices=["legacy", "disaggregated", "financial", "supplemental"],
		default="legacy",
		help="Report type (default: legacy)",
	)
	sp.add_argument(
		"--futures-only",
		action="store_true",
		help="Return futures-only report (default: combined)",
	)
	sp.add_argument("--start", help="Start date (YYYY-MM-DD)")
	sp.add_argument("--end", help="End date (YYYY-MM-DD)")
	sp.add_argument("--limit", type=int, default=100, help="Maximum records to return (default: 100)")
	sp.set_defaults(func=cmd_cot)

	# search
	sp = sub.add_parser("search", help="Search for COT contract names")
	sp.add_argument("query", help="Search term (e.g., gold, crude, s&p)")
	sp.set_defaults(func=cmd_search)

	args = parser.parse_args()
	args.func(args)


if __name__ == "__main__":
	main()
