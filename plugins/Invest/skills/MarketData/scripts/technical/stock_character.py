#!/usr/bin/env python3
"""Stock Character Assessment: ADR%, clean/choppy classification, personality grade, liquidity tier.

Persona-neutral module for assessing a stock's trading personality — how it
moves, how it respects key moving averages, and how liquid it is. Designed
to be reusable by any pipeline (TraderLion, Minervini, Williams, etc.)
without embedding persona-specific logic.

Character assessment answers the question: "Is this stock tradeable for my
style?" A clean-trending, liquid stock with moderate+ ADR% is universally
preferred across momentum methodologies. Choppy, illiquid names waste
capital and emotional energy regardless of how strong the setup looks.

Commands:
	assess: Single stock character assessment
	screen: Multiple stocks batch character assessment

Args:
	symbol (str): Ticker symbol (e.g., "AAPL", "NVDA", "META")
	symbols (list[str]): Multiple ticker symbols for screening

Returns:
	For assess:
	dict: {
		"symbol": str,
		"adr_pct": float,
		"adr_class": str,
		"character": str,
		"dollar_volume_avg": float,
		"liquidity_tier": str,
		"ma_respect": {
			"10sma": float,
			"21ema": float,
			"50sma": float
		},
		"gap_frequency_20d": float,
		"character_grade": str
	}

	For screen:
	dict: {
		"results": [
			{
				"symbol": str,
				"adr_pct": float,
				"adr_class": str,
				"character": str,
				"character_grade": str,
				"liquidity_tier": str
			}
		],
		"ranked_by": str,
		"symbols_analyzed": int
	}

Example:
	>>> python stock_character.py assess NVDA
	{
		"symbol": "NVDA",
		"adr_pct": 3.8,
		"adr_class": "moderate_momentum",
		"character": "clean_trender",
		"dollar_volume_avg": 45000000000,
		"liquidity_tier": "mega",
		"ma_respect": {"10sma": 0.85, "21ema": 0.92, "50sma": 0.78},
		"gap_frequency_20d": 0.15,
		"character_grade": "A"
	}

	>>> python stock_character.py screen AAPL NVDA MSFT META GOOGL
	{
		"results": [
			{"symbol": "NVDA", "adr_pct": 3.8, "adr_class": "moderate_momentum",
			 "character": "clean_trender", "character_grade": "A", "liquidity_tier": "mega"},
			{"symbol": "AAPL", "adr_pct": 1.8, "adr_class": "low_momentum",
			 "character": "moderate", "character_grade": "C", "liquidity_tier": "mega"}
		],
		"ranked_by": "character_grade",
		"symbols_analyzed": 5
	}

Use Cases:
	- Pre-screen stocks before deep analysis to filter out untradeable names
	- Compare trading personality across a watchlist
	- Identify clean-trending stocks suitable for momentum strategies
	- Assess liquidity to ensure position sizing is realistic
	- Filter out choppy names that increase whipsaw risk

Notes:
	- ADR% (Average Daily Range) = mean((High - Low) / Close) * 100 over 20 days
	- ADR Class: tight_range (<1.5%), low_momentum (1.5-3%), moderate_momentum (3-5%),
	  high_momentum (>=5%)
	- MA Respect: for each of [10 SMA, 21 EMA, 50 SMA], count days over 60 days
	  where Low was within 1% above the MA and Close was above the MA (bounce)
	  vs broke through. Ratio = bounces / (bounces + breaks)
	- Gap Frequency: days in last 20 where Open was >1.5% from prior Close
	- Character Classification:
	  clean_trender: avg MA respect >= 0.7 AND gap_frequency < 0.15
	  moderate: avg MA respect >= 0.5 OR gap_frequency < 0.25
	  choppy: everything else
	- Liquidity Tier based on 20-day avg dollar volume:
	  mega (>=10B), large (>=1B), mid (>=100M), small (>=10M), micro (<10M)
	- Character Grade:
	  A: clean_trender + moderate_momentum or higher + large+ liquidity
	  B: clean_trender + any ADR + any liquidity, OR moderate + moderate_momentum+ + large+
	  C: moderate character + any
	  D: choppy
	- Uses 1y data period for full MA lookback coverage

See Also:
	- volume_edge.py: Volume edge detection for breakout confirmation
	- volume_analysis.py: Accumulation/distribution grading
	- closing_range.py: Bar quality classification
	- vcp.py: VCP detection benefits from clean-trending character filter
"""

import argparse
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import yfinance as yf
from utils import output_json, safe_run


def _calc_adr_pct(high, low, close, window=20):
	"""Calculate Average Daily Range % over the given window.

	ADR% = mean((High - Low) / Close) * 100 over last N trading days.
	"""
	n = min(window, len(close))
	h = high.values[-n:].astype(float)
	l = low.values[-n:].astype(float)
	c = close.values[-n:].astype(float)

	mask = c > 0
	if not np.any(mask):
		return 0.0

	daily_range_pct = np.where(mask, (h - l) / c * 100, 0.0)
	return round(float(np.mean(daily_range_pct[mask])), 2)


def _classify_adr(adr_pct):
	"""Classify ADR% into momentum category."""
	if adr_pct >= 5.0:
		return "high_momentum"
	elif adr_pct >= 3.0:
		return "moderate_momentum"
	elif adr_pct >= 1.5:
		return "low_momentum"
	else:
		return "tight_range"


def _calc_ma_respect(data, lookback=60):
	"""Calculate MA respect ratio for 10 SMA, 21 EMA, 50 SMA.

	For each MA, over the last `lookback` trading days, count bounces
	vs breaks. A bounce = Low within 1% above the MA AND Close above
	the MA. A break = Low more than 1% below the MA.
	"""
	close = data["Close"]
	low = data["Low"]

	sma10 = close.rolling(10).mean()
	ema21 = close.ewm(span=21, adjust=False).mean()
	sma50 = close.rolling(50).mean()

	ma_dict = {"10sma": sma10, "21ema": ema21, "50sma": sma50}
	result = {}

	# Need 50 bars for SMA50 to exist, then lookback window on top
	usable = min(lookback, len(close) - 50)
	if usable < 10:
		return {"10sma": 0.0, "21ema": 0.0, "50sma": 0.0}

	for label, ma in ma_dict.items():
		bounces = 0
		breaks = 0
		for i in range(-usable, 0):
			ma_val = float(ma.iloc[i])
			low_val = float(low.iloc[i])
			close_val = float(close.iloc[i])

			if ma_val <= 0 or np.isnan(ma_val):
				continue

			distance_pct = (low_val - ma_val) / ma_val

			# Low within 1% above the MA (touching/near) and Close above MA
			if -0.01 <= distance_pct <= 0.01 and close_val > ma_val:
				bounces += 1
			# Low broke below MA (more than 1% below)
			elif distance_pct < -0.01:
				breaks += 1

		total = bounces + breaks
		result[label] = round(bounces / total, 2) if total > 0 else 0.0

	return result


def _calc_gap_frequency(data, window=20):
	"""Calculate gap frequency over the last N trading days.

	Gap = abs(Open - prev_Close) / prev_Close > 1.5%.
	Frequency = gap_count / window.
	"""
	opens = data["Open"].values.astype(float)
	closes = data["Close"].values.astype(float)
	n = len(closes)

	period = min(window, n - 1)
	if period <= 0:
		return 0.0

	gap_count = 0
	start = n - period
	for i in range(start, n):
		prev_c = closes[i - 1]
		if prev_c <= 0:
			continue
		gap_pct = abs(opens[i] - prev_c) / prev_c
		if gap_pct > 0.015:
			gap_count += 1

	return round(gap_count / period, 2)


def _classify_character(avg_ma_respect, gap_frequency):
	"""Classify stock trading character.

	clean_trender: avg MA respect >= 0.7 AND gap_frequency < 0.15
	moderate: avg MA respect >= 0.5 OR gap_frequency < 0.25
	choppy: everything else
	"""
	if avg_ma_respect >= 0.7 and gap_frequency < 0.15:
		return "clean_trender"
	elif avg_ma_respect >= 0.5 or gap_frequency < 0.25:
		return "moderate"
	else:
		return "choppy"


def _calc_dollar_volume(data, window=20):
	"""Calculate average dollar volume over last N days."""
	n = min(window, len(data))
	recent = data.tail(n)
	dv = recent["Volume"].values.astype(float) * recent["Close"].values.astype(float)
	return round(float(np.mean(dv)), 2)


def _classify_liquidity(dollar_volume):
	"""Classify liquidity tier by average dollar volume."""
	if dollar_volume >= 10_000_000_000:
		return "mega"
	elif dollar_volume >= 1_000_000_000:
		return "large"
	elif dollar_volume >= 100_000_000:
		return "mid"
	elif dollar_volume >= 10_000_000:
		return "small"
	else:
		return "micro"


def _grade_character(character, adr_class, liquidity_tier):
	"""Assign character grade A-D.

	A: clean_trender + moderate_momentum or higher + large+ liquidity
	B: clean_trender + any ADR + any liquidity, OR moderate + moderate_momentum+ + large+
	C: moderate character + any
	D: choppy
	"""
	momentum_rank = {
		"high_momentum": 4,
		"moderate_momentum": 3,
		"low_momentum": 2,
		"tight_range": 1,
	}
	liquidity_rank = {
		"mega": 5,
		"large": 4,
		"mid": 3,
		"small": 2,
		"micro": 1,
	}

	mom = momentum_rank.get(adr_class, 0)
	liq = liquidity_rank.get(liquidity_tier, 0)

	if character == "clean_trender" and mom >= 3 and liq >= 4:
		return "A"
	elif character == "clean_trender":
		return "B"
	elif character == "moderate" and mom >= 3 and liq >= 4:
		return "B"
	elif character == "moderate":
		return "C"
	else:
		return "D"


def _assess_single(symbol, data):
	"""Run full character assessment for a single stock."""
	high = data["High"]
	low = data["Low"]
	close = data["Close"]

	adr_pct = _calc_adr_pct(high, low, close)
	adr_class = _classify_adr(adr_pct)
	ma_respect = _calc_ma_respect(data)
	gap_freq = _calc_gap_frequency(data)

	avg_ma = float(np.mean(list(ma_respect.values())))
	character = _classify_character(avg_ma, gap_freq)

	dollar_vol = _calc_dollar_volume(data)
	liquidity = _classify_liquidity(dollar_vol)
	grade = _grade_character(character, adr_class, liquidity)

	return {
		"symbol": symbol,
		"adr_pct": adr_pct,
		"adr_class": adr_class,
		"character": character,
		"dollar_volume_avg": dollar_vol,
		"liquidity_tier": liquidity,
		"ma_respect": ma_respect,
		"gap_frequency_20d": gap_freq,
		"character_grade": grade,
	}


@safe_run
def cmd_assess(args):
	"""Single stock character assessment."""
	symbol = args.symbol.upper()
	ticker = yf.Ticker(symbol)
	data = ticker.history(period="1y")

	if data.empty or len(data) < 60:
		output_json({
			"error": f"Insufficient data for {symbol}. Need at least 60 trading days.",
			"data_points": len(data),
		})
		return

	result = _assess_single(symbol, data)
	output_json(result)


@safe_run
def cmd_screen(args):
	"""Multiple stocks batch character assessment."""
	results = []
	grade_order = {"A": 4, "B": 3, "C": 2, "D": 1}

	for sym in args.symbols:
		sym = sym.upper()
		try:
			ticker = yf.Ticker(sym)
			data = ticker.history(period="1y")

			if data.empty or len(data) < 60:
				results.append({"symbol": sym, "error": "Insufficient data"})
				continue

			result = _assess_single(sym, data)
			results.append(result)
		except Exception as e:
			results.append({
				"symbol": sym,
				"error": f"{type(e).__name__}: {e}",
			})

	# Sort by character_grade (A > B > C > D)
	valid = [r for r in results if "character_grade" in r]
	errors = [r for r in results if "character_grade" not in r]
	valid.sort(
		key=lambda x: grade_order.get(x.get("character_grade", "D"), 0),
		reverse=True,
	)

	output_json({
		"results": valid + errors,
		"ranked_by": "character_grade",
		"symbols_analyzed": len(results),
	})


def main():
	parser = argparse.ArgumentParser(
		description="Stock Character Assessment: ADR%, classification, grade, liquidity"
	)
	sub = parser.add_subparsers(dest="command", required=True)

	# assess
	sp = sub.add_parser("assess", help="Single stock character assessment")
	sp.add_argument("symbol", help="Ticker symbol")
	sp.set_defaults(func=cmd_assess)

	# screen
	sp = sub.add_parser("screen", help="Multi-stock character screening")
	sp.add_argument("symbols", nargs="+", help="Ticker symbols to screen")
	sp.set_defaults(func=cmd_screen)

	args = parser.parse_args()
	args.func(args)


if __name__ == "__main__":
	main()
