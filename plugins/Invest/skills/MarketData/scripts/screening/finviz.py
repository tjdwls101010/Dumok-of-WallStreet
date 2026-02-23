#!/usr/bin/env python3
"""Finviz stock screening, sector/industry group analysis, and market breadth via finvizfinance.

Provides preset-based stock screening, sector/industry group performance comparison,
sector-specific screening with quality filters, and market breadth analysis (new 52-week
highs vs lows) for comprehensive market analysis.

Commands:
	screen          Screen stocks using predefined presets (minervini_leaders, etc.)
	groups          Sector/industry group performance, valuation, or overview comparison
	presets         List all available screening presets
	sector-screen   Screen stocks within a specific sector with quality filters
	market-breadth  New 52-week highs vs lows count by exchange with sector breakdown

Args:
	For screen:
		--preset (str): Screening preset name (required)
		--limit (int): Maximum results (default: 50)

	For groups:
		--group (str): Group type - sector, industry, country, etc. (default: sector)
		--metric (str): Data metric - performance, valuation, overview (default: performance)
		--order (str): Sort order - perf_week, perf_month, perf_year, etc. (default: perf_week)

	For sector-screen:
		--sector (str): Sector to screen (required)
		--criteria (str): Filter criteria - all, growth, value, momentum, dividend, quality (default: all)
		--limit (int): Maximum results (default: 50)

	For market-breadth:
		No required args. Returns new highs/lows by exchange with sector breakdown.

Returns:
	For screen:
		dict: {"data": [screener rows], "metadata": {preset, count, timestamp}}

	For groups:
		dict: {"data": [group rows with normalized performance], "metadata": {group, metric, count}}

	For market-breadth:
		dict: {
			"nyse": {"new_highs": int, "new_lows": int, "ratio": float},
			"nasdaq": {"new_highs": int, "new_lows": int, "ratio": float},
			"total": {"new_highs": int, "new_lows": int, "ratio": float},
			"new_highs_by_sector": [{"sector": str, "count": int}],
			"interpretation": str,
			"metadata": {"timestamp": str}
		}

Example:
	>>> python finviz.py screen --preset minervini_leaders
	{"data": [{"Ticker": "NVDA", "Sector": "Technology", ...}], "metadata": {...}}

	>>> python finviz.py groups --group industry --metric performance --order perf_month
	{"data": [{"name": "Semiconductors", "performance_1m": 0.12, ...}], "metadata": {...}}

	>>> python finviz.py market-breadth
	{
		"nyse": {"new_highs": 116, "new_lows": 38, "ratio": 3.05},
		"nasdaq": {"new_highs": 81, "new_lows": 154, "ratio": 0.53},
		"total": {"new_highs": 197, "new_lows": 192, "ratio": 1.03},
		"new_highs_by_sector": [{"sector": "Industrials", "count": 60}, ...],
		"interpretation": "Neutral breadth... DIVERGENCE: NYSE healthy but NASDAQ weak..."
	}

Use Cases:
	- Preset-based stock screening for Minervini SEPA candidates
	- Sector/industry group ranking by performance, valuation, or overview
	- Sector-specific screening with growth, value, momentum, or quality filters
	- Market breadth assessment for Type A (market environment) and Type F (risk) analyses
	- NYSE vs NASDAQ divergence detection for sector rotation signals

Notes:
	- Screening presets are defined in finviz_presets.py (minervini_leaders, minervini_breakout, etc.)
	- Group performance data includes normalized percent values (decimals, not strings)
	- Market breadth uses Finviz signal filters (New High / New Low) per exchange
	- Sector breakdown of new highs shows where leadership is concentrated
	- Interpretation includes automatic NYSE/NASDAQ divergence detection

See Also:
	- finviz_presets.py: PRESETS dict with all screening preset definitions
	- sector_leaders.py: Bottom-up sector leadership dashboard using these presets
	- minervini.py: Full SEPA analysis for individual stocks
"""

import argparse
import os
import sys
import time
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from utils import error_json, output_json, safe_run

# User-Agent header to reduce 403 errors from Finviz
HEADERS = {
	"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}


def _fetch_with_retry(func, max_retries=3, base_delay=2):
	"""Execute a Finviz fetch function with exponential backoff retry.

	Retries on 403/forbidden errors with increasing delays.
	Returns the result on success, raises on final failure.
	"""
	last_error = None
	for attempt in range(max_retries):
		try:
			return func()
		except Exception as e:
			last_error = e
			error_str = str(e).lower()
			if "403" in error_str or "forbidden" in error_str:
				if attempt < max_retries - 1:
					delay = base_delay * (2**attempt)
					time.sleep(delay)
					continue
			raise
	raise last_error


try:
	from .finviz_presets import PRESETS
except ImportError:
	from finviz_presets import PRESETS

# Sector filter mappings for finvizfinance screener
SECTOR_FILTERS = {
	"basic_materials": "Basic Materials",
	"communication_services": "Communication Services",
	"consumer_cyclical": "Consumer Cyclical",
	"consumer_defensive": "Consumer Defensive",
	"energy": "Energy",
	"financial": "Financial",
	"healthcare": "Healthcare",
	"industrials": "Industrials",
	"real_estate": "Real Estate",
	"technology": "Technology",
	"utilities": "Utilities",
}

# Group mappings for finvizfinance
GROUPS_DICT = {
	"sector": "Sector",
	"industry": "Industry",
	"country": "Country (U.S. listed stocks only)",
	"capitalization": "Capitalization",
	"energy": "Industry (Energy)",
	"materials": "Industry (Basic Materials)",
	"industrials": "Industry (Industrials)",
	"consumer_cyclical": "Industry (Consumer Cyclical)",
	"consumer_defensive": "Industry (Consumer Defensive)",
	"healthcare": "Industry (Healthcare)",
	"financial": "Industry (Financial)",
	"technology": "Industry (Technology)",
	"communication_services": "Industry (Communication Services)",
	"utilities": "Industry (Utilities)",
	"real_estate": "Industry (Real Estate)",
}


def _parse_percent(val):
	"""Convert percent string to float."""
	if val is None:
		return None
	if isinstance(val, str) and "%" in val:
		return float(val.replace("%", "")) / 100
	return val


def _parse_market_cap(val):
	"""Convert abbreviated market cap to integer."""
	if val is None:
		return None
	if isinstance(val, str):
		val = val.replace("M", "e+6").replace("B", "e+9").replace("T", "e+12").replace("K", "e+3")
		try:
			return int(float(val))
		except (ValueError, TypeError):
			return None
	return val


def _normalize_screener_row(row):
	"""Normalize a screener result row to consistent format."""
	result = {}
	for key, val in row.items():
		# Clean up column names
		clean_key = key.strip() if isinstance(key, str) else key

		# Handle NaN values
		if val != val:  # NaN check
			result[clean_key] = None
		elif isinstance(val, str) and val in ("N/A", "-", ""):
			result[clean_key] = None
		else:
			result[clean_key] = val
	return result


def _normalize_group_row(row):
	"""Normalize a group result row to consistent format."""
	result = {}

	# Column mappings from finvizfinance to normalized names
	mappings = {
		"Name": "name",
		"Number of Stocks": "stocks",
		"Market Cap": "market_cap",
		"Change": "performance_1d",
		"Perf Week": "performance_1w",
		"Perf Month": "performance_1m",
		"Perf Quart": "performance_3m",
		"Perf Half": "performance_6m",
		"Perf Year": "performance_1y",
		"Perf YTD": "performance_ytd",
		"Volume": "volume",
		"Avg Volume": "volume_average",
		"Rel Volume": "volume_relative",
		"P/E": "pe",
		"Fwd P/E": "forward_pe",
		"PEG": "peg",
		"EPS past 5Y": "eps_growth_past_5y",
		"EPS next 5Y": "eps_growth_next_5y",
		"Sales past 5Y": "sales_growth_past_5y",
		"P/S": "price_to_sales",
		"P/B": "price_to_book",
		"P/C": "price_to_cash",
		"P/FCF": "price_to_free_cash_flow",
		"Dividend": "dividend_yield",
		"Float Short": "float_short",
		"Recom": "analyst_recommendation",
	}

	for key, val in row.items():
		clean_key = key.strip() if isinstance(key, str) else key
		normalized_key = mappings.get(clean_key, clean_key)

		# Handle NaN values
		if val != val:  # NaN check
			result[normalized_key] = None
		elif isinstance(val, str) and val in ("N/A", "-", ""):
			result[normalized_key] = None
		else:
			# Parse percent values
			if normalized_key in (
				"performance_1d",
				"performance_1w",
				"performance_1m",
				"performance_3m",
				"performance_6m",
				"performance_1y",
				"performance_ytd",
				"dividend_yield",
				"eps_growth_past_5y",
				"eps_growth_next_5y",
				"sales_growth_past_5y",
				"float_short",
			):
				result[normalized_key] = _parse_percent(val)
			elif normalized_key in ("market_cap", "volume", "volume_average"):
				result[normalized_key] = _parse_market_cap(val)
			else:
				result[normalized_key] = val

	return result


@safe_run
def cmd_screen(args):
	"""Screen stocks using predefined presets."""
	from finvizfinance.screener.overview import Overview

	preset_name = args.preset
	if preset_name not in PRESETS:
		available = ", ".join(sorted(PRESETS.keys()))
		error_json(f"Unknown preset: {preset_name}. Available presets: {available}")

	preset = PRESETS[preset_name]
	filters_dict = preset["filters"]

	foverview = Overview()

	# Set signal if specified in preset
	if "signal" in preset:
		foverview.set_filter(signal=preset["signal"], filters_dict=filters_dict)
	else:
		foverview.set_filter(filters_dict=filters_dict)

	# Get screener results with retry on 403
	try:
		df = _fetch_with_retry(lambda: foverview.screener_view(limit=args.limit, verbose=0))
	except Exception as e:
		error_json(f"Finviz screening failed after retries: {e}. Try again later or use alternative data sources.")

	if df is None or df.empty:
		output_json(
			{
				"data": [],
				"metadata": {
					"preset": preset_name,
					"description": preset["description"],
					"filters": filters_dict,
					"count": 0,
					"timestamp": datetime.now(timezone.utc).isoformat(),
				},
			}
		)
		return

	# Normalize results
	records = [_normalize_screener_row(row) for row in df.to_dict(orient="records")]

	output_json(
		{
			"data": records,
			"metadata": {
				"preset": preset_name,
				"description": preset["description"],
				"filters": filters_dict,
				"count": len(records),
				"timestamp": datetime.now(timezone.utc).isoformat(),
			},
		}
	)


@safe_run
def cmd_groups(args):
	"""Get sector/industry group performance comparison."""
	from finvizfinance.group import Overview, Performance, Valuation

	group = args.group
	if group not in GROUPS_DICT:
		available = ", ".join(sorted(GROUPS_DICT.keys()))
		error_json(f"Unknown group: {group}. Available groups: {available}")

	group_value = GROUPS_DICT[group]

	# Order mapping
	order_mapping = {
		"name": "Name",
		"perf_week": "Performance (Week)",
		"perf_month": "Performance (Month)",
		"perf_year": "Performance (Year)",
		"perf_ytd": "Performance (YTD)",
		"change": "Change",
		"market_cap": "Market Cap",
		"pe": "P/E",
		"forward_pe": "Forward Price/Earnings",
		"peg": "PEG",
		"dividend": "Dividend Yield",
		"volume": "Volume",
	}

	order_value = order_mapping.get(args.order, "Performance (Week)")

	# Determine which view to use based on metric
	metric = args.metric
	try:
		if metric == "performance":
			group_view = Performance()
			df = _fetch_with_retry(lambda: group_view.screener_view(group=group_value, order=order_value))
		elif metric == "valuation":
			group_view = Valuation()
			df = _fetch_with_retry(lambda: group_view.screener_view(group=group_value, order=order_value))
		else:  # overview
			group_view = Overview()
			df = _fetch_with_retry(lambda: group_view.screener_view(group=group_value, order=order_value))
	except Exception as e:
		error_json(f"Finviz group data failed after retries: {e}. Try again later.")

	if df is None or df.empty:
		output_json(
			{
				"data": [],
				"metadata": {
					"group": group,
					"metric": metric,
					"order": args.order,
					"count": 0,
					"timestamp": datetime.now(timezone.utc).isoformat(),
				},
			}
		)
		return

	# Normalize results
	records = [_normalize_group_row(row) for row in df.to_dict(orient="records")]

	output_json(
		{
			"data": records,
			"metadata": {
				"group": group,
				"group_finviz": group_value,
				"metric": metric,
				"order": args.order,
				"count": len(records),
				"timestamp": datetime.now(timezone.utc).isoformat(),
			},
		}
	)


@safe_run
def cmd_presets(args):
	"""List available screening presets."""
	presets_info = {}
	for name, preset in PRESETS.items():
		presets_info[name] = {
			"description": preset["description"],
			"filter_count": len(preset["filters"]),
			"has_signal": "signal" in preset,
		}

	output_json(
		{
			"data": presets_info,
			"metadata": {
				"count": len(presets_info),
				"timestamp": datetime.now(timezone.utc).isoformat(),
			},
		}
	)


@safe_run
def cmd_sector_screen(args):
	"""Screen stocks within a specific sector with quality filters."""
	from finvizfinance.screener.overview import Overview

	sector = args.sector
	if sector not in SECTOR_FILTERS:
		available = ", ".join(sorted(SECTOR_FILTERS.keys()))
		error_json(f"Unknown sector: {sector}. Available sectors: {available}")

	sector_value = SECTOR_FILTERS[sector]

	# Build filters based on criteria
	filters_dict = {"Sector": sector_value}

	# Add quality filters based on criteria argument
	criteria = args.criteria
	if criteria == "growth":
		# High growth stocks in the sector
		filters_dict.update(
			{
				"EPS growththis year": "Over 20%",
				"EPS growthnext year": "Over 10%",
				"Sales growthqtr over qtr": "Over 10%",
			}
		)
	elif criteria == "value":
		# Value stocks in the sector
		filters_dict.update(
			{
				"P/E": "Under 20",
				"P/B": "Under 3",
				"PEG": "Low (<1)",
			}
		)
	elif criteria == "momentum":
		# Momentum stocks in the sector
		filters_dict.update(
			{
				"20-Day Simple Moving Average": "Price above SMA20",
				"50-Day Simple Moving Average": "Price above SMA50",
				"52-Week High/Low": "0-10% below High",
			}
		)
	elif criteria == "dividend":
		# Dividend stocks in the sector
		filters_dict.update(
			{
				"Dividend Yield": "Over 2%",
				"Payout Ratio": "Under 50%",
			}
		)
	elif criteria == "quality":
		# Quality stocks (default)
		filters_dict.update(
			{
				"Return on Equity": "Over +15%",
				"Debt/Equity": "Under 1",
				"EPS growthpast 5 years": "Positive (>0%)",
			}
		)
	# else: "all" - no additional filters

	foverview = Overview()
	foverview.set_filter(filters_dict=filters_dict)

	# Get screener results with retry on 403
	try:
		df = _fetch_with_retry(lambda: foverview.screener_view(limit=args.limit, verbose=0))
	except Exception as e:
		error_json(f"Finviz sector screening failed after retries: {e}. Try again later.")

	if df is None or df.empty:
		output_json(
			{
				"data": [],
				"metadata": {
					"sector": sector,
					"criteria": criteria,
					"filters": filters_dict,
					"count": 0,
					"timestamp": datetime.now(timezone.utc).isoformat(),
				},
			}
		)
		return

	# Normalize results
	records = [_normalize_screener_row(row) for row in df.to_dict(orient="records")]

	output_json(
		{
			"data": records,
			"metadata": {
				"sector": sector,
				"sector_finviz": sector_value,
				"criteria": criteria,
				"filters": filters_dict,
				"count": len(records),
				"timestamp": datetime.now(timezone.utc).isoformat(),
			},
		}
	)


@safe_run
def cmd_market_breadth(args):
	"""Get market breadth via new 52-week highs vs lows by exchange with sector breakdown."""
	from finvizfinance.screener.overview import Overview

	exchanges = ["NYSE", "NASDAQ"]
	results = {}

	for exchange in exchanges:
		exchange_data = {}
		for signal_name, signal_key in [("new_highs", "New High"), ("new_lows", "New Low")]:
			foverview = Overview()
			foverview.set_filter(signal=signal_key, filters_dict={"Exchange": exchange})
			try:
				df = _fetch_with_retry(lambda: foverview.screener_view(verbose=0))
			except Exception:
				df = None
			exchange_data[signal_name] = len(df) if df is not None and not df.empty else 0

		lows = exchange_data["new_lows"]
		exchange_data["ratio"] = round(exchange_data["new_highs"] / max(lows, 1), 2)
		results[exchange.lower()] = exchange_data

	# Also get all new highs (without exchange filter) for sector breakdown
	foverview_all = Overview()
	foverview_all.set_filter(signal="New High")
	try:
		df_all_highs = _fetch_with_retry(lambda: foverview_all.screener_view(verbose=0))
	except Exception:
		df_all_highs = None

	sector_breakdown = []
	if df_all_highs is not None and not df_all_highs.empty:
		sector_counts = df_all_highs["Sector"].value_counts().to_dict()
		sector_breakdown = [
			{"sector": sector, "count": count} for sector, count in sorted(sector_counts.items(), key=lambda x: -x[1])
		]

	total_highs = sum(r["new_highs"] for r in results.values())
	total_lows = sum(r["new_lows"] for r in results.values())
	total_ratio = round(total_highs / max(total_lows, 1), 2)

	# Interpretation based on Minervini methodology
	if total_ratio >= 3.0:
		interpretation = "Strong breadth: new highs dominate. Healthy market environment for SEPA entries."
	elif total_ratio >= 1.5:
		interpretation = "Positive breadth: more new highs than lows. Selective buying appropriate."
	elif total_ratio >= 0.8:
		interpretation = "Neutral breadth: highs and lows roughly balanced. Caution warranted, tighten stops."
	elif total_ratio >= 0.5:
		interpretation = "Weak breadth: new lows exceeding new highs. Reduce exposure, defensive positioning."
	else:
		interpretation = "Bearish breadth: new lows dominate. High risk environment, preserve capital."

	# Add NYSE vs NASDAQ divergence note
	nyse_ratio = results.get("nyse", {}).get("ratio", 0)
	nasdaq_ratio = results.get("nasdaq", {}).get("ratio", 0)
	if nyse_ratio > 2.0 and nasdaq_ratio < 1.0:
		interpretation += " DIVERGENCE: NYSE healthy but NASDAQ weak -- sector rotation from tech to value/cyclical."
	elif nasdaq_ratio > 2.0 and nyse_ratio < 1.0:
		interpretation += " DIVERGENCE: NASDAQ strong but NYSE weak -- narrow tech-led rally."

	output_json(
		{
			**results,
			"total": {
				"new_highs": total_highs,
				"new_lows": total_lows,
				"ratio": total_ratio,
			},
			"new_highs_by_sector": sector_breakdown,
			"interpretation": interpretation,
			"metadata": {
				"timestamp": datetime.now(timezone.utc).isoformat(),
			},
		}
	)


def main():
	parser = argparse.ArgumentParser(description="Finviz stock screening and group analysis")
	sub = parser.add_subparsers(dest="command", required=True)

	# screen - Stock screening with presets
	p_screen = sub.add_parser("screen", help="Screen stocks using predefined presets")
	p_screen.add_argument(
		"--preset",
		required=True,
		choices=list(PRESETS.keys()),
		help="Screening preset to use",
	)
	p_screen.add_argument(
		"--limit",
		type=int,
		default=50,
		help="Maximum number of results (default: 50)",
	)
	p_screen.set_defaults(func=cmd_screen)

	# groups - Sector/Industry group comparison
	p_groups = sub.add_parser("groups", help="Get sector/industry group performance")
	p_groups.add_argument(
		"--group",
		default="sector",
		choices=list(GROUPS_DICT.keys()),
		help="Group type (default: sector)",
	)
	p_groups.add_argument(
		"--metric",
		default="performance",
		choices=["performance", "valuation", "overview"],
		help="Data metric to return (default: performance)",
	)
	p_groups.add_argument(
		"--order",
		default="perf_week",
		choices=[
			"name",
			"perf_week",
			"perf_month",
			"perf_year",
			"perf_ytd",
			"change",
			"market_cap",
			"pe",
			"forward_pe",
			"peg",
			"dividend",
			"volume",
		],
		help="Sort order (default: perf_week)",
	)
	p_groups.set_defaults(func=cmd_groups)

	# presets - List available presets
	p_presets = sub.add_parser("presets", help="List available screening presets")
	p_presets.set_defaults(func=cmd_presets)

	# sector-screen - Screen stocks within a specific sector
	p_sector = sub.add_parser("sector-screen", help="Screen stocks within a specific sector")
	p_sector.add_argument(
		"--sector",
		required=True,
		choices=list(SECTOR_FILTERS.keys()),
		help="Sector to screen",
	)
	p_sector.add_argument(
		"--criteria",
		default="all",
		choices=["all", "growth", "value", "momentum", "dividend", "quality"],
		help="Screening criteria (default: all - no filters)",
	)
	p_sector.add_argument(
		"--limit",
		type=int,
		default=50,
		help="Maximum number of results (default: 50)",
	)
	p_sector.set_defaults(func=cmd_sector_screen)

	# market-breadth - New 52-week highs vs lows
	p_breadth = sub.add_parser(
		"market-breadth",
		help="New 52-week highs vs lows by exchange with sector breakdown",
	)
	p_breadth.set_defaults(func=cmd_market_breadth)

	args = parser.parse_args()
	args.func(args)


if __name__ == "__main__":
	main()
