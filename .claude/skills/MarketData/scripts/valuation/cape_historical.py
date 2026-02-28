#!/usr/bin/env python3
"""Historical CAPE data from Robert Shiller dataset.

Provides access to the full historical CAPE (Cyclically Adjusted Price-to-Earnings)
ratio dataset from Robert Shiller's Yale server, with monthly data going back to 1871.
This is the authoritative source for long-term CAPE analysis but depends on the Yale
server being available. Data is cached locally for 7 days to minimize network requests.

The Shiller dataset includes not just CAPE but also S&P 500 price (P), 10-year average
earnings (E), dividends (D), CPI, and long-term interest rates (Rate GS10).

Args:
	Command: get-cape | get-range | get-current

	get-cape:
		--date (str): Target date to query (YYYY-MM-DD, required)
		--refresh (flag): Force refresh of cached data

	get-range:
		--start-date (str): Range start date (YYYY-MM-DD, required)
		--end-date (str): Range end date (YYYY-MM-DD, required)
		--refresh (flag): Force refresh of cached data

	get-current:
		--refresh (flag): Force refresh of cached data

Returns:
	get-cape -> dict: {
		"query_date": str,         # Requested date
		"actual_date": str,        # Closest available data date
		"date_diff_days": int,     # Days between query and actual
		"cape": float,             # CAPE ratio at that date
		"sp500_price": float,      # S&P 500 price (if available)
		"earnings_10y_avg": float, # 10-year average earnings (if available)
		"source": str
	}

	get-range -> dict: {
		"start_date": str, "end_date": str,
		"data_points": int,
		"cape_data": {str: float},  # {date: cape_value, ...}
		"source": str
	}

	get-current -> dict: {
		"date": str,
		"cape": float,
		"sp500_price": float,       # If available
		"earnings_10y_avg": float,  # If available
		"source": str
	}

Example:
	>>> python valuation/cape_historical.py get-current
	{"date": "2025-12-01", "cape": 39.89, "source": "Robert Shiller (Yale)"}

	>>> python valuation/cape_historical.py get-cape --date 2000-03-01
	{"query_date": "2000-03-01", "cape": 43.77, "sp500_price": 1498.58}

	>>> python valuation/cape_historical.py get-range --start-date 2020-01-01 --end-date 2025-12-31
	{"data_points": 72, "cape_data": {"2020-01-01": 31.32, ...}}

Use Cases:
	- Long-term CAPE analysis: compare current valuation vs 150+ years of history
	- Dot-com era comparison: CAPE peaked at ~44 in Dec 1999
	- Historical regime classification: CAPE < 15 = cheap, 15-25 = fair, > 25 = expensive
	- Fallback data source for macro/erp.py when cached Shiller data is available

Notes:
	- Data source: http://www.econ.yale.edu/~shiller/data.htm (Excel file)
	- Data is monthly, from January 1871 to present
	- Cache stored at scripts/.cache/shiller_cape.csv (7-day TTL)
	- Yale server can be unreliable; use valuation/cape.py (YCharts) as primary
	- Date format in source: Year.Month (e.g., 1998.08 = August 1998)
	- Additional columns available: P (price), E (earnings), D (dividends), CPI

See Also:
	- valuation/cape.py: YCharts scraping (primary, more reliable, ~4 years)
	- macro/erp.py: ERP calculation (uses YCharts primary, Shiller cache fallback)
	- Personas/Sidneykim0/thresholds.md: CAPE interpretation thresholds
"""

import argparse
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pandas as pd
from utils import error_json, output_json, safe_run

SHILLER_DATA_URL = "https://www.econ.yale.edu/~shiller/data/ie_data.xls"
CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".cache")
CACHE_FILE = os.path.join(CACHE_DIR, "shiller_cape.csv")


def download_shiller_data(force_refresh=False):
	"""Download and cache Shiller CAPE data."""
	if os.path.exists(CACHE_FILE) and not force_refresh:
		# Check cache age (refresh if older than 7 days)
		cache_age = (datetime.now().timestamp() - os.path.getmtime(CACHE_FILE)) / 86400
		if cache_age < 7:
			return pd.read_csv(CACHE_FILE, parse_dates=["Date"])

	# Create cache directory
	os.makedirs(CACHE_DIR, exist_ok=True)

	# Download Shiller data
	try:
		# Download Excel file with requests (more reliable than urllib)
		import requests

		response = requests.get(SHILLER_DATA_URL, timeout=30)
		response.raise_for_status()

		# Save to temporary file
		temp_file = os.path.join(CACHE_DIR, "temp_shiller.xls")
		with open(temp_file, "wb") as f:
			f.write(response.content)

		# Read Excel file (sheet "Data", skip first 7 rows)
		df = pd.read_excel(temp_file, sheet_name="Data", skiprows=7)

		# Remove temp file
		os.remove(temp_file)

		# Clean column names (remove leading/trailing spaces)
		df.columns = df.columns.str.strip()

		# Parse date from Year.Month format (e.g., 1998.08 = August 1998)
		# Column name varies: could be "Date", "Year", or "Year.1"
		date_col = None
		for col in ["Date", "Year", "Year.1"]:
			if col in df.columns:
				date_col = col
				break

		if date_col is None:
			raise ValueError("Cannot find date column in Shiller data")

		# Convert Year.Month to datetime
		date_series = df[date_col].astype(str)
		date_series = date_series.str.replace(r"\.(\d)$", r".0\1", regex=True)
		date_series = date_series.apply(lambda x: x + ".01")
		df["Date"] = pd.to_datetime(date_series, format="%Y.%m.%d")

		# Select relevant columns
		# Column names: CAPE, P, E, CPI, etc.
		columns_to_keep = ["Date"]
		for col in ["CAPE", "P", "E", "D", "CPI", "Rate GS10", "Earnings"]:
			if col in df.columns:
				columns_to_keep.append(col)

		df = df[columns_to_keep].copy()

		# Remove rows with missing CAPE
		df = df.dropna(subset=["CAPE"])

		# Save to cache
		df.to_csv(CACHE_FILE, index=False)
		return df

	except Exception as e:
		raise ValueError(f"Failed to download Shiller data: {e}")


def find_closest_date(df, target_date):
	"""Find closest CAPE data to target date."""
	df["DateDiff"] = abs((df["Date"] - target_date).dt.days)
	closest_idx = df["DateDiff"].idxmin()
	return df.loc[closest_idx]


@safe_run
def cmd_get_cape(args):
	"""Get historical CAPE for specific date."""
	# Parse target date
	try:
		target_date = pd.to_datetime(args.date)
	except Exception:
		error_json(f"Invalid date format: {args.date}. Use YYYY-MM-DD.")
		return

	# Download/load Shiller data
	df = download_shiller_data(force_refresh=args.refresh)

	# Find closest date
	closest = find_closest_date(df, target_date)
	date_diff_days = int(closest["DateDiff"])

	result = {
		"query_date": args.date,
		"actual_date": str(closest["Date"].date()),
		"date_diff_days": date_diff_days,
		"cape": round(float(closest["CAPE"]), 2),
		"source": "Robert Shiller (Yale)",
		"dataset_url": "http://www.econ.yale.edu/~shiller/data.htm",
	}

	# Add optional fields if available
	if "P" in closest:
		result["sp500_price"] = round(float(closest["P"]), 2)
	if "E" in closest:
		result["earnings_10y_avg"] = round(float(closest["E"]), 2)
	if "D" in closest:
		result["dividend"] = round(float(closest["D"]), 2)

	output_json(result)


@safe_run
def cmd_get_range(args):
	"""Get CAPE data for date range."""
	# Parse dates
	try:
		start_date = pd.to_datetime(args.start_date)
		end_date = pd.to_datetime(args.end_date)
	except Exception:
		error_json("Invalid date format. Use YYYY-MM-DD.")
		return

	# Download/load Shiller data
	df = download_shiller_data(force_refresh=args.refresh)

	# Filter by date range
	df_range = df[(df["Date"] >= start_date) & (df["Date"] <= end_date)].copy()

	if df_range.empty:
		error_json(f"No data found for range {args.start_date} to {args.end_date}")
		return

	# Format output
	cape_data = {}
	for _, row in df_range.iterrows():
		date_str = str(row["Date"].date())
		cape_data[date_str] = round(float(row["CAPE"]), 2)

	result = {
		"start_date": args.start_date,
		"end_date": args.end_date,
		"data_points": len(cape_data),
		"cape_data": cape_data,
		"source": "Robert Shiller (Yale)",
	}

	output_json(result)


@safe_run
def cmd_get_current(args):
	"""Get most recent CAPE data."""
	# Download/load Shiller data
	df = download_shiller_data(force_refresh=args.refresh)

	# Get most recent row
	latest = df.iloc[-1]

	result = {
		"date": str(latest["Date"].date()),
		"cape": round(float(latest["CAPE"]), 2),
		"source": "Robert Shiller (Yale)",
		"dataset_url": "http://www.econ.yale.edu/~shiller/data.htm",
	}

	# Add optional fields
	if "P" in latest:
		result["sp500_price"] = round(float(latest["P"]), 2)
	if "E" in latest:
		result["earnings_10y_avg"] = round(float(latest["E"]), 2)

	output_json(result)


if __name__ == "__main__":
	parser = argparse.ArgumentParser(description="Historical CAPE data from Robert Shiller dataset")
	subparsers = parser.add_subparsers(dest="command", help="Available commands")

	# get-cape command
	sp_get = subparsers.add_parser("get-cape", help="Get CAPE for specific date")
	sp_get.add_argument("--date", required=True, help="Date in YYYY-MM-DD format")
	sp_get.add_argument("--refresh", action="store_true", help="Force refresh cached data")

	# get-range command
	sp_range = subparsers.add_parser("get-range", help="Get CAPE for date range")
	sp_range.add_argument("--start-date", required=True, help="Start date (YYYY-MM-DD)")
	sp_range.add_argument("--end-date", required=True, help="End date (YYYY-MM-DD)")
	sp_range.add_argument("--refresh", action="store_true", help="Force refresh cached data")

	# get-current command
	sp_current = subparsers.add_parser("get-current", help="Get most recent CAPE")
	sp_current.add_argument("--refresh", action="store_true", help="Force refresh cached data")

	args = parser.parse_args()

	# Dispatch
	if args.command == "get-cape":
		cmd_get_cape(args)
	elif args.command == "get-range":
		cmd_get_range(args)
	elif args.command == "get-current":
		cmd_get_current(args)
	else:
		parser.print_help()
		sys.exit(1)
