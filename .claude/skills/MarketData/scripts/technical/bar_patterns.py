#!/usr/bin/env python3
"""Williams Bar Patterns: 5 short-term chart pattern detectors.

Scans recent price bars for Larry Williams' pattern setups from "Long-Term
Secrets to Short-Term Trading" (2011 edition). Each pattern includes
historically tested accuracy, entry/stop levels, and electronic-era validity.

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
			"direction": str,
			"entry_price": float,
			"stop_price": float,
			"electronic_era_caveat": bool,
			"historical_accuracy": float,
			"strength": str,
			"confirmation_needed": str
		}],
		"pattern_count": int,
		"scan_window_days": int
	}

Example:
	>>> python bar_patterns.py scan SPY --lookback 5
	{
		"symbol": "SPY",
		"patterns_detected": [
			{
				"pattern": "outside_day",
				"date": "2026-02-27",
				"direction": "bullish",
				"entry_price": 520.50,
				"stop_price": 515.20,
				"electronic_era_caveat": false,
				"historical_accuracy": 0.85,
				"strength": "high",
				"confirmation_needed": "next_bar_open_buy"
			}
		],
		"pattern_count": 1,
		"scan_window_days": 5
	}

Use Cases:
	- Identify short-term reversal setups for entry timing
	- Filter patterns by strength and electronic-era validity
	- Combine with TDW/TDM bias for higher-probability trades
	- Flag Oops! patterns that may be unreliable in electronic markets

Notes:
	- Outside Day: ~85% accuracy (S&P 109 trades, 1982-1998). 90% accuracy
	  with TDW filter excluding Thursday (Bonds, 41 trades). $420/trade average.
	- Smash Day: ~76% accuracy (S&P 25 trades). Bond Thursday->Friday sells:
	  28 trades, 89% accuracy, $13,303 profit. Best as trend continuation entry.
	- Hidden Smash Day: ~89% accuracy (T-Bonds 28 trades). Higher accuracy than
	  regular smash because the trap is more subtle. Lower 25% threshold is key
	  discriminator.
	- Specialists' Trap: ~80% accuracy. Derived from Wyckoff (1930s). False
	  breakout from 5-10 day box, reversal within 1-3 days.
	- Oops!: ~82% accuracy in pit era. Greatly diminished in electronic era
	  (reduced gap dynamics). Retains value on Sunday opens and post-news events.
	- Electronic Era Status: Outside Day, Smash Day, Hidden Smash, Specialists'
	  Trap all remain valid. Oops! greatly diminished.

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
	"outside_day": {"accuracy": 0.85, "source": "S&P 109 trades (1982-1998)"},
	"smash_day": {"accuracy": 0.76, "source": "S&P 25 trades"},
	"hidden_smash_day": {"accuracy": 0.89, "source": "T-Bonds 28 trades"},
	"specialists_trap": {"accuracy": 0.80, "source": "estimated from book examples"},
	"oops": {"accuracy": 0.82, "source": "S&P 98 trades (diminished in electronic era)"},
}

# ── Pattern detection functions ────────────────────────────────────────────


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
	"""Smash Day (Naked): close below prior bar's low -> buy above next bar's high."""
	if idx < 1:
		return None
	curr = df.iloc[idx]
	prev = df.iloc[idx - 1]
	if curr["Close"] < prev["Low"]:
		return {
			"pattern": "smash_day",
			"date": df.index[idx].strftime("%Y-%m-%d"),
			"direction": "bullish",
			"entry_price": round(float(curr["High"]), 2),
			"stop_price": round(float(curr["Low"]), 2),
			"electronic_era_caveat": False,
			"historical_accuracy": PATTERN_ACCURACY["smash_day"]["accuracy"],
			"strength": "low",
			"confirmation_needed": "next_bar_above_high",
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
	"""Specialists' Trap: 5-10 day box, fake breakout, reversal within 1-3 days."""
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
		return {
			"pattern": "specialists_trap",
			"date": df.index[idx].strftime("%Y-%m-%d"),
			"direction": "bullish",
			"entry_price": round(float(box_high), 2),
			"stop_price": round(float(curr["Low"]), 2),
			"electronic_era_caveat": False,
			"historical_accuracy": PATTERN_ACCURACY["specialists_trap"]["accuracy"],
			"strength": "medium",
			"confirmation_needed": "price_above_box_high",
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


# ── All detectors in execution order ──────────────────────────────────────

_DETECTORS = [
	_detect_outside_day,
	_detect_smash_day,
	_detect_hidden_smash_day,
	_detect_specialists_trap,
	_detect_oops,
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

	output_json({
		"symbol": symbol,
		"patterns_detected": patterns_detected,
		"pattern_count": len(patterns_detected),
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
