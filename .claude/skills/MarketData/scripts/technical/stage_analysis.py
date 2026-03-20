#!/usr/bin/env python3
"""Minervini Stage Analysis: classify stocks into Stage 1-4 lifecycle phases.

Determines which of the four stock lifecycle stages a stock is currently in,
based on Mark Minervini's stage analysis framework from "Trade Like a Stock
Market Wizard" (Chapter 5). Each stage is scored using specific factor-based
criteria derived from Minervini's stage characteristics.

9 evidence measurements are computed for every stock (stage-agnostic). Each
evidence includes a value and thresholds string showing how it maps to each
stage's scoring rules, enabling full score traceability.

Commands:
	classify: Determine current stage (1-4) for a ticker
	transitions: Detect Stage 1->2 transition signals

Args:
	symbol (str): Ticker symbol (e.g., "AAPL", "NVDA", "META")
	--period (str): Historical data period (default: "2y")

Returns:
	For classify:
		dict: {
			"symbol": str,
			"date": str,
			"current_price": float,
			"stage": int,
			"scores": {"1": int, "2": int, ...},  # only non-zero stages
			"evidences": {
				"200ma_slope": {"value": float, "thresholds": str},
				"price_vs_200ma_pct": {"value": float, "thresholds": str},
				"trend_structure": {"value": {"higher_highs": bool, "higher_lows": bool}, "thresholds": str},
				"volume_balance": {"value": {"50d_ratio": float, "20d_ratio": float}, "thresholds": str},
				"volatility_regime": {"value": float, "thresholds": str},
				"ma_alignment": {"value": {"50>150": bool, "150>200": bool}, "thresholds": str},
				"decline_severity": {"value": float, "thresholds": str},
				"proximity_to_lows": {"value": float, "thresholds": str},
				"50ma_momentum": {"value": float, "thresholds": str}
			},
			"max_scores": "S1:80 | S2:95 | S3:90 | S4:100"
		}

	For transitions:
		dict: {
			"symbol": str,
			"date": str,
			"current_price": float,
			"transition_type": str,
			"signals": list,
			"detected_count": int,
			"total_signals": int,
			"transition_strength": str
		}

Example:
	>>> python stage_analysis.py classify NVDA --period 2y
	{
		"symbol": "NVDA",
		"date": "2026-03-18",
		"current_price": 135.50,
		"stage": 2,
		"scores": {"2": 80, "1": 25},
		"evidences": {
			"200ma_slope": {"value": 0.0312, "thresholds": "S1:|slope|<0.02->25 | S2:>0.02->15 | S3:-0.02~+0.02->15 | S4:<-0.02->20"},
			...
		},
		"max_scores": "S1:80 | S2:95 | S3:90 | S4:100"
	}

Use Cases:
	- Identify Stage 2 stocks for SEPA methodology entry
	- Detect Stage 2->3 transitions via evidence tracing
	- Filter out Stage 4 declining stocks
	- Monitor Stage 1->2 transitions for early entry

Notes:
	- Stage 2 (Advancing) is the only stage to buy in SEPA methodology
	- 9 evidences are always computed for every stock, regardless of winning stage
	- Each evidence has value + thresholds for full score traceability
	- Stage 2 wins ties (Minervini actionable stage preference)
	- Scoring factors derived from Minervini Chapter 5 stage characteristics
	- Higher highs/lows use swing point detection (5-bar confirmation)

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

# Theoretical maximum scores per stage (sum of all factor points)
_STAGE_THEORETICAL_MAX = {1: 80, 2: 95, 3: 90, 4: 100}


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


def _find_swing_points(series, confirmation_bars=5):
	"""Find swing highs and swing lows using N-bar confirmation.

	A swing high is a local maximum with confirmation_bars lower highs on each side.
	A swing low is a local minimum with confirmation_bars higher lows on each side.

	Returns (swing_highs, swing_lows) as lists of (index, value) tuples,
	sorted by index (chronological order).
	"""
	values = series.values.astype(float)
	n = len(values)
	swing_highs = []
	swing_lows = []

	for i in range(confirmation_bars, n - confirmation_bars):
		# Check swing high: values[i] >= all neighbors within confirmation_bars
		is_high = True
		for j in range(1, confirmation_bars + 1):
			if values[i] < values[i - j] or values[i] < values[i + j]:
				is_high = False
				break
		if is_high:
			swing_highs.append((i, float(values[i])))

		# Check swing low: values[i] <= all neighbors within confirmation_bars
		is_low = True
		for j in range(1, confirmation_bars + 1):
			if values[i] > values[i - j] or values[i] > values[i + j]:
				is_low = False
				break
		if is_low:
			swing_lows.append((i, float(values[i])))

	return swing_highs, swing_lows


def _higher_highs_higher_lows(highs, lows, window=20, count=3):
	"""Check for pattern of higher highs/lows and lower highs/lows using swing points.

	Uses 5-bar confirmation to find swing highs and swing lows.
	HH = True if last 2 swing highs are ascending.
	HL = True if last 2 swing lows are ascending.
	LH = True if last 2 swing highs are descending (Stage 4 downtrend).
	LL = True if last 2 swing lows are descending (Stage 4 downtrend).
	"""
	if len(highs) < window * count:
		return False, False, False, False, 0, 0

	swing_highs, _ = _find_swing_points(highs, confirmation_bars=5)
	_, swing_lows = _find_swing_points(lows, confirmation_bars=5)

	# HH: last 2 swing highs are ascending
	hh = False
	lh = False
	if len(swing_highs) >= 2:
		last_two_highs = swing_highs[-2:]
		hh = last_two_highs[1][1] > last_two_highs[0][1]
		lh = last_two_highs[1][1] < last_two_highs[0][1]

	# HL: last 2 swing lows are ascending
	hl = False
	ll = False
	if len(swing_lows) >= 2:
		last_two_lows = swing_lows[-2:]
		hl = last_two_lows[1][1] > last_two_lows[0][1]
		ll = last_two_lows[1][1] < last_two_lows[0][1]

	return hh, hl, lh, ll, len(swing_highs), len(swing_lows)


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


def _max_daily_decline_90d(closes):
	"""Find the largest single-day percentage decline in the last 90 trading days."""
	recent = closes.tail(90)
	daily_returns = recent.pct_change() * 100
	return float(daily_returns.min()) if len(daily_returns) > 1 else 0.0


def _rally_volume_spike_ratio(volumes, closes, lookback=50):
	"""Fraction of up-days with volume > 150% of 50-day average.

	High ratio = institutional buying on rallies (Stage 2 characteristic).
	"""
	if len(volumes) < lookback or len(closes) < lookback:
		return 0.0
	recent_vol = volumes.tail(lookback).values.astype(float)
	recent_ret = closes.tail(lookback).pct_change().values
	avg_vol = float(volumes.tail(50).mean())
	if avg_vol <= 0:
		return 0.0

	up_mask = recent_ret > 0
	up_volumes = recent_vol[up_mask]
	if len(up_volumes) == 0:
		return 0.0

	spike_count = (up_volumes > avg_vol * 1.5).sum()
	return round(float(spike_count) / len(up_volumes), 3)


def _down_volume_spike_ratio(volumes, closes, lookback=50):
	"""Fraction of down-days with volume > 150% of 50-day average.

	High ratio = institutional selling on declines (Stage 4 characteristic).
	"""
	if len(volumes) < lookback or len(closes) < lookback:
		return 0.0
	recent_vol = volumes.tail(lookback).values.astype(float)
	recent_ret = closes.tail(lookback).pct_change().values
	avg_vol = float(volumes.tail(50).mean())
	if avg_vol <= 0:
		return 0.0

	down_mask = recent_ret < 0
	down_volumes = recent_vol[down_mask]
	if len(down_volumes) == 0:
		return 0.0

	spike_count = (down_volumes > avg_vol * 1.5).sum()
	return round(float(spike_count) / len(down_volumes), 3)


def _weekly_volume_bias(volumes, closes, weeks=10):
	"""Up-week volume / down-week volume ratio over recent weeks.

	> 1.2 = more volume on up weeks (Stage 2 accumulation).
	< 0.8 = more volume on down weeks (Stage 4 distribution).
	"""
	if len(volumes) < weeks * 5:
		return 1.0

	try:
		weekly_close = closes.resample("W").last().dropna()
		weekly_vol = volumes.resample("W").sum().dropna()

		# Align and take recent weeks
		min_len = min(len(weekly_close), len(weekly_vol))
		weekly_close = weekly_close.tail(min(weeks, min_len))
		weekly_vol = weekly_vol.tail(min(weeks, min_len))

		weekly_returns = weekly_close.pct_change().dropna()
		weekly_vol = weekly_vol.iloc[-len(weekly_returns):]

		up_weeks_vol = float(weekly_vol[weekly_returns > 0].sum())
		down_weeks_vol = float(weekly_vol[weekly_returns <= 0].sum())

		if down_weeks_vol == 0:
			return 2.0
		return round(up_weeks_vol / down_weeks_vol, 3)
	except Exception:
		return 1.0


def _compute_all_scores(metrics):
	"""Compute all 9 evidence measurements and apply each stage's scoring rules.

	Args:
		metrics: dict with all pre-computed technical measurements

	Returns:
		(scores_dict, evidences_dict) where:
		- scores_dict: {1: int, 2: int, 3: int, 4: int}
		- evidences_dict: 9-field dict with value + thresholds per evidence
	"""
	sma200_slope = metrics["sma200_slope"]
	sma50_slope = metrics["sma50_slope"]
	price_distance_200ma_pct = metrics["price_distance_200ma_pct"]
	hh = metrics["hh"]
	hl = metrics["hl"]
	lh = metrics["lh"]
	ll = metrics["ll"]
	vol_ratio = metrics["vol_ratio"]
	vol_ratio_20d = metrics["vol_ratio_20d"]
	volatility_ratio = metrics["volatility_ratio"]
	c_sma50 = metrics["c_sma50"]
	c_sma150 = metrics["c_sma150"]
	c_sma200 = metrics["c_sma200"]
	current_price = metrics["current_price"]
	max_daily_decline = metrics["max_daily_decline_90d"]
	pct_above_52w_low = metrics["pct_above_52w_low"]
	largest_decline = metrics["largest_decline"]
	vol_50avg = metrics["vol_50avg"]
	vol_200avg = metrics["vol_200avg"]
	rally_spike = metrics["rally_spike_ratio"]
	down_spike = metrics["down_spike_ratio"]
	weekly_bias = metrics["weekly_volume_bias"]

	# Build evidences (stage-agnostic, 11 fields)
	# Each evidence: value + unit + thresholds (§2.8 Self-Documenting Output)
	evidences = {
		"200ma_slope": {
			"value": round(sma200_slope, 4),
			"unit": "%/day",
			"thresholds": {
				"S1": "flat (|slope|<0.02) = 25pts",
				"S2": "rising (>0.02) = 15pts",
				"S3": "rolling (-0.02~+0.02) = 15pts",
				"S4": "declining (<-0.02) = 20pts",
			},
		},
		"price_vs_200ma_pct": {
			"value": round(price_distance_200ma_pct, 1),
			"unit": "% distance from 200MA",
			"thresholds": {
				"S1": "near 200MA (within ±5%) = 20pts",
				"S2": "above 200MA = 5pts",
				"S3": "oscillating near 200MA (within ±10%) = 15pts",
				"S4": "below 200MA = 15pts",
			},
		},
		"trend_structure": {
			"value": {"higher_highs": hh, "higher_lows": hl, "lower_highs": lh, "lower_lows": ll},
			"unit": "boolean flags (5-bar swing confirmation)",
			"thresholds": {
				"S1": "no HH and no HL = 10pts",
				"S2": "HH and HL = 20pts",
				"S3": "not HH (lost uptrend) = 15pts",
				"S4": "LH and LL, or (no HH+HL and decline>20%) = 15pts",
			},
		},
		"volume_balance": {
			"value": {"updown_50d": round(vol_ratio, 3), "updown_20d": round(vol_ratio_20d, 3)},
			"unit": "up-day vol / down-day vol",
			"thresholds": {
				"S1": "50d avg vol < 70% of 200d avg = 15pts",
				"S2": "ratio > 1.15 (accumulation) = 10pts",
				"S3": "ratio 0.85~1.15 (neutral) = 15pts",
				"S4": "ratio < 0.85 (distribution) = 10pts",
			},
		},
		"volatility_regime": {
			"value": round(volatility_ratio, 2),
			"unit": "ATR30 / ATR90",
			"thresholds": {
				"S1": "low volatility (<1.2) = 10pts",
				"S3": "expanding volatility (>1.2) = 20pts",
			},
		},
		"ma_alignment": {
			"value": {"50>150": c_sma50 > c_sma150, "150>200": c_sma150 > c_sma200},
			"unit": "boolean flags",
			"thresholds": {
				"S2": "bullish stack (50>150>200) = 20pts",
				"S4": "bearish (50<150 or price<150 and price<200) = 20pts",
			},
		},
		"decline_severity": {
			"value": round(max_daily_decline, 1),
			"unit": "% (max single-day decline in last 90 trading days)",
			"thresholds": {
				"S3": "severe daily drop (>5%) = 10pts",
			},
		},
		"proximity_to_lows": {
			"value": round(pct_above_52w_low, 1),
			"unit": "% above 52-week low",
			"thresholds": {
				"S2": "rallied 25%+ from lows = 5pts",
				"S4": "near 52w low (within 20%) = 15pts",
			},
		},
		"50ma_momentum": {
			"value": round(sma50_slope, 4),
			"unit": "%/day",
			"thresholds": {
				"S2": "rising (slope>0) = 10pts",
			},
		},
		"rally_volume_spike": {
			"value": {"up_spike_ratio": rally_spike, "down_spike_ratio": down_spike},
			"unit": "fraction of up/down days with vol > 150% of 50d avg",
			"thresholds": {
				"S2": "up-day spikes > 20% frequency = 5pts",
				"S4": "down-day spikes > 20% frequency = 5pts",
			},
		},
		"weekly_volume_bias": {
			"value": round(weekly_bias, 3),
			"unit": "up-week vol / down-week vol",
			"thresholds": {
				"S2": "up-week dominant (>1.2) = 5pts",
				"S4": "down-week dominant (<0.8) = 5pts",
			},
		},
	}

	# Score each stage
	scores = {1: 0, 2: 0, 3: 0, 4: 0}

	# --- Stage 1 (Consolidation) — max 80 ---
	if abs(sma200_slope) < 0.02:
		scores[1] += 25
	if abs(price_distance_200ma_pct) < 5:
		scores[1] += 20
	if vol_200avg > 0 and vol_50avg < vol_200avg * 0.7:
		scores[1] += 15
	if not hh and not hl:
		scores[1] += 10
	if volatility_ratio < 1.2:
		scores[1] += 10

	# --- Stage 2 (Advancing) — max 95 ---
	# above_200ma -> 5 (reduced: MA stacking already implies this)
	if price_distance_200ma_pct > 0:
		scores[2] += 5
	# 200ma_slope > 0.02 -> 15
	if sma200_slope > 0.02:
		scores[2] += 15
	# 50>150>200 -> 20
	if c_sma50 > c_sma150 > c_sma200:
		scores[2] += 20
	# hh and hl -> 20
	if hh and hl:
		scores[2] += 20
	# accumulation_volume (up/down ratio) -> 10 (reduced: rally_spike shares role)
	if vol_ratio > 1.15:
		scores[2] += 10
	# 50ma_slope > 0 -> 10
	if sma50_slope > 0:
		scores[2] += 10
	# NEW: rally_from_lows — 25%+ above 52w low -> 5
	if pct_above_52w_low >= 25:
		scores[2] += 5
	# NEW: rally_volume_spike — up-day spikes > 20% frequency -> 5
	if rally_spike > 0.20:
		scores[2] += 5
	# NEW: weekly_volume_bias > 1.2 -> 5
	if weekly_bias > 1.2:
		scores[2] += 5

	# --- Stage 3 (Topping) — max 90 ---
	if volatility_ratio > 1.2:
		scores[3] += 20
	if -0.02 <= sma200_slope <= 0.02:
		scores[3] += 15
	# FIX: ±15% -> ±10% (stock 14% above 200MA is Stage 2, not oscillating)
	if abs(price_distance_200ma_pct) < 10:
		scores[3] += 15
	if 0.85 <= vol_ratio <= 1.15:
		scores[3] += 15
	# not hh (lost uptrend) -> 15
	# Caveat: cannot distinguish "lost HH" from "never had HH" — other factors
	# (200MA slope, volatility, price position) mitigate Stage 1 vs Stage 3 confusion
	if not hh:
		scores[3] += 15
	if max_daily_decline < -5:
		scores[3] += 10

	# --- Stage 4 (Declining) — max 100 ---
	if price_distance_200ma_pct < 0:
		scores[4] += 15
	if sma200_slope < -0.02:
		scores[4] += 20
	if (c_sma50 < c_sma150) or (current_price < c_sma150 and current_price < c_sma200):
		scores[4] += 20
	if pct_above_52w_low < 20:
		scores[4] += 15
	# FIX: Check for actual downtrend structure (LH & LL) OR fallback
	if (lh and ll) or (not hh and not hl and largest_decline < -20):
		scores[4] += 15
	if vol_ratio < 0.85:
		scores[4] += 10
	# NEW: distribution spike on down-days -> 5
	if down_spike > 0.20:
		scores[4] += 5

	return scores, evidences


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
	sma200_slope = _ma_slope(sma200, lookback=40)
	sma50_slope = _ma_slope(sma50, lookback=20)
	hh, hl, lh, ll, _, _ = _higher_highs_higher_lows(highs, lows)
	_, vol_ratio = _volume_trend(volumes, closes)

	# Volume averages
	vol_50avg = float(volumes.tail(50).mean())
	vol_200avg = float(volumes.tail(200).mean()) if len(volumes) >= 200 else vol_50avg

	# 20-day Up/Down volume ratio
	vol_ratio_20d, _, _ = _calc_up_down_ratio(volumes, closes, 20)

	# Volatility ratio (30-day vs 90-day ATR)
	tr = np.maximum(
		highs.values - lows.values,
		np.maximum(
			np.abs(highs.values - np.roll(closes.values, 1)),
			np.abs(lows.values - np.roll(closes.values, 1)),
		),
	)
	atr_30 = float(np.mean(tr[-30:])) if len(tr) >= 30 else 0
	atr_90 = float(np.mean(tr[-90:])) if len(tr) >= 90 else atr_30
	volatility_ratio = round(atr_30 / atr_90, 2) if atr_90 > 0 else 0.0

	# Price distance from 200MA
	price_distance_200ma_pct = (current_price / c_sma200 - 1) * 100

	# Largest decline since Stage 2 start
	largest_decline = _largest_decline_since_start(closes, sma200)

	# Max single-day decline in last 90 days
	max_daily_decline = _max_daily_decline_90d(closes)

	# Proximity to 52-week low
	week52_low = float(lows.tail(252).min()) if len(lows) >= 252 else float(lows.min())
	pct_above_52w_low = (current_price / week52_low - 1) * 100 if week52_low > 0 else 0.0

	# New metrics: volume spike ratios and weekly bias
	rally_spike = _rally_volume_spike_ratio(volumes, closes)
	down_spike = _down_volume_spike_ratio(volumes, closes)
	weekly_bias = _weekly_volume_bias(volumes, closes)

	# Build metrics dict for scoring
	metrics = {
		"sma200_slope": sma200_slope,
		"sma50_slope": sma50_slope,
		"price_distance_200ma_pct": price_distance_200ma_pct,
		"hh": hh,
		"hl": hl,
		"lh": lh,
		"ll": ll,
		"vol_ratio": vol_ratio,
		"vol_ratio_20d": vol_ratio_20d,
		"volatility_ratio": volatility_ratio,
		"c_sma50": c_sma50,
		"c_sma150": c_sma150,
		"c_sma200": c_sma200,
		"current_price": current_price,
		"max_daily_decline_90d": max_daily_decline,
		"pct_above_52w_low": pct_above_52w_low,
		"largest_decline": largest_decline,
		"vol_50avg": vol_50avg,
		"vol_200avg": vol_200avg,
		"rally_spike_ratio": rally_spike,
		"down_spike_ratio": down_spike,
		"weekly_volume_bias": weekly_bias,
	}

	scores, evidences = _compute_all_scores(metrics)

	# Determine stage with highest score (Stage 2 wins ties -- Minervini actionable stage)
	max_score = max(scores.values())
	tied_stages = [s for s, v in scores.items() if v == max_score]
	winning_stage = 2 if 2 in tied_stages else min(tied_stages)

	# Build output: only non-zero scores
	non_zero_scores = {str(k): v for k, v in scores.items() if v > 0}

	output_json(
		{
			"symbol": symbol,
			"date": date_str,
			"current_price": round(current_price, 2),
			"stage": winning_stage,
			"scores": non_zero_scores,
			"evidences": evidences,
			"max_scores": "S1:80 | S2:95 | S3:90 | S4:100",
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
	hh, hl, _, _, _, _ = _higher_highs_higher_lows(highs, lows, window=20, count=3)
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
