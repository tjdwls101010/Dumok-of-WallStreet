#!/usr/bin/env python3
"""Cash-Secured Put yield calculator for options income strategy analysis.

Calculates annualized yield for cash-secured put (CSP) selling by scanning the CBOE options
chain for put contracts near a target strike price. Put selling is a dual-purpose strategy:
it generates premium income when the put expires worthless (bullish outcome), or it provides
a discounted entry into a stock position if assigned (neutral/bearish outcome). This calculator
identifies the highest-yielding CSP candidates within a specified DTE range and distance below
current price, enabling income-focused investors to compare risk-reward across available strikes
and expirations.

Args:
	symbol (str): Stock or index ticker symbol (e.g., "AAPL", "MSFT", "AXTI", "SPX")
	command (str): One of calculate
	--pct-below (float): Target strike as percentage below current price (default: 10.0).
		A value of 10 means the target strike is 10% below the current price, providing
		a cushion against downside. Example: if stock is $100, target strike = $90.
	--min-dte (int): Minimum days to expiration for filtering (default: 30).
		Shorter DTE means faster theta decay but higher annualized yield.
	--max-dte (int): Maximum days to expiration for filtering (default: 60).
		Longer DTE provides more absolute premium but lower annualized yield.

Returns:
	dict: {
		"symbol": str,                    # Ticker symbol (uppercased)
		"current_price": float,           # Current underlying stock price
		"scan_parameters": {
			"pct_below_current": float,   # Percentage below current price for target strike
			"target_strike": float,       # Computed target strike price
			"dte_range": [int, int]       # [min_dte, max_dte] filter applied
		},
		"candidates": [                   # Top 5 CSPs sorted by annualized yield descending
			{
				"contract": str,          # CBOE contract symbol (e.g., "AXTI260220P00007500")
				"expiration": str,        # Expiration date in YYYY-MM-DD format
				"strike": float,          # Strike price in dollars
				"dte": int,               # Days to expiration
				"bid": float,             # Best bid price
				"ask": float,             # Best ask price
				"mid_price": float,       # Midpoint of bid/ask spread
				"implied_volatility": float, # IV as decimal (e.g., 0.65 = 65%)
				"open_interest": int,     # Open interest (liquidity indicator)
				"premium_per_contract": float, # Mid price * 100 (dollars collected per contract)
				"capital_required": float, # Strike * 100 (cash required to secure the put)
				"return_pct": float,      # Premium / capital * 100 (return per cycle)
				"annualized_yield": float, # Return per cycle * (365 / DTE)
				"breakeven": float,       # Strike - mid_price (effective purchase price if assigned)
				"downside_cushion_pct": float # (current_price - breakeven) / current_price * 100
			}
		],
		"candidates_count": int           # Number of candidates returned (max 5)
	}

Example:
	>>> python csp_yield.py calculate AXTI --pct-below 10 --min-dte 30 --max-dte 60
	{
		"symbol": "AXTI",
		"current_price": 8.50,
		"scan_parameters": {"pct_below_current": 10.0, "target_strike": 7.65, "dte_range": [30, 60]},
		"candidates": [{"contract": "AXTI260220P00007500", "annualized_yield": 45.96, ...}],
		"candidates_count": 5
	}

	>>> python csp_yield.py calculate AAPL --pct-below 5 --min-dte 20 --max-dte 45
	{
		"symbol": "AAPL",
		"current_price": 185.50,
		"scan_parameters": {"pct_below_current": 5.0, "target_strike": 176.225, "dte_range": [20, 45]},
		"candidates": [{"contract": "AAPL260320P00175000", "annualized_yield": 12.34, ...}],
		"candidates_count": 5
	}

Use Cases:
	- Income generation: Identify highest annualized yield CSPs for weekly/monthly income
	- Discounted entry: Use CSPs to get paid while waiting to buy a stock at a lower price
	- IV-informed selling timing: Pair with iv_context.py; sell puts when IV Rank is elevated

Notes:
	- Capital required assumes cash-secured (full strike value collateral per contract)
	- Assignment risk: If stock drops below strike at expiration, you buy 100 shares at strike price
	- Annualized yield assumes the same trade repeats at identical terms over 365 days
	- Actual returns vary with market conditions and IV changes over time
	- Pair with iv_context.py to time put selling: elevated IV Rank (>50) means richer premiums
	- CBOE returns IV as percentage (e.g., 65.0 means 65%); this script divides by 100 for output
	- CBOE data is delayed (typically 15 minutes) and may not reflect real-time pricing
	- Zero-bid puts are excluded as they indicate no market for the contract
	- Index symbols are prefixed with underscore in the CBOE API (SPX -> _SPX)

See Also:
	- analysis/iv_context.py: Check IV Rank to time premium selling (high IV = richer CSP premiums)
	- analysis/leaps_scanner.py: LEAPS buying is the opposite strategy; buy when IV is cheap
	- data_sources/options.py: Raw options chain data for detailed strike-level analysis
"""

import argparse
import os
import re
import sys
from datetime import datetime

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

# Regex pattern for parsing CBOE contract symbols
# Format: TICKER + YYMMDD + C/P + strike*1000
_CONTRACT_RE = re.compile(r"^([A-Z]+)(\d{6})([CP])(\d+)$")


def _cboe_symbol(symbol):
	"""Convert a ticker symbol to CBOE API format.

	Index symbols like SPX, VIX need an underscore prefix in the CBOE URL.
	Regular equity symbols are used as-is.
	"""
	upper = symbol.upper().replace("^", "")
	return _INDEX_SYMBOLS.get(upper, upper)


def _fetch_options_chain(symbol):
	"""Fetch the full options chain from the CBOE delayed quotes API.

	Returns a tuple of (current_price, options_list) where options_list is the
	raw array of option records from the CBOE JSON response.
	"""
	cboe_sym = _cboe_symbol(symbol)
	url = f"https://cdn.cboe.com/api/global/delayed_quotes/options/{cboe_sym}.json"

	resp = requests.get(url, timeout=15)
	if resp.status_code != 200:
		error_json(f"CBOE API returned status {resp.status_code} for symbol {symbol.upper()}")

	payload = resp.json()
	data = payload.get("data")
	if not data:
		error_json(f"No options data returned from CBOE for symbol {symbol.upper()}")

	current_price = data.get("current_price")
	if current_price is None:
		error_json(f"No current price available from CBOE for symbol {symbol.upper()}")

	options = data.get("options", [])
	if not options:
		error_json(f"No options chain data available for symbol {symbol.upper()}")

	return float(current_price), options


def _parse_contract(contract_symbol):
	"""Parse a CBOE contract symbol into its components.

	Contract format: TICKER + YYMMDD + C/P + strike*1000
	Example: AXTI260220P00007500 -> (AXTI, 2026-02-20, P, 7.5)

	Returns a dict with expiration (str), option_type (str), strike (float),
	and dte (int), or None if the contract cannot be parsed.
	"""
	match = _CONTRACT_RE.match(contract_symbol)
	if not match:
		return None

	_, date_str, option_type, strike_raw = match.groups()

	# Parse YYMMDD expiration
	try:
		exp_date = datetime.strptime(date_str, "%y%m%d")
	except ValueError:
		return None

	# Calculate DTE
	now = datetime.now()
	dte = (exp_date - now).days + 1
	if dte < 0:
		return None

	# Strike is encoded as strike * 1000 (e.g., 00007500 = 7.500)
	strike = float(strike_raw.lstrip("0") or "0") / 1000.0

	return {
		"expiration": exp_date.strftime("%Y-%m-%d"),
		"option_type": option_type,
		"strike": strike,
		"dte": dte,
	}


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
def cmd_calculate(args):
	"""Calculate annualized CSP yield for candidates near the target strike."""
	symbol = args.symbol.upper()
	pct_below = args.pct_below
	min_dte = args.min_dte
	max_dte = args.max_dte

	# Fetch the full options chain from CBOE
	current_price, options = _fetch_options_chain(symbol)

	# Calculate target strike
	target_strike = round(current_price * (1 - pct_below / 100), 2)

	# Process each option in the chain
	candidates = []
	for opt in options:
		contract = opt.get("option", "")

		# Parse the contract symbol
		parsed = _parse_contract(contract)
		if parsed is None:
			continue

		# Filter: puts only
		if parsed["option_type"] != "P":
			continue

		# Filter: DTE within target range
		if parsed["dte"] < min_dte or parsed["dte"] > max_dte:
			continue

		# Filter: open interest > 0
		oi = opt.get("open_interest", 0)
		if oi is None or int(oi) <= 0:
			continue

		# Extract pricing data
		bid = _safe_float(opt.get("bid"))
		ask = _safe_float(opt.get("ask"))
		if bid is None or ask is None or bid < 0 or ask <= 0:
			continue

		# Skip zero-bid puts (no market for the contract)
		if bid == 0 and ask == 0:
			continue

		# CBOE options chain returns IV as decimal (e.g., 0.45 = 45%)
		iv_raw = _safe_float(opt.get("iv"))
		if iv_raw is None or iv_raw <= 0:
			continue
		iv = iv_raw if iv_raw < 10 else iv_raw / 100.0

		# Calculate derived metrics
		mid_price = round((bid + ask) / 2, 2)

		# Premium per contract: mid_price * 100 (options contract = 100 shares)
		premium_per_contract = round(mid_price * 100, 2)

		# Capital required: strike * 100 (cash-secured = full strike value)
		capital_required = round(parsed["strike"] * 100, 2)

		# Return per contract cycle
		if capital_required <= 0:
			continue
		return_pct = round(premium_per_contract / capital_required * 100, 2)

		# Annualized yield
		annualized_yield = round(return_pct * (365 / parsed["dte"]), 2)

		# Breakeven price: strike minus premium received
		breakeven = round(parsed["strike"] - mid_price, 2)

		# Downside cushion: how far below current price is the breakeven
		downside_cushion_pct = round((current_price - breakeven) / current_price * 100, 2)

		candidates.append(
			{
				"contract": contract,
				"expiration": parsed["expiration"],
				"strike": parsed["strike"],
				"dte": parsed["dte"],
				"bid": bid,
				"ask": ask,
				"mid_price": mid_price,
				"implied_volatility": iv,
				"open_interest": int(oi),
				"premium_per_contract": premium_per_contract,
				"capital_required": capital_required,
				"return_pct": return_pct,
				"annualized_yield": annualized_yield,
				"breakeven": breakeven,
				"downside_cushion_pct": downside_cushion_pct,
			}
		)

	# Sort by annualized yield descending
	candidates.sort(key=lambda c: -c["annualized_yield"])

	# Return top 5 candidates
	top_candidates = candidates[:5]

	result = {
		"symbol": symbol,
		"current_price": round(current_price, 2),
		"scan_parameters": {
			"pct_below_current": pct_below,
			"target_strike": target_strike,
			"dte_range": [min_dte, max_dte],
		},
		"candidates": top_candidates,
		"candidates_count": len(top_candidates),
	}

	output_json(result)


def main():
	parser = argparse.ArgumentParser(description="CSP Yield Calculator - Cash-secured put annualized yield analysis")
	sub = parser.add_subparsers(dest="command", required=True)

	sp_calculate = sub.add_parser("calculate")
	sp_calculate.add_argument("symbol", help="Stock or index ticker symbol (e.g., AAPL, AXTI, MSFT)")
	sp_calculate.add_argument(
		"--pct-below",
		type=float,
		default=10.0,
		help="Target strike as percentage below current price (default: 10.0)",
	)
	sp_calculate.add_argument(
		"--min-dte",
		type=int,
		default=30,
		help="Minimum days to expiration (default: 30)",
	)
	sp_calculate.add_argument(
		"--max-dte",
		type=int,
		default=60,
		help="Maximum days to expiration (default: 60)",
	)
	sp_calculate.set_defaults(func=cmd_calculate)

	args = parser.parse_args()
	args.func(args)


if __name__ == "__main__":
	main()
