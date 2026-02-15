#!/usr/bin/env python3
"""CAPE (Cyclically Adjusted Price-to-Earnings) Ratio data from YCharts.

Scrapes current and recent historical CAPE ratio data from YCharts public page.
This is the primary CAPE data source for SidneyKim0's valuation analysis since
the original Shiller dataset requires direct Yale server access which can be
unreliable. YCharts provides ~4 years of monthly CAPE data via web scraping.

CAPE (Shiller PE) smooths earnings over 10 years and adjusts for inflation,
providing a more stable valuation metric than trailing P/E. At the current
level (~40), the S&P 500 is historically expensive -- comparable to late 1990s
dot-com era levels.

Args:
	Command: get-current | get-history | get-percentile

	get-current:
		(no arguments)

	get-history:
		--start-date (str): Start date filter (YYYY-MM-DD)
		--end-date (str): End date filter (YYYY-MM-DD)
		--limit (int): Limit number of results (most recent first)

	get-percentile:
		(no arguments)

Returns:
	get-current -> dict: {
		"date": str,           # Most recent CAPE date
		"cape": float,         # Current CAPE ratio
		"source": str          # "YCharts (S&P 500 Shiller CAPE Ratio)"
	}

	get-history -> dict: {
		"count": int,          # Number of data points
		"data": [{"date": str, "cape": float}, ...],
		"source": str
	}

	get-percentile -> dict: {
		"date": str,
		"current_cape": float,
		"percentile": float,           # Percentile vs available history
		"historical_range": {"min": float, "max": float, "mean": float},
		"data_points": int,
		"interpretation": str,         # "Expensive" | "Fair" | "Cheap"
		"source": str
	}

Example:
	>>> python valuation/cape.py get-current
	{"date": "2026-01-31", "cape": 39.85, "source": "YCharts ..."}

	>>> python valuation/cape.py get-percentile
	{"current_cape": 39.85, "percentile": 96.0, "interpretation": "Expensive"}

	>>> python valuation/cape.py get-history --limit 3
	{"count": 3, "data": [{"date": "2026-01-31", "cape": 39.85}, ...]}

Use Cases:
	- Get current CAPE for ERP calculation (macro/erp.py uses this as primary source)
	- Track CAPE trend over recent years for valuation context
	- Calculate CAPE percentile to assess relative expensiveness
	- SidneyKim0 Step 3: Statistical Significance Validation (valuation input)

Notes:
	- Data source: https://ycharts.com/indicators/cyclically_adjusted_pe_ratio
	- Scrapes HTML via curl with browser-like User-Agent header
	- Provides ~50 monthly data points (~4 years of history)
	- No API key required (public page scraping)
	- For longer history (back to 1871), use cape_historical.py (Shiller dataset)
	- CAPE > 30 historically indicates expensive market (long-term mean ~17)

See Also:
	- valuation/cape_historical.py: Full Shiller dataset (1871-present, requires Yale server)
	- macro/erp.py: ERP calculation uses this as primary CAPE source
	- Personas/Sidneykim0/thresholds.md: CAPE interpretation thresholds
"""

import argparse
import os
import re
import subprocess
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from utils import output_json, safe_run

YCHARTS_URL = "https://ycharts.com/indicators/cyclically_adjusted_pe_ratio"


def fetch_ycharts_html() -> str:
	"""Fetch HTML from YCharts using curl with browser-like headers."""
	try:
		result = subprocess.run(
			[
				"curl",
				"-L",
				"-s",
				"-A",
				"Mozilla/5.0",
				YCHARTS_URL,
			],
			capture_output=True,
			text=True,
			timeout=10,
		)
		if result.returncode != 0:
			raise Exception(f"curl failed: {result.stderr}")
		return result.stdout
	except subprocess.TimeoutExpired:
		raise Exception("Request timeout")
	except Exception as e:
		raise Exception(f"Failed to fetch data: {str(e)}")


def parse_cape_table(html: str) -> list:
	"""Parse CAPE data table from HTML.

	Returns:
		List of dicts with 'date' and 'cape' keys.
	"""
	# Pattern: Date followed by Value in table cells
	# Example: <td>January 31, 2026</td>\n<td>39.85</td>
	pattern = (
		r"(January|February|March|April|May|June|July|August|September|"
		r"October|November|December)\s+(\d{1,2}),\s+(\d{4})\s*</td>\s*"
		r"<td[^>]*>\s*([0-9.]+)"
	)

	matches = re.findall(pattern, html, re.IGNORECASE)

	if not matches:
		raise Exception("No CAPE data found in HTML")

	results = []
	month_map = {
		"January": "01",
		"February": "02",
		"March": "03",
		"April": "04",
		"May": "05",
		"June": "06",
		"July": "07",
		"August": "08",
		"September": "09",
		"October": "10",
		"November": "11",
		"December": "12",
	}

	for month, day, year, value in matches:
		date_str = f"{year}-{month_map[month]}-{day.zfill(2)}"
		results.append({"date": date_str, "cape": float(value)})

	return results


@safe_run
def cmd_get_current(args):
	"""Get current CAPE ratio."""
	html = fetch_ycharts_html()
	data = parse_cape_table(html)

	if not data:
		output_json({"error": "No CAPE data available"})
		return

	# First entry is the most recent
	latest = data[0]
	output_json(
		{
			"date": latest["date"],
			"cape": latest["cape"],
			"source": "YCharts (S&P 500 Shiller CAPE Ratio)",
		}
	)


@safe_run
def cmd_get_history(args):
	"""Get historical CAPE ratio data."""
	html = fetch_ycharts_html()
	data = parse_cape_table(html)

	if not data:
		output_json({"error": "No CAPE data available"})
		return

	# Filter by date range if specified
	if args.start_date:
		start = datetime.strptime(args.start_date, "%Y-%m-%d")
		data = [d for d in data if datetime.strptime(d["date"], "%Y-%m-%d") >= start]

	if args.end_date:
		end = datetime.strptime(args.end_date, "%Y-%m-%d")
		data = [d for d in data if datetime.strptime(d["date"], "%Y-%m-%d") <= end]

	# Apply limit
	if args.limit:
		data = data[: args.limit]

	output_json(
		{
			"count": len(data),
			"data": data,
			"source": "YCharts (S&P 500 Shiller CAPE Ratio)",
		}
	)


@safe_run
def cmd_get_percentile(args):
	"""Calculate current CAPE percentile vs historical range."""
	html = fetch_ycharts_html()
	data = parse_cape_table(html)

	if not data:
		output_json({"error": "No CAPE data available"})
		return

	current = data[0]
	cape_values = [d["cape"] for d in data]

	# Calculate percentile
	current_cape = current["cape"]
	below_count = sum(1 for v in cape_values if v < current_cape)
	percentile = (below_count / len(cape_values)) * 100

	# Calculate statistics
	cape_min = min(cape_values)
	cape_max = max(cape_values)
	cape_mean = sum(cape_values) / len(cape_values)

	output_json(
		{
			"date": current["date"],
			"current_cape": current_cape,
			"percentile": round(percentile, 2),
			"historical_range": {
				"min": round(cape_min, 2),
				"max": round(cape_max, 2),
				"mean": round(cape_mean, 2),
			},
			"data_points": len(cape_values),
			"interpretation": ("Expensive" if percentile > 75 else "Fair" if percentile > 25 else "Cheap"),
			"source": "YCharts (S&P 500 Shiller CAPE Ratio)",
		}
	)


def main():
	parser = argparse.ArgumentParser(description="CAPE (Cyclically Adjusted PE) Ratio data from YCharts")
	subparsers = parser.add_subparsers(dest="command", help="Available commands")

	# get-current command
	subparsers.add_parser("get-current", help="Get current CAPE ratio")

	# get-history command
	parser_history = subparsers.add_parser("get-history", help="Get historical CAPE ratio data")
	parser_history.add_argument("--start-date", type=str, help="Start date (YYYY-MM-DD)")
	parser_history.add_argument("--end-date", type=str, help="End date (YYYY-MM-DD)")
	parser_history.add_argument("--limit", type=int, help="Limit number of results (most recent first)")

	# get-percentile command
	subparsers.add_parser("get-percentile", help="Calculate current CAPE percentile vs historical range")

	args = parser.parse_args()

	if not args.command:
		parser.print_help()
		sys.exit(1)

	if args.command == "get-current":
		cmd_get_current(args)
	elif args.command == "get-history":
		cmd_get_history(args)
	elif args.command == "get-percentile":
		cmd_get_percentile(args)


if __name__ == "__main__":
	main()
