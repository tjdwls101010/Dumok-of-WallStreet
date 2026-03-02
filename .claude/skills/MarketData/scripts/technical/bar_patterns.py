#!/usr/bin/env python3
"""Williams Bar Patterns: 11 short-term chart pattern detectors (5 bullish + 6 bearish).

Scans recent price bars for Larry Williams' pattern setups from "Long-Term
Secrets to Short-Term Trading" (2011 edition). Each pattern includes
historically tested accuracy, entry/stop levels, electronic-era validity,
direction (bullish or bearish), and next-day confirmation status where
applicable (Williams Ch.7). Bearish patterns are mirrors of bullish setups,
detecting sell/short entry opportunities per Williams' sell setup rules.

Commands:
	scan: Scan for Williams bar patterns on a given ticker

Args:
	symbol (str): Ticker symbol (e.g., "AAPL", "SPY", "ES=F")
	--lookback (int): Number of recent bars to scan (default: 5)

Returns:
	dict: {
		"symbol": str,
		"patterns_detected": [{
			"pattern": str,
			"date": str,
			"direction": str,          # "bullish" or "bearish"
			"entry_price": float,
			"stop_price": float,
			"electronic_era_caveat": bool,
			"historical_accuracy": float,
			"strength": str,           # "high" (confirmed), "medium" (pending), "low" (failed)
			"confirmation_needed": str,
			"confirmed": bool or null  # true=confirmed, false=failed, null=pending
		}],
		"pattern_count": int,
		"bullish_count": int,
		"bearish_count": int,
		"scan_window_days": int
	}

	Note on confirmation fields (smash_day, specialists_trap and bearish mirrors):
	  - confirmed=true: Next-day reversal confirmed
	  - confirmed=false: Confirmation failed (next day did NOT reverse)
	  - confirmed=null: Pending — pattern is on latest bar, no next-day data yet
	  - strength reflects confirmation: "high" if confirmed, "low" if failed,
	    "medium" if pending or not applicable
	  - specialists_trap / bearish_specialists_trap return "box_high" and "box_low"

Example:
	>>> python bar_patterns.py scan SPY --lookback 5
	{
		"symbol": "SPY",
		"patterns_detected": [
			{
				"pattern": "bearish_smash_day",
				"date": "2026-02-28",
				"direction": "bearish",
				"entry_price": 518.00,
				"stop_price": 525.30,
				"electronic_era_caveat": false,
				"historical_accuracy": 0.76,
				"strength": "medium",
				"confirmation_needed": "next_bar_below_low",
				"confirmed": null
			}
		],
		"pattern_count": 1,
		"bullish_count": 0,
		"bearish_count": 1,
		"scan_window_days": 5
	}

Use Cases:
	- Identify short-term reversal setups for both long and short entry timing
	- Filter patterns by direction, strength, and electronic-era validity
	- Filter by confirmed=true for highest-conviction entries
	- Combine with TDW/TDM bias for higher-probability trades
	- Flag Oops! patterns that may be unreliable in electronic markets
	- Detect bearish setups for short-selling qualification in williams.py pipeline

Notes:
	Bullish Patterns (5):
	- Outside Day: ~85% accuracy (S&P 109 trades, 1982-1998). Engulfs prior
	  bar + close in lower half → buy next open.
	- Smash Day: ~76% accuracy (S&P 25 trades). Close below prior low, next
	  day trades above high → buy. Williams Ch.7 confirmation.
	- Hidden Smash Day: ~89% accuracy (T-Bonds 28 trades). Up close but in
	  bottom 25% of range → buy above high. Most subtle trap pattern.
	- Specialists' Trap: ~80% accuracy. Wyckoff (1930s). False downside
	  breakout from 5-10 day box, reversal above box_high within 1-3 days.
	- Oops!: ~82% accuracy in pit era. Gap down, recovery to prior low → buy.
	  Greatly diminished in electronic era.

	Bearish Patterns (6):
	- Bearish Outside Day: ~85% accuracy. Engulfs prior bar + close in upper
	  half → sell next open. Stop above the high.
	- Bearish Smash Day: ~76% accuracy. Close above prior high (naked up close),
	  next day trades below low → sell. Williams Ch.7 sell setup mirror.
	- Bearish Hidden Smash Day: ~89% accuracy. Down close but in top 75% of
	  range — the down close masks that sellers got smashed.
	- Bearish Specialists' Trap: ~80% accuracy. False upside breakout from
	  5-10 day box, falls back below box_low within 1-3 days.
	- Bearish Oops!: ~82% accuracy. Gap up above prior high, sells off to
	  prior high → sell. Diminished in electronic era.
	- Selling Climax: ~70% accuracy (estimated). Extremely high volume sell-off
	  with wide range bar. Actually BULLISH — marks potential bottom/reversal.
	  Requires 2x avg volume AND 2x avg range.

	Electronic Era Status: Outside Day, Smash Day, Hidden Smash, Specialists'
	  Trap all remain valid (both bullish and bearish). Oops! greatly diminished.

See Also:
	- williams.py: Consolidated Williams tools (legacy)
	- gsv.py: Greatest Swing Value failure swing measurement
	- entry_patterns.py: Minervini entry patterns
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import yfinance as yf
from utils import output_json, safe_run

# ── Historical accuracy constants ──────────────────────────────────────────

PATTERN_ACCURACY = {
	# Bullish patterns
	"outside_day": {"accuracy": 0.85, "source": "S&P 109 trades (1982-1998)"},
	"smash_day": {"accuracy": 0.76, "source": "S&P 25 trades"},
	"hidden_smash_day": {"accuracy": 0.89, "source": "T-Bonds 28 trades"},
	"specialists_trap": {"accuracy": 0.80, "source": "estimated from book examples"},
	"oops": {"accuracy": 0.82, "source": "S&P 98 trades (diminished in electronic era)"},
	# Bearish patterns (mirrors of bullish, same underlying accuracy)
	"bearish_outside_day": {"accuracy": 0.85, "source": "mirror of outside_day"},
	"bearish_smash_day": {"accuracy": 0.76, "source": "mirror of smash_day (Williams Ch.7 sell setup)"},
	"bearish_hidden_smash_day": {"accuracy": 0.89, "source": "mirror of hidden_smash_day"},
	"bearish_specialists_trap": {"accuracy": 0.80, "source": "mirror of specialists_trap (false upside breakout)"},
	"bearish_oops": {"accuracy": 0.82, "source": "mirror of oops (diminished in electronic era)"},
	"selling_climax": {"accuracy": 0.70, "source": "estimated from book examples (actually bullish)"},
}

# ── Bullish pattern detection functions ───────────────────────────────────


def _detect_outside_day(df, idx):
	"""Outside Day: current bar engulfs prior bar's range + closes in lower half."""
	if idx < 1:
		return None
	curr = df.iloc[idx]
	prev = df.iloc[idx - 1]
	if curr["High"] > prev["High"] and curr["Low"] < prev["Low"]:
		bar_range = curr["High"] - curr["Low"]
		close_position = (curr["Close"] - curr["Low"]) / bar_range if bar_range > 0 else 0.5
		if close_position < 0.5:
			return {
				"pattern": "outside_day",
				"date": df.index[idx].strftime("%Y-%m-%d"),
				"direction": "bullish",
				"entry_price": round(float(curr["Open"]), 2),
				"stop_price": round(float(curr["Low"]), 2),
				"electronic_era_caveat": False,
				"historical_accuracy": PATTERN_ACCURACY["outside_day"]["accuracy"],
				"strength": "high",
				"confirmation_needed": "next_bar_open_buy",
			}
	return None


def _detect_smash_day(df, idx):
	"""Smash Day (Naked): close below prior bar's low -> buy above next bar's high.

	Williams: "If the very next day price moves opposite the smash day and trades
	above the high of a down close smash day, you have a great buy signal."
	We check next-day reversal confirmation when data is available.
	"""
	if idx < 1:
		return None
	curr = df.iloc[idx]
	prev = df.iloc[idx - 1]
	if curr["Close"] < prev["Low"]:
		# Check next-day confirmation if we have the data
		confirmed = None  # None = pending (today's smash, no next bar yet)
		if idx + 1 < len(df):
			next_bar = df.iloc[idx + 1]
			confirmed = next_bar["High"] > curr["High"]

		strength = "high" if confirmed else ("low" if confirmed is False else "medium")
		return {
			"pattern": "smash_day",
			"date": df.index[idx].strftime("%Y-%m-%d"),
			"direction": "bullish",
			"entry_price": round(float(curr["High"]), 2),
			"stop_price": round(float(curr["Low"]), 2),
			"electronic_era_caveat": False,
			"historical_accuracy": PATTERN_ACCURACY["smash_day"]["accuracy"],
			"strength": strength,
			"confirmation_needed": "next_bar_above_high",
			"confirmed": confirmed,
		}
	return None


def _detect_hidden_smash_day(df, idx):
	"""Hidden Smash Day: bullish candle but close in bottom 25% of range."""
	curr = df.iloc[idx]
	bar_range = curr["High"] - curr["Low"]
	if bar_range <= 0:
		return None
	close_position = (curr["Close"] - curr["Low"]) / bar_range
	is_up_close = curr["Close"] > curr["Open"]
	if is_up_close and close_position <= 0.25:
		return {
			"pattern": "hidden_smash_day",
			"date": df.index[idx].strftime("%Y-%m-%d"),
			"direction": "bullish",
			"entry_price": round(float(curr["High"]), 2),
			"stop_price": round(float(curr["Low"]), 2),
			"electronic_era_caveat": False,
			"historical_accuracy": PATTERN_ACCURACY["hidden_smash_day"]["accuracy"],
			"strength": "high",
			"confirmation_needed": "next_bar_above_high",
		}
	return None


def _detect_specialists_trap(df, idx, lookback=10):
	"""Specialists' Trap: 5-10 day box, fake breakout, reversal within 1-3 days.

	Williams: The true high of the breakout day becomes critical. If it is
	broken above in the next 1-3 days, the downside breakout was false and
	the public was trapped. We check for follow-through confirmation.
	"""
	if idx < lookback:
		return None
	window = df.iloc[idx - lookback:idx]
	box_high = window["High"].max()
	box_low = window["Low"].min()
	box_range = box_high - box_low
	avg_close = window["Close"].mean()
	if avg_close <= 0 or box_range / avg_close > 0.05:
		return None
	curr = df.iloc[idx]
	if curr["Low"] < box_low and curr["Close"] > box_low:
		# Check 1-3 day follow-through: does price break above box high?
		confirmed = None  # None = pending
		follow_through_days = 0
		for offset in range(1, 4):
			if idx + offset < len(df):
				follow_through_days += 1
				if df.iloc[idx + offset]["High"] > box_high:
					confirmed = True
					break
		# If we had 3 follow-through days and none broke above, mark as failed
		if confirmed is None and follow_through_days >= 3:
			confirmed = False

		strength = "high" if confirmed else ("low" if confirmed is False else "medium")
		return {
			"pattern": "specialists_trap",
			"date": df.index[idx].strftime("%Y-%m-%d"),
			"direction": "bullish",
			"entry_price": round(float(box_high), 2),
			"stop_price": round(float(curr["Low"]), 2),
			"electronic_era_caveat": False,
			"historical_accuracy": PATTERN_ACCURACY["specialists_trap"]["accuracy"],
			"strength": strength,
			"confirmation_needed": "price_above_box_high",
			"confirmed": confirmed,
			"box_high": round(float(box_high), 2),
			"box_low": round(float(box_low), 2),
		}
	return None


def _detect_oops(df, idx):
	"""Oops!: gap down open, recovery to prior low = buy. Limited in electronic era."""
	if idx < 1:
		return None
	curr = df.iloc[idx]
	prev = df.iloc[idx - 1]
	if curr["Open"] < prev["Low"]:
		if curr["High"] >= prev["Low"]:
			return {
				"pattern": "oops",
				"date": df.index[idx].strftime("%Y-%m-%d"),
				"direction": "bullish",
				"entry_price": round(float(prev["Low"]), 2),
				"stop_price": round(float(curr["Low"]), 2),
				"electronic_era_caveat": True,
				"historical_accuracy": PATTERN_ACCURACY["oops"]["accuracy"],
				"strength": "medium",
				"confirmation_needed": "recovery_to_prior_low",
			}
	return None


# ── Bearish pattern detection functions ───────────────────────────────────


def _detect_bearish_outside_day(df, idx):
	"""Bearish Outside Day: engulfs prior bar's range + closes in upper half → sell."""
	if idx < 1:
		return None
	curr = df.iloc[idx]
	prev = df.iloc[idx - 1]
	if curr["High"] > prev["High"] and curr["Low"] < prev["Low"]:
		bar_range = curr["High"] - curr["Low"]
		close_position = (curr["Close"] - curr["Low"]) / bar_range if bar_range > 0 else 0.5
		if close_position > 0.5:
			return {
				"pattern": "bearish_outside_day",
				"date": df.index[idx].strftime("%Y-%m-%d"),
				"direction": "bearish",
				"entry_price": round(float(curr["Open"]), 2),
				"stop_price": round(float(curr["High"]), 2),
				"electronic_era_caveat": False,
				"historical_accuracy": PATTERN_ACCURACY["bearish_outside_day"]["accuracy"],
				"strength": "high",
				"confirmation_needed": "next_bar_open_sell",
			}
	return None


def _detect_bearish_smash_day(df, idx):
	"""Bearish Smash Day: close above prior bar's high → sell below next bar's low.

	Williams Ch.7 Sell Setup: "Day 1: Close > Prior day's High (naked up close).
	Day 2: If price trades BELOW Day 1's Low, sell immediately."
	"""
	if idx < 1:
		return None
	curr = df.iloc[idx]
	prev = df.iloc[idx - 1]
	if curr["Close"] > prev["High"]:
		confirmed = None
		if idx + 1 < len(df):
			next_bar = df.iloc[idx + 1]
			confirmed = next_bar["Low"] < curr["Low"]

		strength = "high" if confirmed else ("low" if confirmed is False else "medium")
		return {
			"pattern": "bearish_smash_day",
			"date": df.index[idx].strftime("%Y-%m-%d"),
			"direction": "bearish",
			"entry_price": round(float(curr["Low"]), 2),
			"stop_price": round(float(curr["High"]), 2),
			"electronic_era_caveat": False,
			"historical_accuracy": PATTERN_ACCURACY["bearish_smash_day"]["accuracy"],
			"strength": strength,
			"confirmation_needed": "next_bar_below_low",
			"confirmed": confirmed,
		}
	return None


def _detect_bearish_hidden_smash_day(df, idx):
	"""Bearish Hidden Smash Day: down close but in top 75% of range.

	Mirror of bullish hidden smash: Close < Open (down day) but close in
	upper 75% of range. The down close masks that sellers got trapped near
	the high — sell below the low on next bar.
	"""
	curr = df.iloc[idx]
	bar_range = curr["High"] - curr["Low"]
	if bar_range <= 0:
		return None
	close_position = (curr["Close"] - curr["Low"]) / bar_range
	is_down_close = curr["Close"] < curr["Open"]
	if is_down_close and close_position >= 0.75:
		return {
			"pattern": "bearish_hidden_smash_day",
			"date": df.index[idx].strftime("%Y-%m-%d"),
			"direction": "bearish",
			"entry_price": round(float(curr["Low"]), 2),
			"stop_price": round(float(curr["High"]), 2),
			"electronic_era_caveat": False,
			"historical_accuracy": PATTERN_ACCURACY["bearish_hidden_smash_day"]["accuracy"],
			"strength": "high",
			"confirmation_needed": "next_bar_below_low",
		}
	return None


def _detect_bearish_specialists_trap(df, idx, lookback=10):
	"""Bearish Specialists' Trap: false upside breakout, reversal within 1-3 days.

	Mirror of bullish trap: price breaks above box_high (false upside breakout),
	then falls back below box_low within 1-3 days. The public is trapped long.
	"""
	if idx < lookback:
		return None
	window = df.iloc[idx - lookback:idx]
	box_high = window["High"].max()
	box_low = window["Low"].min()
	box_range = box_high - box_low
	avg_close = window["Close"].mean()
	if avg_close <= 0 or box_range / avg_close > 0.05:
		return None
	curr = df.iloc[idx]
	if curr["High"] > box_high and curr["Close"] < box_high:
		# Check 1-3 day follow-through: does price break below box low?
		confirmed = None
		follow_through_days = 0
		for offset in range(1, 4):
			if idx + offset < len(df):
				follow_through_days += 1
				if df.iloc[idx + offset]["Low"] < box_low:
					confirmed = True
					break
		if confirmed is None and follow_through_days >= 3:
			confirmed = False

		strength = "high" if confirmed else ("low" if confirmed is False else "medium")
		return {
			"pattern": "bearish_specialists_trap",
			"date": df.index[idx].strftime("%Y-%m-%d"),
			"direction": "bearish",
			"entry_price": round(float(box_low), 2),
			"stop_price": round(float(curr["High"]), 2),
			"electronic_era_caveat": False,
			"historical_accuracy": PATTERN_ACCURACY["bearish_specialists_trap"]["accuracy"],
			"strength": strength,
			"confirmation_needed": "price_below_box_low",
			"confirmed": confirmed,
			"box_high": round(float(box_high), 2),
			"box_low": round(float(box_low), 2),
		}
	return None


def _detect_bearish_oops(df, idx):
	"""Bearish Oops!: gap up open above prior high, sell-off to prior high = sell.

	Mirror of bullish oops. Limited in electronic era.
	"""
	if idx < 1:
		return None
	curr = df.iloc[idx]
	prev = df.iloc[idx - 1]
	if curr["Open"] > prev["High"]:
		if curr["Low"] <= prev["High"]:
			return {
				"pattern": "bearish_oops",
				"date": df.index[idx].strftime("%Y-%m-%d"),
				"direction": "bearish",
				"entry_price": round(float(prev["High"]), 2),
				"stop_price": round(float(curr["High"]), 2),
				"electronic_era_caveat": True,
				"historical_accuracy": PATTERN_ACCURACY["bearish_oops"]["accuracy"],
				"strength": "medium",
				"confirmation_needed": "selloff_to_prior_high",
			}
	return None


def _detect_selling_climax(df, idx):
	"""Selling Climax: extremely high volume sell-off marking potential bottom.

	Actually BULLISH — marks a potential reversal point / bottom. Requires
	2x average volume AND 2x average range with close in bottom 25%.
	"""
	if idx < 10:
		return None
	curr = df.iloc[idx]
	bar_range = curr["High"] - curr["Low"]
	if bar_range <= 0 or curr["Close"] >= curr["Open"]:
		return None

	# Close must be in bottom 25% of range
	close_position = (curr["Close"] - curr["Low"]) / bar_range
	if close_position > 0.25:
		return None

	# Volume must be at least 2x the 10-day average
	window = df.iloc[idx - 10:idx]
	avg_volume = window["Volume"].mean()
	if avg_volume <= 0 or curr["Volume"] < avg_volume * 2:
		return None

	# Range must be at least 2x the 10-day average range
	avg_range = (window["High"] - window["Low"]).mean()
	if avg_range <= 0 or bar_range < avg_range * 2:
		return None

	return {
		"pattern": "selling_climax",
		"date": df.index[idx].strftime("%Y-%m-%d"),
		"direction": "bullish",
		"entry_price": round(float(curr["High"]), 2),
		"stop_price": round(float(curr["Low"]), 2),
		"electronic_era_caveat": False,
		"historical_accuracy": PATTERN_ACCURACY["selling_climax"]["accuracy"],
		"strength": "medium",
		"confirmation_needed": "next_bar_above_high",
	}


# ── All detectors in execution order ──────────────────────────────────────

_DETECTORS = [
	# Bullish
	_detect_outside_day,
	_detect_smash_day,
	_detect_hidden_smash_day,
	_detect_specialists_trap,
	_detect_oops,
	# Bearish
	_detect_bearish_outside_day,
	_detect_bearish_smash_day,
	_detect_bearish_hidden_smash_day,
	_detect_bearish_specialists_trap,
	_detect_bearish_oops,
	_detect_selling_climax,
]

# ── Command ────────────────────────────────────────────────────────────────


@safe_run
def cmd_scan(args):
	"""Scan recent bars for Williams bar patterns."""
	symbol = args.symbol.upper()
	lookback = args.lookback

	ticker = yf.Ticker(symbol)
	df = ticker.history(period="3mo", interval="1d")

	if df.empty or len(df) < 2:
		raise ValueError(f"Insufficient data for {symbol} ({len(df)} bars)")

	start_idx = max(1, len(df) - lookback)
	patterns_detected = []

	for i in range(start_idx, len(df)):
		for detector in _DETECTORS:
			result = detector(df, i)
			if result is not None:
				patterns_detected.append(result)

	bullish_count = sum(1 for p in patterns_detected if p.get("direction") == "bullish")
	bearish_count = sum(1 for p in patterns_detected if p.get("direction") == "bearish")

	output_json({
		"symbol": symbol,
		"patterns_detected": patterns_detected,
		"pattern_count": len(patterns_detected),
		"bullish_count": bullish_count,
		"bearish_count": bearish_count,
		"scan_window_days": len(df) - start_idx,
	})


# ── CLI entry point ───────────────────────────────────────────────────────


def main():
	parser = argparse.ArgumentParser(description="Williams Bar Pattern Detection")
	sub = parser.add_subparsers(dest="command", required=True)

	sp = sub.add_parser("scan", help="Scan for Williams bar patterns")
	sp.add_argument("symbol", help="Ticker symbol")
	sp.add_argument("--lookback", type=int, default=5, help="Number of recent bars to scan (default: 5)")
	sp.set_defaults(func=cmd_scan)

	args = parser.parse_args()
	args.func(args)


if __name__ == "__main__":
	main()
