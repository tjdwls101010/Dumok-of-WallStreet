#!/usr/bin/env python3
"""IV Context Analyzer: Determine if current implied volatility is relatively high or low for options timing.

Retrieves 30-day implied volatility (IV30) and historical volatility (HV30) data from the CBOE
delayed quotes API to calculate IV Rank, a normalized percentile measure of where current IV sits
within its 1-year range. IV Rank is the primary metric for options timing decisions: low IV Rank
signals cheap options ideal for buying LEAPS or debit spreads, while high IV Rank signals expensive
options ideal for selling premium through covered calls or cash-secured puts.

Args:
	symbol (str): Stock or index ticker symbol (e.g., "AAPL", "MSFT", "SPX", "VIX")
	command (str): One of analyze

Returns:
	dict: {
		"symbol": str,               # Ticker symbol (uppercased)
		"current_price": float,      # Current stock/index price
		"iv30": float,               # Current 30-day implied volatility (percentage)
		"iv30_annual_high": float,   # 1-year high of IV30 (percentage)
		"iv30_annual_low": float,    # 1-year low of IV30 (percentage)
		"iv_rank": float,            # IV Rank: (iv30 - low) / (high - low) * 100
		"hv30_annual_high": float,   # 1-year high of 30-day realized volatility (percentage)
		"hv30_annual_low": float,    # 1-year low of 30-day realized volatility (percentage)
		"iv_vs_hv_spread": float,    # iv30 minus midpoint of HV30 range (percentage points)
		"interpretation": str        # cheap | fair | elevated | expensive
	}

Example:
	>>> python iv_context.py analyze AAPL
	{
		"symbol": "AAPL",
		"current_price": 185.50,
		"iv30": 22.5,
		"iv30_annual_high": 45.0,
		"iv30_annual_low": 15.0,
		"iv_rank": 25.0,
		"hv30_annual_high": 38.0,
		"hv30_annual_low": 12.0,
		"iv_vs_hv_spread": -2.5,
		"interpretation": "fair"
	}

	>>> python iv_context.py analyze SPX
	{
		"symbol": "SPX",
		"current_price": 5450.00,
		"iv30": 14.2,
		"iv_rank": 18.5,
		"interpretation": "cheap"
	}

Use Cases:
	- Options timing: Identify when IV is cheap for buying calls, puts, or LEAPS
	- LEAPS entry: IV Rank below 25 signals favorable entry for long-dated options
	- Premium selling: IV Rank above 50 indicates elevated premium for covered calls or CSPs
	- IV vs HV spread: Positive spread means options are overpriced relative to realized moves
	- Earnings positioning: Compare pre-earnings IV Rank to assess if volatility crush is priced in

Notes:
	- IV Rank ranges from 0 to 100; it measures where current IV sits within its annual range
	- IV Rank < 25: "cheap" (favorable for buying options)
	- IV Rank 25-50: "fair" (neutral, no strong edge either way)
	- IV Rank 50-75: "elevated" (consider selling premium)
	- IV Rank > 75: "expensive" (best for premium sellers, worst for option buyers)
	- CBOE data is delayed (typically 15 minutes) and may not reflect real-time IV
	- CBOE returns IV values as percentages (e.g., 22.5 means 22.5%)
	- Index symbols are prefixed with underscore in the CBOE API (SPX -> _SPX)
	- Some tickers may lack IV data if they have no listed options

See Also:
	- data_sources/options.py: Raw options chain data for detailed strike-level analysis
	- analysis/putcall_ratio.py: Sentiment overlay using put/call volume ratios
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import requests

# Support both standalone execution and module imports
try:
	from ..utils import error_json, output_json, safe_run
except ImportError:
	from utils import error_json, output_json, safe_run


# CBOE index symbols require underscore prefix
_INDEX_SYMBOLS = {
	"SPX": "_SPX",
	"VIX": "_VIX",
	"RUT": "_RUT",
	"DJX": "_DJX",
	"NDX": "_NDX",
	"OEX": "_OEX",
	"XSP": "_XSP",
}


def _cboe_symbol(symbol):
	"""Convert a ticker symbol to CBOE API format.

	Index symbols like SPX, VIX need an underscore prefix in the CBOE URL.
	Regular equity symbols are used as-is.
	"""
	upper = symbol.upper().replace("^", "")
	return _INDEX_SYMBOLS.get(upper, upper)


def _fetch_cboe_quote(symbol):
	"""Fetch delayed quote data from the CBOE API.

	Returns the 'data' dict from the CBOE JSON response, which includes
	current_price, iv30, iv30_annual_high, iv30_annual_low, etc.
	"""
	cboe_sym = _cboe_symbol(symbol)
	url = f"https://cdn.cboe.com/api/global/delayed_quotes/quotes/{cboe_sym}.json"

	resp = requests.get(url, timeout=15)
	if resp.status_code != 200:
		error_json(f"CBOE API returned status {resp.status_code} for symbol {symbol.upper()}")

	payload = resp.json()
	data = payload.get("data")
	if not data:
		error_json(f"No quote data returned from CBOE for symbol {symbol.upper()}")

	return data


def _fetch_cboe_iv_history(symbol):
	"""Fetch historical IV data from the CBOE API.

	Returns the 'data' dict containing iv30_annual_high, iv30_annual_low,
	hv30_annual_high, hv30_annual_low, and other volatility fields.
	"""
	cboe_sym = _cboe_symbol(symbol)
	url = f"https://cdn.cboe.com/api/global/delayed_quotes/historical_data/{cboe_sym}.json"

	resp = requests.get(url, timeout=15)
	if resp.status_code != 200:
		return {}

	payload = resp.json()
	return payload.get("data", {})


def _classify_iv(iv_rank):
	"""Classify IV environment based on IV Rank percentile.

	IV Rank < 25: cheap (favorable for buying options/LEAPS)
	IV Rank 25-50: fair (neutral)
	IV Rank 50-75: elevated (consider selling premium)
	IV Rank > 75: expensive (best for premium selling, worst for buying)
	"""
	if iv_rank is None:
		return "unknown"
	if iv_rank < 25:
		return "cheap"
	if iv_rank <= 50:
		return "fair"
	if iv_rank <= 75:
		return "elevated"
	return "expensive"


def _safe_float(value):
	"""Safely convert a value to float, returning None for missing or invalid data."""
	if value is None:
		return None
	try:
		f = float(value)
		if f != f:  # NaN check
			return None
		return f
	except (ValueError, TypeError):
		return None


@safe_run
def cmd_analyze(args):
	"""Analyze IV context for a given symbol using CBOE delayed quote data."""
	symbol = args.symbol.upper()

	# Fetch quote data (current_price, possibly some IV fields)
	quote_data = _fetch_cboe_quote(symbol)

	# Fetch historical IV data (annual high/low for IV and HV)
	iv_history = _fetch_cboe_iv_history(symbol)

	# Extract current price
	current_price = _safe_float(quote_data.get("current_price"))

	# Extract IV30 from quote data; CBOE returns percentages (e.g., 22.5 = 22.5%)
	iv30 = _safe_float(quote_data.get("iv30"))

	# IV annual range: prefer historical_data endpoint, fall back to quote data
	iv30_annual_high = _safe_float(iv_history.get("iv30_annual_high") or quote_data.get("iv30_annual_high"))
	iv30_annual_low = _safe_float(iv_history.get("iv30_annual_low") or quote_data.get("iv30_annual_low"))

	# HV annual range from historical data
	hv30_annual_high = _safe_float(iv_history.get("hv30_annual_high") or quote_data.get("hv30_annual_high"))
	hv30_annual_low = _safe_float(iv_history.get("hv30_annual_low") or quote_data.get("hv30_annual_low"))

	# Calculate IV Rank: (current_iv30 - annual_low) / (annual_high - annual_low) * 100
	iv_rank = None
	if iv30 is not None and iv30_annual_high is not None and iv30_annual_low is not None:
		iv_range = iv30_annual_high - iv30_annual_low
		if iv_range > 0:
			iv_rank = round((iv30 - iv30_annual_low) / iv_range * 100, 2)

	# Calculate IV vs HV spread: iv30 minus midpoint of HV30 range
	iv_vs_hv_spread = None
	if iv30 is not None and hv30_annual_high is not None and hv30_annual_low is not None:
		hv30_midpoint = (hv30_annual_high + hv30_annual_low) / 2
		iv_vs_hv_spread = round(iv30 - hv30_midpoint, 2)

	result = {
		"symbol": symbol,
		"current_price": round(current_price, 2) if current_price is not None else None,
		"iv30": round(iv30, 2) if iv30 is not None else None,
		"iv30_annual_high": round(iv30_annual_high, 2) if iv30_annual_high is not None else None,
		"iv30_annual_low": round(iv30_annual_low, 2) if iv30_annual_low is not None else None,
		"iv_rank": iv_rank,
		"hv30_annual_high": round(hv30_annual_high, 2) if hv30_annual_high is not None else None,
		"hv30_annual_low": round(hv30_annual_low, 2) if hv30_annual_low is not None else None,
		"iv_vs_hv_spread": iv_vs_hv_spread,
		"interpretation": _classify_iv(iv_rank),
	}

	output_json(result)


def main():
	parser = argparse.ArgumentParser(description="IV Context Analyzer - Implied volatility ranking for options timing")
	sub = parser.add_subparsers(dest="command", required=True)

	sp_analyze = sub.add_parser("analyze")
	sp_analyze.add_argument("symbol", help="Stock or index ticker symbol (e.g., AAPL, SPX, VIX)")
	sp_analyze.set_defaults(func=cmd_analyze)

	args = parser.parse_args()
	args.func(args)


if __name__ == "__main__":
	main()
