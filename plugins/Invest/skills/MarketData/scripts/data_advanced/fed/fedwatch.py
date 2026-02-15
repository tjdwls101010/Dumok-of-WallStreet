#!/usr/bin/env python3
"""CME FedWatch Tool - FOMC rate change probabilities from Fed Funds futures.

Scrapes CME FedWatch HTML to extract market-implied probabilities for the next FOMC rate
decision (Cut/Hold/Hike). Provides probabilistic distribution across rate scenarios and
identifies current market consensus. Based on zekele-fed implementation (MIT License).

Args:
	None (no command-line arguments required)

Returns:
	dict: {
		"next_meeting": str,					 # Date of next FOMC meeting (YYYY-MM-DD)
		"data_as_of": str,					   # Timestamp of FedWatch data (UTC)
		"current_rate_bps": int,				 # Current Fed Funds rate in basis points
		"probabilities": {
			"cut": float,						# Probability of rate cut (percent)
			"hold": float,					   # Probability of no change (percent)
			"hike": float						# Probability of rate hike (percent)
		},
		"interpretation": str,				   # Human-readable interpretation
		"rate_scenarios": [
			{
				"rate_bps": int,				 # Target rate scenario in basis points
				"rate_pct": str,				 # Rate as percentage (formatted)
				"delta_bps": int,				# Change from current rate (basis points)
				"probability": float			 # Scenario probability (percent)
			},
			...
		]
	}

Example:
	>>> python fedwatch.py
	{
		"next_meeting": "2026-03-18",
		"data_as_of": "2026-02-05 14:30:00 UTC",
		"current_rate_bps": 425,
		"probabilities": {
			"cut": 65.2,
			"hold": 32.1,
			"hike": 2.7
		},
		"interpretation": "High Probability Cut Expected",
		"rate_scenarios": [
			{
				"rate_bps": 400,
				"rate_pct": "4.00%",
				"delta_bps": -25,
				"probability": 65.2
			},
			{
				"rate_bps": 425,
				"rate_pct": "4.25%",
				"delta_bps": 0,
				"probability": 32.1
			}
		]
	}

Use Cases:
	- Gauge market expectations for upcoming FOMC meetings
	- Identify divergence between Fed forward guidance and market pricing
	- Track evolution of rate probabilities leading up to FOMC decision
	- Assess uncertainty in monetary policy outlook (high hold probability = consensus)
	- Compare FedWatch probabilities with Fed dot plot projections
	- Build trading strategies around FOMC meeting risk premium

Notes:
	- No API key required (scrapes public CME website)
	- Rate limits: Use responsibly, avoid excessive requests (scraping-based)
	- Data delays: Real-time updates based on Fed Funds futures pricing
	- Data source: CME FedWatch Tool at https://www.cmegroup.com/markets/interest-rates/cme-fedwatch-tool.html
	- Probabilities derived from 30-day Fed Funds futures contract pricing
	- Interpretation thresholds: >70% = High Probability, <70% = Mixed Expectations
	- Time zone handling: Chicago Time (CT) converted to UTC with DST awareness
	- FedWatch accuracy: Historical accuracy ~85% for near-term meetings (1-2 meetings ahead)

See Also:
	- fed/fomc_calendar.py: Official FOMC meeting schedule
	- fred/rates.py: Current Fed Funds rate and historical data
	- fred/policy.py: Fed balance sheet and policy stance indicators
	- statistics/correlation.py: Correlation between FedWatch and market volatility
"""

import os
import re
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

import requests
from fomc_calendar import get_next_meeting_time
from utils import output_json, safe_run

# Static view URL (optimized, no need to fetch entry page)
VIEW_URL = "https://cmegroup-tools.quikstrike.net/User/QuikStrikeView.aspx?viewitemid=IntegratedFedWatchTool&userId=lwolf&jobRole=&company=&companyType="

HEADERS = {
	"User-Agent": (
		"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
		"AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36"
	),
	"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
	"Accept-Language": "en-US,en;q=0.9",
	"Accept-Encoding": "gzip, deflate, br",
	"Cache-Control": "no-cache",
	"Referer": "https://www.cmegroup.com/markets/interest-rates/cme-fedwatch-tool.html",
}


def fetch_view_html() -> str:
	"""Fetch the FedWatch view HTML.

	Returns:
		Raw HTML string

	Raises:
		requests.HTTPError: If request fails
	"""
	response = requests.get(VIEW_URL, headers=HEADERS, timeout=10)
	response.raise_for_status()
	return response.text


def parse_table(view_html: str) -> str:
	"""Extract the FedWatch probability table from HTML.

	Args:
		view_html: Raw HTML from FedWatch view

	Returns:
		Inner HTML of probability table (rows only)

	Raises:
		ValueError: If table not found
	"""
	# Match table with "Target Rate" and "Probability" headers
	pattern = (
		r"<table[^>]*>\s*<tr[^>]*>[\s\S]*?<th[^>]*>\s*Target\s+Rate[\s\S]*?</th>"
		r"[\s\S]*?<th[^>]*>\s*Probability[\s\S]*?</th>[\s\S]*?</tr>([\s\S]*?)</table>"
	)
	match = re.search(pattern, view_html, re.IGNORECASE)

	if not match:
		raise ValueError("FedWatch probability table not found in HTML")

	return match.group(1).strip()


def parse_rate_probs(table: str) -> list[dict]:
	"""Parse rate probabilities from FedWatch table.

	Args:
		table: Inner HTML of probability table

	Returns:
		List of rate probabilities with deltaRate, rate, and prob

	Raises:
		ValueError: If parsing fails or current rate not found
	"""
	cells = []
	current_cell = None

	# Match each row: <tr><td>rate</td><td>prob</td></tr>
	row_pattern = r"<tr[^>]*>\s*<td[^>]*>([^<]+?)</td>\s*<td[^>]*>([^<]*?)</td>[\s\S]*?</tr>"

	for match in re.finditer(row_pattern, table, re.IGNORECASE):
		rate_text = match.group(1).strip()
		prob_text = match.group(2).strip()

		if not rate_text:
			continue

		# Parse rate: "450-475 (Current)" or "475-500"
		rate_match = re.match(r"^\d+-(\d+)(\s*\(Current\))?$", rate_text, re.IGNORECASE)
		if not rate_match:
			continue

		rate = int(rate_match.group(1))
		is_current = bool(rate_match.group(2))

		if not prob_text:
			continue

		# Parse probability: "65.2 %"
		prob_match = re.match(r"^(\d+\.\d)\s*%$", prob_text)
		if not prob_match:
			raise ValueError(f"Invalid probability format: {prob_text}")

		# Convert "65.2" to 652 (basis points * 10)
		prob_str = prob_match.group(1).replace(".", "")
		prob = int(prob_str.ljust(2, "0"))  # Pad to 2 digits

		# Skip zero probabilities unless it's current rate
		if not is_current and prob == 0:
			continue

		cell = {"rate": rate, "prob": prob}
		if is_current:
			if current_cell is not None:
				raise ValueError("Duplicate current rate found")
			current_cell = cell

		cells.append(cell)

	if current_cell is None:
		raise ValueError("Current rate not found in table")

	# Sort by rate and calculate deltaRate
	cells.sort(key=lambda x: x["rate"])
	rate_probs = []
	for cell in cells:
		rate_probs.append(
			{
				"rate": cell["rate"],
				"prob": cell["prob"],
				"deltaRate": cell["rate"] - current_cell["rate"],
			}
		)

	return rate_probs


def parse_rate_probs_time(table: str) -> int:
	"""Parse the 'Data as of' timestamp from FedWatch table.

	Handles Chicago time (CT) with DST conversion to UTC.

	Args:
		table: Inner HTML of probability table

	Returns:
		Unix timestamp in milliseconds

	Raises:
		ValueError: If timestamp not found
	"""
	# Match: "Data as of 4 Feb 2026 14:30:00 CT"
	months = r"Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec"
	pattern = (
		rf"Data as of\s+(\d{{1,2}})\s+({months})\s+"
		rf"(\d{{2,4}})\s+(\d{{1,2}}):(\d{{1,2}}):(\d{{1,2}})\s+CT"
	)
	match = re.search(pattern, table, re.IGNORECASE)

	if not match:
		raise ValueError("Data timestamp not found in table")

	month_map = {
		"jan": 1,
		"feb": 2,
		"mar": 3,
		"apr": 4,
		"may": 5,
		"jun": 6,
		"jul": 7,
		"aug": 8,
		"sep": 9,
		"oct": 10,
		"nov": 11,
		"dec": 12,
	}

	day = int(match.group(1))
	month = month_map[match.group(2).lower()]
	year = int(match.group(3))
	hour = int(match.group(4))
	minute = int(match.group(5))
	second = int(match.group(6))

	# Chicago time offset: UTC-6 (CST) or UTC-5 (CDT)
	chicago_offset_hours = 6  # CST (winter)

	# Check if date is in CDT (roughly March-November)
	if 3 <= month <= 10:  # Approximate DST period
		chicago_offset_hours = 5  # CDT (summer)

	dt_utc = datetime(year, month, day, hour, minute, second, tzinfo=timezone.utc)
	timestamp_ms = int(dt_utc.timestamp() * 1000) + (chicago_offset_hours * 3600 * 1000)

	return timestamp_ms


@safe_run
def cmd_fedwatch(args):
	"""Get CME FedWatch FOMC rate change probabilities.

	Fetches current market-implied probabilities for the next FOMC decision.
	"""
	# Fetch and parse
	view_html = fetch_view_html()
	table = parse_table(view_html)
	rate_probs = parse_rate_probs(table)
	rate_probs_time = parse_rate_probs_time(table)

	# Get next FOMC meeting
	next_meeting = get_next_meeting_time()

	# Calculate probability categories
	current_rate = next(p for p in rate_probs if p["deltaRate"] == 0)["rate"]

	cut_prob = sum(p["prob"] for p in rate_probs if p["deltaRate"] < 0)
	hold_prob = sum(p["prob"] for p in rate_probs if p["deltaRate"] == 0)
	hike_prob = sum(p["prob"] for p in rate_probs if p["deltaRate"] > 0)

	# Interpretation (use raw prob values in basis points * 10)
	if cut_prob > 700:
		interpretation = "High Probability Cut Expected"
	elif hike_prob > 700:
		interpretation = "High Probability Hike Expected"
	elif hold_prob > 700:
		interpretation = "High Probability Hold Expected"
	else:
		interpretation = "Mixed Expectations"

	result = {
		"next_meeting": next_meeting.strftime("%Y-%m-%d"),
		"data_as_of": datetime.fromtimestamp(rate_probs_time / 1000, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
		"current_rate_bps": current_rate,
		"probabilities": {
			"cut": round(cut_prob / 10, 1),  # Convert to percentage
			"hold": round(hold_prob / 10, 1),
			"hike": round(hike_prob / 10, 1),
		},
		"interpretation": interpretation,
		"rate_scenarios": [
			{
				"rate_bps": p["rate"],
				"rate_pct": f"{p['rate'] / 100:.2f}%",
				"delta_bps": p["deltaRate"],
				"probability": round(p["prob"] / 10, 1),
			}
			for p in rate_probs
			if p["prob"] > 0  # Only non-zero probabilities
		],
	}

	output_json(result)


if __name__ == "__main__":
	import argparse

	parser = argparse.ArgumentParser(description="CME FedWatch - FOMC rate probabilities")
	args = parser.parse_args()

	cmd_fedwatch(args)
