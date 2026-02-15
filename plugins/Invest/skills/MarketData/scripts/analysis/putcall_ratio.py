#!/usr/bin/env python3
"""Put/Call Ratio analyzing options market sentiment through put vs call volume imbalance.

Calculates the ratio of put option volume to call option volume as a contrarian sentiment indicator.
Extreme ratios signal potential market reversals: high put/call (>1.0) suggests bearish sentiment and
possible bullish reversal, while low put/call (<0.7) indicates bullish sentiment and potential correction.

Args:
	symbol (str): Stock ticker symbol (e.g., "SPY", "QQQ", "AAPL")
	--expiration (str): Specific expiration date in YYYY-MM-DD format (optional, uses nearest if not provided)

Returns:
	dict: {
		"symbol": str,
		"expiration": str,                # Options expiration date
		"put_call_ratio": float,          # Put volume / Call volume
		"sentiment": str,                 # Extremely Bearish, Bearish, Neutral, Bullish, Extremely Bullish
		"interpretation": str,            # Market sentiment description
		"volumes": {
			"put_volume": int,            # Total put option volume
			"call_volume": int,           # Total call option volume
			"total_volume": int           # Combined volume
		},
		"open_interest": {
			"put_oi": int,                # Put open interest
			"call_oi": int,               # Call open interest
			"oi_ratio": float             # Put OI / Call OI
		},
		"strikes": {
			"put_contracts": int,         # Number of put strikes
			"call_contracts": int,        # Number of call strikes
			"total_contracts": int        # Total strike count
		}
	}

Example:
	>>> python putcall_ratio.py SPY
	{
		"symbol": "SPY",
		"expiration": "2026-02-20",
		"put_call_ratio": 1.25,
		"sentiment": "Bearish",
		"volumes": {
			"put_volume": 250000,
			"call_volume": 200000
		}
	}
    
	>>> python putcall_ratio.py QQQ --expiration 2026-03-21
	{
		"symbol": "QQQ",
		"put_call_ratio": 0.65,
		"sentiment": "Bullish",
		"interpretation": "Market sentiment: Bullish"
	}

Use Cases:
	- Contrarian reversal signals: Extreme ratios (>1.5 or <0.5) signal potential trend reversals
	- Multi-asset sentiment divergence: Compare SPY vs QQQ put/call for sector rotation signals
	- VIX confirmation: High put/call + high VIX confirms fear, low put/call + low VIX confirms complacency
	- Earnings hedging: Pre-earnings put/call spikes indicate uncertainty or bearish positioning
	- Regime detection: Sustained high put/call (>1.2) signals persistent risk-off regime

Notes:
	- Put/Call Ratio > 1.0: Bearish sentiment (more hedging/protection buying)
	- Put/Call Ratio < 0.7: Bullish sentiment (more speculative call buying)
	- Extremely high ratios (>1.5): Panic selling, contrarian buy signal
	- Extremely low ratios (<0.5): Euphoria, contrarian sell signal
	- Equity options skew bullish (normal range 0.7-1.0)
	- Open Interest ratio more stable than volume ratio (smooths noise)
	- Index options (SPX, SPY, QQQ) more reliable than individual stocks

See Also:
	- sentiment/fear_greed.py: CNN Fear & Greed Index includes put/call as subcomponent
	- divergence.py: Compare put/call divergence across SPY, QQQ, IWM for sector signals
	- convergence.py: Combine put/call with technical RSI and macro models
	- technical/volatility.py: VIX confirmation for put/call sentiment signals
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import yfinance as yf
from utils import output_json, safe_run


@safe_run
def cmd_putcall_ratio(args):
	"""Calculate Put/Call Ratio as market sentiment indicator.

	Put/Call Ratio = Total Put Volume / Total Call Volume

	Interpretation:
	- Ratio > 1.0: Bearish sentiment (more puts, expecting decline)
	- Ratio < 0.7: Bullish sentiment (more calls, expecting rise)
	- 0.7-1.0: Neutral sentiment

	Args:
		symbol: Ticker symbol (e.g., SPY, QQQ, AAPL)
		expiration: Specific expiration date (optional, uses nearest if not provided)
	"""
	ticker = yf.Ticker(args.symbol)

	# Get available expiration dates
	try:
		expirations = ticker.options
		if not expirations:
			output_json({"error": f"No options data available for {args.symbol}"})
			return
	except Exception as e:
		output_json({"error": f"Failed to fetch options data: {str(e)}"})
		return

	# Use specified expiration or nearest one
	expiration = args.expiration if args.expiration else expirations[0]

	if expiration not in expirations:
		output_json(
			{
				"error": f"Invalid expiration date. Available: {', '.join(expirations[:5])}..."
			}
		)
		return

	# Get option chain
	try:
		chain = ticker.option_chain(expiration)
		calls = chain.calls
		puts = chain.puts
	except Exception as e:
		output_json({"error": f"Failed to fetch option chain: {str(e)}"})
		return

	# Calculate total volumes
	call_volume = calls["volume"].sum() if "volume" in calls.columns else 0
	put_volume = puts["volume"].sum() if "volume" in puts.columns else 0

	if call_volume == 0:
		output_json(
			{
				"error": "No call volume data available (market closed or insufficient trading activity)"
			}
		)
		return

	# Calculate Put/Call Ratio
	pc_ratio = put_volume / call_volume if call_volume > 0 else 0

	# Sentiment interpretation
	if pc_ratio > 1.0:
		if pc_ratio > 1.5:
			sentiment = "Extremely Bearish"
		else:
			sentiment = "Bearish"
	elif pc_ratio < 0.7:
		if pc_ratio < 0.5:
			sentiment = "Extremely Bullish"
		else:
			sentiment = "Bullish"
	else:
		sentiment = "Neutral"

	# Additional metrics
	call_oi = calls["openInterest"].sum() if "openInterest" in calls.columns else 0
	put_oi = puts["openInterest"].sum() if "openInterest" in puts.columns else 0
	oi_ratio = put_oi / call_oi if call_oi > 0 else 0

	result = {
		"symbol": args.symbol,
		"expiration": expiration,
		"put_call_ratio": round(pc_ratio, 4),
		"sentiment": sentiment,
		"interpretation": f"Market sentiment: {sentiment}",
		"volumes": {
			"put_volume": int(put_volume),
			"call_volume": int(call_volume),
			"total_volume": int(put_volume + call_volume),
		},
		"open_interest": {
			"put_oi": int(put_oi),
			"call_oi": int(call_oi),
			"oi_ratio": round(oi_ratio, 4),
		},
		"strikes": {
			"put_contracts": len(puts),
			"call_contracts": len(calls),
			"total_contracts": len(puts) + len(calls),
		},
	}

	output_json(result)


if __name__ == "__main__":
	parser = argparse.ArgumentParser(
		description="Put/Call Ratio - Market sentiment indicator"
	)
	parser.add_argument("symbol", help="Ticker symbol (e.g., SPY, QQQ, AAPL)")
	parser.add_argument(
		"--expiration",
		help="Expiration date (YYYY-MM-DD), uses nearest if not specified",
	)
	args = parser.parse_args()

	cmd_putcall_ratio(args)
