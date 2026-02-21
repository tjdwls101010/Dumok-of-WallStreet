#!/usr/bin/env python3
"""Larry Williams Short-Term Trading Tools: volatility breakouts, range analysis, and swing identification.

Implements Larry Williams' core short-term trading techniques from
"Long-Term Secrets to Short-Term Trading." Includes Williams %R oscillator,
volatility breakout signals (his primary entry system), daily range
expansion/contraction analysis, and mechanical swing point identification
based on Williams' market structure framework.

Williams' central thesis: trends are set in motion by "explosions of price
activity" — when volatility expands beyond recent proportion, the trend
continues until an equal or greater explosion occurs in the opposite
direction. The volatility breakout entry, filtered by Trading Day of Week
and trend confirmation, is the most consistently profitable mechanical
entry technique he has found across decades of trading.

Commands:
	williams_r: Williams %R oscillator calculation with overbought/oversold signals
	volatility_breakout: Volatility breakout buy/sell signals (Williams' core entry system)
	range_analysis: Daily range expansion/contraction analysis with True Range
	swing_points: Mechanical swing high/low identification and trend direction

Args:
	ticker (str): Ticker symbol (e.g., "AAPL", "NVDA", "SPY")
	--period (int): Williams %R lookback period in days (default: 14)
	--lookback (int): Historical data lookback in trading days (default: 60)
	--multiplier (float): Volatility breakout multiplier (default: 1.0)
	--window (int): Swing point identification window in bars (default: 5)

Returns:
	For williams_r:
	dict: {
		"symbol": str,
		"date": str,
		"current_price": float,
		"period": int,
		"lookback_days": int,
		"latest": {
			"williams_r": float,
			"zone": str,
			"close": float
		},
		"history": [
			{
				"date": str,
				"close": float,
				"williams_r": float,
				"zone": str
			}
		],
		"summary": {
			"current_zone": str,
			"days_in_current_zone": int,
			"overbought_pct": float,
			"oversold_pct": float,
			"neutral_pct": float,
			"mean_r": float
		}
	}

	For volatility_breakout:
	dict: {
		"symbol": str,
		"date": str,
		"current_price": float,
		"multiplier": float,
		"lookback_days": int,
		"next_session": {
			"buy_level": float,
			"sell_level": float,
			"reference_close": float,
			"true_range": float,
			"atr_3": float
		},
		"recent_signals": [
			{
				"date": str,
				"signal": str,
				"entry_level": float,
				"close": float,
				"result_pct": float
			}
		],
		"summary": {
			"total_signals": int,
			"buy_signals": int,
			"sell_signals": int,
			"avg_true_range": float,
			"current_range_vs_avg": float
		}
	}

	For range_analysis:
	dict: {
		"symbol": str,
		"date": str,
		"current_price": float,
		"period": int,
		"latest": {
			"true_range": float,
			"true_range_pct": float,
			"avg_true_range": float,
			"range_ratio": float,
			"phase": str
		},
		"history": [
			{
				"date": str,
				"true_range": float,
				"true_range_pct": float,
				"range_ratio": float,
				"phase": str
			}
		],
		"summary": {
			"current_phase": str,
			"expansion_days": int,
			"contraction_days": int,
			"normal_days": int,
			"avg_true_range": float,
			"max_true_range": float,
			"min_true_range": float,
			"current_percentile": float
		}
	}

	For swing_points:
	dict: {
		"symbol": str,
		"date": str,
		"current_price": float,
		"window": int,
		"lookback_days": int,
		"swing_highs": [
			{
				"date": str,
				"price": float,
				"level": str
			}
		],
		"swing_lows": [
			{
				"date": str,
				"price": float,
				"level": str
			}
		],
		"trend": {
			"short_term": str,
			"intermediate": str,
			"last_swing_high": float,
			"last_swing_low": float,
			"current_position": str
		}
	}

Example:
	>>> python williams.py williams_r AAPL --period 14 --lookback 60
	{
		"symbol": "AAPL",
		"date": "2026-02-20",
		"current_price": 245.50,
		"period": 14,
		"latest": {
			"williams_r": -25.3,
			"zone": "overbought",
			"close": 245.50
		},
		"summary": {
			"current_zone": "overbought",
			"days_in_current_zone": 3,
			"overbought_pct": 28.3,
			"oversold_pct": 15.0,
			"neutral_pct": 56.7,
			"mean_r": -48.2
		}
	}

	>>> python williams.py volatility_breakout SPY --multiplier 0.6 --lookback 60
	{
		"symbol": "SPY",
		"date": "2026-02-20",
		"current_price": 502.30,
		"multiplier": 0.6,
		"next_session": {
			"buy_level": 505.12,
			"sell_level": 499.48,
			"reference_close": 502.30,
			"true_range": 4.70,
			"atr_3": 4.82
		}
	}

Use Cases:
	- Generate daily volatility breakout entry levels for next-session trading
	- Identify overbought/oversold conditions with Williams %R for timing entries
	- Detect range expansion phases that signal new trend legs forming
	- Map mechanical swing highs/lows to determine market structure and trend
	- Combine range analysis with breakout signals for conviction filtering

Notes:
	- Williams %R scale: -100 (extreme oversold) to 0 (extreme overbought)
	- Overbought zone: %R > -20; Oversold zone: %R < -80; Neutral: between
	- Volatility breakout formula: Entry = Close + (multiplier x ATR(3))
	- True Range = max(H-L, |H-prevClose|, |L-prevClose|)
	- Range ratio > 1.5 = expansion (trending); ratio < 0.5 = contraction
	- Swing points use Williams' nested structure: short -> intermediate -> long

See Also:
	- closing_range.py: Bar classification for institutional accumulation signals
	- volume_edge.py: Volume edge detection for breakout confirmation
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import yfinance as yf
from utils import output_json, safe_run


def _true_range(high, low, prev_close):
	"""Calculate True Range: max(H-L, |H-prevC|, |L-prevC|)."""
	return max(high - low, abs(high - prev_close), abs(low - prev_close))


def _classify_wr_zone(wr):
	"""Classify Williams %R value into overbought/oversold/neutral."""
	if wr > -20:
		return "overbought"
	if wr < -80:
		return "oversold"
	return "neutral"


@safe_run
def cmd_williams_r(args):
	"""Williams %R oscillator with overbought/oversold signal detection."""
	symbol = args.ticker.upper()
	period = args.period
	lookback = args.lookback

	# Fetch extra data for the rolling window
	fetch_days = lookback + period + 30
	ticker = yf.Ticker(symbol)
	data = ticker.history(period=f"{fetch_days}d", interval="1d")

	if data.empty or len(data) < period + 5:
		output_json({
			"error": f"Insufficient data for {symbol}. Need at least {period + 5} trading days.",
			"data_points": len(data),
		})
		return

	highs = data["High"]
	lows = data["Low"]
	closes = data["Close"]

	# Calculate Williams %R for the lookback window
	results = []
	start_idx = max(period, len(data) - lookback)
	for i in range(start_idx, len(data)):
		highest_high = float(highs.iloc[i - period + 1:i + 1].max())
		lowest_low = float(lows.iloc[i - period + 1:i + 1].min())
		close = float(closes.iloc[i])

		if highest_high == lowest_low:
			wr = -50.0
		else:
			wr = round((highest_high - close) / (highest_high - lowest_low) * -100, 1)

		zone = _classify_wr_zone(wr)
		results.append({
			"date": str(data.index[i].date()),
			"close": round(close, 2),
			"williams_r": wr,
			"zone": zone,
		})

	if not results:
		output_json({"error": f"No Williams %R values could be computed for {symbol}."})
		return

	latest = results[-1]

	# Count consecutive days in current zone
	days_in_zone = 0
	for r in reversed(results):
		if r["zone"] == latest["zone"]:
			days_in_zone += 1
		else:
			break

	total = len(results)
	overbought_count = sum(1 for r in results if r["zone"] == "overbought")
	oversold_count = sum(1 for r in results if r["zone"] == "oversold")
	neutral_count = total - overbought_count - oversold_count
	mean_r = round(sum(r["williams_r"] for r in results) / total, 1)

	output_json({
		"symbol": symbol,
		"date": latest["date"],
		"current_price": latest["close"],
		"period": period,
		"lookback_days": total,
		"latest": {
			"williams_r": latest["williams_r"],
			"zone": latest["zone"],
			"close": latest["close"],
		},
		"history": results,
		"summary": {
			"current_zone": latest["zone"],
			"days_in_current_zone": days_in_zone,
			"overbought_pct": round(overbought_count / total * 100, 1),
			"oversold_pct": round(oversold_count / total * 100, 1),
			"neutral_pct": round(neutral_count / total * 100, 1),
			"mean_r": mean_r,
		},
	})


@safe_run
def cmd_volatility_breakout(args):
	"""Volatility breakout signals based on Williams' core entry system."""
	symbol = args.ticker.upper()
	lookback = args.lookback
	multiplier = args.multiplier

	fetch_days = lookback + 30
	ticker = yf.Ticker(symbol)
	data = ticker.history(period=f"{fetch_days}d", interval="1d")

	if data.empty or len(data) < 10:
		output_json({
			"error": f"Insufficient data for {symbol}. Need at least 10 trading days.",
			"data_points": len(data),
		})
		return

	highs = data["High"]
	lows = data["Low"]
	closes = data["Close"]
	opens = data["Open"]

	# Calculate True Range series
	tr_list = []
	for i in range(1, len(data)):
		h = float(highs.iloc[i])
		l = float(lows.iloc[i])
		pc = float(closes.iloc[i - 1])
		tr_list.append(_true_range(h, l, pc))

	# Generate breakout signals for lookback period
	signals = []
	start_idx = max(4, len(data) - lookback)
	for i in range(start_idx, len(data)):
		tr_idx = i - 1  # tr_list is offset by 1
		if tr_idx < 3:
			continue

		# ATR of past 3 days
		atr3 = sum(tr_list[tr_idx - 2:tr_idx + 1]) / 3
		prev_close = float(closes.iloc[i - 1])
		open_price = float(opens.iloc[i])
		close_price = float(closes.iloc[i])
		high_price = float(highs.iloc[i])
		low_price = float(lows.iloc[i])

		buy_level = round(prev_close + multiplier * atr3, 2)
		sell_level = round(prev_close - multiplier * atr3, 2)

		signal = None
		entry_level = None
		if high_price >= buy_level:
			signal = "buy"
			entry_level = buy_level
		elif low_price <= sell_level:
			signal = "sell"
			entry_level = sell_level

		if signal:
			if signal == "buy":
				result_pct = round((close_price - entry_level) / entry_level * 100, 2)
			else:
				result_pct = round((entry_level - close_price) / entry_level * 100, 2)

			signals.append({
				"date": str(data.index[i].date()),
				"signal": signal,
				"entry_level": entry_level,
				"close": round(close_price, 2),
				"result_pct": result_pct,
			})

	# Next session levels
	last_tr_idx = len(tr_list) - 1
	if last_tr_idx >= 2:
		next_atr3 = sum(tr_list[last_tr_idx - 2:last_tr_idx + 1]) / 3
	else:
		next_atr3 = tr_list[-1] if tr_list else 0

	last_close = round(float(closes.iloc[-1]), 2)
	last_tr = round(tr_list[-1], 2) if tr_list else 0

	# Summary stats
	total_tr = tr_list[max(0, len(tr_list) - lookback):]
	avg_tr = round(sum(total_tr) / len(total_tr), 2) if total_tr else 0
	current_range_vs_avg = round(last_tr / avg_tr, 2) if avg_tr > 0 else 0

	buy_signals = sum(1 for s in signals if s["signal"] == "buy")
	sell_signals = sum(1 for s in signals if s["signal"] == "sell")

	output_json({
		"symbol": symbol,
		"date": str(data.index[-1].date()),
		"current_price": last_close,
		"multiplier": multiplier,
		"lookback_days": len(total_tr),
		"next_session": {
			"buy_level": round(last_close + multiplier * next_atr3, 2),
			"sell_level": round(last_close - multiplier * next_atr3, 2),
			"reference_close": last_close,
			"true_range": last_tr,
			"atr_3": round(next_atr3, 2),
		},
		"recent_signals": signals[-20:],
		"summary": {
			"total_signals": len(signals),
			"buy_signals": buy_signals,
			"sell_signals": sell_signals,
			"avg_true_range": avg_tr,
			"current_range_vs_avg": current_range_vs_avg,
		},
	})


@safe_run
def cmd_range_analysis(args):
	"""Daily range expansion/contraction analysis with True Range."""
	symbol = args.ticker.upper()
	period = args.period

	fetch_days = period + 60
	ticker = yf.Ticker(symbol)
	data = ticker.history(period=f"{fetch_days}d", interval="1d")

	if data.empty or len(data) < period + 5:
		output_json({
			"error": f"Insufficient data for {symbol}. Need at least {period + 5} trading days.",
			"data_points": len(data),
		})
		return

	highs = data["High"]
	lows = data["Low"]
	closes = data["Close"]

	# Calculate True Range series
	tr_values = []
	for i in range(1, len(data)):
		h = float(highs.iloc[i])
		l = float(lows.iloc[i])
		pc = float(closes.iloc[i - 1])
		tr_values.append({
			"index": i,
			"date": str(data.index[i].date()),
			"true_range": round(_true_range(h, l, pc), 4),
			"close": round(float(closes.iloc[i]), 2),
		})

	# Compute rolling ATR and classify phases
	results = []
	for j, tr in enumerate(tr_values):
		if j < period:
			continue
		window = tr_values[j - period:j]
		atr = sum(w["true_range"] for w in window) / period
		tr_pct = round(tr["true_range"] / tr["close"] * 100, 2) if tr["close"] > 0 else 0
		ratio = round(tr["true_range"] / atr, 2) if atr > 0 else 0

		if ratio >= 1.5:
			phase = "expansion"
		elif ratio <= 0.5:
			phase = "contraction"
		else:
			phase = "normal"

		results.append({
			"date": tr["date"],
			"true_range": tr["true_range"],
			"true_range_pct": tr_pct,
			"avg_true_range": round(atr, 4),
			"range_ratio": ratio,
			"phase": phase,
		})

	if not results:
		output_json({"error": f"Could not compute range analysis for {symbol}."})
		return

	latest = results[-1]

	# Percentile of current True Range
	all_tr = sorted(r["true_range"] for r in results)
	current_rank = sum(1 for t in all_tr if t <= latest["true_range"])
	current_percentile = round(current_rank / len(all_tr) * 100, 1)

	expansion_days = sum(1 for r in results if r["phase"] == "expansion")
	contraction_days = sum(1 for r in results if r["phase"] == "contraction")
	normal_days = len(results) - expansion_days - contraction_days

	output_json({
		"symbol": symbol,
		"date": latest["date"],
		"current_price": round(float(closes.iloc[-1]), 2),
		"period": period,
		"latest": {
			"true_range": latest["true_range"],
			"true_range_pct": latest["true_range_pct"],
			"avg_true_range": latest["avg_true_range"],
			"range_ratio": latest["range_ratio"],
			"phase": latest["phase"],
		},
		"history": results,
		"summary": {
			"current_phase": latest["phase"],
			"expansion_days": expansion_days,
			"contraction_days": contraction_days,
			"normal_days": normal_days,
			"avg_true_range": latest["avg_true_range"],
			"max_true_range": round(max(r["true_range"] for r in results), 4),
			"min_true_range": round(min(r["true_range"] for r in results), 4),
			"current_percentile": current_percentile,
		},
	})


@safe_run
def cmd_swing_points(args):
	"""Swing high/low identification with trend direction analysis."""
	symbol = args.ticker.upper()
	window = args.window
	lookback = args.lookback

	fetch_days = lookback + 30
	ticker = yf.Ticker(symbol)
	data = ticker.history(period=f"{fetch_days}d", interval="1d")

	if data.empty or len(data) < window * 3:
		output_json({
			"error": f"Insufficient data for {symbol}. Need at least {window * 3} trading days.",
			"data_points": len(data),
		})
		return

	# Trim to lookback
	if len(data) > lookback:
		data = data.iloc[-lookback:]

	highs = data["High"]
	lows = data["Low"]
	closes = data["Close"]

	# Identify short-term swing highs: a day with lower highs on both sides
	swing_highs = []
	swing_lows = []

	for i in range(window, len(data) - window):
		h = float(highs.iloc[i])
		l = float(lows.iloc[i])

		# Check for swing high: all surrounding highs are lower
		is_high = True
		for j in range(1, window + 1):
			if float(highs.iloc[i - j]) >= h or float(highs.iloc[i + j]) >= h:
				is_high = False
				break

		if is_high:
			swing_highs.append({
				"date": str(data.index[i].date()),
				"price": round(h, 2),
				"index": i,
			})

		# Check for swing low: all surrounding lows are higher
		is_low = True
		for j in range(1, window + 1):
			if float(lows.iloc[i - j]) <= l or float(lows.iloc[i + j]) <= l:
				is_low = False
				break

		if is_low:
			swing_lows.append({
				"date": str(data.index[i].date()),
				"price": round(l, 2),
				"index": i,
			})

	# Classify intermediate-term swings (short-term high with lower short-term highs on both sides)
	for i, sh in enumerate(swing_highs):
		if i > 0 and i < len(swing_highs) - 1:
			if swing_highs[i - 1]["price"] < sh["price"] and swing_highs[i + 1]["price"] < sh["price"]:
				sh["level"] = "intermediate"
			else:
				sh["level"] = "short_term"
		else:
			sh["level"] = "short_term"

	for i, sl in enumerate(swing_lows):
		if i > 0 and i < len(swing_lows) - 1:
			if swing_lows[i - 1]["price"] > sl["price"] and swing_lows[i + 1]["price"] > sl["price"]:
				sl["level"] = "intermediate"
			else:
				sl["level"] = "short_term"
		else:
			sl["level"] = "short_term"

	# Determine trend from swing points
	current_price = round(float(closes.iloc[-1]), 2)

	# Short-term trend from last two swing highs and lows
	st_trend = "neutral"
	if len(swing_highs) >= 2 and len(swing_lows) >= 2:
		if swing_highs[-1]["price"] > swing_highs[-2]["price"] and swing_lows[-1]["price"] > swing_lows[-2]["price"]:
			st_trend = "up"
		elif swing_highs[-1]["price"] < swing_highs[-2]["price"] and swing_lows[-1]["price"] < swing_lows[-2]["price"]:
			st_trend = "down"

	# Intermediate trend from intermediate swing points
	int_highs = [sh for sh in swing_highs if sh["level"] == "intermediate"]
	int_lows = [sl for sl in swing_lows if sl["level"] == "intermediate"]

	int_trend = "neutral"
	if len(int_highs) >= 2 and len(int_lows) >= 2:
		if int_highs[-1]["price"] > int_highs[-2]["price"] and int_lows[-1]["price"] > int_lows[-2]["price"]:
			int_trend = "up"
		elif int_highs[-1]["price"] < int_highs[-2]["price"] and int_lows[-1]["price"] < int_lows[-2]["price"]:
			int_trend = "down"

	last_sh = swing_highs[-1]["price"] if swing_highs else None
	last_sl = swing_lows[-1]["price"] if swing_lows else None

	# Current position relative to last swings
	if last_sh and last_sl:
		if current_price > last_sh:
			current_position = "above_last_swing_high"
		elif current_price < last_sl:
			current_position = "below_last_swing_low"
		else:
			current_position = "between_swings"
	else:
		current_position = "insufficient_data"

	# Clean output (remove internal index field)
	out_highs = [{"date": sh["date"], "price": sh["price"], "level": sh["level"]} for sh in swing_highs]
	out_lows = [{"date": sl["date"], "price": sl["price"], "level": sl["level"]} for sl in swing_lows]

	output_json({
		"symbol": symbol,
		"date": str(data.index[-1].date()),
		"current_price": current_price,
		"window": window,
		"lookback_days": len(data),
		"swing_highs": out_highs,
		"swing_lows": out_lows,
		"trend": {
			"short_term": st_trend,
			"intermediate": int_trend,
			"last_swing_high": last_sh,
			"last_swing_low": last_sl,
			"current_position": current_position,
		},
	})


def main():
	parser = argparse.ArgumentParser(
		description="Larry Williams Short-Term Trading Tools"
	)
	sub = parser.add_subparsers(dest="command", required=True)

	# williams_r
	sp = sub.add_parser("williams_r", help="Williams %%R oscillator")
	sp.add_argument("ticker", help="Ticker symbol")
	sp.add_argument("--period", type=int, default=14, help="Lookback period (default: 14)")
	sp.add_argument("--lookback", type=int, default=60, help="Historical days to compute (default: 60)")
	sp.set_defaults(func=cmd_williams_r)

	# volatility_breakout
	sp = sub.add_parser("volatility_breakout", help="Volatility breakout signals")
	sp.add_argument("ticker", help="Ticker symbol")
	sp.add_argument("--lookback", type=int, default=60, help="Historical days (default: 60)")
	sp.add_argument("--multiplier", type=float, default=1.0, help="ATR multiplier (default: 1.0)")
	sp.set_defaults(func=cmd_volatility_breakout)

	# range_analysis
	sp = sub.add_parser("range_analysis", help="Range expansion/contraction analysis")
	sp.add_argument("ticker", help="Ticker symbol")
	sp.add_argument("--period", type=int, default=20, help="ATR averaging period (default: 20)")
	sp.set_defaults(func=cmd_range_analysis)

	# swing_points
	sp = sub.add_parser("swing_points", help="Swing high/low identification")
	sp.add_argument("ticker", help="Ticker symbol")
	sp.add_argument("--window", type=int, default=5, help="Bars on each side for swing ID (default: 5)")
	sp.add_argument("--lookback", type=int, default=120, help="Historical days (default: 120)")
	sp.set_defaults(func=cmd_swing_points)

	args = parser.parse_args()
	args.func(args)


if __name__ == "__main__":
	main()
