#!/usr/bin/env python3
"""LEAPS Scanner: Find optimal Long-Term Equity Anticipation Securities for leveraged long exposure.

Scans the CBOE options chain for long-dated call options (LEAPS) that provide leveraged exposure
to high-conviction positions. LEAPS are calls with expiration dates typically 9+ months out,
offering stock-like delta at a fraction of the capital outlay. This scanner identifies the best
LEAPS candidates by estimating delta via Black-Scholes approximation and ranking by proximity
to a target delta (default 0.70), which balances directional exposure with cost efficiency.

Args:
	symbol (str): Stock ticker symbol (e.g., "NVDA", "AAPL", "MSFT", "AMZN")
	command (str): One of scan
	--delta (float): Target delta for LEAPS selection (default: 0.70). Range 0.55-0.85.
	--min-dte (int): Minimum days to expiration (default: 270). Standard LEAPS threshold is ~9 months.

Returns:
	dict: {
		"symbol": str,                    # Ticker symbol (uppercased)
		"current_price": float,           # Current underlying stock price
		"scan_parameters": {
			"target_delta": float,        # Target delta used for scanning
			"min_dte": int,               # Minimum DTE filter applied
			"delta_range": [float, float] # Accepted delta window [low, high]
		},
		"candidates": [                   # Top 5 LEAPS sorted by delta proximity
			{
				"contract": str,          # CBOE contract symbol (e.g., "NVDA260116C00100000")
				"expiration": str,        # Expiration date in YYYY-MM-DD format
				"strike": float,          # Strike price in dollars
				"dte": int,               # Days to expiration
				"bid": float,             # Best bid price
				"ask": float,             # Best ask price
				"mid_price": float,       # Midpoint of bid/ask spread
				"implied_volatility": float, # IV as decimal (e.g., 0.45 = 45%)
				"estimated_delta": float, # Black-Scholes estimated delta
				"open_interest": int,     # Open interest (liquidity indicator)
				"breakeven": float,       # Strike + mid_price (breakeven at expiration)
				"annualized_cost_pct": float, # Annualized premium cost as % of stock price
				"leverage_ratio": float   # Stock price / mid_price (capital efficiency)
			}
		],
		"candidates_count": int           # Number of candidates returned
	}

Example:
	>>> python leaps_scanner.py scan NVDA
	{
		"symbol": "NVDA",
		"current_price": 125.50,
		"scan_parameters": {"target_delta": 0.70, "min_dte": 270},
		"candidates": [{"contract": "NVDA260116C00100000", "estimated_delta": 0.72, ...}],
		"candidates_count": 5
	}

	>>> python leaps_scanner.py scan AAPL --delta 0.80 --min-dte 365
	{
		"symbol": "AAPL",
		"current_price": 185.00,
		"scan_parameters": {"target_delta": 0.80, "min_dte": 365},
		"candidates": [{"contract": "AAPL270115C00160000", "estimated_delta": 0.81, ...}],
		"candidates_count": 3
	}

Use Cases:
	- Position construction: Replace 100 shares with a deep ITM LEAPS for 3-4x capital efficiency
	- Leveraged exposure on conviction names: Use as long leg of a poor man's covered call (PMCC)
	- Risk-defined stock replacement: Maximum loss limited to premium paid, unlike shares
	- Portfolio margin optimization: LEAPS consume less buying power, enabling broader diversification

Notes:
	- Delta estimation uses Black-Scholes (scipy) when available, else moneyness-based approximation
	- Risk-free rate hardcoded at 4.5%; sensitivity to rate assumptions is low for delta estimation
	- CBOE returns IV as percentage (e.g., 45.0 means 45%); scanner divides by 100 for calculations
	- LEAPS lose time value (theta decay) and have no dividend rights, but offer defined risk
	- Open interest > 100 preferred for liquidity; scanner requires OI > 0 as minimum filter
	- Annualized cost percentage compares LEAPS across expirations: lower means cheaper leverage
	- CBOE data is delayed (typically 15 minutes) and may not reflect real-time pricing

See Also:
	- analysis/iv_context.py: Check IV Rank before buying LEAPS; low IV Rank signals cheaper entry
	- data_sources/options.py: Raw options chain data for detailed strike-level analysis
"""

import argparse
import math
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

# Optional scipy import for Black-Scholes delta estimation
try:
	from scipy.stats import norm

	_HAS_SCIPY = True
except ImportError:
	_HAS_SCIPY = False

# Risk-free rate assumption for Black-Scholes
_RISK_FREE_RATE = 0.045

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
	Example: NVDA260116C00100000 -> (NVDA, 2026-01-16, C, 100.0)

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

	# Strike is encoded as strike * 1000 (e.g., 00100000 = 100.000)
	strike = float(strike_raw.lstrip("0") or "0") / 1000.0

	return {
		"expiration": exp_date.strftime("%Y-%m-%d"),
		"option_type": option_type,
		"strike": strike,
		"dte": dte,
	}


def _estimate_delta_bs(spot, strike, tte, iv, r=_RISK_FREE_RATE):
	"""Estimate call delta using Black-Scholes formula with scipy.

	Parameters:
		spot: Current underlying price
		strike: Option strike price
		tte: Time to expiration in years
		iv: Implied volatility as decimal (e.g., 0.45)
		r: Risk-free rate as decimal

	Returns:
		Estimated call delta (0 to 1)
	"""
	if tte <= 0 or iv <= 0 or spot <= 0 or strike <= 0:
		return None

	d1 = (math.log(spot / strike) + (r + iv * iv / 2) * tte) / (iv * math.sqrt(tte))
	return round(norm.cdf(d1), 4)


def _estimate_delta_approx(spot, strike, tte, iv):
	"""Estimate call delta using a moneyness-based linear approximation.

	Fallback when scipy is not available. Uses a simplified mapping from
	moneyness to delta that works reasonably for near-the-money options.

	Parameters:
		spot: Current underlying price
		strike: Option strike price
		tte: Time to expiration in years
		iv: Implied volatility as decimal

	Returns:
		Estimated call delta (0.01 to 0.99)
	"""
	if tte <= 0 or iv <= 0 or spot <= 0 or strike <= 0:
		return None

	delta = 0.5 + (spot - strike) / (spot * iv * math.sqrt(tte)) * 0.4
	return round(max(0.01, min(0.99, delta)), 4)


def _estimate_delta(spot, strike, tte, iv):
	"""Estimate call delta, using Black-Scholes if scipy is available."""
	if _HAS_SCIPY:
		return _estimate_delta_bs(spot, strike, tte, iv)
	return _estimate_delta_approx(spot, strike, tte, iv)


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
def cmd_scan(args):
	"""Scan for optimal LEAPS candidates from the CBOE options chain."""
	symbol = args.symbol.upper()
	target_delta = args.delta
	min_dte = args.min_dte
	delta_low = target_delta - 0.15
	delta_high = target_delta + 0.15

	# Fetch the full options chain from CBOE
	current_price, options = _fetch_options_chain(symbol)

	# Process each option in the chain
	candidates = []
	for opt in options:
		contract = opt.get("option", "")

		# Parse the contract symbol
		parsed = _parse_contract(contract)
		if parsed is None:
			continue

		# Filter: calls only
		if parsed["option_type"] != "C":
			continue

		# Filter: minimum DTE
		if parsed["dte"] < min_dte:
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

		# CBOE options chain returns IV as decimal (e.g., 0.45 = 45%)
		iv_raw = _safe_float(opt.get("iv"))
		if iv_raw is None or iv_raw <= 0:
			continue
		iv = iv_raw if iv_raw < 10 else iv_raw / 100.0

		# Use CBOE-provided delta when available, fallback to estimation
		tte = parsed["dte"] / 365.0
		cboe_delta = _safe_float(opt.get("delta"))
		if cboe_delta is not None and 0 < cboe_delta <= 1:
			delta = round(cboe_delta, 4)
		else:
			delta = _estimate_delta(current_price, parsed["strike"], tte, iv)
			if delta is None:
				continue

		# Filter: delta within target range
		if delta < delta_low or delta > delta_high:
			continue

		# Calculate derived metrics
		mid_price = round((bid + ask) / 2, 2)
		breakeven = round(parsed["strike"] + mid_price, 2)

		# Annualized cost: (mid_price / stock_price) / (DTE / 365) * 100
		annualized_cost_pct = round((mid_price / current_price) / tte * 100, 2) if tte > 0 else None

		# Leverage ratio: stock_price / mid_price
		leverage_ratio = round(current_price / mid_price, 2) if mid_price > 0 else None

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
				"estimated_delta": delta,
				"open_interest": int(oi),
				"breakeven": breakeven,
				"annualized_cost_pct": annualized_cost_pct,
				"leverage_ratio": leverage_ratio,
			}
		)

	# Sort by proximity to target delta, then by DTE descending for tie-breaking
	candidates.sort(key=lambda c: (abs(c["estimated_delta"] - target_delta), -c["dte"]))

	# Return top 5 candidates
	top_candidates = candidates[:5]

	result = {
		"symbol": symbol,
		"current_price": round(current_price, 2),
		"scan_parameters": {
			"target_delta": target_delta,
			"min_dte": min_dte,
			"delta_range": [round(delta_low, 2), round(delta_high, 2)],
		},
		"candidates": top_candidates,
		"candidates_count": len(top_candidates),
	}

	output_json(result)


def main():
	parser = argparse.ArgumentParser(description="LEAPS Scanner - Find optimal long-dated call options")
	sub = parser.add_subparsers(dest="command", required=True)

	sp_scan = sub.add_parser("scan")
	sp_scan.add_argument("symbol", help="Stock ticker symbol (e.g., NVDA, AAPL, MSFT)")
	sp_scan.add_argument(
		"--delta",
		type=float,
		default=0.70,
		help="Target delta for LEAPS selection (default: 0.70)",
	)
	sp_scan.add_argument(
		"--min-dte",
		type=int,
		default=270,
		help="Minimum days to expiration (default: 270)",
	)
	sp_scan.set_defaults(func=cmd_scan)

	args = parser.parse_args()
	args.func(args)


if __name__ == "__main__":
	main()
