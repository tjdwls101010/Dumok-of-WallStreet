#!/usr/bin/env python3
"""S&P 500 dividend yield calculation.

Calculates S&P 500 dividend yield using two methods: SPY ETF proxy (fast, default)
or full constituent weighted average (slow but more accurate). YFinance does not
provide index-level dividend yield for ^GSPC directly, so these proxy methods are
required.

Dividend yield is a key input for SidneyKim0's valuation framework. Combined with
CAPE and ERP, it provides a complete picture of equity market valuation relative to
bonds and historical norms.

Args:
	Command: sp500-yield | compare-methods

	sp500-yield:
		--method (str): "spy_etf" (default, fast) or "constituents" (slow, accurate)

	compare-methods:
		(no arguments) - compares SPY, VOO, IVV ETF yields

Returns:
	sp500-yield -> dict: {
		"index": str,              # "S&P 500"
		"symbol": str,             # "^GSPC"
		"dividend_yield": float,   # Decimal (e.g., 0.0132 for 1.32%)
		"dividend_yield_pct": str, # Formatted (e.g., "1.32%")
		"date": str,               # Calculation date
		"method": str,             # "spy_etf_proxy" | "constituent_weighted_average"
		"calculation_details": dict # (constituents method only)
	}

	compare-methods -> dict: {
		"index": str,
		"date": str,
		"comparisons": [{"method": str, "yield": float, "yield_pct": str}, ...]
	}

Example:
	>>> python valuation/dividend_yield.py sp500-yield
	{
		"dividend_yield": 0.0132,
		"dividend_yield_pct": "1.32%",
		"method": "spy_etf_proxy"
	}

	>>> python valuation/dividend_yield.py sp500-yield --method constituents
	{
		"dividend_yield": 0.0128,
		"dividend_yield_pct": "1.28%",
		"method": "constituent_weighted_average",
		"calculation_details": {"successful_symbols": 490, "coverage_pct": 98.0}
	}

	>>> python valuation/dividend_yield.py compare-methods
	{"comparisons": [{"method": "spy_etf", "yield_pct": "1.32%"}, ...]}

Use Cases:
	- Quick S&P 500 dividend yield check for valuation context
	- Compare dividend yield across SPY, VOO, IVV for consistency check
	- Input for Gordon Growth Model: Fair Value = Dividends / (Required Return - Growth)
	- Historical comparison: S&P 500 avg dividend yield ~2%, current ~1.3% = low

Notes:
	- SPY ETF method is fast (single API call) but includes ETF expense ratio drag
	- Constituent method fetches all 500+ stocks (takes several minutes)
	- Constituent method uses market-cap weighted average for accuracy
	- Progress updates printed to stderr during constituent calculation
	- Low dividend yield + high CAPE = expensive market signal
	- No API key required (uses YFinance)

See Also:
	- valuation/cape.py: CAPE ratio (another key valuation metric)
	- macro/erp.py: ERP uses earnings yield (1/CAPE), complementary to dividend yield
	- Personas/Sidneykim0/thresholds.md: Valuation interpretation thresholds
"""

import argparse
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pandas as pd
import yfinance as yf
from utils import error_json, output_json, safe_run


def get_sp500_constituents():
	"""Get S&P 500 constituent symbols from Wikipedia."""
	try:
		# Read S&P 500 constituents from Wikipedia
		url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
		tables = pd.read_html(url)
		sp500_table = tables[0]

		# Get symbols
		symbols = sp500_table["Symbol"].tolist()

		# Clean symbols (remove dots for YFinance compatibility)
		symbols = [s.replace(".", "-") for s in symbols]

		return symbols
	except Exception as e:
		raise ValueError(f"Failed to fetch S&P 500 constituents: {e}")


def calculate_weighted_dividend_yield(symbols, max_retries=3):
	"""Calculate weighted average dividend yield from constituents."""
	total_market_cap = 0
	total_dividend_value = 0
	successful = 0
	failed = 0

	print(f"Fetching data for {len(symbols)} constituents...", file=sys.stderr)

	for i, symbol in enumerate(symbols):
		if i % 50 == 0:
			print(f"Progress: {i}/{len(symbols)}", file=sys.stderr)

		retry_count = 0
		while retry_count < max_retries:
			try:
				ticker = yf.Ticker(symbol)
				info = ticker.info

				# Get market cap and dividend yield
				market_cap = info.get("marketCap", 0)
				dividend_yield = info.get("dividendYield", 0)

				if market_cap and market_cap > 0:
					total_market_cap += market_cap
					if dividend_yield and dividend_yield > 0:
						total_dividend_value += market_cap * dividend_yield
					successful += 1
					break
				else:
					failed += 1
					break

			except Exception:
				retry_count += 1
				if retry_count >= max_retries:
					failed += 1
					break

	if total_market_cap == 0:
		raise ValueError("No market cap data available for constituents")

	weighted_yield = total_dividend_value / total_market_cap

	return {
		"weighted_yield": weighted_yield,
		"total_market_cap": total_market_cap,
		"successful_symbols": successful,
		"failed_symbols": failed,
		"total_symbols": len(symbols),
		"coverage_pct": (successful / len(symbols)) * 100,
	}


@safe_run
def cmd_sp500_yield(args):
	"""Calculate S&P 500 dividend yield."""
	if args.method == "constituents":
		# Method 1: Calculate from constituents
		print("Fetching S&P 500 constituents...", file=sys.stderr)
		symbols = get_sp500_constituents()

		print(f"Calculating weighted dividend yield from {len(symbols)} constituents...", file=sys.stderr)
		calc_result = calculate_weighted_dividend_yield(symbols)

		result = {
			"index": "S&P 500",
			"symbol": "^GSPC",
			"dividend_yield": round(calc_result["weighted_yield"], 6),
			"dividend_yield_pct": f"{calc_result['weighted_yield'] * 100:.2f}%",
			"date": str(datetime.now().date()),
			"method": "constituent_weighted_average",
			"calculation_details": {
				"total_market_cap": calc_result["total_market_cap"],
				"successful_symbols": calc_result["successful_symbols"],
				"failed_symbols": calc_result["failed_symbols"],
				"coverage_pct": round(calc_result["coverage_pct"], 2),
			},
			"note": "Calculated from constituent weighted average. May differ from official S&P data.",
		}

	elif args.method == "spy_etf":
		# Method 2: Use SPY ETF as proxy
		spy = yf.Ticker("SPY")
		info = spy.info

		# Use trailingAnnualDividendYield (more reliable than dividendYield)
		dividend_yield = info.get("trailingAnnualDividendYield") or info.get("yield")
		if not dividend_yield:
			error_json("SPY ETF dividend yield not available from YFinance")
			return

		result = {
			"index": "S&P 500",
			"symbol": "^GSPC",
			"dividend_yield": round(dividend_yield, 6),
			"dividend_yield_pct": f"{dividend_yield * 100:.2f}%",
			"date": str(datetime.now().date()),
			"method": "spy_etf_proxy",
			"note": "Using SPY ETF as proxy. Tracks S&P 500 closely but may have slight expense ratio impact.",
		}

	else:
		error_json(f"Unknown method: {args.method}")
		return

	output_json(result)


@safe_run
def cmd_compare_methods(args):
	"""Compare dividend yield from different methods."""
	results = []

	# Try SPY ETF
	try:
		spy = yf.Ticker("SPY")
		info = spy.info
		dividend_yield = info.get("trailingAnnualDividendYield") or info.get("yield")
		if dividend_yield:
			results.append({"method": "spy_etf", "yield": dividend_yield, "yield_pct": f"{dividend_yield * 100:.2f}%"})
	except Exception as e:
		results.append({"method": "spy_etf", "error": str(e)})

	# Try VOO ETF (Vanguard S&P 500)
	try:
		voo = yf.Ticker("VOO")
		info = voo.info
		dividend_yield = info.get("trailingAnnualDividendYield") or info.get("yield")
		if dividend_yield:
			results.append({"method": "voo_etf", "yield": dividend_yield, "yield_pct": f"{dividend_yield * 100:.2f}%"})
	except Exception as e:
		results.append({"method": "voo_etf", "error": str(e)})

	# Try IVV ETF (iShares S&P 500)
	try:
		ivv = yf.Ticker("IVV")
		info = ivv.info
		dividend_yield = info.get("trailingAnnualDividendYield") or info.get("yield")
		if dividend_yield:
			results.append({"method": "ivv_etf", "yield": dividend_yield, "yield_pct": f"{dividend_yield * 100:.2f}%"})
	except Exception as e:
		results.append({"method": "ivv_etf", "error": str(e)})

	output_json({"index": "S&P 500", "date": str(datetime.now().date()), "comparisons": results})


if __name__ == "__main__":
	parser = argparse.ArgumentParser(description="S&P 500 dividend yield calculation")
	subparsers = parser.add_subparsers(dest="command", help="Available commands")

	# sp500-yield command
	sp_yield = subparsers.add_parser("sp500-yield", help="Calculate S&P 500 dividend yield")
	sp_yield.add_argument(
		"--method",
		choices=["constituents", "spy_etf"],
		default="spy_etf",
		help="Calculation method (default: spy_etf for speed)",
	)

	# compare-methods command
	sp_compare = subparsers.add_parser("compare-methods", help="Compare dividend yield from different methods")

	args = parser.parse_args()

	# Dispatch
	if args.command == "sp500-yield":
		cmd_sp500_yield(args)
	elif args.command == "compare-methods":
		cmd_compare_methods(args)
	else:
		parser.print_help()
		sys.exit(1)
