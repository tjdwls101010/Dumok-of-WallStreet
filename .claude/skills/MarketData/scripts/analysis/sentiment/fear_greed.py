#!/usr/bin/env python3
"""CNN Fear & Greed Index tracking market sentiment through 7-indicator composite scoring system.

Fetches real-time sentiment data from CNN's Fear & Greed Index combining market momentum, stock strength,
market breadth, put/call options, junk bond demand, volatility (VIX), and safe haven demand.
Composite score ranges from Extreme Fear (0) to Extreme Greed (100) for contrarian trading signals.

Args:
	--include-indicators (flag): Include detailed breakdown of all 7 individual sentiment indicators

Returns:
	dict: {
		"current": {
			"score": float,             # 0-100 composite sentiment score
			"rating": str,              # Extreme Fear, Fear, Neutral, Greed, Extreme Greed
			"timestamp": str            # Data timestamp
		},
		"previous": {
			"close": float,             # Previous close score
			"1_week_ago": float,        # Score 1 week ago
			"1_month_ago": float,       # Score 1 month ago
			"1_year_ago": float         # Score 1 year ago
		},
		"indicators": {                 # Optional, if --include-indicators flag set
			"market_momentum_sp500": {
				"score": float,
				"rating": str
			},
			"stock_price_strength": {
				"score": float,
				"rating": str
			},
			"stock_price_breadth": {
				"score": float,
				"rating": str
			},
			"put_call_options": {
				"score": float,
				"rating": str
			},
			"junk_bond_demand": {
				"score": float,
				"rating": str
			},
			"market_volatility_vix": {
				"score": float,
				"rating": str
			},
			"safe_haven_demand": {
				"score": float,
				"rating": str
			}
		},
		"interpretation": str           # Contextual interpretation with contrarian guidance
	}

Example:
	>>> python fear_greed.py
	{
		"current": {
			"score": 25,
			"rating": "Fear",
			"timestamp": "2026-02-05T12:00:00Z"
		},
		"previous": {
			"1_week_ago": 45,
			"1_month_ago": 65
		},
		"interpretation": "Fear (25): Bearish sentiment, potential buying opportunity"
	}
    
	>>> python fear_greed.py --include-indicators
	{
		"current": {"score": 85, "rating": "Extreme Greed"},
		"indicators": {
			"put_call_options": {"score": 92, "rating": "Extreme Greed"},
			"market_volatility_vix": {"score": 78, "rating": "Greed"}
		},
		"interpretation": "Extreme Greed (85): Market euphoria, potential correction risk"
	}

Use Cases:
	- Contrarian reversal signals: Extreme Fear (<25) = buy signal, Extreme Greed (>75) = sell signal
	- Multi-asset divergence: Compare Fear & Greed with SPY/QQQ put/call for confirmation
	- Sentiment regime detection: Prolonged Fear periods precede bull markets, Greed precedes corrections
	- VIX confirmation: Extreme Fear + high VIX = capitulation, Extreme Greed + low VIX = complacency
	- Historical context: Compare current score to 1-month/1-year ago for trend analysis

Notes:
	- Extreme Fear (0-25): Panic selling, strong contrarian buy signal (historically profitable)
	- Fear (25-45): Bearish sentiment, potential buying opportunity
	- Neutral (45-55): Balanced market, no clear directional signal
	- Greed (55-75): Bullish sentiment, overbought conditions possible
	- Extreme Greed (75-100): Euphoria, correction risk high (contrarian sell signal)
	- Index mean-reverts: Extreme readings (>75 or <25) typically reverse within 2-4 weeks
	- Put/Call component most reliable for near-term reversals
	- VIX component lags price action (smoothing effect)

See Also:
	- putcall_ratio.py: Individual put/call analysis vs composite Fear & Greed
	- divergence.py: Safe haven divergence (component of Fear & Greed)
	- convergence.py: Combine Fear & Greed with technical RSI and macro models
	- technical/volatility.py: VIX analysis (key Fear & Greed component)
"""

import argparse
import os
import sys

import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from utils import output_json, safe_run


@safe_run
def cmd_fear_greed_index(args):
	"""Fetch CNN Fear & Greed Index data from JSON API.

	The Fear & Greed Index measures market sentiment using 7 indicators:
	- Market Momentum (S&P 500 vs 125-day average)
	- Stock Price Strength (52-week highs vs lows)
	- Stock Price Breadth (advancing vs declining volume)
	- Put/Call Options (put volume vs call volume)
	- Junk Bond Demand (spread over investment grade)
	- Market Volatility (VIX)
	- Safe Haven Demand (stocks vs bonds performance)

	Args:
		include_indicators: If True, includes detailed breakdown of all 11 indicators

	Returns:
		JSON with current score, rating, previous values, and optional indicators
	"""
	# CNN Fear & Greed Index API endpoint
	url = "https://production.dataviz.cnn.io/index/fearandgreed/graphdata"

	# Required headers to avoid HTTP 418 (I'm a teapot) error
	headers = {
		"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
		"Referer": "https://money.cnn.com/data/fear-and-greed/",
		"Origin": "https://money.cnn.com",
	}

	try:
		response = requests.get(url, headers=headers, timeout=10)
		response.raise_for_status()
	except requests.exceptions.RequestException as e:
		output_json({"error": f"Failed to fetch Fear & Greed Index: {e}"})
		return

	data = response.json()

	# Extract main fear & greed data
	fg_data = data.get("fear_and_greed", {})

	result = {
		"current": {
			"score": round(fg_data.get("score", 0), 2),
			"rating": fg_data.get("rating", "unknown"),
			"timestamp": fg_data.get("timestamp", ""),
		},
		"previous": {
			"close": round(fg_data.get("previous_close", 0), 2),
			"1_week_ago": round(fg_data.get("previous_1_week", 0), 2),
			"1_month_ago": round(fg_data.get("previous_1_month", 0), 2),
			"1_year_ago": round(fg_data.get("previous_1_year", 0), 2),
		},
	}

	# Add indicators if requested
	if args.include_indicators:
		indicators = {}
		indicator_keys = [
			"junk_bond_demand",
			"market_volatility_vix",
			"market_volatility_vix_50",
			"put_call_options",
			"market_momentum_sp500",
			"market_momentum_sp125",
			"stock_price_strength",
			"stock_price_breadth",
			"safe_haven_demand",
		]

		for key in indicator_keys:
			if key in data:
				ind_data = data[key]
				indicators[key] = {
					"score": round(ind_data.get("score", 0), 2),
					"rating": ind_data.get("rating", "unknown"),
				}

		result["indicators"] = indicators

	# Interpretation based on score
	score = result["current"]["score"]

	if score >= 75:
		interpretation = f"Extreme Greed ({score}): Market euphoria, potential correction risk"
	elif score >= 55:
		interpretation = f"Greed ({score}): Bullish sentiment, overbought conditions possible"
	elif score >= 45:
		interpretation = f"Neutral ({score}): Balanced market sentiment"
	elif score >= 25:
		interpretation = f"Fear ({score}): Bearish sentiment, potential buying opportunity"
	else:
		interpretation = f"Extreme Fear ({score}): Market panic, strong contrarian buy signal"

	result["interpretation"] = interpretation

	output_json(result)


if __name__ == "__main__":
	parser = argparse.ArgumentParser(description="CNN Fear & Greed Index - Market Sentiment Indicator")
	parser.add_argument(
		"--include-indicators",
		action="store_true",
		help="Include all 11 individual sentiment indicators in output",
	)

	args = parser.parse_args()
	cmd_fear_greed_index(args)
