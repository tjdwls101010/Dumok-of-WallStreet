#!/usr/bin/env python3
"""Bottom-up sector leadership dashboard for Minervini SEPA methodology.

Identifies which industry groups are producing concentrated leader emergence
by screening for Minervini leaders and aggregating by sector/industry group.
This implements Minervini's bottom-up approach: "Let stocks point you to the sector."

Commands:
	scan        Full sector leadership scan with group performance enrichment
	top-groups  Quick top N industry groups by leader concentration

Args:
	For scan:
	--limit (int): Maximum leader stocks to screen (default: 200)
	--preset (str): Screening preset name from finviz_presets.py (default: minervini_leaders)

	For top-groups:
	--top (int): Number of top groups to return (default: 10)
	--limit (int): Maximum leader stocks to screen (default: 200)
	--preset (str): Screening preset name from finviz_presets.py (default: minervini_leaders)

Returns:
	dict: {
	"leadership_dashboard": [
	{
		"industry_group": str,
		"sector": str,
		"leader_count": int,
		"leader_tickers": list[str],
		"group_perf_1w": float | None,
		"group_perf_1m": float | None,
		"group_perf_3m": float | None,
		"group_perf_1y": float | None,
		"group_total_stocks": int | None,
		"leadership_rank": int
	}
	],
	"metadata": {
	"total_leaders_found": int,
	"groups_with_leaders": int,
	"scan_preset": str,
	"timestamp": str
	}
	}

Example:
	>>> python sector_leaders.py scan
	{
	"leadership_dashboard": [
	{
		"industry_group": "Semiconductors",
		"sector": "Technology",
		"leader_count": 8,
		"leader_tickers": ["AMD", "AVGO", "NVDA", ...],
		"group_perf_1m": 0.12,
		"group_perf_3m": 0.28,
		"leadership_rank": 1
	}
	],
	"metadata": {"total_leaders_found": 45, "groups_with_leaders": 12}
	}

	>>> python sector_leaders.py scan --preset minervini_stage2
	{"leadership_dashboard": [...], "metadata": {"scan_preset": "minervini_stage2", ...}}

	>>> python sector_leaders.py top-groups --top 5
	{"top_groups": [...top 5 entries...], "metadata": {...}}

Use Cases:
	- Market health assessment via leader count and distribution (Type A queries)
	- Sector-first stock discovery: find the leading group, then drill into leaders (Type C)
	- Risk monitoring: detect narrowing leadership or rotation (Type F)
	- Sector rotation tracking: compare dashboard snapshots over time

Notes:
	- Default preset is minervini_leaders from finviz_presets.py (Year +20%, Quarter +10%,
	  near 52W high, EPS growth >25%, above 200MA, volume >200K)
	- --preset parameter allows using any preset from finviz_presets.py (Module Neutrality)
	- Enriches with Finviz industry group performance data for context
	- Groups are ranked by leader count (descending) as the primary sort key
	- Performance enrichment may fail gracefully (returns dashboard without perf data)

See Also:
	- finviz.py: Underlying Finviz screening and group analysis
	- finviz_presets.py: PRESETS dict with minervini_leaders definition
	- minervini.py: Full SEPA analysis for individual stocks found in dashboard
	- sector_leadership.md: Workflow guide for interpreting dashboard results
"""

import argparse
import os
import sys
from collections import defaultdict
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from utils import output_json, safe_run

try:
	from .finviz_presets import PRESETS
except ImportError:
	from finviz_presets import PRESETS

# Sector ETF mappings for fallback when Finviz is unavailable
SECTOR_ETFS = {
	"Technology": "XLK",
	"Healthcare": "XLV",
	"Financial": "XLF",
	"Communication Services": "XLC",
	"Industrials": "XLI",
	"Consumer Staples": "XLP",
	"Consumer Discretionary": "XLY",
	"Energy": "XLE",
	"Real Estate": "XLRE",
	"Materials": "XLB",
	"Utilities": "XLU",
}


def _scan_via_etf(period="6mo"):
	"""ETF-based sector leadership scan as fallback when Finviz is unavailable.

	Compares 11 sector ETFs against SPY using RS scoring to identify
	leading and lagging sectors. Note: this provides sector-level leadership
	only -- individual stock identification within sectors is not possible.

	Args:
			period: Historical data period for RS calculation (default: "6mo").

	Returns:
			list[dict]: Sector entries with RS scores, sorted by RS descending.
	"""
	import yfinance as yf

	spy_data = yf.Ticker("SPY").history(period=period)
	if spy_data.empty:
		return []

	spy_close = spy_data["Close"]
	spy_ret_3m = (
		(float(spy_close.iloc[-1]) / float(spy_close.iloc[-min(63, len(spy_close))]) - 1) * 100
		if len(spy_close) > 63
		else 0
	)
	spy_ret_6m = (float(spy_close.iloc[-1]) / float(spy_close.iloc[0]) - 1) * 100

	results = []
	for sector, etf in SECTOR_ETFS.items():
		try:
			etf_data = yf.Ticker(etf).history(period=period)
			if etf_data.empty:
				continue
			etf_close = etf_data["Close"]
			ret_3m = (
				(float(etf_close.iloc[-1]) / float(etf_close.iloc[-min(63, len(etf_close))]) - 1) * 100
				if len(etf_close) > 63
				else 0
			)
			ret_6m = (float(etf_close.iloc[-1]) / float(etf_close.iloc[0]) - 1) * 100

			# Weighted RS composite vs SPY (3m x2 + 6m x1)
			spy_composite = spy_ret_3m * 2 + spy_ret_6m
			etf_composite = ret_3m * 2 + ret_6m
			rs_vs_spy = etf_composite / spy_composite if spy_composite != 0 else 1.0

			results.append(
				{
					"sector": sector,
					"etf": etf,
					"return_3m_pct": round(ret_3m, 2),
					"return_6m_pct": round(ret_6m, 2),
					"rs_vs_spy": round(rs_vs_spy, 3),
					"leadership_rank": 0,
				}
			)
		except Exception:
			continue

	results.sort(key=lambda x: -x["rs_vs_spy"])
	for i, entry in enumerate(results, 1):
		entry["leadership_rank"] = i

	return results


def _screen_leaders(limit=200, preset_name="minervini_leaders"):
	"""Screen for leaders using a configurable preset from finviz_presets.py.

	Uses finvizfinance Overview screener with the specified preset filter set.
	Defaults to minervini_leaders (Year +20%, Quarter +10%, near 52W high,
	EPS QoQ >25%, Volume >200K, above 200MA).

	Args:
			limit (int): Maximum number of stocks to return from the screener. Default 200.
			preset_name (str): Preset name from finviz_presets.py PRESETS dict.
					Default "minervini_leaders".

	Returns:
			list[dict]: List of screener result rows. Each dict contains at minimum
					Ticker, Sector, Industry, Price, Change, Volume columns from Finviz.
					Returns empty list if no stocks match or screener fails.
	"""
	from finvizfinance.screener.overview import Overview

	preset = PRESETS[preset_name]
	filters_dict = preset["filters"]

	foverview = Overview()
	if "signal" in preset:
		foverview.set_filter(signal=preset["signal"], filters_dict=filters_dict)
	else:
		foverview.set_filter(filters_dict=filters_dict)

	df = foverview.screener_view(limit=limit, verbose=0)
	if df is None or df.empty:
		return []

	return df.to_dict(orient="records")


def _group_by_industry(leaders):
	"""Group leader stocks by industry, collecting tickers and sector info.

	Args:
			leaders (list[dict]): Screener result rows from _screen_leaders().

	Returns:
			defaultdict: Mapping of industry name to {"tickers": list[str], "sector": str}.
					Each industry entry accumulates all leader tickers and retains the first
					sector encountered for that industry group.
	"""
	groups = defaultdict(lambda: {"tickers": [], "sector": None})

	for row in leaders:
		industry = row.get("Industry", "Unknown")
		ticker = row.get("Ticker", "")
		sector = row.get("Sector", "Unknown")

		if industry and ticker:
			groups[industry]["tickers"].append(ticker)
			if groups[industry]["sector"] is None:
				groups[industry]["sector"] = sector

	return groups


def _fetch_group_performance():
	"""Fetch industry group performance data from Finviz for enrichment.

	Retrieves weekly, monthly, quarterly, half-year, yearly, and YTD performance
	for all Finviz industry groups. Used to enrich the leadership dashboard with
	aggregate group-level price performance context.

	Returns:
			dict: Mapping of industry group name (str) to performance dict containing:
					perf_1w (float|None), perf_1m (float|None), perf_3m (float|None),
					perf_6m (float|None), perf_1y (float|None), perf_ytd (float|None),
					num_stocks (int|None).
					Returns empty dict on any failure (graceful degradation).
	"""
	try:
		from finvizfinance.group import Performance

		group_view = Performance()
		df = group_view.screener_view(group="Industry", order="Performance (Week)")

		if df is None or df.empty:
			return {}

		perf_map = {}
		for row in df.to_dict(orient="records"):
			name = row.get("Name", "")
			if not name:
				continue

			def parse_pct(val):
				if val is None or (isinstance(val, float) and val != val):
					return None
				if isinstance(val, str) and "%" in val:
					return round(float(val.replace("%", "")) / 100, 4)
				if isinstance(val, (int, float)):
					return round(float(val), 4)
				return None

			perf_map[name] = {
				"perf_1w": parse_pct(row.get("Perf Week")),
				"perf_1m": parse_pct(row.get("Perf Month")),
				"perf_3m": parse_pct(row.get("Perf Quart")),
				"perf_6m": parse_pct(row.get("Perf Half")),
				"perf_1y": parse_pct(row.get("Perf Year")),
				"perf_ytd": parse_pct(row.get("Perf YTD")),
				"num_stocks": row.get("Number of Stocks"),
			}

		return perf_map

	except Exception:
		return {}


def _build_dashboard(leaders, enrich_performance=True):
	"""Build the sector leadership dashboard from screened leaders.

	Groups leaders by industry, optionally enriches with Finviz group performance
	data, sorts by leader concentration (descending), and assigns leadership rank.

	Args:
			leaders (list[dict]): Screener result rows from _screen_leaders().
			enrich_performance (bool): Whether to fetch and merge group-level performance
					data from Finviz. Default True. Set False for faster execution when
					only leader counts are needed.

	Returns:
			list[dict]: Sorted dashboard entries, each containing industry_group, sector,
					leader_count, leader_tickers, leadership_rank, and optionally group_perf_*
					fields when enrichment is enabled.
	"""
	groups = _group_by_industry(leaders)

	# Optionally enrich with group-level performance data
	perf_map = _fetch_group_performance() if enrich_performance else {}

	dashboard = []
	for industry, data in groups.items():
		entry = {
			"industry_group": industry,
			"sector": data["sector"],
			"leader_count": len(data["tickers"]),
			"leader_tickers": sorted(data["tickers"]),
		}

		# Enrich with performance data if available
		perf = perf_map.get(industry, {})
		if perf:
			entry["group_perf_1w"] = perf.get("perf_1w")
			entry["group_perf_1m"] = perf.get("perf_1m")
			entry["group_perf_3m"] = perf.get("perf_3m")
			entry["group_perf_1y"] = perf.get("perf_1y")
			entry["group_total_stocks"] = perf.get("num_stocks")

		dashboard.append(entry)

	# Sort by leader count descending, then alphabetically
	dashboard.sort(key=lambda x: (-x["leader_count"], x["industry_group"]))

	# Assign leadership rank
	for i, entry in enumerate(dashboard, 1):
		entry["leadership_rank"] = i

	return dashboard


@safe_run
def cmd_scan(args):
	"""Full sector leadership scan: find leaders, group by industry, rank by concentration.

	Screens for Minervini leaders, groups them by industry, enriches with group
	performance data, and outputs a ranked leadership dashboard as JSON.
	Falls back to ETF-based sector analysis when Finviz is unavailable.

	Args:
			args: Parsed argparse namespace with:
					limit (int): Maximum leader stocks to screen.
					fallback (str|None): Fallback mode ('etf' or None).

	Returns:
			Outputs JSON to stdout with leadership_dashboard array and metadata.
	"""
	use_etf = getattr(args, "fallback", None) == "etf"
	preset_name = getattr(args, "preset", "minervini_leaders")

	if not use_etf:
		try:
			leaders = _screen_leaders(limit=args.limit, preset_name=preset_name)
		except Exception:
			leaders = []
			use_etf = True  # Auto-fallback on Finviz failure

		if not leaders and not use_etf:
			use_etf = True  # Auto-fallback when no results

	if use_etf:
		etf_results = _scan_via_etf()
		output_json(
			{
				"leadership_dashboard": etf_results,
				"metadata": {
					"total_leaders_found": 0,
					"groups_with_leaders": len(etf_results),
					"scan_mode": "etf_fallback",
					"note": "ETF-based sector analysis: provides sector-level leadership only. "
					"Individual stock identification requires Finviz or manual screening.",
					"timestamp": datetime.now(timezone.utc).isoformat(),
				},
			}
		)
		return

	dashboard = _build_dashboard(leaders, enrich_performance=True)

	output_json(
		{
			"leadership_dashboard": dashboard,
			"metadata": {
				"total_leaders_found": len(leaders),
				"groups_with_leaders": len(dashboard),
				"scan_preset": preset_name,
				"timestamp": datetime.now(timezone.utc).isoformat(),
			},
		}
	)


@safe_run
def cmd_top_groups(args):
	"""Quick top N industry groups by leader concentration.

	Same as scan but truncates output to the top N groups. Useful for quick
	sector-first discovery workflows where only the leading groups matter.

	Args:
			args: Parsed argparse namespace with:
					top (int): Number of top groups to return.
					limit (int): Maximum leader stocks to screen.

	Returns:
			Outputs JSON to stdout with top_groups array and metadata.
	"""
	preset_name = getattr(args, "preset", "minervini_leaders")
	leaders = _screen_leaders(limit=args.limit, preset_name=preset_name)

	if not leaders:
		output_json(
			{
				"top_groups": [],
				"metadata": {
					"total_leaders_found": 0,
					"top_n": args.top,
					"scan_preset": preset_name,
					"timestamp": datetime.now(timezone.utc).isoformat(),
				},
			}
		)
		return

	dashboard = _build_dashboard(leaders, enrich_performance=True)
	top = dashboard[: args.top]

	output_json(
		{
			"top_groups": top,
			"metadata": {
				"total_leaders_found": len(leaders),
				"groups_with_leaders": len(dashboard),
				"top_n": args.top,
				"scan_preset": preset_name,
				"timestamp": datetime.now(timezone.utc).isoformat(),
			},
		}
	)


def main():
	parser = argparse.ArgumentParser(description="Bottom-up sector leadership dashboard for Minervini SEPA")
	sub = parser.add_subparsers(dest="command", required=True)

	# scan - Full sector leadership scan
	p_scan = sub.add_parser("scan", help="Full sector leadership scan")
	p_scan.add_argument(
		"--limit",
		type=int,
		default=200,
		help="Maximum number of leader stocks to screen (default: 200)",
	)
	p_scan.add_argument(
		"--preset",
		default="minervini_leaders",
		choices=list(PRESETS.keys()),
		help="Screening preset from finviz_presets.py (default: minervini_leaders)",
	)
	p_scan.add_argument(
		"--fallback",
		choices=["etf"],
		default=None,
		help="Fallback mode: 'etf' for ETF-based sector analysis when Finviz is unavailable",
	)
	p_scan.set_defaults(func=cmd_scan)

	# top-groups - Quick top N groups
	p_top = sub.add_parser("top-groups", help="Top N industry groups by leader count")
	p_top.add_argument(
		"--top",
		type=int,
		default=10,
		help="Number of top groups to show (default: 10)",
	)
	p_top.add_argument(
		"--limit",
		type=int,
		default=200,
		help="Maximum number of leader stocks to screen (default: 200)",
	)
	p_top.add_argument(
		"--preset",
		default="minervini_leaders",
		choices=list(PRESETS.keys()),
		help="Screening preset from finviz_presets.py (default: minervini_leaders)",
	)
	p_top.set_defaults(func=cmd_top_groups)

	args = parser.parse_args()
	args.func(args)


if __name__ == "__main__":
	main()
