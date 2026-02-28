#!/usr/bin/env python3
"""SEC Failures to Deliver (FTD) and litigation releases data.

Provides access to SEC Failures to Deliver dataset (settlement failures for equity securities)
and enforcement litigation releases RSS feed. FTD data indicates trading or operational
issues. Litigation releases track SEC enforcement actions.

Args:
	cmd_ftd:
	symbol (str): Stock ticker symbol (e.g., "GME", "AMC", "TSLA")
	--start-date (str): Start date filter (YYYY-MM-DD format) (optional)
	--end-date (str): End date filter (YYYY-MM-DD format) (optional)

	cmd_litigation:
	--limit (int): Maximum number of litigation releases to return (optional)

Returns:
	cmd_ftd:
	dict: {
		"data": [
			{
				"settlement_date": str,          # Settlement date (YYYYMMDD format)
				"symbol": str,                   # Stock ticker symbol
				"cusip": str,                    # CUSIP identifier
				"quantity": int,                 # Number of shares failed to deliver
				"description": str,              # Security description
				"price": float                   # Price per share (may be null)
			},
			...
		],
		"metadata": {
			"symbol": str,
			"start_date": str,
			"end_date": str,
			"total_results": int
		}
	}

	cmd_litigation:
	dict: {
		"data": [
			{
				"title": str,                    # Litigation release title
				"link": str,                     # URL to full release
				"summary": str,                  # Brief summary text
				"published": str,                # Publication date/time
				"id": str                        # Release identifier
			},
			...
		],
		"metadata": {
			"source": str,                       # "SEC Litigation Releases RSS"
			"total_results": int
		}
	}

Example:
	>>> python ftd.py GME --start-date 2025-01-01 --end-date 2026-02-05
	{
		"data": [
			{
				"settlement_date": "20260203",
				"symbol": "GME",
				"cusip": "36467W109",
				"quantity": 125000,
				"description": "GAMESTOP CORP NEW CL A",
				"price": 28.50
			}
		],
		"metadata": {
			"symbol": "GME",
			"start_date": "2025-01-01",
			"end_date": "2026-02-05",
			"total_results": 45
		}
	}

	>>> python ftd.py litigation --limit 10
	{
		"data": [
			{
				"title": "SEC Charges Investment Adviser...",
				"link": "https://www.sec.gov/litigation/litreleases/...",
				"summary": "The Securities and Exchange Commission...",
				"published": "Thu, 30 Jan 2026 10:00:00 EST"
			}
		]
	}

Use Cases:
	- Identify potential short squeeze candidates with persistent high FTDs
	- Monitor FTD spikes for settlement or operational risk signals
	- Track SEC enforcement actions for industry-wide compliance trends
	- Analyze FTD patterns around corporate events (earnings, M&A)
	- Screen for stocks with unusual FTD activity relative to float
	- Research historical FTD data for regulatory event studies

Notes:
	- No API key required (public SEC data access)
	- Rate limits: 10 requests per second per IP address (SEC enforced)
	- Data delays: FTD data published twice monthly (first and second half of month)
	- FTD threshold: Data includes all fails, no minimum threshold
	- Settlement cycle: T+2 for equities (fails occur when delivery not made by T+2)
	- Regulation SHO: Persistent FTDs trigger threshold security designation
	- Data format: Pipe-delimited text files in ZIP archives
	- Litigation releases: RSS feed updated as enforcement actions are announced

See Also:
	- sec/filings.py: SEC filings for fundamental company research
	- sec/insider.py: Insider trading activity
	- analysis/short_interest.py: Short interest data for FTD context
	- statistics/extremes.py: Extreme FTD detection and analysis
"""
import sys
import os
import re
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
import requests
from utils import output_json, safe_run

# Import shared utilities
from . import SEC_HEADERS


@safe_run
def cmd_ftd(args):
	"""Get Fail-to-Deliver data for a symbol."""
	# Get FTD data URLs from SEC data.json
	url = "https://www.sec.gov/data.json"
	response = requests.get(url, headers=SEC_HEADERS, timeout=30)
	response.raise_for_status()
	data = response.json()

	# Find the Fails-to-Deliver dataset
	ftd_urls = []
	for dataset in data.get("dataset", []):
		if dataset.get("title") == "Fails-to-Deliver Data":
			distribution = dataset.get("distribution", [])
			for dist in distribution:
				download_url = dist.get("downloadURL")
				if download_url:
					ftd_urls.append(download_url)
			break

	if not ftd_urls:
		output_json({
			"data": [],
			"metadata": {"symbol": args.symbol, "error": "FTD data URLs not found"}
		})
		return

	# Filter by date if provided
	results = []
	symbol_upper = args.symbol.upper()

	# Limit to most recent files to avoid excessive downloads
	max_files = 3
	for ftd_url in ftd_urls[:max_files]:
		try:
			resp = requests.get(ftd_url, headers=SEC_HEADERS, timeout=60)
			resp.raise_for_status()

			# Parse the zip file content
			import io
			import zipfile

			with zipfile.ZipFile(io.BytesIO(resp.content)) as z:
				for filename in z.namelist():
					with z.open(filename) as f:
						content = f.read().decode("latin-1")
						lines = content.strip().split("\n")

						# Skip header
						for line in lines[1:]:
							parts = line.split("|")
							if len(parts) >= 6:
								symbol = parts[1].strip() if len(parts) > 1 else ""
								if symbol == symbol_upper:
									settlement_date = parts[0].strip()
									# Apply date filters
									if args.start_date:
										try:
											sd = datetime.strptime(settlement_date, "%Y%m%d")
											start = datetime.strptime(args.start_date, "%Y-%m-%d")
											if sd < start:
												continue
										except ValueError:
											pass
									if args.end_date:
										try:
											sd = datetime.strptime(settlement_date, "%Y%m%d")
											end = datetime.strptime(args.end_date, "%Y-%m-%d")
											if sd > end:
												continue
										except ValueError:
											pass

									results.append({
										"settlement_date": settlement_date,
										"symbol": symbol,
										"cusip": parts[2].strip() if len(parts) > 2 else None,
										"quantity": int(parts[3].strip()) if len(parts) > 3 and parts[3].strip().isdigit() else None,
										"description": parts[4].strip() if len(parts) > 4 else None,
										"price": float(parts[5].strip()) if len(parts) > 5 and parts[5].strip().replace(".", "").isdigit() else None,
									})
		except Exception:
			# Skip files that fail to download/parse
			continue

	# Sort by date descending
	results.sort(key=lambda x: x.get("settlement_date", ""), reverse=True)

	output_json({
		"data": results,
		"metadata": {
			"symbol": args.symbol,
			"start_date": args.start_date,
			"end_date": args.end_date,
			"total_results": len(results),
		}
	})


@safe_run
def cmd_litigation(args):
	"""Get SEC enforcement actions from RSS feed."""
	url = "https://www.sec.gov/enforcement-litigation/litigation-releases/rss"
	response = requests.get(url, headers=SEC_HEADERS, timeout=30)
	response.raise_for_status()

	# Parse RSS XML
	import xml.etree.ElementTree as ET

	# Clean XML content for invalid entities
	content = response.text
	content = re.sub(r"&(?!amp;|lt;|gt;|quot;|apos;)", "&amp;", content)

	root = ET.fromstring(content)
	channel = root.find("channel")

	results = []
	if channel is not None:
		for item in channel.findall("item"):
			title = item.find("title")
			link = item.find("link")
			description = item.find("description")
			pub_date = item.find("pubDate")
			creator = item.find("{http://purl.org/dc/elements/1.1/}creator")

			# Clean up text
			title_text = title.text if title is not None else ""
			title_text = re.sub(r"[^\w\s]|_", "", title_text).replace("\n", " ")

			summary_text = description.text if description is not None else ""
			summary_text = re.sub(r"[^\w\s]|_", "", summary_text).replace("\n", " ")

			results.append({
				"title": title_text,
				"link": link.text if link is not None else None,
				"summary": summary_text,
				"published": pub_date.text if pub_date is not None else None,
				"id": creator.text if creator is not None else None,
			})

			if args.limit and len(results) >= args.limit:
				break

	output_json({
		"data": results,
		"metadata": {
			"source": "SEC Litigation Releases RSS",
			"total_results": len(results),
		}
	})
