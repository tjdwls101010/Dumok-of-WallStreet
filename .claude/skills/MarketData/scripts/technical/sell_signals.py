#!/usr/bin/env python3
"""Sell Signal Detection: technical warning signals for position management.

Detects six core sell signals that indicate deteriorating price action in a
stock. Signals range from early warnings (MA breach) to high-conviction
reversal patterns (key reversal, high-volume reversal). When multiple signals
cluster, probability of further downside increases significantly.

Persona-neutral module — reusable by any pipeline or analysis workflow.

Commands:
	check: Scan all 6 sell signals for a single stock
	audit: Disposition effect audit for a held position with entry price

Args:
	symbol (str): Ticker symbol (e.g., "AAPL", "NVDA", "META")
	--entry-price (float): Position entry price (audit command only)

Returns:
	For check:
	dict: {
		"symbol": str,
		"active_sell_signals": list[str],
		"signal_count": int,
		"severity": str,
		"signals": {
			"MA_BREACH_21EMA": {
				"active": bool,
				"days_below": int,
				"distance_pct": float
			},
			"MA_BREACH_50SMA": {
				"active": bool,
				"distance_pct": float
			},
			"HIGH_VOL_REVERSAL": {
				"active": bool,
				"date": str or null,
				"volume_ratio": float,
				"closing_range": float
			},
			"VERTICAL_ACCELERATION": {
				"active": bool,
				"extension_pct": float,
				"range_expanding": bool,
				"weeks_of_advance": int
			},
			"KEY_REVERSAL": {
				"active": bool,
				"criteria_met": int,
				"required": 4,
				"date": str or null
			},
			"DISTRIBUTION_CLUSTER": {
				"active": bool,
				"dist_days_25d": int
			}
		}
	}

	For audit:
	dict: {
		...all check fields...,
		"entry_price": float,
		"current_price": float,
		"gain_loss_pct": float,
		"disposition_effect_level": str
	}

Example:
	>>> python sell_signals.py check NVDA
	{
		"symbol": "NVDA",
		"active_sell_signals": ["MA_BREACH_21EMA"],
		"signal_count": 1,
		"severity": "caution",
		"signals": {
			"MA_BREACH_21EMA": {"active": true, "days_below": 2, "distance_pct": -1.3},
			"MA_BREACH_50SMA": {"active": false, "distance_pct": 5.2},
			"HIGH_VOL_REVERSAL": {"active": false},
			"VERTICAL_ACCELERATION": {"active": false, "extension_pct": 12.5, "range_expanding": false, "weeks_of_advance": 3},
			"KEY_REVERSAL": {"active": false, "criteria_met": 2, "required": 4},
			"DISTRIBUTION_CLUSTER": {"active": false, "dist_days_25d": 2}
		}
	}

	>>> python sell_signals.py audit NVDA --entry-price 140.0
	{
		"symbol": "NVDA",
		"active_sell_signals": ["MA_BREACH_21EMA"],
		"signal_count": 1,
		"severity": "caution",
		"entry_price": 140.0,
		"current_price": 138.5,
		"gain_loss_pct": -1.07,
		"disposition_effect_level": "caution"
	}

Use Cases:
	- Monitor held positions for deteriorating technicals
	- Detect early warning signs before a breakdown accelerates
	- Audit disposition effect bias — are you holding losers too long?
	- Screen for clustering sell signals that indicate high-probability downside
	- Combine with volume edge or breakout analysis for full trade lifecycle

Notes:
	- MA_BREACH_21EMA: 2+ consecutive closes below 21 EMA = short-term trend loss
	- MA_BREACH_50SMA: Close below 50 SMA = intermediate trend loss
	- HIGH_VOL_REVERSAL: Heavy volume + weak close + close below prior low
	- VERTICAL_ACCELERATION: Overextended advance ripe for mean reversion
	- KEY_REVERSAL: Multi-criteria reversal day (4+ of 6 criteria met)
	- DISTRIBUTION_CLUSTER: 4+ distribution days in 25 sessions = institutional selling
	- Severity levels: healthy (0), caution (1), warning (2), critical (3+)
	- Disposition effect: tendency to hold losers and sell winners too early
	- All calculations use yfinance daily data with 1-year history

See Also:
	- volume_edge.py: Institutional volume events for breakout confirmation
	- volume_analysis.py: Accumulation/distribution grading
	- closing_range.py: Bar quality classification
	- stage_analysis.py: Trend stage identification
"""

import argparse
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import yfinance as yf
from utils import output_json, safe_run


def _ma_breach_21ema(data):
	"""Detect consecutive closes below the 21 EMA.

	Active if 2+ consecutive closes below 21 EMA in the last 5 days.
	"""
	close = data["Close"]
	if len(close) < 21:
		return {"active": False, "days_below": 0, "distance_pct": 0.0}

	ema21 = close.ewm(span=21, adjust=False).mean()
	last5_close = close.iloc[-5:]
	last5_ema = ema21.iloc[-5:]

	# Count consecutive closes below EMA from most recent bar backwards
	days_below = 0
	for i in range(len(last5_close) - 1, -1, -1):
		if float(last5_close.iloc[i]) < float(last5_ema.iloc[i]):
			days_below += 1
		else:
			break

	latest_close = float(close.iloc[-1])
	latest_ema = float(ema21.iloc[-1])
	distance_pct = round((latest_close - latest_ema) / latest_ema * 100, 2) if latest_ema != 0 else 0.0

	return {
		"active": days_below >= 2,
		"days_below": days_below,
		"distance_pct": distance_pct,
	}


def _ma_breach_50sma(data):
	"""Detect close below the 50 SMA.

	Active if latest close is below 50 SMA.
	"""
	close = data["Close"]
	if len(close) < 50:
		return {"active": False, "distance_pct": 0.0}

	sma50 = close.rolling(50).mean()
	latest_close = float(close.iloc[-1])
	latest_sma = float(sma50.iloc[-1])
	distance_pct = round((latest_close - latest_sma) / latest_sma * 100, 2) if latest_sma != 0 else 0.0

	return {
		"active": latest_close < latest_sma,
		"distance_pct": distance_pct,
	}


def _high_vol_reversal(data):
	"""Detect high-volume reversal bars.

	Checks last 3 bars for: volume > 1.5x 50-day avg AND
	closing range < 30% AND close < prior day's low.
	"""
	if len(data) < 51:
		return {"active": False, "date": None, "volume_ratio": 0.0, "closing_range": 0.0}

	volumes = data["Volume"]
	high = data["High"]
	low = data["Low"]
	close = data["Close"]

	avg_vol_50 = float(volumes.iloc[-51:-1].mean())

	for i in range(-1, -4, -1):
		idx = len(data) + i
		if idx < 1:
			continue

		v = float(volumes.iloc[idx])
		h = float(high.iloc[idx])
		l = float(low.iloc[idx])
		c = float(close.iloc[idx])
		prior_low = float(low.iloc[idx - 1])

		vol_ratio = round(v / avg_vol_50, 2) if avg_vol_50 > 0 else 0.0
		cr = round((c - l) / (h - l) * 100, 1) if h != l else 50.0

		if vol_ratio > 1.5 and cr < 30.0 and c < prior_low:
			return {
				"active": True,
				"date": str(data.index[idx].date()),
				"volume_ratio": vol_ratio,
				"closing_range": cr,
			}

	return {"active": False, "date": None, "volume_ratio": 0.0, "closing_range": 0.0}


def _vertical_acceleration(data):
	"""Detect overextended vertical advance.

	Active if: extension from 21 EMA > 25% AND daily ranges expanding
	(5-day ADR avg > 1.3x 60-day ADR avg) AND 8+ weeks of advance
	(~40 trading days since price was at or below 21 EMA).
	"""
	close = data["Close"]
	high = data["High"]
	low = data["Low"]

	if len(data) < 60:
		return {
			"active": False,
			"extension_pct": 0.0,
			"range_expanding": False,
			"weeks_of_advance": 0,
		}

	ema21 = close.ewm(span=21, adjust=False).mean()
	latest_close = float(close.iloc[-1])
	latest_ema = float(ema21.iloc[-1])

	# Extension from 21 EMA
	extension_pct = round((latest_close - latest_ema) / latest_ema * 100, 2) if latest_ema != 0 else 0.0

	# ADR: (High - Low) / Close * 100
	adr = ((high - low) / close * 100).astype(float)
	adr_5d = float(adr.iloc[-5:].mean())
	adr_60d = float(adr.iloc[-60:].mean())
	range_expanding = adr_5d > 1.3 * adr_60d if adr_60d > 0 else False

	# Count trading days since price was last at or below 21 EMA
	days_since_ema = 0
	for i in range(len(close) - 1, -1, -1):
		if float(close.iloc[i]) <= float(ema21.iloc[i]):
			break
		days_since_ema += 1

	weeks_of_advance = days_since_ema // 5

	return {
		"active": extension_pct > 25.0 and range_expanding and weeks_of_advance >= 8,
		"extension_pct": extension_pct,
		"range_expanding": bool(range_expanding),
		"weeks_of_advance": weeks_of_advance,
	}


def _key_reversal(data):
	"""Detect key reversal day meeting 4+ of 6 criteria.

	Criteria:
	  a) Extension from 21 EMA > 15%
	  b) Gap up that fills (open > prior close by 1%+ and close < open)
	  c) Close below prior day's low
	  d) Volume > 1.5x 50-day avg
	  e) Widest daily range in last 20 bars
	  f) Closing range < 30%
	"""
	if len(data) < 51:
		return {"active": False, "criteria_met": 0, "required": 4, "date": None}

	close = data["Close"]
	high = data["High"]
	low = data["Low"]
	opn = data["Open"]
	volumes = data["Volume"]

	ema21 = close.ewm(span=21, adjust=False).mean()
	avg_vol_50 = float(volumes.iloc[-51:-1].mean())

	best_criteria = 0
	best_date = None

	for i in range(-1, -4, -1):
		idx = len(data) + i
		if idx < 20:
			continue

		c = float(close.iloc[idx])
		h = float(high.iloc[idx])
		l = float(low.iloc[idx])
		o = float(opn.iloc[idx])
		v = float(volumes.iloc[idx])
		ema_val = float(ema21.iloc[idx])
		prior_close = float(close.iloc[idx - 1])
		prior_low = float(low.iloc[idx - 1])

		criteria = 0

		# a) Extension from 21 EMA > 15%
		ext = (c - ema_val) / ema_val * 100 if ema_val != 0 else 0
		if ext > 15:
			criteria += 1

		# b) Gap up that fills: open > prior close by 1%+ and close < open
		gap_pct = (o - prior_close) / prior_close * 100 if prior_close != 0 else 0
		if gap_pct > 1.0 and c < o:
			criteria += 1

		# c) Close below prior day's low
		if c < prior_low:
			criteria += 1

		# d) Volume > 1.5x 50-day avg
		vol_ratio = v / avg_vol_50 if avg_vol_50 > 0 else 0
		if vol_ratio > 1.5:
			criteria += 1

		# e) Widest daily range in last 20 bars
		current_range = h - l
		prior_ranges = (high.iloc[idx - 19:idx] - low.iloc[idx - 19:idx]).astype(float)
		if current_range > float(prior_ranges.max()):
			criteria += 1

		# f) Closing range < 30%
		cr = (c - l) / (h - l) * 100 if h != l else 50.0
		if cr < 30:
			criteria += 1

		if criteria > best_criteria:
			best_criteria = criteria
			best_date = str(data.index[idx].date())

	return {
		"active": best_criteria >= 4,
		"criteria_met": best_criteria,
		"required": 4,
		"date": best_date if best_criteria >= 4 else None,
	}


def _distribution_cluster(data):
	"""Detect distribution day cluster.

	A distribution day = close < prior close with volume above 50-day average.
	Active if 4+ distribution days in the last 25 trading days.
	"""
	if len(data) < 51:
		return {"active": False, "dist_days_25d": 0}

	close = data["Close"]
	volumes = data["Volume"]

	# Use the 50-day avg volume ending before the 25-day window
	avg_vol_50 = float(volumes.iloc[-76:-26].mean()) if len(data) >= 76 else float(volumes.iloc[:-26].mean()) if len(data) > 26 else float(volumes.mean())

	window = data.iloc[-25:]
	dist_days = 0

	for i in range(1, len(window)):
		c = float(window["Close"].iloc[i])
		prev_c = float(window["Close"].iloc[i - 1])
		v = float(window["Volume"].iloc[i])

		if c < prev_c and v > avg_vol_50:
			dist_days += 1

	return {
		"active": dist_days >= 4,
		"dist_days_25d": dist_days,
	}


def _severity(signal_count):
	"""Determine severity level from active signal count."""
	if signal_count == 0:
		return "healthy"
	if signal_count == 1:
		return "caution"
	if signal_count == 2:
		return "warning"
	return "critical"


def _disposition_effect_level(signal_count, gain_loss_pct):
	"""Determine disposition effect level for held positions."""
	profitable = gain_loss_pct >= 0

	if signal_count >= 3 and not profitable:
		return "critical"
	if signal_count >= 3 or (not profitable and signal_count >= 2):
		return "warning"
	if signal_count >= 2 or (not profitable and signal_count >= 1):
		return "caution"
	return "healthy"


def _run_all_signals(data):
	"""Run all 6 sell signals and return structured results."""
	sig_21ema = _ma_breach_21ema(data)
	sig_50sma = _ma_breach_50sma(data)
	sig_hvr = _high_vol_reversal(data)
	sig_vert = _vertical_acceleration(data)
	sig_key = _key_reversal(data)
	sig_dist = _distribution_cluster(data)

	signals = {
		"MA_BREACH_21EMA": sig_21ema,
		"MA_BREACH_50SMA": sig_50sma,
		"HIGH_VOL_REVERSAL": sig_hvr,
		"VERTICAL_ACCELERATION": sig_vert,
		"KEY_REVERSAL": sig_key,
		"DISTRIBUTION_CLUSTER": sig_dist,
	}

	active = [name for name, sig in signals.items() if sig.get("active")]
	return signals, active


@safe_run
def cmd_check(args):
	"""Scan all 6 sell signals for a single stock."""
	symbol = args.symbol.upper()
	ticker = yf.Ticker(symbol)
	data = ticker.history(period="1y")

	if data.empty or len(data) < 50:
		output_json({
			"error": f"Insufficient data for {symbol}. Need at least 50 trading days.",
			"data_points": len(data),
		})
		return

	signals, active = _run_all_signals(data)

	output_json({
		"symbol": symbol,
		"active_sell_signals": active,
		"signal_count": len(active),
		"severity": _severity(len(active)),
		"signals": signals,
	})


@safe_run
def cmd_audit(args):
	"""Disposition effect audit for a held position with entry price."""
	symbol = args.symbol.upper()
	entry_price = args.entry_price
	ticker = yf.Ticker(symbol)
	data = ticker.history(period="1y")

	if data.empty or len(data) < 50:
		output_json({
			"error": f"Insufficient data for {symbol}. Need at least 50 trading days.",
			"data_points": len(data),
		})
		return

	signals, active = _run_all_signals(data)
	current_price = round(float(data["Close"].iloc[-1]), 2)
	gain_loss_pct = round((current_price - entry_price) / entry_price * 100, 2) if entry_price != 0 else 0.0

	output_json({
		"symbol": symbol,
		"active_sell_signals": active,
		"signal_count": len(active),
		"severity": _severity(len(active)),
		"signals": signals,
		"entry_price": entry_price,
		"current_price": current_price,
		"gain_loss_pct": gain_loss_pct,
		"disposition_effect_level": _disposition_effect_level(len(active), gain_loss_pct),
	})


def main():
	parser = argparse.ArgumentParser(
		description="Sell Signal Detection: technical warning signals"
	)
	sub = parser.add_subparsers(dest="command", required=True)

	# check
	sp = sub.add_parser("check", help="Scan all 6 sell signals for a stock")
	sp.add_argument("symbol", help="Ticker symbol")
	sp.set_defaults(func=cmd_check)

	# audit
	sp = sub.add_parser("audit", help="Disposition effect audit with entry price")
	sp.add_argument("symbol", help="Ticker symbol")
	sp.add_argument(
		"--entry-price", type=float, required=True,
		help="Position entry price",
	)
	sp.set_defaults(func=cmd_audit)

	args = parser.parse_args()
	args.func(args)


if __name__ == "__main__":
	main()
