#!/usr/bin/env python3
"""Federal Reserve Economic Data (FRED) generic series access utility.

Provides direct access to any FRED series by series ID. Useful for accessing FRED datasets
not covered by specialized commands (rates, inflation, policy). Supports multiple series
retrieval with metadata and time series filtering.

Args:
	series_id (str): Comma-separated FRED series IDs (e.g., "DFF,CPIAUCSL,UNRATE")
	--start-date (str): Start date for time series in YYYY-MM-DD format (optional)
	--end-date (str): End date for time series in YYYY-MM-DD format (optional)
	--limit (int): Maximum number of observations to return, most recent first (optional)

Returns:
	dict: {
		"data": {
			"SERIES_ID": {
				"YYYY-MM-DD": float,  # Date-keyed observations
				...
			},
			...
		},
		"metadata": {
			"SERIES_ID": {
				"title": str,                    # Full series description
				"units": str,                    # Measurement unit
				"frequency": str,                # Data frequency
				"seasonal_adjustment": str,      # Adjustment type
				"last_updated": str              # Last FRED database update timestamp
			},
			...
		}
	}

Example:
	>>> python series.py UNRATE,GDP,M2SL --limit 12
	{
		"data": {
			"UNRATE": {
				"2026-01-01": 3.7,
				"2025-12-01": 3.7
			},
			"GDP": {
				"2025-10-01": 29353.821,
				"2025-07-01": 29229.478
			},
			"M2SL": {
				"2025-12-01": 21456.4,
				"2025-11-01": 21398.2
			}
		},
		"metadata": {
			"UNRATE": {
				"title": "Unemployment Rate",
				"units": "Percent",
				"frequency": "Monthly",
				"seasonal_adjustment": "Seasonally Adjusted"
			},
			"GDP": {
				"title": "Gross Domestic Product",
				"units": "Billions of Dollars",
				"frequency": "Quarterly",
				"seasonal_adjustment": "Seasonally Adjusted Annual Rate"
			}
		}
	}

	>>> python series.py VIXCLS --start-date 2025-01-01 --limit 100
	>>> python series.py DXY,DTWEXBGS --end-date 2026-02-01

Use Cases:
	- Access FRED series not covered by specialized commands
	- Retrieve economic indicators like unemployment (UNRATE), GDP, retail sales
	- Fetch financial market indicators like VIX, dollar index (DXY)
	- Build custom datasets by combining multiple FRED series
	- Research custom series IDs from FRED website for specialized analysis
	- Combine with statistics scripts for correlation and regression analysis

Notes:
	- FRED API key required: Set FRED_API_KEY in .env file
	- Rate limits: 120 requests per minute per API key
	- Series ID discovery: Browse https://fred.stlouisfed.org/ to find series IDs
	- Common series: UNRATE (unemployment), GDP, VIXCLS (VIX), M2SL (money supply)
	- Data delays vary by series: Daily (VIX), monthly (CPI, unemployment), quarterly (GDP)
	- Use comma separation for multiple series: "UNRATE,GDP,M2SL"

See Also:
	- fred/rates.py: Interest rate series (DFF, DGS10, SOFR, etc.)
	- fred/inflation.py: Inflation series (CPIAUCSL, PCEPI, etc.)
	- fred/policy.py: Policy indicators (WALCL, USEPUINDXD, TGA, etc.)
	- statistics/correlation.py: Multi-series correlation analysis
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from fredapi import Fred
from utils import output_json, safe_run

FRED_API_KEY = "c383a49d4aa1a348f60780d92b7c6970"


def get_fred_client():
	"""Get FRED API client with API key."""
	return Fred(api_key=FRED_API_KEY)


def fetch_series(series_ids, start_date=None, end_date=None, limit=None):
	"""Fetch multiple FRED series and return combined data with metadata."""
	fred = get_fred_client()

	if isinstance(series_ids, str):
		series_ids = [series_ids]

	results = {}
	metadata = {}

	for series_id in series_ids:
		try:
			# Get series data
			data = fred.get_series(series_id, observation_start=start_date, observation_end=end_date)

			# Apply limit if specified
			if limit and len(data) > limit:
				data = data.tail(limit)

			# Convert to dict with date strings as keys
			results[series_id] = {str(idx.date()): float(val) if val == val else None for idx, val in data.items()}

			# Get series info for metadata
			info = fred.get_series_info(series_id)
			metadata[series_id] = {
				"title": info.get("title", ""),
				"units": info.get("units", ""),
				"frequency": info.get("frequency", ""),
				"seasonal_adjustment": info.get("seasonal_adjustment", ""),
				"last_updated": str(info.get("last_updated", "")),
			}
		except Exception as e:
			results[series_id] = {"error": str(e)}
			metadata[series_id] = {"error": str(e)}

	return {"data": results, "metadata": metadata}


@safe_run
def cmd_series(args):
	"""Get generic FRED series by ID."""
	series_ids = [s.strip() for s in args.series_id.split(",")]

	result = fetch_series(series_ids, start_date=args.start_date, end_date=args.end_date, limit=args.limit)
	output_json(result)


def add_common_args(parser):
	"""Add common arguments to a subparser."""
	parser.add_argument("--start-date", default=None, help="Start date (YYYY-MM-DD format)")
	parser.add_argument("--end-date", default=None, help="End date (YYYY-MM-DD format)")
	parser.add_argument("--limit", type=int, default=None, help="Number of observations to return (most recent)")
