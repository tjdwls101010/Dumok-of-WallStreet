#!/usr/bin/env python3
"""Forward P/E calculator using analyst earnings estimates with Walmart benchmark comparison.

Computes forward 1-year and 2-year P/E ratios from consensus analyst EPS estimates,
compares valuation to a Walmart P/E benchmark (45x), and assesses whether a stock
appears undervalued, fairly valued, or overvalued relative to its growth profile.

Args:
		symbol (str): Stock ticker symbol (e.g., "MU", "NVDA", "AAPL")
		command (str): One of calculate, compare, batch

Returns:
		dict: Structure varies by command, typical fields include:
		{
				"symbol": str,                  # Ticker symbol
				"current_price": float,         # Current stock price
				"forward_1y_eps": float,        # Consensus forward 1Y EPS
				"forward_2y_eps": float,        # Consensus forward 2Y EPS
				"forward_1y_pe": float,         # Forward 1Y P/E ratio
				"forward_2y_pe": float,         # Forward 2Y P/E ratio
				"revenue_growth_yoy": float,    # YoY revenue growth estimate %
				"walmart_pe_benchmark": int,    # WMT benchmark P/E (45x)
				"valuation_gap": str,           # Narrative comparison to benchmark
				"assessment": str               # "undervalued" | "fairly_valued" | "overvalued"
		}

Example:
		>>> python forward_pe.py calculate MU
		{
				"symbol": "MU",
				"current_price": 95.50,
				"forward_1y_eps": 8.25,
				"forward_2y_eps": 10.50,
				"forward_1y_pe": 11.6,
				"forward_2y_pe": 9.1,
				"revenue_growth_yoy": 45.2,
				"walmart_pe_benchmark": 45,
				"valuation_gap": "Forward P/E (11.6x) significantly below WMT benchmark (45x) despite higher growth",
				"assessment": "undervalued"
		}

		>>> python forward_pe.py batch NVDA MU AMD AVGO
		[
				{"symbol": "NVDA", "forward_1y_pe": 28.5, "assessment": "fairly_valued", ...},
				{"symbol": "MU", "forward_1y_pe": 11.6, "assessment": "undervalued", ...},
				...
		]

Use Cases:
		- Screen for undervalued growth stocks vs mature benchmarks
		- Compare forward P/E across semiconductor or tech peers
		- Identify valuation dislocations where growth is not priced in
		- Track P/E compression or expansion over time via batch runs

Notes:
		- Forward EPS estimates are consensus averages and subject to revision
		- Walmart benchmark (45x) represents a mature, low-growth reference point
		- Revenue growth context is critical: a 15x P/E with 50% growth is very different from 15x with 5% growth
		- Forward P/E is more useful than trailing P/E for cyclical or high-growth names
		- Estimates tend to be optimistic; actual earnings often miss consensus

See Also:
		- analysis.py: Analyst estimates, EPS trends, and revisions
		- sbc_analyzer.py: SBC-adjusted FCF for real profitability assessment
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import yfinance as yf

# Support both standalone execution and module imports
try:
	from ..utils import error_json, output_json, safe_run
except ImportError:
	from utils import error_json, output_json, safe_run

WALMART_PE_BENCHMARK = 45


def _assess_valuation(forward_1y_pe, revenue_growth):
	"""Determine valuation assessment based on P/E and growth."""
	if forward_1y_pe is None:
		return "insufficient_data"
	if forward_1y_pe < 20 and revenue_growth is not None and revenue_growth > 20:
		return "undervalued"
	elif 20 <= forward_1y_pe <= 40:
		return "fairly_valued"
	elif forward_1y_pe > 40 and (revenue_growth is None or revenue_growth < 20):
		return "overvalued"
	elif forward_1y_pe < 20:
		return "fairly_valued"
	else:
		return "fairly_valued"


def _build_valuation_gap(symbol, forward_1y_pe, revenue_growth):
	"""Build narrative valuation gap description."""
	if forward_1y_pe is None:
		return "Insufficient data for valuation gap analysis"

	gap_direction = ""
	if forward_1y_pe < WALMART_PE_BENCHMARK:
		gap_direction = "below"
	elif forward_1y_pe > WALMART_PE_BENCHMARK:
		gap_direction = "above"
	else:
		gap_direction = "equal to"

	magnitude = ""
	diff = abs(forward_1y_pe - WALMART_PE_BENCHMARK)
	if diff > 20:
		magnitude = "significantly "
	elif diff > 10:
		magnitude = "moderately "
	else:
		magnitude = "slightly "

	growth_context = ""
	if revenue_growth is not None and revenue_growth > 20:
		growth_context = " despite higher growth"
	elif revenue_growth is not None and revenue_growth < 5:
		growth_context = " with low growth"

	return (
		f"Forward P/E ({forward_1y_pe}x) {magnitude}{gap_direction} "
		f"WMT benchmark ({WALMART_PE_BENCHMARK}x){growth_context}"
	)


def _calculate_forward_pe(symbol):
	"""Calculate forward P/E data for a single symbol."""
	ticker = yf.Ticker(symbol)

	# Get current price
	current_price = None
	try:
		current_price = ticker.info.get("currentPrice")
	except Exception:
		pass
	if current_price is None:
		try:
			current_price = ticker.fast_info.last_price
		except Exception:
			pass
	if current_price is None:
		error_json(f"Cannot retrieve current price for {symbol}")

	# Get forward EPS estimates
	# yfinance returns DataFrame with index=['0q','+1q','0y','+1y'] and columns=['avg','low','high',...]
	forward_1y_eps = None
	forward_2y_eps = None
	try:
		earnings_est = ticker.get_earnings_estimate()
		if earnings_est is not None and not earnings_est.empty:
			if "+1y" in earnings_est.index and "avg" in earnings_est.columns:
				val = earnings_est.loc["+1y", "avg"]
				if val == val:  # NaN check
					forward_1y_eps = float(val)
			# Use '0y' (current year) as forward_1y if '+1y' not available
			if forward_1y_eps is None and "0y" in earnings_est.index and "avg" in earnings_est.columns:
				val = earnings_est.loc["0y", "avg"]
				if val == val:
					forward_1y_eps = float(val)
	except Exception:
		pass

	# Calculate forward P/E
	forward_1y_pe = None
	forward_2y_pe = None
	if forward_1y_eps and forward_1y_eps > 0:
		forward_1y_pe = round(current_price / forward_1y_eps, 1)
	if forward_2y_eps and forward_2y_eps > 0:
		forward_2y_pe = round(current_price / forward_2y_eps, 1)

	# Get revenue growth estimate
	# yfinance returns DataFrame with index=['0q','+1q','0y','+1y'] and columns=['avg',...,'growth']
	revenue_growth = None
	try:
		rev_est = ticker.get_revenue_estimate()
		if rev_est is not None and not rev_est.empty:
			if "+1y" in rev_est.index and "growth" in rev_est.columns:
				val = rev_est.loc["+1y", "growth"]
				if val == val:  # NaN check
					revenue_growth = round(float(val) * 100, 1)
			# Fallback to current year growth
			if revenue_growth is None and "0y" in rev_est.index and "growth" in rev_est.columns:
				val = rev_est.loc["0y", "growth"]
				if val == val:
					revenue_growth = round(float(val) * 100, 1)
	except Exception:
		pass

	assessment = _assess_valuation(forward_1y_pe, revenue_growth)
	valuation_gap = _build_valuation_gap(symbol, forward_1y_pe, revenue_growth)

	return {
		"symbol": symbol.upper(),
		"current_price": round(current_price, 2),
		"forward_1y_eps": forward_1y_eps,
		"forward_2y_eps": forward_2y_eps,
		"forward_1y_pe": forward_1y_pe,
		"forward_2y_pe": forward_2y_pe,
		"revenue_growth_yoy": revenue_growth,
		"walmart_pe_benchmark": WALMART_PE_BENCHMARK,
		"valuation_gap": valuation_gap,
		"assessment": assessment,
	}


@safe_run
def cmd_calculate(args):
	result = _calculate_forward_pe(args.symbol)
	output_json(result)


@safe_run
def cmd_compare(args):
	results = []
	for symbol in [args.symbol1, args.symbol2]:
		results.append(_calculate_forward_pe(symbol))
	output_json(results)


@safe_run
def cmd_batch(args):
	results = []
	for symbol in args.symbols:
		results.append(_calculate_forward_pe(symbol))
	output_json(results)


def main():
	parser = argparse.ArgumentParser(description="Forward P/E calculator with benchmark comparison")
	sub = parser.add_subparsers(dest="command", required=True)

	sp_calc = sub.add_parser("calculate")
	sp_calc.add_argument("symbol")
	sp_calc.set_defaults(func=cmd_calculate)

	sp_cmp = sub.add_parser("compare")
	sp_cmp.add_argument("symbol1")
	sp_cmp.add_argument("symbol2")
	sp_cmp.set_defaults(func=cmd_compare)

	sp_batch = sub.add_parser("batch")
	sp_batch.add_argument("symbols", nargs="+")
	sp_batch.set_defaults(func=cmd_batch)

	args = parser.parse_args()
	args.func(args)


if __name__ == "__main__":
	main()
