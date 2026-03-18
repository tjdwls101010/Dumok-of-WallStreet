#!/usr/bin/env python3
"""Superinvestor holdings from Dataroma.

Retrieve superinvestor (top fund manager) holdings data for a given stock ticker.
Uses cached data from the Dataroma-Analyzer, tracking 81 institutional investors
including Warren Buffett, Bill Ackman, Charlie Munger, and others with $1.7T+ AUM.

Commands:
	get-superinvestor-info: Superinvestor holdings and recent activity for a ticker

Args:
	symbol (str): Ticker symbol (e.g., "NVDA", "MSFT", "BN")

Returns:
	dict: {
		"manager_count": int,                # Number of superinvestors holding this stock
		"ownership_rank": int|null,           # Rank among ~3300 tracked stocks (1 = most held)
		"avg_portfolio_pct": float,           # Average portfolio allocation among holding managers
		"adding_count": int,                  # Managers with Buy or Add activity in latest quarter
		"reducing_count": int,                # Managers with Sell or Reduce activity in latest quarter
		"managers": [
			{
				"name": str,                  # Manager/fund name
				"portfolio_pct": float,       # Position as % of their portfolio
				"recent_activity": str|null   # Latest quarter action: "Buy", "Add X%", "Reduce X%", "Sell"
			}
		],
		"thresholds": str                     # Classification criteria
	}

Example:
	>>> python superinvestor.py get-superinvestor-info BN
	{
		"manager_count": 9,
		"ownership_rank": 36,
		"avg_portfolio_pct": 7.78,
		"adding_count": 2,
		"reducing_count": 6,
		"managers": [
			{
				"name": "Bill Ackman",
				"portfolio_pct": 18.15,
				"recent_activity": "Reduce 0.21%"
			}
		],
		"thresholds": "ownership_rank: 1=most held (out of ~3300) | adding: Buy+Add | reducing: Sell+Reduce"
	}

Use Cases:
	- Smart money tracking: Which top investors hold this stock?
	- Conviction assessment: High avg_portfolio_pct = high conviction
	- Direction assessment: adding_count vs reducing_count shows accumulation/distribution trend
	- Cross-validation: Compare insider buying/selling with superinvestor activity

Notes:
	- Data sourced from Dataroma.com (scraped SEC 13F filings)
	- 81 tracked managers with curated quality weighting
	- 13F data has ~45-day lag from quarter end
	- Cache updated periodically — may not reflect latest quarter
	- Returns empty result (manager_count: 0) if ticker not found in cache

See Also:
	- holders.py: Insider transactions (SEC Form 4 via Finviz)
	- analysis/institutional_quality.py: Institutional ownership quality scoring (13F aggregate)
"""

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from utils import output_json, safe_run

_REPO_ROOT = Path(__file__).resolve().parents[5]
_DATAROMA_PATH = _REPO_ROOT / "References" / "Dataroma-Analyzer"
_CACHE_DIR = _DATAROMA_PATH / "cache"


def _load_dataroma():
	"""Load Dataroma holdings and compute ownership stats.

	Returns (holdings_df, stats_dict) or (None, {}) on failure.
	"""
	try:
		p = str(_DATAROMA_PATH)
		if p not in sys.path:
			sys.path.insert(0, p)
		from lib.data.data_loader import DataLoader

		dl = DataLoader(cache_dir=str(_CACHE_DIR))
		if not dl.load_all_data():
			return None, {}

		holdings = dl.holdings_df
		if holdings is None or holdings.empty:
			return None, {}

		stats = holdings.groupby("ticker").agg(
			manager_count=("manager_name", "count"),
			avg_portfolio_pct=("portfolio_percent", "mean"),
		).reset_index()
		stats = stats.sort_values("manager_count", ascending=False).reset_index(drop=True)
		stats["ownership_rank"] = stats.index + 1

		stats_dict = {}
		for _, row in stats.iterrows():
			stats_dict[row["ticker"]] = {
				"manager_count": int(row["manager_count"]),
				"ownership_rank": int(row["ownership_rank"]),
				"avg_portfolio_pct": round(float(row["avg_portfolio_pct"]), 2),
			}

		return holdings, stats_dict
	except Exception:
		return None, {}


@safe_run
def cmd_superinvestor_info(args):
	holdings, stats = _load_dataroma()
	ticker = args.symbol.upper()

	info = stats.get(ticker, {})
	if not info or holdings is None:
		output_json({
			"manager_count": 0,
			"ownership_rank": None,
			"avg_portfolio_pct": 0,
			"adding_count": 0,
			"reducing_count": 0,
			"managers": [],
			"thresholds": "ownership_rank: 1=most held (out of ~3300) | adding: Buy+Add | reducing: Sell+Reduce",
		})
		return

	ticker_holdings = holdings[holdings["ticker"] == ticker]
	managers = []
	adding = 0
	reducing = 0

	for _, row in ticker_holdings.iterrows():
		activity = str(row.get("recent_activity", "") or "")
		managers.append({
			"name": row.get("manager_name", ""),
			"portfolio_pct": round(float(row.get("portfolio_percent", 0)), 2),
			"recent_activity": activity if activity else None,
		})
		al = activity.lower()
		if al.startswith("buy") or al.startswith("add"):
			adding += 1
		elif al.startswith("sell") or al.startswith("reduce"):
			reducing += 1

	managers.sort(key=lambda m: m["portfolio_pct"], reverse=True)

	output_json({
		"manager_count": info["manager_count"],
		"ownership_rank": info["ownership_rank"],
		"avg_portfolio_pct": info["avg_portfolio_pct"],
		"adding_count": adding,
		"reducing_count": reducing,
		"managers": managers,
		"thresholds": "ownership_rank: 1=most held (out of ~3300) | adding: Buy+Add | reducing: Sell+Reduce",
	})


def main():
	parser = argparse.ArgumentParser(description="Superinvestor holdings data")
	sub = parser.add_subparsers(dest="command", required=True)

	sp = sub.add_parser("get-superinvestor-info")
	sp.add_argument("symbol")
	sp.set_defaults(func=cmd_superinvestor_info)

	args = parser.parse_args()
	args.func(args)


if __name__ == "__main__":
	main()
