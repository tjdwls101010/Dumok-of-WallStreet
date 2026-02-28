#!/usr/bin/env python3
"""Federal Reserve Economic Data (FRED) monetary policy and liquidity indicators.

Provides access to FRED's policy-related datasets including Fed balance sheet (WALCL),
Economic Policy Uncertainty Index, Treasury General Account (TGA), Reverse Repo operations,
and credit market spreads (High Yield, Investment Grade). Tracks liquidity conditions and
policy stance.

Args:
	series_id (str): FRED series identifier (e.g., "WALCL" for Fed balance sheet, "USEPUINDXD" for policy uncertainty)
	--start-date (str): Start date for time series in YYYY-MM-DD format (optional)
	--end-date (str): End date for time series in YYYY-MM-DD format (optional)
	--limit (int): Maximum number of observations to return, most recent first (optional)
	--indicator (str): Policy indicator type (e.g., "fed_balance_sheet", "policy_uncertainty", "all")
	--spread-type (str): Credit spread type (e.g., "hy_spread", "ig_spread", "bbb_spread")
	--series-type (str): TGA series type (e.g., "weekly_avg", "wednesday", "daily")

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
				"units": str,                    # Measurement unit (Millions of Dollars, Index, Percent)
				"frequency": str,                # Daily, Weekly, Monthly
				"seasonal_adjustment": str,      # SA or NSA
				"last_updated": str              # Last FRED database update timestamp
			},
			...
		}
	}

Example:
	>>> python policy.py policy --indicator fed_balance_sheet --limit 30
	{
		"data": {
			"WALCL": {
				"2026-02-05": 7245000.0,
				"2026-01-29": 7238000.0
			}
		},
		"metadata": {
			"WALCL": {
				"title": "Assets: Total Assets: Total Assets (Less Eliminations from Consolidation)",
				"units": "Millions of Dollars",
				"frequency": "Weekly, Ending Wednesday",
				"seasonal_adjustment": "Not Seasonally Adjusted"
			}
		}
	}

	>>> python policy.py credit-spreads --spread-type hy_spread
	>>> python policy.py tga --series-type weekly_avg

Use Cases:
	- Track Quantitative Tightening (QT) progress via Fed balance sheet runoff
	- Monitor policy uncertainty for volatility regime identification
	- Analyze Treasury General Account for liquidity impact on money markets
	- Assess credit market stress via High Yield and Investment Grade spreads
	- Track Reverse Repo operations for excess liquidity measurement
	- Compare TGA balance with Fed funds rate for liquidity-driven volatility

Notes:
	- FRED API key required: Set FRED_API_KEY in .env file
	- Rate limits: 120 requests per minute per API key
	- Data delays: Fed balance sheet (weekly, Wednesday release), TGA (daily/weekly), credit spreads (daily)
	- TGA interpretation: High balance = restrictive liquidity, Low balance = accommodative
	- Policy Uncertainty Index: Higher values indicate elevated uncertainty (elections, crises)
	- Credit spreads: Widening signals stress, narrowing signals risk appetite
	- Reverse Repo (RRPONTSYD): High usage indicates excess liquidity in financial system

See Also:
	- fred/rates.py: Fed Funds rate for policy rate context
	- fred/inflation.py: Inflation data for policy decision analysis
	- fed/fedwatch.py: Market-implied rate change probabilities
	- statistics/correlation.py: Correlation between policy indicators and market returns
"""

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


# FRED Series IDs for policy indicators
POLICY_SERIES = {
	"fed_balance_sheet": "WALCL",
	"policy_uncertainty": "USEPUINDXD",
	"tga_balance": "WTREGEN",
	"reverse_repo": "RRPONTSYD",
}

CREDIT_SERIES = {
	"hy_spread": "BAMLH0A0HYM2",
	"ig_spread": "BAMLC0A0CM",
	"bbb_spread": "BAMLC0A4CBBB",
}

TGA_SERIES = {
	"weekly_avg": "WTREGEN",  # Week Average
	"wednesday": "WDTGAL",  # Wednesday Level
	"daily": "LDGUST",  # Daily Level (discontinued but has historical data)
}


@safe_run
def cmd_policy(args):
	"""Get Policy and Liquidity Indicators (Fed balance sheet, policy uncertainty)."""
	series_to_fetch = []

	if args.indicator == "all":
		series_to_fetch = list(POLICY_SERIES.values())
	elif args.indicator in POLICY_SERIES:
		series_to_fetch = [POLICY_SERIES[args.indicator]]
	else:
		series_to_fetch = [POLICY_SERIES["fed_balance_sheet"], POLICY_SERIES["policy_uncertainty"]]

	result = fetch_series(series_to_fetch, start_date=args.start_date, end_date=args.end_date, limit=args.limit)
	output_json(result)


@safe_run
def cmd_credit_spreads(args):
	"""Get Credit Market Spreads (high yield, investment grade)."""
	series_to_fetch = []

	if args.spread_type == "all":
		series_to_fetch = list(CREDIT_SERIES.values())
	elif args.spread_type in CREDIT_SERIES:
		series_to_fetch = [CREDIT_SERIES[args.spread_type]]
	else:
		series_to_fetch = [CREDIT_SERIES["hy_spread"], CREDIT_SERIES["ig_spread"]]

	result = fetch_series(series_to_fetch, start_date=args.start_date, end_date=args.end_date, limit=args.limit)
	output_json(result)


@safe_run
def cmd_tga(args):
	"""Get Treasury General Account (TGA) balance with liquidity analysis."""
	import numpy as np

	fred = get_fred_client()

	# Select TGA series
	if args.series_type in TGA_SERIES:
		series_id = TGA_SERIES[args.series_type]
	else:
		series_id = TGA_SERIES["weekly_avg"]

	# Fetch data
	data = fred.get_series(series_id, observation_start=args.start_date, observation_end=args.end_date)

	if data.empty:
		output_json({"error": "No data available for the selected series"})
		return

	# Apply limit if specified
	if args.limit and len(data) > args.limit:
		data = data.tail(args.limit)

	# Calculate statistics for full dataset (for z-score)
	current_value = float(data.iloc[-1])
	mean_value = float(data.mean())
	std_value = float(data.std())
	z_score = (current_value - mean_value) / std_value if std_value > 0 else 0

	# Percentile ranking
	percentile = float(np.percentile(data, 100 * (data < current_value).sum() / len(data)))

	# Get series info
	info = fred.get_series_info(series_id)

	# Liquidity interpretation
	if z_score > 2:
		liquidity = "Extremely High (Restrictive)"
	elif z_score > 1:
		liquidity = "High (Moderately Restrictive)"
	elif abs(z_score) <= 1:
		liquidity = "Normal"
	elif z_score > -2:
		liquidity = "Low (Accommodative)"
	else:
		liquidity = "Extremely Low (Very Accommodative)"

	result = {
		"date": str(data.index[-1].date()),
		"series_id": series_id,
		"series_type": args.series_type,
		"current_value": round(current_value, 2),
		"units": info.get("units", "Millions of Dollars"),
		"statistics": {
			"mean": round(mean_value, 2),
			"std": round(std_value, 2),
			"z_score": round(z_score, 4),
			"percentile": round(percentile, 2),
		},
		"liquidity_interpretation": liquidity,
		"data_points": len(data),
		"recent_values": {str(idx.date()): round(float(val), 2) for idx, val in data.tail(20).items()},
		"metadata": {
			"title": info.get("title", ""),
			"frequency": info.get("frequency", ""),
			"last_updated": str(info.get("last_updated", "")),
		},
	}
	output_json(result)


def add_common_args(parser):
	"""Add common arguments to a subparser."""
	parser.add_argument("--start-date", default=None, help="Start date (YYYY-MM-DD format)")
	parser.add_argument("--end-date", default=None, help="End date (YYYY-MM-DD format)")
	parser.add_argument("--limit", type=int, default=None, help="Number of observations to return (most recent)")
