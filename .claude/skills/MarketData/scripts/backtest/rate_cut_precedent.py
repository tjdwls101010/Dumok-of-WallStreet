#!/usr/bin/env python3
"""Analyze historical Fed rate cut cycles and S&P 500 forward returns.

Detects Federal Reserve rate cutting cycles (defined as N consecutive monthly rate cuts)
and calculates S&P 500 forward returns at multiple horizons (30/60/90/180/365 days) after
cycle initiation. Provides precedent-based analysis for current rate cut environments.

Args:
	--cuts (int): Minimum consecutive rate cuts to define a cycle (default: 3)
		- 3 cuts: Captures most easing cycles
		- 4+ cuts: Filters for more aggressive easing

Returns:
	dict: {
		"analysis": str,        # Analysis description
		"cuts_required": int,   # Minimum cuts threshold used
		"cycles_found": int,    # Number of historical cycles detected
		"cycles": [             # List of cycle details
			{
				"date": str,            # First cut date in cycle
				"rate": float,          # Fed Funds rate at cycle start
				"total_cuts": int,      # Total cuts in this cycle
				"spy_start_date": str,  # Nearest S&P 500 trading date
				"spy_start_price": float, # S&P 500 price at cycle start
				"forward_returns": {
					"30d": float,       # 30-day forward return %
					"60d": float,       # 60-day forward return %
					"90d": float,       # 90-day forward return %
					"180d": float,      # 180-day forward return %
					"365d": float       # 365-day forward return %
				}
			}
		],
		"average_returns": {    # Aggregated statistics across all cycles
			"30d": {
				"mean": float,      # Average 30-day return
				"std": float,       # Standard deviation
				"min": float,       # Worst outcome
				"max": float,       # Best outcome
				"count": int        # Number of cycles with data
			},
			"60d": {...},
			"90d": {...},
			"180d": {...},
			"365d": {...}
		},
		"date": str             # Analysis date
	}

Example:
	>>> python rate_cut_precedent.py --cuts 3
	{
		"analysis": "Historical Rate Cut Cycles",
		"cuts_required": 3,
		"cycles_found": 4,
		"cycles": [
			{
				"date": "2007-09-01",
				"rate": 5.25,
				"total_cuts": 10,
				"forward_returns": {
					"30d": -4.5,
					"60d": -8.2,
					"90d": -15.3,
					"180d": -28.5,
					"365d": -35.2
				}
			}
		],
		"average_returns": {
			"30d": {"mean": 2.1, "std": 5.8, "min": -4.5, "max": 8.3, "count": 4},
			"90d": {"mean": 4.5, "std": 12.5, "min": -15.3, "max": 18.2, "count": 4}
		},
		"date": "2026-02-05"
	}

Use Cases:
	- Precedent analysis: Compare current rate cut cycle to historical patterns
	- Forward return estimation: Assess expected S&P 500 performance during easing
	- Risk assessment: Quantify dispersion of outcomes across cycles
	- Macro strategy validation: Test if rate cuts reliably predict equity returns
	- Market timing: Determine optimal entry/exit timing relative to Fed actions

Notes:
	- Survivorship bias: Analysis uses S&P 500 index (survivor-biased)
	- Small sample size: Limited number of rate cut cycles since 2000 (low N)
	- Overfitting risk: Each cycle has unique macro context (2008 crisis vs COVID)
	- Non-stationarity: Market structure and Fed policy tools have evolved
	- Delayed effect: Rate cuts may take 6-12 months to impact economy
	- Regime dependency: Outcomes vary by recession depth and credit conditions
	- Look-ahead bias: Ensure analysis doesn't use data unavailable at cycle start

See Also:
	- conditional.py: Calculate probability of specific return targets
	- event_returns.py: Analyze return distributions after macro events
	- extreme_reversals.py: Study market extremes during crisis periods
"""

import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import numpy as np
import pandas as pd
import yfinance as yf
from utils import output_json, safe_run


@safe_run
def cmd_rate_cut_precedent(args):
	"""Analyze historical rate cut cycles and forward returns.

	Detects rate cut cycles (N consecutive cuts) and calculates S&P 500
	forward returns at 30/60/90/180/365 days after cycle start.
	"""
	# 1. Fetch Fed Funds Rate from FRED (use monthly data for cleaner cycle detection)
	fred_script = os.path.join(os.path.dirname(__file__), "..", "data_advanced", "fred", "__init__.py")
	result = subprocess.run(
		[sys.executable, fred_script, "fed-funds", "--start-date", "2000-01-01"],
		capture_output=True,
		text=True,
		timeout=30,
	)

	if result.returncode != 0:
		output_json({"error": "Failed to fetch FRED data", "stderr": result.stderr})
		return

	fred_data = json.loads(result.stdout)
	fedfunds_dict = fred_data["data"]["FEDFUNDS"]  # Monthly data

	# Convert to pandas Series with datetime index
	fed_rate = pd.Series({pd.Timestamp(k): v for k, v in fedfunds_dict.items()}).sort_index()

	# 2. Detect rate cut cycles (N consecutive cuts)
	# Rate cut = current rate < previous rate
	rate_diff = fed_rate.diff()
	is_cut = rate_diff < -0.01  # At least 1 bp cut

	# Find consecutive cut sequences
	cut_groups = (is_cut != is_cut.shift()).cumsum()
	consecutive_cuts = is_cut.groupby(cut_groups).cumsum()

	# Find cycle starts (first cut in sequence with N+ total cuts)
	min_cuts = args.cuts
	cycle_starts = []

	for group_id in cut_groups[is_cut].unique():
		group_mask = (cut_groups == group_id) & is_cut
		group_data = consecutive_cuts[group_mask]

		if len(group_data) >= min_cuts:
			# First cut date in this cycle
			first_cut_date = group_data.index[0]
			total_cuts = len(group_data)
			start_rate = fed_rate[first_cut_date]

			cycle_starts.append(
				{"date": str(first_cut_date.date()), "rate": round(float(start_rate), 2), "total_cuts": total_cuts}
			)

	if not cycle_starts:
		output_json(
			{
				"message": f"No rate cut cycles with {min_cuts}+ consecutive cuts found since 2000",
				"cuts_required": min_cuts,
				"date": str(pd.Timestamp.now().date()),
			}
		)
		return

	# 3. Calculate S&P 500 forward returns for each cycle
	ticker = yf.Ticker("^GSPC")
	spy_data = ticker.history(period="max", interval="1d")

	forward_days = [30, 60, 90, 180, 365]

	for cycle in cycle_starts:
		cycle_date = pd.Timestamp(cycle["date"])

		# Convert to timezone-aware if spy_data has timezone
		if spy_data.index.tz is not None:
			cycle_date = cycle_date.tz_localize(spy_data.index.tz)

		try:
			# Find nearest trading day
			idx = spy_data.index.get_indexer([cycle_date], method="nearest")[0]
			actual_date = spy_data.index[idx]
			start_price = spy_data["Close"].iloc[idx]

			cycle["spy_start_date"] = str(actual_date.date())
			cycle["spy_start_price"] = round(float(start_price), 2)
			cycle["forward_returns"] = {}

			for days in forward_days:
				if idx + days < len(spy_data):
					future_price = spy_data["Close"].iloc[idx + days]
					ret = (future_price - start_price) / start_price * 100
					cycle["forward_returns"][f"{days}d"] = round(float(ret), 2)
				else:
					cycle["forward_returns"][f"{days}d"] = None

		except Exception as e:
			cycle["error"] = str(e)

	# 4. Calculate average returns across all cycles
	avg_returns = {}
	for days in forward_days:
		key = f"{days}d"
		returns = [
			c["forward_returns"][key]
			for c in cycle_starts
			if key in c.get("forward_returns", {}) and c["forward_returns"][key] is not None
		]
		if returns:
			avg_returns[key] = {
				"mean": round(np.mean(returns), 2),
				"std": round(np.std(returns), 2),
				"min": round(min(returns), 2),
				"max": round(max(returns), 2),
				"count": len(returns),
			}

	result = {
		"analysis": "Historical Rate Cut Cycles",
		"cuts_required": min_cuts,
		"cycles_found": len(cycle_starts),
		"cycles": cycle_starts,
		"average_returns": avg_returns,
		"date": str(pd.Timestamp.now().date()),
	}
	output_json(result)


if __name__ == "__main__":
	import argparse

	parser = argparse.ArgumentParser(description="Analyze historical rate cut cycles and forward returns")
	parser.add_argument("--cuts", type=int, default=3, help="Minimum consecutive rate cuts required")
	args = parser.parse_args()
	cmd_rate_cut_precedent(args)
