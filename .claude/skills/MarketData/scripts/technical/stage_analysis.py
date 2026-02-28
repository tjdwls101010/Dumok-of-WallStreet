#!/usr/bin/env python3
"""Minervini Stage Analysis: classify stocks into Stage 1-4 lifecycle phases.

Determines which of the four stock lifecycle stages a stock is currently in,
along with confidence level and transition signals. Based on Mark Minervini's
stage analysis framework from "Trade Like a Stock Market Wizard."

Uses both 50-day and 20-day Up/Down volume ratios for early transition
detection. When the 20-day ratio diverges from the 50-day ratio, it signals
an emerging stage transition before it becomes obvious in price action.

Commands:
	classify: Determine current stage (1-4) for a ticker
	transitions: Detect Stage 1->2 transition signals

Args:
	symbol (str): Ticker symbol (e.g., "AAPL", "NVDA", "META")
	--period (str): Historical data period (default: "2y")

Returns:
	dict: {
		"symbol": str,
		"date": str,
		"current_price": float,
		"current_stage": int,
		"stage_name": str,
		"stage_confidence": float,
		"evidence": {
			"price_vs_200ma": str,
			"up_down_volume_ratio": float,
			"up_down_volume_ratio_20d": float,
			"volume_divergence_50d_vs_20d": str,
			"volume_grade": str,
			"higher_highs": bool,
			"higher_lows": bool,
			"volatility_expanding": bool,
			"largest_decline_pct": float
		},
		"runner_up_stage": int or null,
		"runner_up_score": int,
		"stage_gap": int,
		"transition_risk": str,
		"stage_scores": dict
	}

Example:
	>>> python stage_analysis.py classify NVDA --period 2y
	{
		"symbol": "NVDA",
		"date": "2026-02-07",
		"current_price": 135.50,
		"current_stage": 2,
		"stage_name": "Advancing (Accumulation)",
		"stage_confidence": 85.0,
		"evidence": {
			"price_vs_200ma": "above",
			"up_down_volume_ratio": 1.45,
			"up_down_volume_ratio_20d": 1.32,
			"volume_divergence_50d_vs_20d": "stable",
			"volume_pattern": "accumulation"
		}
	}

Use Cases:
	- Identify Stage 2 stocks for SEPA methodology entry
	- Detect Stage 2->3 transitions via 20d/50d volume ratio divergence
	- Filter out Stage 4 declining stocks
	- Monitor Stage 1->2 transitions for early entry

Notes:
	- Stage 2 (Advancing) is the only stage to buy in SEPA methodology
	- Stage 3 detection relies on volatility increase and MA flattening
	- 20-day volume ratio < 0.5 adds +10 to Stage 3 score (early warning)
	- 20d/50d divergence (20d < 0.5 but 50d > 0.8) adds +5 to Stage 3
	- Confidence below 60% suggests ambiguous stage (possible transition)
	- Transition signals are forward-looking indicators of stage change
	- Transition risk: high (<20 gap to Stage 3), moderate (<40), low (>=40)

See Also:
	- trend_template.py: 8-criteria Trend Template for Stage 2 confirmation
	- rs_ranking.py: Relative strength ranking for leader identification
	- volume_analysis.py: Volume-based accumulation/distribution analysis
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import numpy as np
import yfinance as yf
from technical.indicators import calculate_sma
from technical.volume_analysis import (
	_calc_up_down_ratio,
	_count_accumulation_days,
	_count_distribution_days,
	_grade_accumulation,
)
from utils import output_json, safe_run

STAGE_NAMES = {
	1: "Neglect / Consolidation (Basing)",
	2: "Advancing (Accumulation)",
	3: "Topping (Distribution)",
	4: "Declining (Capitulation)",
}


def _ma_slope(series, lookback=20):
	"""Calculate slope direction of a moving average over lookback days."""
	if len(series) < lookback:
		return 0.0
	recent = series.dropna().tail(lookback)
	if len(recent) < 2:
		return 0.0
	x = np.arange(len(recent))
	y = recent.values.astype(float)
	slope = np.polyfit(x, y, 1)[0]
	# Normalize as percent per day
	mean_val = np.mean(y)
	if mean_val == 0:
		return 0.0
	return (slope / mean_val) * 100


def _higher_highs_higher_lows(highs, lows, window=20, count=3):
	"""Check for pattern of higher highs and higher lows."""
	if len(highs) < window * count:
		return False, False

	swing_highs = []
	swing_lows = []
	for i in range(count):
		start = -(window * (count - i))
		end = -(window * (count - i - 1)) if i < count - 1 else None
		segment_h = highs.iloc[start:end]
		segment_l = lows.iloc[start:end]
		if len(segment_h) > 0:
			swing_highs.append(float(segment_h.max()))
		if len(segment_l) > 0:
			swing_lows.append(float(segment_l.min()))

	hh = (
		all(swing_highs[i] > swing_highs[i - 1] for i in range(1, len(swing_highs))) if len(swing_highs) >= 2 else False
	)
	hl = all(swing_lows[i] > swing_lows[i - 1] for i in range(1, len(swing_lows))) if len(swing_lows) >= 2 else False
	return hh, hl


def _volume_trend(volumes, closes, lookback=50):
	"""Analyze up-day vs down-day volume ratio.

	Delegates to volume_analysis._calc_up_down_ratio for the core calculation,
	then applies the same classification thresholds (>1.3 accumulation, <0.7
	distribution).
	"""
	if len(volumes) < lookback or len(closes) < lookback:
		return "neutral", 1.0

	ratio, _, _ = _calc_up_down_ratio(volumes, closes, lookback)

	if ratio > 1.3:
		return "accumulation", ratio
	elif ratio < 0.7:
		return "distribution", ratio
	else:
		return "neutral", ratio


def _largest_decline_since_start(closes, sma200, stage2_start_idx=None):
	"""Calculate largest peak-to-trough decline since Stage 2 start."""
	if stage2_start_idx is not None:
		segment = closes.iloc[stage2_start_idx:]
	else:
		# Approximate: find where price first crossed above SMA200
		above = closes > sma200
		crossover_points = above.astype(int).diff()
		cross_up = crossover_points[crossover_points == 1]
		if len(cross_up) == 0:
			segment = closes
		else:
			segment = closes.iloc[cross_up.index.get_loc(cross_up.index[0]) :]

	if len(segment) < 2:
		return 0.0

	running_max = segment.expanding().max()
	drawdowns = (segment / running_max - 1) * 100
	return float(drawdowns.min())


@safe_run
def cmd_classify(args):
	"""Classify a stock into Stage 1-4."""
	symbol = args.symbol.upper()
	ticker = yf.Ticker(symbol)
	data = ticker.history(period=args.period, interval="1d")

	if data.empty or len(data) < 200:
		output_json(
			{
				"error": f"Insufficient data for {symbol}. Need at least 200 trading days.",
				"data_points": len(data),
			}
		)
		return

	closes = data["Close"]
	highs = data["High"]
	lows = data["Low"]
	volumes = data["Volume"]
	current_price = float(closes.iloc[-1])
	date_str = str(data.index[-1].date())

	sma50 = calculate_sma(closes, 50)
	sma150 = calculate_sma(closes, 150)
	sma200 = calculate_sma(closes, 200)

	c_sma50 = float(sma50.iloc[-1])
	c_sma150 = float(sma150.iloc[-1])
	c_sma200 = float(sma200.iloc[-1])

	# Key metrics
	price_above_200 = current_price > c_sma200
	sma200_slope = _ma_slope(sma200, lookback=40)
	sma50_slope = _ma_slope(sma50, lookback=20)
	hh, hl = _higher_highs_higher_lows(highs, lows)
	vol_pattern, vol_ratio = _volume_trend(volumes, closes)

	# Richer volume metrics
	vol_50avg = float(volumes.tail(50).mean())
	vol_200avg = float(volumes.tail(200).mean()) if len(volumes) >= 200 else vol_50avg
	acc_days, _ = _count_accumulation_days(volumes, closes, vol_50avg, 50)
	dist_days, _ = _count_distribution_days(volumes, closes, vol_50avg, 50)
	current_vol = float(volumes.iloc[-1])
	vol_vs_50avg_pct = round(current_vol / vol_50avg * 100, 1) if vol_50avg > 0 else 0.0
	vol_grade = _grade_accumulation(vol_ratio, acc_days, dist_days, vol_vs_50avg_pct)

	# 20-day Up/Down volume ratio for early transition detection
	vol_ratio_20d, _, _ = _calc_up_down_ratio(volumes, closes, 20)

	# Recent volatility (30-day vs 90-day ATR ratio)
	tr = np.maximum(
		highs.values - lows.values,
		np.maximum(
			np.abs(highs.values - np.roll(closes.values, 1)),
			np.abs(lows.values - np.roll(closes.values, 1)),
		),
	)
	atr_30 = float(np.mean(tr[-30:])) if len(tr) >= 30 else 0
	atr_90 = float(np.mean(tr[-90:])) if len(tr) >= 90 else atr_30
	volatility_expanding = atr_30 > atr_90 * 1.2 if atr_90 > 0 else False

	# Largest decline
	largest_decline = _largest_decline_since_start(closes, sma200)

	# Stage classification scoring
	scores = {1: 0, 2: 0, 3: 0, 4: 0}

	# Stage 1: Price oscillating around flat 200MA, low volume
	if abs(sma200_slope) < 0.02:
		scores[1] += 30
	if abs(current_price / c_sma200 - 1) < 0.05:
		scores[1] += 20
	if vol_pattern == "neutral":
		scores[1] += 15
	if not hh and not hl:
		scores[1] += 15

	# Stage 2: Price > 200MA, uptrend, higher highs/lows, accumulation
	if price_above_200:
		scores[2] += 20
	if sma200_slope > 0.02:
		scores[2] += 15
	if current_price > c_sma50 > c_sma150 > c_sma200:
		scores[2] += 20
	if hh and hl:
		scores[2] += 15
	if vol_pattern == "accumulation":
		scores[2] += 15
	if sma50_slope > 0:
		scores[2] += 10

	# Stage 3: Increased volatility, MA flattening, distribution
	if volatility_expanding:
		scores[3] += 20
	if abs(sma200_slope) < 0.03 and sma200_slope >= 0:
		scores[3] += 15
	if vol_pattern == "distribution":
		scores[3] += 20
	if largest_decline < -15:
		scores[3] += 15
	if price_above_200 and not (c_sma50 > c_sma150):
		scores[3] += 15

	# Stage 4: Price < 200MA, downtrend, lower lows
	if not price_above_200:
		scores[4] += 25
	if sma200_slope < -0.02:
		scores[4] += 20
	if vol_pattern == "distribution":
		scores[4] += 15
	if current_price < c_sma50 < c_sma200:
		scores[4] += 20

	# Enhanced Stage 3: severe decline and transition zone detection
	if largest_decline < -25:
		scores[3] += 30  # Severe decline strongly suggests Stage 3+
	if (c_sma50 > c_sma150 > c_sma200) and not price_above_200:
		scores[3] += 25  # Bullish MA alignment but price below 200MA = transition zone
	price_distance_below_200 = (current_price / c_sma200 - 1) * 100
	if price_distance_below_200 < -10:
		scores[3] += 15  # Price 10%+ below 200MA
		scores[4] += 10  # Also contributes to Stage 4
	if sma200_slope > 0 and not price_above_200:
		scores[3] += 20  # Rising 200MA but price collapse = distribution
		scores[4] += 10  # Contributes to Stage 4 when 200MA still rising

	# Stage-specific volume scoring (graduated by vol_grade)
	# Stage 1: volume contraction (50d avg < 70% of 200d avg)
	if vol_200avg > 0 and vol_50avg < vol_200avg * 0.7:
		scores[1] += 10
	# Stage 2: graduated by accumulation grade
	if vol_grade in ("A+", "A"):
		scores[2] += 10
	elif vol_grade in ("B+", "B"):
		scores[2] += 5
	elif vol_grade == "D":
		scores[2] -= 5
	elif vol_grade == "E":
		scores[2] -= 10
	# Stage 3: distribution grade boosts topping signal
	if vol_grade in ("D", "E"):
		scores[3] += 10
	# Stage 4: severe distribution
	if vol_grade == "E":
		scores[4] += 10

	# 20-day volume ratio cross-cutting influence
	if vol_ratio_20d < 0.5:
		scores[3] += 10  # Recent volume heavily distribution-weighted
	if vol_ratio_20d < 0.5 and vol_ratio > 0.8:
		scores[3] += 5  # 50d vs 20d divergence: early transition signal
	if vol_ratio_20d < 0.3:
		scores[4] += 5  # Severe recent distribution

	# Stage 1 overscoring prevention for severe declines
	if largest_decline < -30:
		scores[1] -= 20  # Large decline incompatible with Stage 1 consolidation

	# Determine stage with highest score
	current_stage = max(scores, key=scores.get)
	max_score = scores[current_stage]
	total_possible = max(sum(scores.values()), 1)
	confidence = round(max_score / total_possible * 100, 1)

	# Transition risk: how close is the runner-up stage?
	sorted_stages = sorted(scores.items(), key=lambda x: x[1], reverse=True)
	runner_up_stage = sorted_stages[1][0] if len(sorted_stages) > 1 else None
	runner_up_score = sorted_stages[1][1] if len(sorted_stages) > 1 else 0
	stage_gap = max_score - runner_up_score

	if runner_up_stage and runner_up_stage == 3 and stage_gap < 20:
		transition_risk = "high"
	elif runner_up_stage and runner_up_stage == 3 and stage_gap < 40:
		transition_risk = "moderate"
	else:
		transition_risk = "low"

	# Evidence
	evidence = {
		"price_vs_200ma": "above" if price_above_200 else "below",
		"price_distance_from_200ma_pct": round((current_price / c_sma200 - 1) * 100, 2),
		"sma200_slope_pct_per_day": round(sma200_slope, 4),
		"ma_alignment": "bullish (50>150>200)"
		if c_sma50 > c_sma150 > c_sma200
		else "bearish"
		if c_sma50 < c_sma150 < c_sma200
		else "mixed",
		"volume_pattern": vol_pattern,
		"up_down_volume_ratio": round(vol_ratio, 2),
		"up_down_volume_ratio_20d": round(vol_ratio_20d, 2),
		"volume_divergence_50d_vs_20d": "deteriorating"
		if vol_ratio_20d < vol_ratio * 0.7
		else "improving"
		if vol_ratio_20d > vol_ratio * 1.3
		else "stable",
		"accumulation_days_50d": acc_days,
		"distribution_days_50d": dist_days,
		"net_acc_dist": acc_days - dist_days,
		"volume_grade": vol_grade,
		"higher_highs": hh,
		"higher_lows": hl,
		"volatility_expanding": volatility_expanding,
		"largest_decline_pct": round(largest_decline, 2),
	}

	output_json(
		{
			"symbol": symbol,
			"date": date_str,
			"current_price": round(current_price, 2),
			"current_stage": current_stage,
			"stage_name": STAGE_NAMES[current_stage],
			"stage_confidence": confidence,
			"runner_up_stage": runner_up_stage,
			"runner_up_score": runner_up_score,
			"stage_gap": stage_gap,
			"transition_risk": transition_risk,
			"stage_scores": {f"stage_{k}": v for k, v in scores.items()},
			"evidence": evidence,
			"moving_averages": {
				"sma50": round(c_sma50, 2),
				"sma150": round(c_sma150, 2),
				"sma200": round(c_sma200, 2),
			},
		}
	)


@safe_run
def cmd_transitions(args):
	"""Detect Stage 1->2 transition signals."""
	symbol = args.symbol.upper()
	ticker = yf.Ticker(symbol)
	data = ticker.history(period=args.period, interval="1d")

	if data.empty or len(data) < 200:
		output_json(
			{
				"error": f"Insufficient data for {symbol}.",
				"data_points": len(data),
			}
		)
		return

	closes = data["Close"]
	highs = data["High"]
	lows = data["Low"]
	volumes = data["Volume"]
	current_price = float(closes.iloc[-1])

	sma50 = calculate_sma(closes, 50)
	sma150 = calculate_sma(closes, 150)
	sma200 = calculate_sma(closes, 200)

	c_sma50 = float(sma50.iloc[-1])
	c_sma150 = float(sma150.iloc[-1])
	c_sma200 = float(sma200.iloc[-1])
	sma200_slope = _ma_slope(sma200, lookback=40)

	# Volume analysis
	vol_50avg = float(volumes.tail(50).mean())
	recent_vol = float(volumes.tail(5).mean())
	vol_expansion = recent_vol > vol_50avg * 1.25

	# 52-week range
	year_data = closes.tail(252)
	week52_high = float(year_data.max())

	# 7 Stage 1->2 transition signals
	signals = []

	# 1. Price breaks above 200-day MA on above-average volume
	price_above_200 = current_price > c_sma200
	signals.append(
		{
			"signal": "Price breaks above 200-day MA on volume",
			"detected": price_above_200 and vol_expansion,
			"detail": f"Price {'>' if price_above_200 else '<'} SMA200, Vol {'expanded' if vol_expansion else 'normal'}",
		}
	)

	# 2. 50-day MA turns up and crosses above 200-day MA
	sma50_above_200 = c_sma50 > c_sma200
	sma50_rising = _ma_slope(sma50, 20) > 0
	signals.append(
		{
			"signal": "50-day MA crosses above 200-day MA (Golden Cross)",
			"detected": sma50_above_200 and sma50_rising,
			"detail": f"SMA50={'above' if sma50_above_200 else 'below'} SMA200, SMA50 {'rising' if sma50_rising else 'falling'}",
		}
	)

	# 3. Price makes higher high above prior resistance
	hh, hl = _higher_highs_higher_lows(highs, lows, window=20, count=3)
	signals.append(
		{
			"signal": "Higher highs and higher lows forming",
			"detected": hh and hl,
			"detail": f"Higher highs: {hh}, Higher lows: {hl}",
		}
	)

	# 4. 200-day MA starts to flatten or turn up
	sma200_flattening_or_rising = sma200_slope > -0.01
	signals.append(
		{
			"signal": "200-day MA flattening or turning up",
			"detected": sma200_flattening_or_rising,
			"detail": f"SMA200 slope: {sma200_slope:.4f}% per day",
		}
	)

	# 5. Up-volume exceeds down-volume
	vol_pattern, vol_ratio = _volume_trend(volumes, closes, lookback=30)
	t_vol_50avg = float(volumes.tail(50).mean())
	t_acc_days, _ = _count_accumulation_days(volumes, closes, t_vol_50avg, 50)
	t_dist_days, _ = _count_distribution_days(volumes, closes, t_vol_50avg, 50)
	signals.append(
		{
			"signal": "Up-volume exceeds down-volume",
			"detected": vol_pattern == "accumulation",
			"detail": f"Up/Down volume ratio: {vol_ratio:.2f}, Acc days: {t_acc_days}, Dist days: {t_dist_days}",
		}
	)

	# 6. Price within 25% of 52-week high
	within_25_pct = current_price >= week52_high * 0.75
	signals.append(
		{
			"signal": "Price within 25% of 52-week high",
			"detected": within_25_pct,
			"detail": f"{((current_price / week52_high - 1) * 100):.1f}% from 52w high",
		}
	)

	# 7. RS improving (price outperforming market recently)
	try:
		spy_data = yf.Ticker("SPY").history(period="3mo")
		spy_return = (float(spy_data["Close"].iloc[-1]) / float(spy_data["Close"].iloc[0]) - 1) * 100
		stock_3m = closes.tail(63)
		stock_return = (float(stock_3m.iloc[-1]) / float(stock_3m.iloc[0]) - 1) * 100
		rs_improving = stock_return > spy_return
		rs_detail = f"Stock 3m: {stock_return:.1f}%, SPY 3m: {spy_return:.1f}%"
	except Exception:
		rs_improving = False
		rs_detail = "Unable to calculate"

	signals.append(
		{
			"signal": "Relative strength improving vs S&P 500",
			"detected": rs_improving,
			"detail": rs_detail,
		}
	)

	detected_count = sum(1 for s in signals if s["detected"])

	output_json(
		{
			"symbol": symbol,
			"date": str(data.index[-1].date()),
			"current_price": round(current_price, 2),
			"transition_type": "Stage 1 -> Stage 2",
			"signals": signals,
			"detected_count": detected_count,
			"total_signals": len(signals),
			"transition_strength": "strong" if detected_count >= 5 else "moderate" if detected_count >= 3 else "weak",
		}
	)


def main():
	parser = argparse.ArgumentParser(description="Minervini Stage Analysis (1-4)")
	sub = parser.add_subparsers(dest="command", required=True)

	sp = sub.add_parser("classify", help="Classify stock into Stage 1-4")
	sp.add_argument("symbol", help="Ticker symbol")
	sp.add_argument("--period", default="2y", help="Data period (default: 2y)")
	sp.set_defaults(func=cmd_classify)

	sp = sub.add_parser("transitions", help="Detect Stage 1->2 transition signals")
	sp.add_argument("symbol", help="Ticker symbol")
	sp.add_argument("--period", default="2y", help="Data period (default: 2y)")
	sp.set_defaults(func=cmd_transitions)

	args = parser.parse_args()
	args.func(args)


if __name__ == "__main__":
	main()
