#!/usr/bin/env python3
"""Larry Williams short-term trading tools: Williams %R, volatility breakout levels,
range analysis, swing point identification, pattern scanning, Greatest Swing Value
analysis, and TDW/TDM calendar bias.

Implements core analysis tools from Larry Williams' "Long-Term Secrets to Short-Term
Trading" (2011 edition). All indicators are persona-neutral — interpretation context
is provided by the Williams command and persona files.

Commands:
	williams-r: Williams %R momentum oscillator (0 to -100 scale)
	volatility-breakout: ATR-based breakout entry/exit levels
	range-analysis: Range expansion/contraction phase detection
	swing-points: Mechanical swing point identification (3 hierarchy levels)
	pattern-scan: 5 Williams chart pattern detection
	gsv: Greatest Swing Value failure swing measurement
	tdw-tdm: Today's Trading Day of Week / Trading Day of Month bias

Args:
	For williams-r:
		symbol (str): Ticker symbol (e.g., "AAPL", "SPY")
		--period (int): Lookback period (default: 14)
		--history (int): Number of historical values to return (default: 10)

	For volatility-breakout:
		symbol (str): Ticker symbol (e.g., "AAPL", "SPY")
		--atr-period (int): ATR calculation period (default: 3)
		--pct (float): Breakout percentage multiplier (default: 0.6)

	For range-analysis:
		symbol (str): Ticker symbol (e.g., "AAPL", "SPY")
		--lookback (int): Analysis window in days (default: 20)

	For swing-points:
		symbol (str): Ticker symbol (e.g., "AAPL", "SPY")
		--level (str): Hierarchy level: "short", "intermediate", "long" (default: "short")

	For pattern-scan:
		symbol (str): Ticker symbol (e.g., "AAPL", "SPY")
		--lookback (int): Days to scan for patterns (default: 5)

	For gsv:
		symbol (str): Ticker symbol (e.g., "AAPL", "SPY")

	For tdw-tdm:
		(no arguments — returns today's bias)

Returns:
	For williams-r:
		dict: {
			"symbol": str,
			"current_wr": float,              # Current Williams %R (-100 to 0)
			"signal": str,                     # "overbought" (>-20), "oversold" (<-80), "neutral"
			"period": int,
			"wr_history": dict,                # Recent values {date: wr_value}
			"statistics": {
				"mean": float,
				"std": float,
				"pct_time_overbought": float,
				"pct_time_oversold": float
			}
		}

	For volatility-breakout:
		dict: {
			"symbol": str,
			"date": str,
			"open": float,
			"previous_close": float,
			"atr_3day": float,                 # 3-day ATR value
			"classic_buy_level": float,        # Open + pct × ATR
			"classic_sell_level": float,        # Open - pct × ATR
			"electronic_buy_level": float,      # Low + 20% of 3d ATR (after down close)
			"electronic_sell_level": float,     # High - 20% of 3d ATR (after up close)
			"yesterday_close_direction": str,   # "up" or "down"
			"active_signal": str,               # Which formula is active today
			"current_price": float,
			"breakout_triggered": bool
		}

	For range-analysis:
		dict: {
			"symbol": str,
			"current_range_pct": float,        # Today's range as % of close
			"avg_range_pct": float,            # Average range over lookback
			"range_ratio": float,              # Current / Average
			"phase": str,                      # "contraction", "expansion", "neutral"
			"consecutive_small_ranges": int,   # Count of below-avg ranges in a row
			"consecutive_large_ranges": int,
			"axiom_signal": str,               # "expansion_imminent", "contraction_imminent", "neutral"
			"range_history": [{"date": str, "range_pct": float, "phase": str}],
			"close_position": {
				"buying_power": float,         # Close - Low (Williams Buying Power)
				"selling_pressure": float,     # High - Close (Williams Selling Pressure)
				"close_pct": float,            # Close position within range (0-100%)
				"recent_bias": str,            # "buying_dominant", "selling_dominant", "neutral"
				"consecutive_upper_closes": int,
				"consecutive_lower_closes": int
			}
		}

	For swing-points:
		dict: {
			"symbol": str,
			"level": str,
			"swing_highs": [{"date": str, "price": float, "index": int}],
			"swing_lows": [{"date": str, "price": float, "index": int}],
			"current_trend": str,              # "up", "down", "neutral"
			"last_swing_high": {"date": str, "price": float},
			"last_swing_low": {"date": str, "price": float},
			"projected_target": float,          # Intermediate High + (High - Low)
			"current_price": float
		}

	For pattern-scan:
		dict: {
			"symbol": str,
			"patterns_detected": [{
				"pattern": str,                # Pattern name
				"date": str,                   # Detection date
				"direction": str,              # "bullish" or "bearish"
				"entry_price": float,          # Suggested entry
				"stop_price": float,           # Suggested stop
				"electronic_era_caveat": bool, # True for Oops! pattern
				"historical_accuracy": float,  # Backtested accuracy (0-1)
				"strength": str,               # "high", "medium", or "low"
				"confirmation_needed": str     # Required confirmation type
			}],
			"pattern_count": int,
			"scan_window_days": int
		}

	For gsv:
		dict: {
			"symbol": str,
			"avg_buy_swing": float,            # Average buy swing (High - Open on down days)
			"avg_sell_swing": float,            # Average sell swing (Open - Low on up days)
			"buy_entry_level": float,           # Open - (avg_sell_swing × 1.80)
			"buy_stop_level": float,            # Open - (avg_sell_swing × 2.25)
			"sell_entry_level": float,           # Open + (avg_buy_swing × 1.80)
			"sell_stop_level": float,            # Open + (avg_buy_swing × 2.25)
			"swing_period_days": int,            # Number of recent swings used (4)
			"recent_gsv_exceeded": bool,         # True if 225% threshold exceeded recently
			"swing_history": [{"date": str, "type": str, "value": float}]
		}

	For tdw-tdm:
		dict: {
			"date": str,
			"day_of_week": str,
			"trading_day_of_week": int,        # 1=Mon to 5=Fri
			"trading_day_of_month": int,        # 1-based TDM
			"tdw_bias": str,                   # "bullish", "bearish", "neutral"
			"tdm_bias": str,                   # "bullish", "bearish", "neutral"
			"tdw_note": str,                   # Historical context
			"tdm_note": str,                   # Historical context
			"combined_bias": str               # Overall bias assessment
		}

Example:
	>>> python technical/williams.py williams-r AAPL --period 14
	{
		"symbol": "AAPL",
		"current_wr": -35.2,
		"signal": "neutral",
		"period": 14,
		"statistics": {"mean": -48.5, "std": 22.3}
	}

	>>> python technical/williams.py volatility-breakout SPY --atr-period 3
	{
		"symbol": "SPY",
		"open": 475.50,
		"atr_3day": 8.25,
		"classic_buy_level": 480.45,
		"breakout_triggered": false
	}

	>>> python technical/williams.py pattern-scan AAPL --lookback 5
	{
		"symbol": "AAPL",
		"patterns_detected": [
			{"pattern": "smash_day", "direction": "bullish", "entry_price": 178.50,
			 "historical_accuracy": 0.76, "strength": "medium"}
		],
		"pattern_count": 1
	}

	>>> python technical/williams.py gsv AAPL
	{
		"symbol": "AAPL",
		"avg_buy_swing": 2.15,
		"avg_sell_swing": 1.85,
		"buy_entry_level": 172.17,
		"sell_entry_level": 179.37
	}

	>>> python technical/williams.py tdw-tdm
	{
		"date": "2026-02-25",
		"day_of_week": "Wednesday",
		"tdw_bias": "neutral",
		"tdm_bias": "bullish",
		"combined_bias": "slightly_bullish"
	}

Use Cases:
	- Short-term (2-5 day) trade qualification using Williams' mechanical framework
	- Volatility breakout entry level calculation for intraday/swing setups
	- Pattern detection for 5 Williams-specific chart patterns
	- TDW/TDM calendar bias assessment for timing confirmation
	- Greatest Swing Value failure swing analysis for entry/stop level calculation

Notes:
	- Williams %R scale: 0 to -100 (0 = overbought, -100 = oversold)
	- Volatility breakout uses 3-day ATR (not standard 14-day) per Williams' preference
	- Electronic era adaptations applied to classic formulas where Williams specified
	- Oops! pattern flagged with electronic_era_caveat (Williams noted reduced reliability)
	- TDW/TDM biases based on 2011 edition historical statistics (S&P 500 focused)
	- Bond data uses TLT ETF as Treasury Bond proxy (yfinance accessible)
	- Position sizing uses Williams' formula: Contracts = (Balance × Risk%) / MaxLoss

See Also:
	- oscillators.py: RSI and MACD for complementary momentum analysis
	- trend.py: SMA/EMA for moving average trend confirmation
	- price.py: Historical OHLCV data retrieval
"""

import argparse
import datetime
import os
import sys

import numpy as np
import pandas as pd
import yfinance as yf

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from utils import output_json, safe_run


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fetch_ohlcv(symbol, period="1y", interval="1d"):
	"""Fetch OHLCV data via yfinance, return DataFrame."""
	ticker = yf.Ticker(symbol)
	df = ticker.history(period=period, interval=interval)
	if df.empty:
		raise ValueError(f"No data returned for {symbol}")
	return df


def _atr(df, period=3):
	"""Calculate Average True Range over given period."""
	high = df["High"]
	low = df["Low"]
	prev_close = df["Close"].shift(1)
	tr = pd.concat([
		high - low,
		(high - prev_close).abs(),
		(low - prev_close).abs(),
	], axis=1).max(axis=1)
	return tr.rolling(period).mean()


def _williams_pct_r(df, period=14):
	"""Calculate Williams %R for the dataframe."""
	highest_high = df["High"].rolling(period).max()
	lowest_low = df["Low"].rolling(period).min()
	wr = -100 * (highest_high - df["Close"]) / (highest_high - lowest_low)
	return wr


# ---------------------------------------------------------------------------
# TDW / TDM reference tables (from Williams 2011 edition, S&P 500 focus)
# ---------------------------------------------------------------------------

# TDW bias: 1=Monday, 2=Tuesday, ..., 5=Friday
TDW_BIAS = {
	1: {"bias": "bullish", "note": "Monday historically bullish for S&P; strong open tendency"},
	2: {"bias": "bullish", "note": "Tuesday continues Monday momentum; second strongest day"},
	3: {"bias": "neutral", "note": "Wednesday mixed; mid-week consolidation typical"},
	4: {"bias": "bearish", "note": "Thursday historically weakest day; profit-taking common"},
	5: {"bias": "neutral", "note": "Friday mixed; position squaring before weekend"},
}

# TDM bias: day-of-month ranges
# Month start (1-3) and month end (25-31): bullish
# Mid-month (10-18): bearish
# Other: neutral
def _tdm_bias(day):
	"""Return TDM bias based on trading day of month."""
	if day <= 3:
		return {"bias": "bullish", "note": "Month-start effect: institutional inflows, fund deployment"}
	elif day >= 25:
		return {"bias": "bullish", "note": "Month-end effect: window dressing, fund inflows"}
	elif 10 <= day <= 18:
		return {"bias": "bearish", "note": "Mid-month weakness: tax payments, low institutional activity"}
	else:
		return {"bias": "neutral", "note": "Transition zone; no strong historical bias"}


def _combine_bias(tdw_bias, tdm_bias):
	"""Combine TDW and TDM biases into overall assessment."""
	score = 0
	if tdw_bias == "bullish":
		score += 1
	elif tdw_bias == "bearish":
		score -= 1
	if tdm_bias == "bullish":
		score += 1
	elif tdm_bias == "bearish":
		score -= 1

	if score >= 2:
		return "bullish"
	elif score == 1:
		return "slightly_bullish"
	elif score == -1:
		return "slightly_bearish"
	elif score <= -2:
		return "bearish"
	return "neutral"


# Pattern accuracy constants (Williams.db backtested data)
PATTERN_ACCURACY = {
	"outside_day": {"accuracy": 0.85, "source": "S&P 109 trades (1982-1998)"},
	"smash_day": {"accuracy": 0.76, "source": "S&P 25 trades"},
	"hidden_smash_day": {"accuracy": 0.89, "source": "T-Bonds 28 trades"},
	"specialists_trap": {"accuracy": 0.80, "source": "estimated from book examples"},
	"oops": {"accuracy": 0.82, "source": "S&P 98 trades (diminished in electronic era)"},
}


# ---------------------------------------------------------------------------
# Swing Point Detection
# ---------------------------------------------------------------------------

def _find_swing_points(df, n=1):
	"""Find swing highs and lows.

	Short-term: n=1 (1 bar each side)
	Intermediate: n=3 (3 bars each side)
	Long-term: n=5 (5 bars each side)
	"""
	highs = []
	lows = []
	for i in range(n, len(df) - n):
		# Swing high: higher than n bars on each side
		is_high = True
		is_low = True
		for j in range(1, n + 1):
			if df["High"].iloc[i] <= df["High"].iloc[i - j] or df["High"].iloc[i] <= df["High"].iloc[i + j]:
				is_high = False
			if df["Low"].iloc[i] >= df["Low"].iloc[i - j] or df["Low"].iloc[i] >= df["Low"].iloc[i + j]:
				is_low = False
		if is_high:
			highs.append({
				"date": df.index[i].strftime("%Y-%m-%d"),
				"price": round(float(df["High"].iloc[i]), 2),
				"index": i,
			})
		if is_low:
			lows.append({
				"date": df.index[i].strftime("%Y-%m-%d"),
				"price": round(float(df["Low"].iloc[i]), 2),
				"index": i,
			})
	return highs, lows


# ---------------------------------------------------------------------------
# Pattern Detection
# ---------------------------------------------------------------------------

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
			# Bearish outside day → next day buy signal (reversal)
			return {
				"pattern": "outside_day",
				"date": df.index[idx].strftime("%Y-%m-%d"),
				"direction": "bullish",
				"entry_price": round(float(curr["Open"]), 2),  # Buy at next open
				"stop_price": round(float(curr["Low"]), 2),
				"electronic_era_caveat": False,
				"historical_accuracy": PATTERN_ACCURACY["outside_day"]["accuracy"],
				"strength": "high",
				"confirmation_needed": "next_bar_open_buy",
			}
	return None


def _detect_smash_day(df, idx):
	"""Smash Day (Naked): close below prior bar's low → buy above next bar's high."""
	if idx < 1:
		return None
	curr = df.iloc[idx]
	prev = df.iloc[idx - 1]
	if curr["Close"] < prev["Low"]:
		return {
			"pattern": "smash_day",
			"date": df.index[idx].strftime("%Y-%m-%d"),
			"direction": "bullish",
			"entry_price": round(float(curr["High"]), 2),  # Buy above today's high
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
			"entry_price": round(float(curr["High"]), 2),  # Buy above today's high
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

	# Check for tight box (range < 5% of close)
	avg_close = window["Close"].mean()
	if avg_close <= 0 or box_range / avg_close > 0.05:
		return None

	curr = df.iloc[idx]
	# Check if today broke below box and recovered (bull trap reversal)
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
	# Gap down: open below prior low
	if curr["Open"] < prev["Low"]:
		# Recovered to prior low
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


# ---------------------------------------------------------------------------
# Command implementations
# ---------------------------------------------------------------------------

@safe_run
def cmd_williams_r(args):
	"""Williams %R momentum oscillator."""
	symbol = args.symbol.upper()
	df = _fetch_ohlcv(symbol, period="1y")

	wr = _williams_pct_r(df, period=args.period)
	wr_clean = wr.dropna()

	if wr_clean.empty:
		raise ValueError(f"Insufficient data to calculate Williams %R for {symbol}")

	current_wr = round(float(wr_clean.iloc[-1]), 2)

	# Signal
	if current_wr > -20:
		signal = "overbought"
	elif current_wr < -80:
		signal = "oversold"
	else:
		signal = "neutral"

	# History
	history_count = min(args.history, len(wr_clean))
	wr_history = {}
	for i in range(-history_count, 0):
		date_str = wr_clean.index[i].strftime("%Y-%m-%d")
		wr_history[date_str] = round(float(wr_clean.iloc[i]), 2)

	# Statistics
	mean_wr = round(float(wr_clean.mean()), 2)
	std_wr = round(float(wr_clean.std()), 2)
	pct_overbought = round(float((wr_clean > -20).sum() / len(wr_clean) * 100), 1)
	pct_oversold = round(float((wr_clean < -80).sum() / len(wr_clean) * 100), 1)

	output_json({
		"symbol": symbol,
		"current_wr": current_wr,
		"signal": signal,
		"period": args.period,
		"wr_history": wr_history,
		"statistics": {
			"mean": mean_wr,
			"std": std_wr,
			"pct_time_overbought": pct_overbought,
			"pct_time_oversold": pct_oversold,
		},
	})


@safe_run
def cmd_volatility_breakout(args):
	"""ATR-based volatility breakout entry/exit levels."""
	symbol = args.symbol.upper()
	df = _fetch_ohlcv(symbol, period="3mo")

	if len(df) < args.atr_period + 2:
		raise ValueError(f"Insufficient data for ATR calculation ({len(df)} bars)")

	atr_series = _atr(df, period=args.atr_period)
	atr_val = float(atr_series.iloc[-1])
	today = df.iloc[-1]
	yesterday = df.iloc[-2]

	open_price = float(today["Open"])
	current_price = float(today["Close"])
	prev_close = float(yesterday["Close"])

	# Classic Williams formula
	classic_buy = round(open_price + args.pct * atr_val, 2)
	classic_sell = round(open_price - args.pct * atr_val, 2)

	# Electronic era adaptations
	yesterday_direction = "down" if yesterday["Close"] < yesterday["Open"] else "up"

	if yesterday_direction == "down":
		# After down close: Low + 20% of 3-day ATR
		electronic_buy = round(float(today["Low"]) + 0.20 * atr_val, 2)
		electronic_sell = round(float(today["High"]) - 0.60 * atr_val, 2)
		active_signal = "electronic_down_close"
	else:
		# After up close: Open + 60% of 3-day ATR
		electronic_buy = round(open_price + 0.60 * atr_val, 2)
		electronic_sell = round(open_price - 0.60 * atr_val, 2)
		active_signal = "electronic_up_close"

	# Check if breakout triggered
	breakout_triggered = current_price >= classic_buy

	output_json({
		"symbol": symbol,
		"date": df.index[-1].strftime("%Y-%m-%d"),
		"open": round(open_price, 2),
		"previous_close": round(prev_close, 2),
		"atr_3day": round(atr_val, 2),
		"classic_buy_level": classic_buy,
		"classic_sell_level": classic_sell,
		"electronic_buy_level": electronic_buy,
		"electronic_sell_level": electronic_sell,
		"yesterday_close_direction": yesterday_direction,
		"active_signal": active_signal,
		"current_price": round(current_price, 2),
		"breakout_triggered": breakout_triggered,
	})


@safe_run
def cmd_range_analysis(args):
	"""Range expansion/contraction phase detection."""
	symbol = args.symbol.upper()
	df = _fetch_ohlcv(symbol, period="6mo")

	if len(df) < args.lookback + 5:
		raise ValueError(f"Insufficient data for range analysis ({len(df)} bars)")

	# Calculate daily range as percentage of close
	df["range_pct"] = (df["High"] - df["Low"]) / df["Close"] * 100

	# Recent window
	recent = df.tail(args.lookback)
	avg_range = float(recent["range_pct"].mean())
	current_range = float(df["range_pct"].iloc[-1])
	range_ratio = round(current_range / avg_range, 2) if avg_range > 0 else 1.0

	# Phase detection
	if range_ratio < 0.7:
		phase = "contraction"
	elif range_ratio > 1.3:
		phase = "expansion"
	else:
		phase = "neutral"

	# Count consecutive small/large ranges
	consecutive_small = 0
	consecutive_large = 0
	for i in range(len(df) - 1, max(len(df) - 20, 0) - 1, -1):
		r = float(df["range_pct"].iloc[i])
		if r < avg_range * 0.7:
			consecutive_small += 1
		else:
			break
	for i in range(len(df) - 1, max(len(df) - 20, 0) - 1, -1):
		r = float(df["range_pct"].iloc[i])
		if r > avg_range * 1.3:
			consecutive_large += 1
		else:
			break

	# Williams axiom signal
	if consecutive_small >= 3:
		axiom_signal = "expansion_imminent"
	elif consecutive_large >= 3:
		axiom_signal = "contraction_imminent"
	else:
		axiom_signal = "neutral"

	# Range history (last 10 bars)
	range_history = []
	for i in range(-min(10, len(recent)), 0):
		row = recent.iloc[i]
		r = float(row["range_pct"])
		p = "contraction" if r < avg_range * 0.7 else ("expansion" if r > avg_range * 1.3 else "neutral")
		range_history.append({
			"date": recent.index[i].strftime("%Y-%m-%d"),
			"range_pct": round(r, 3),
			"phase": p,
		})

	# Close-as-Trend-Indicator (Williams: Buying Power = Close - Low, Selling Pressure = High - Close)
	close = float(df["Close"].iloc[-1])
	high = float(df["High"].iloc[-1])
	low = float(df["Low"].iloc[-1])
	bar_range = high - low
	close_pct = round((close - low) / bar_range * 100, 1) if bar_range > 0 else 50.0
	buying_power = round(close - low, 2)
	selling_pressure = round(high - close, 2)

	# Recent bias: average buying power vs selling pressure over last 5 days
	recent_bp = []
	recent_sp = []
	for i in range(-min(5, len(df)), 0):
		row = df.iloc[i]
		bp = float(row["Close"]) - float(row["Low"])
		sp_val = float(row["High"]) - float(row["Close"])
		recent_bp.append(bp)
		recent_sp.append(sp_val)
	avg_bp = sum(recent_bp) / len(recent_bp)
	avg_sp = sum(recent_sp) / len(recent_sp)
	if avg_bp > avg_sp * 1.2:
		recent_bias = "buying_dominant"
	elif avg_sp > avg_bp * 1.2:
		recent_bias = "selling_dominant"
	else:
		recent_bias = "neutral"

	# Consecutive upper/lower closes
	consecutive_upper = 0
	consecutive_lower = 0
	for i in range(len(df) - 1, max(len(df) - 20, 0) - 1, -1):
		row = df.iloc[i]
		r = float(row["High"]) - float(row["Low"])
		if r > 0:
			cp = (float(row["Close"]) - float(row["Low"])) / r * 100
			if cp >= 65:
				consecutive_upper += 1
			else:
				break
	for i in range(len(df) - 1, max(len(df) - 20, 0) - 1, -1):
		row = df.iloc[i]
		r = float(row["High"]) - float(row["Low"])
		if r > 0:
			cp = (float(row["Close"]) - float(row["Low"])) / r * 100
			if cp <= 35:
				consecutive_lower += 1
			else:
				break

	output_json({
		"symbol": symbol,
		"current_range_pct": round(current_range, 3),
		"avg_range_pct": round(avg_range, 3),
		"range_ratio": range_ratio,
		"phase": phase,
		"consecutive_small_ranges": consecutive_small,
		"consecutive_large_ranges": consecutive_large,
		"axiom_signal": axiom_signal,
		"range_history": range_history,
		"close_position": {
			"buying_power": buying_power,
			"selling_pressure": selling_pressure,
			"close_pct": close_pct,
			"recent_bias": recent_bias,
			"consecutive_upper_closes": consecutive_upper,
			"consecutive_lower_closes": consecutive_lower,
		},
	})


@safe_run
def cmd_swing_points(args):
	"""Mechanical swing point identification (3 hierarchy levels)."""
	symbol = args.symbol.upper()
	df = _fetch_ohlcv(symbol, period="1y")

	level_map = {"short": 1, "intermediate": 3, "long": 5}
	n = level_map.get(args.level, 1)

	if len(df) < n * 2 + 5:
		raise ValueError(f"Insufficient data for swing point detection ({len(df)} bars)")

	highs, lows = _find_swing_points(df, n=n)

	# Current trend based on last swing points
	current_trend = "neutral"
	if highs and lows:
		last_high = highs[-1]
		last_low = lows[-1]
		if last_high["index"] > last_low["index"]:
			current_trend = "up"
		elif last_low["index"] > last_high["index"]:
			current_trend = "down"

	# Projected target (Williams method)
	projected_target = None
	if len(highs) >= 2 and len(lows) >= 1:
		recent_high = highs[-1]["price"]
		prev_high = highs[-2]["price"]
		recent_low = lows[-1]["price"]
		swing_range = recent_high - recent_low
		projected_target = round(recent_high + swing_range, 2)

	current_price = round(float(df["Close"].iloc[-1]), 2)

	# Limit output to last 10 swing points each
	output_json({
		"symbol": symbol,
		"level": args.level,
		"swing_highs": highs[-10:],
		"swing_lows": lows[-10:],
		"current_trend": current_trend,
		"last_swing_high": highs[-1] if highs else None,
		"last_swing_low": lows[-1] if lows else None,
		"projected_target": projected_target,
		"current_price": current_price,
	})


@safe_run
def cmd_pattern_scan(args):
	"""Scan for 5 Williams chart patterns."""
	symbol = args.symbol.upper()
	df = _fetch_ohlcv(symbol, period="3mo")

	if len(df) < 15:
		raise ValueError(f"Insufficient data for pattern scan ({len(df)} bars)")

	patterns = []
	scan_start = max(1, len(df) - args.lookback)

	for idx in range(scan_start, len(df)):
		# Test each pattern
		p = _detect_outside_day(df, idx)
		if p:
			patterns.append(p)
		p = _detect_smash_day(df, idx)
		if p:
			patterns.append(p)
		p = _detect_hidden_smash_day(df, idx)
		if p:
			patterns.append(p)
		p = _detect_specialists_trap(df, idx)
		if p:
			patterns.append(p)
		p = _detect_oops(df, idx)
		if p:
			patterns.append(p)

	output_json({
		"symbol": symbol,
		"patterns_detected": patterns,
		"pattern_count": len(patterns),
		"scan_window_days": args.lookback,
	})


@safe_run
def cmd_gsv(args):
	"""Greatest Swing Value: failure swing measurement.

	Measures the distance price swings against the close direction:
	- Buy Swing: High - Open on down-close days (bulls failed)
	- Sell Swing: Open - Low on up-close days (bears failed)

	Returns average swing values and threshold levels (180%, 225%).
	"""
	symbol = args.symbol.upper()
	df = _fetch_ohlcv(symbol, period="3mo")

	if len(df) < 15:
		raise ValueError(f"Insufficient data for GSV calculation ({len(df)} bars)")

	# Separate buy swings (down-close days) and sell swings (up-close days)
	buy_swings = []  # High - Open on down close days
	sell_swings = []  # Open - Low on up close days

	for i in range(len(df)):
		row = df.iloc[i]
		if row["Close"] < row["Open"]:  # Down close day
			buy_swings.append(float(row["High"] - row["Open"]))
		else:  # Up close day
			sell_swings.append(float(row["Open"] - row["Low"]))

	# Use last 4 valid values for each
	recent_buy_swings = buy_swings[-4:] if len(buy_swings) >= 4 else buy_swings
	recent_sell_swings = sell_swings[-4:] if len(sell_swings) >= 4 else sell_swings

	avg_buy_swing = round(sum(recent_buy_swings) / len(recent_buy_swings), 2) if recent_buy_swings else 0.0
	avg_sell_swing = round(sum(recent_sell_swings) / len(recent_sell_swings), 2) if recent_sell_swings else 0.0

	current_open = float(df["Open"].iloc[-1])

	# Entry and stop levels
	buy_entry_level = round(current_open - (avg_sell_swing * 1.80), 2)
	buy_stop_level = round(current_open - (avg_sell_swing * 2.25), 2)
	sell_entry_level = round(current_open + (avg_buy_swing * 1.80), 2)
	sell_stop_level = round(current_open + (avg_buy_swing * 2.25), 2)

	# Check if recent GSV exceeded 225% threshold (exhaustion signal)
	recent_gsv_exceeded = False
	for i in range(-min(5, len(df)), 0):
		row = df.iloc[i]
		if row["Close"] < row["Open"]:
			swing = float(row["High"] - row["Open"])
			if avg_buy_swing > 0 and swing > avg_buy_swing * 2.25:
				recent_gsv_exceeded = True
				break
		else:
			swing = float(row["Open"] - row["Low"])
			if avg_sell_swing > 0 and swing > avg_sell_swing * 2.25:
				recent_gsv_exceeded = True
				break

	# Swing history (last 10 days)
	swing_history = []
	for i in range(-min(10, len(df)), 0):
		row = df.iloc[i]
		date_str = df.index[i].strftime("%Y-%m-%d")
		if row["Close"] < row["Open"]:
			swing_history.append({
				"date": date_str,
				"type": "buy_swing",
				"value": round(float(row["High"] - row["Open"]), 2),
			})
		else:
			swing_history.append({
				"date": date_str,
				"type": "sell_swing",
				"value": round(float(row["Open"] - row["Low"]), 2),
			})

	output_json({
		"symbol": symbol,
		"avg_buy_swing": avg_buy_swing,
		"avg_sell_swing": avg_sell_swing,
		"buy_entry_level": buy_entry_level,
		"buy_stop_level": buy_stop_level,
		"sell_entry_level": sell_entry_level,
		"sell_stop_level": sell_stop_level,
		"swing_period_days": 4,
		"recent_gsv_exceeded": recent_gsv_exceeded,
		"swing_history": swing_history,
	})


@safe_run
def cmd_tdw_tdm(args):
	"""Today's Trading Day of Week / Trading Day of Month bias."""
	today = datetime.date.today()
	dow = today.isoweekday()  # 1=Mon ... 7=Sun
	day_names = {1: "Monday", 2: "Tuesday", 3: "Wednesday", 4: "Thursday",
				 5: "Friday", 6: "Saturday", 7: "Sunday"}

	tdw_info = TDW_BIAS.get(dow, {"bias": "neutral", "note": "Weekend - markets closed"})
	tdm_info = _tdm_bias(today.day)
	combined = _combine_bias(tdw_info["bias"], tdm_info["bias"])

	output_json({
		"date": today.isoformat(),
		"day_of_week": day_names.get(dow, "Unknown"),
		"trading_day_of_week": min(dow, 5),
		"trading_day_of_month": today.day,
		"tdw_bias": tdw_info["bias"],
		"tdm_bias": tdm_info["bias"],
		"tdw_note": tdw_info["note"],
		"tdm_note": tdm_info["note"],
		"combined_bias": combined,
	})


# ---------------------------------------------------------------------------
# Main dispatch
# ---------------------------------------------------------------------------

def main():
	parser = argparse.ArgumentParser(
		description="Larry Williams Short-Term Trading Tools"
	)
	sub = parser.add_subparsers(dest="command", required=True)

	# williams-r
	sp = sub.add_parser("williams-r", help="Williams %%R oscillator")
	sp.add_argument("symbol", help="Ticker symbol")
	sp.add_argument("--period", type=int, default=14, help="Lookback period (default: 14)")
	sp.add_argument("--history", type=int, default=10, help="History values to return (default: 10)")
	sp.set_defaults(func=cmd_williams_r)

	# volatility-breakout
	sp = sub.add_parser("volatility-breakout", help="ATR-based breakout levels")
	sp.add_argument("symbol", help="Ticker symbol")
	sp.add_argument("--atr-period", type=int, default=3, help="ATR period (default: 3)")
	sp.add_argument("--pct", type=float, default=0.6, help="Breakout pct multiplier (default: 0.6)")
	sp.set_defaults(func=cmd_volatility_breakout)

	# range-analysis
	sp = sub.add_parser("range-analysis", help="Range expansion/contraction detection")
	sp.add_argument("symbol", help="Ticker symbol")
	sp.add_argument("--lookback", type=int, default=20, help="Analysis window (default: 20)")
	sp.set_defaults(func=cmd_range_analysis)

	# swing-points
	sp = sub.add_parser("swing-points", help="Swing point identification")
	sp.add_argument("symbol", help="Ticker symbol")
	sp.add_argument("--level", default="short", choices=["short", "intermediate", "long"],
					help="Hierarchy level (default: short)")
	sp.set_defaults(func=cmd_swing_points)

	# pattern-scan
	sp = sub.add_parser("pattern-scan", help="Williams pattern detection")
	sp.add_argument("symbol", help="Ticker symbol")
	sp.add_argument("--lookback", type=int, default=5, help="Scan window days (default: 5)")
	sp.set_defaults(func=cmd_pattern_scan)

	# tdw-tdm
	sp = sub.add_parser("tdw-tdm", help="Today's TDW/TDM bias")
	sp.set_defaults(func=cmd_tdw_tdm)

	# gsv
	sp = sub.add_parser("gsv", help="Greatest Swing Value failure swing measurement")
	sp.add_argument("symbol", help="Ticker symbol")
	sp.set_defaults(func=cmd_gsv)

	args = parser.parse_args()
	args.func(args)


if __name__ == "__main__":
	main()
