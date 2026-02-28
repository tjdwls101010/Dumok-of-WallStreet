#!/usr/bin/env python3
"""Volatility Contraction Pattern (VCP) detection for Minervini SEPA methodology.

Detects VCP formations where price corrections progressively tighten, indicating
decreasing selling pressure and potential breakout setup. Identifies pattern type,
contraction ratios, pivot price, technical footprint notation, Cup & Handle,
Power Play, shakeout grading, and setup readiness scoring.

Commands:
		detect: Scan for VCP pattern in a ticker's recent price action

Args:
		symbol (str): Ticker symbol (e.g., "AAPL", "NVDA", "META")
		--period (str): Historical data period (default: "1y")
		--min-contractions (int): Minimum number of contractions required (default: 2)
		--interval (str): Data interval: "1d" (daily, default) or "1wk" (weekly)

Returns:
		dict: {
		"symbol": str,
		"interval": str,  # "1d" or "1wk"
		"vcp_detected": bool,
		"contractions_count": int,
		"contraction_ratios": [float],
		"contraction_ratio_grades": [str],  # ideal/acceptable/poor per ratio
		"base_duration_weeks": int,
		"correction_depths": [float],
		"pivot_price": float,
		"technical_footprint": str,
		"pattern_type": str,
		"pattern_quality": str,
		"first_correction_zone": str,  # shallow/constructive_shallow/constructive/deep_acceptable/excessive
		"setup_readiness": {
				"score": float,  # 0-100 composite
				"classification": str  # prime/actionable/developing/early/weak
		},
		"cup_and_handle": {
				"detected": bool,
				"cup_depth_pct": float,
				"shape": str,  # u_shape/moderate/v_shape
				"handle_depth_pct": float,
				"quality": str  # textbook/acceptable/flawed
		},
		"cup_completion_cheat": {
				"detected": bool,
				"cup_peak_price": float,
				"cup_bottom_price": float,
				"recovery_pct": float,  # how much recovered from bottom toward peak (33-50% ideal)
				"pause_range_pct": float,  # price range of pause zone
				"pause_duration_days": int,
				"pause_volume_dryup": bool,
				"has_shakeout_in_pause": bool,
				"entry_price": float,  # pause high + 0.1%
				"quality": str  # textbook/acceptable/marginal
		},
		"relative_correction": {
				"stock_correction_pct": float,  # first contraction depth
				"spy_correction_pct": float,  # SPY decline in same period
				"ratio": float,  # stock/spy ratio
				"excessive_relative": bool  # True if ratio > 2.5
		},
		"power_play": {
				"detected": bool,
				"gap_pct": float,
				"gap_volume_ratio": float,
				"consolidation_range_pct": float,
				"quality": str  # textbook/acceptable/marginal
		},
		"shakeout": {
				"count": int,
				"has_constructive_shakeout": bool,
				"shakeout_quality_score": float,  # 0-10
				"shakeouts_detail": [{
						"date": str,
						"location": str,
						"grade": str,  # constructive/neutral/destructive
						"duration_below_days": int,
						"recovery_volume_ratio": float,
						"reclaimed_support": bool
				}]
		},
		"time_symmetry": {
				"left_side_days": int,
				"right_side_days": int,
				"symmetry_ratio": float,
				"time_compressed": bool,
				"right_side_quality": str
		},
		"demand_evidence": {
				"right_side_up_spikes": int,
				"left_side_down_spikes": int,
				"demand_dominance": bool,
				"post_shakeout_demand": bool
		},
		"pivot_tightness": {
				"atr_ratio": float,
				"max_close_change_5d_pct": float,
				"pre_pivot_volume_percentile": float,
				"is_tight": bool
		},
		"volume": {
				"contraction_vol_declining": bool,
				"contraction_vol_strongly_declining": bool,
				"contraction_vol_ratios": [float],
				"contraction_avg_volumes": [int],
				"pivot_area_dryup": bool,
				"pivot_vol_vs_base_pct": float,
				"vol_50d_avg": int,
				"current_vol": int,
				"current_vs_avg_pct": float,
				"breakout_vol_target_min": int,
				"breakout_vol_target_ideal": int,
				"volume_confirmation": str
		}
		}

Example:
		>>> python vcp.py detect NVDA --period 1y
		{
		"symbol": "NVDA",
		"vcp_detected": true,
		"contractions_count": 3,
		"contraction_ratios": [0.52, 0.48],
		"contraction_ratio_grades": ["ideal", "ideal"],
		"base_duration_weeks": 12,
		"correction_depths": [18.5, 9.6, 4.6],
		"pivot_price": 142.30,
		"technical_footprint": "12W 19/10/5 3T",
		"pattern_type": "Cup with Handle",
		"pattern_quality": "high",
		"first_correction_zone": "constructive",
		"setup_readiness": {"score": 78.5, "classification": "actionable"}
		}

Use Cases:
		- Identify optimal entry points in Stage 2 uptrends
		- Evaluate base quality before breakout
		- Calculate pivot price for buy point determination
		- Assess pattern reliability based on contraction quality
		- Detect Cup & Handle and Power Play patterns independently
		- Score setup readiness (0-100) for actionability ranking

Notes:
		- VCP requires progressively smaller corrections (each ~50% of prior)
		- 2-6 contractions is typical range
		- 10-35% initial correction is constructive; 60%+ suggests failure
		- Pivot price is the high of the last contraction
		- Technical footprint: "XW Y/Z/... NT" = X weeks, Y%/Z%/... corrections, N tightenings
		- Pattern types: Cup with Handle, Progressive 3T, Power Play, Flat Base
		- Volume should decline across successive contractions (supply drying up)
		- Breakout volume: minimum 25% above 50-day avg, ideal 100-200%
		- volume_confirmation grades: strongly_confirmed > confirmed > supportive > neutral > suspect > divergent
		- breakout_volume_confirmed requires up-close on 125%+ volume within 2% of pivot
		- divergent volume (rising across contractions) caps pattern_quality at "low"
		- Shakeout grades: constructive (<=3 days + volume surge), neutral, destructive (>=5 days, no surge)
		- Constructive shakeout can upgrade quality moderate->high; destructive can downgrade high->moderate
		- Cup & Handle: U-shaped cup (12-35% depth), handle (<50% of cup depth)
		- 3C (Cup Completion Cheat): earliest cup recovery entry (33-50% recovery, pause, dryup)
		- Power Play: gap-up (3%+) on high volume (1.5x+), tight consolidation (<7%)
		- relative_correction: first correction depth vs SPY; ratio > 2.5 = excessive
		- Setup readiness: prime(80+) / actionable(60-79) / developing(40-59) / early(20-39) / weak(0-19)
		- Time symmetry: right_side_quality grades base recovery speed (constructive > compressed > v_shape)
		- Demand evidence: compares volume spikes on up-days (right side) vs down-days (left side)
		- Pivot tightness: ATR ratio < 0.5 AND volume percentile < 30 = tight pivot (highest reliability)
		- Weekly mode: 3-bar swing window (vs 5-bar daily), 26-bar minimum data

See Also:
		- base_count.py: Track base number within Stage 2 advance
		- volume_analysis.py: Volume confirmation for breakout validation
		- trend_template.py: Verify stock passes Trend Template before VCP entry
		- pocket_pivot.py: Alternative entry via pocket pivot volume signals
		- low_cheat.py: Lower-risk entry below pivot price
		- tight_closes.py: Tight close cluster detection for supply dryup
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import numpy as np
import yfinance as yf
from utils import output_json, safe_run


def _find_swing_points(highs, lows, closes, window=5):
	"""Identify swing highs and swing lows in price data.

	A swing high is a high that is higher than `window` bars on each side.
	A swing low is a low that is lower than `window` bars on each side.
	"""
	swing_highs = []
	swing_lows = []

	highs_arr = highs.values.astype(float)
	lows_arr = lows.values.astype(float)

	for i in range(window, len(highs_arr) - window):
		# Swing high
		if all(highs_arr[i] >= highs_arr[i - j] for j in range(1, window + 1)) and all(
			highs_arr[i] >= highs_arr[i + j] for j in range(1, window + 1)
		):
			swing_highs.append((i, highs_arr[i]))

		# Swing low
		if all(lows_arr[i] <= lows_arr[i - j] for j in range(1, window + 1)) and all(
			lows_arr[i] <= lows_arr[i + j] for j in range(1, window + 1)
		):
			swing_lows.append((i, lows_arr[i]))

	return swing_highs, swing_lows


def _detect_contractions(swing_highs, swing_lows, closes):
	"""Detect VCP contractions from swing points.

	A contraction is measured as the decline from a swing high to the next swing low,
	expressed as a percentage.
	"""
	if not swing_highs or not swing_lows:
		return []

	contractions = []
	used_lows = set()

	for h_idx, h_price in swing_highs:
		# Find the nearest swing low after this high
		best_low = None
		for l_idx, l_price in swing_lows:
			if l_idx > h_idx and l_idx not in used_lows:
				best_low = (l_idx, l_price)
				break

		if best_low is not None:
			l_idx, l_price = best_low
			depth_pct = (h_price - l_price) / h_price * 100
			if depth_pct > 2:  # Minimum 2% to count as a contraction
				contractions.append(
					{
						"high_idx": h_idx,
						"high_price": round(h_price, 2),
						"low_idx": l_idx,
						"low_price": round(l_price, 2),
						"depth_pct": round(depth_pct, 2),
					}
				)
				used_lows.add(l_idx)

	return contractions


def _classify_pattern(contractions, base_weeks, overall_depth):
	"""Classify the VCP base pattern type."""
	if not contractions:
		return "No Pattern"

	depth = contractions[0]["depth_pct"] if contractions else 0
	num_contractions = len(contractions)

	# Cup with Handle: deep initial correction (15-35%), followed by handle (5-15%)
	if depth >= 15 and depth <= 35 and num_contractions >= 2 and base_weeks >= 7:
		last_depth = contractions[-1]["depth_pct"]
		if last_depth < depth * 0.5:
			return "Cup with Handle"

	# Progressive 3T: 3 contractions with verified progressive tightening
	if num_contractions == 3:
		depths = [c["depth_pct"] for c in contractions]
		if all(depths[i] < depths[i - 1] for i in range(1, len(depths))):
			return "Progressive 3T"

	# Power Play: short, shallow base (< 4 weeks, < 20% correction)
	if base_weeks <= 4 and depth < 20:
		return "Power Play"

	# Flat Base: shallow correction (< 15%), extended duration
	if depth < 15 and base_weeks >= 5:
		return "Flat Base"

	# High Tight Flag: > 100% gain in 4-8 weeks, then < 25% correction
	if depth < 25 and base_weeks <= 6:
		return "High Tight Flag"

	return "Standard VCP"


def _analyze_contraction_volume(volumes, contractions):
	"""Analyze volume behavior across successive VCP contractions.

	For each contraction, calculates the average daily volume across the
	high-to-low span. Computes volume ratios between successive contractions
	to determine if volume is declining (supply drying up).
	"""
	vol_arr = volumes.values.astype(float)
	avg_volumes = []
	for c in contractions:
		start = c["high_idx"]
		end = c["low_idx"]
		span = end - start
		if span < 3:
			continue
		seg = vol_arr[start : end + 1]
		avg_volumes.append(round(float(np.mean(seg))))

	vol_ratios = []
	for i in range(1, len(avg_volumes)):
		if avg_volumes[i - 1] > 0:
			vol_ratios.append(round(avg_volumes[i] / avg_volumes[i - 1], 3))

	declining = len(vol_ratios) > 0 and all(r < 1.0 for r in vol_ratios)
	strongly_declining = len(vol_ratios) > 0 and all(r < 0.75 for r in vol_ratios)

	return {
		"avg_volumes": avg_volumes,
		"vol_ratios": vol_ratios,
		"declining": declining,
		"strongly_declining": strongly_declining,
	}


def _check_volume_dryup(volumes, base_start_idx, pivot_idx, lookback=10):
	"""Check if volume dries up near the pivot relative to the full base.

	Compares average volume in the pivot area (last ``lookback`` days before
	the pivot) against the average volume across the entire base formation.
	"""
	vol_arr = volumes.values.astype(float)

	pivot_start = max(base_start_idx, pivot_idx - lookback)
	pivot_area = vol_arr[pivot_start : pivot_idx + 1]
	base_area = vol_arr[base_start_idx : pivot_idx + 1]

	if len(pivot_area) == 0 or len(base_area) == 0:
		return {
			"dryup_detected": False,
			"pivot_area_avg_vol": 0,
			"base_avg_vol": 0,
			"ratio_pct": 100.0,
		}

	pivot_avg = float(np.mean(pivot_area))
	base_avg = float(np.mean(base_area))
	ratio_pct = round(pivot_avg / base_avg * 100, 1) if base_avg > 0 else 100.0

	return {
		"dryup_detected": ratio_pct < 70.0,
		"pivot_area_avg_vol": round(pivot_avg),
		"base_avg_vol": round(base_avg),
		"ratio_pct": ratio_pct,
	}


def _assess_breakout_volume(volumes, closes, pivot_price=None):
	"""Calculate current volume metrics relative to 50-day average.

	Provides breakout volume targets per Minervini's guidelines:
	minimum 125% of 50-day average, ideal 200%+.  Also checks whether
	any of the last 5 trading days had an up-close on breakout-level
	volume (>= 125% of 50-day average) near the pivot price (within 2%).
	"""
	vol_arr = volumes.values.astype(float)
	close_arr = closes.values.astype(float)
	vol_50d_avg = float(np.mean(vol_arr[-50:])) if len(vol_arr) >= 50 else float(np.mean(vol_arr))
	current_vol = float(vol_arr[-1])
	current_vs_avg_pct = round(current_vol / vol_50d_avg * 100, 1) if vol_50d_avg > 0 else 0.0

	# Check last 5 days for breakout-level volume on an up day near the pivot
	breakout_confirmed = False
	if len(vol_arr) >= 6 and len(close_arr) >= 6:
		for i in range(-5, 0):
			price_up = close_arr[i] > close_arr[i - 1]
			vol_above = vol_arr[i] >= vol_50d_avg * 1.25
			near_pivot = close_arr[i] >= pivot_price * 0.98 if pivot_price else True
			if price_up and vol_above and near_pivot:
				breakout_confirmed = True
				break

	return {
		"vol_50d_avg": round(vol_50d_avg),
		"current_vol": round(current_vol),
		"current_vs_avg_pct": current_vs_avg_pct,
		"breakout_target_min": round(vol_50d_avg * 1.25),
		"breakout_target_ideal": round(vol_50d_avg * 2.0),
		"breakout_volume_confirmed": breakout_confirmed,
	}


def _detect_shakeouts(lows, closes, volumes, swing_lows, contractions, vol_50d_avg):
	"""Detect shakeout events within the base formation with grading.

	A shakeout occurs when price undercuts a prior swing low then recovers
	quickly on above-average volume, trapping weak holders before the real
	advance.  Per Minervini (p.214): "you want to see one or more price
	shakeouts at certain key points during the base-building period."

	Each shakeout is graded as constructive, neutral, or destructive based on
	recovery speed, volume surge, and location within the base.
	"""
	location_weights = {"pivot_area": 3, "right_side": 2, "handle": 2, "base_bottom": 1}
	grade_multipliers = {"constructive": 1.0, "neutral": 0.5, "destructive": 0.0}

	if not contractions or not swing_lows:
		return {
			"count": 0,
			"has_constructive_shakeout": False,
			"last_shakeout_date": None,
			"last_shakeout_location": None,
			"last_shakeout_recovery_volume_surge": False,
			"shakeout_quality_score": 0,
			"shakeouts_detail": [],
		}

	lows_arr = lows.values.astype(float)
	close_arr = closes.values.astype(float)
	vol_arr = volumes.values.astype(float)
	dates = lows.index

	base_start = contractions[0]["high_idx"]
	base_end = contractions[-1]["low_idx"]
	base_mid = (base_start + base_end) // 2
	pivot_zone_start = max(base_start, base_end - 15)

	shakeouts = []
	for i, (sl_idx, sl_price) in enumerate(swing_lows):
		if sl_idx < base_start or sl_idx > base_end:
			continue
		# Check if a subsequent low undercuts this swing low
		for j in range(sl_idx + 1, min(sl_idx + 20, len(lows_arr))):
			if j > base_end + 10:
				break
			if lows_arr[j] < sl_price:
				# Undercut detected -- measure recovery
				recovered = False
				surge = False
				duration_below = 0
				recovery_vol_ratio = 0.0
				reclaimed = False

				for k in range(j, min(j + 20, len(lows_arr))):
					if close_arr[k] < sl_price:
						duration_below += 1
					else:
						reclaimed = True
						if k > j:
							recovery_vol_ratio = round(vol_arr[k] / vol_50d_avg, 2) if vol_50d_avg > 0 else 0.0
							surge = recovery_vol_ratio >= 1.5
						recovered = True
						break

				if recovered:
					if sl_idx >= pivot_zone_start:
						loc = "pivot_area"
					elif sl_idx >= base_mid:
						loc = "right_side"
					elif sl_idx <= base_start + (base_mid - base_start) // 3:
						loc = "base_bottom"
					else:
						loc = "handle"

					# Grade: constructive / neutral / destructive
					if duration_below <= 3 and surge:
						grade = "constructive"
					elif duration_below >= 5 or (duration_below >= 3 and not surge):
						grade = "destructive"
					else:
						grade = "neutral"

					shakeouts.append(
						{
							"idx": j,
							"date": str(dates[j].date()) if j < len(dates) else None,
							"location": loc,
							"volume_surge": surge,
							"duration_below_days": duration_below,
							"recovery_volume_ratio": recovery_vol_ratio,
							"reclaimed_support": reclaimed,
							"grade": grade,
						}
					)
				break  # only count one undercut per swing low

	# Shakeout quality score (0-10)
	raw_score = 0
	for s in shakeouts:
		loc_w = location_weights.get(s["location"], 1)
		grade_m = grade_multipliers.get(s["grade"], 0.5)
		raw_score += loc_w * grade_m
	shakeout_quality_score = min(10, round(raw_score, 1))

	last = shakeouts[-1] if shakeouts else None
	has_constructive = any(s["grade"] == "constructive" for s in shakeouts)
	return {
		"count": len(shakeouts),
		"has_constructive_shakeout": has_constructive,
		"last_shakeout_date": last["date"] if last else None,
		"last_shakeout_location": last["location"] if last else None,
		"last_shakeout_recovery_volume_surge": last["volume_surge"] if last else False,
		"shakeout_quality_score": shakeout_quality_score,
		"shakeouts_detail": [
			{
				"date": s["date"],
				"location": s["location"],
				"grade": s["grade"],
				"duration_below_days": s["duration_below_days"],
				"recovery_volume_ratio": s["recovery_volume_ratio"],
				"reclaimed_support": s["reclaimed_support"],
			}
			for s in shakeouts
		],
	}


def _detect_time_symmetry(contractions):
	"""Assess left-side vs right-side time symmetry of the base.

	Per Minervini (p.212): "If a stock advances too quickly up the right
	side, this forms a hazardous time compression."  A V-shaped recovery
	is less reliable than a gradual, constructive right side.
	"""
	if not contractions:
		return {
			"left_side_days": 0,
			"right_side_days": 0,
			"symmetry_ratio": 0.0,
			"time_compressed": False,
			"right_side_quality": "constructive",
		}

	base_high_idx = contractions[0]["high_idx"]
	base_low_idx = min(c["low_idx"] for c in contractions)
	pivot_idx = contractions[-1]["high_idx"]

	left_side_days = max(1, base_low_idx - base_high_idx)
	right_side_days = max(1, pivot_idx - base_low_idx)
	ratio = round(right_side_days / left_side_days, 2)

	compressed = ratio < 0.3
	v_shape = right_side_days < 10 and left_side_days > 20

	if v_shape:
		quality = "v_shape"
	elif compressed:
		quality = "compressed"
	else:
		quality = "constructive"

	return {
		"left_side_days": left_side_days,
		"right_side_days": right_side_days,
		"symmetry_ratio": ratio,
		"time_compressed": compressed or v_shape,
		"right_side_quality": quality,
	}


def _detect_demand_evidence(closes, volumes, contractions, shakeout_result, vol_50d_avg):
	"""Detect demand evidence on the right side of the base.

	Per Minervini (p.219): "Look for significant, above-average increases
	in volume on upward moves coming off the lows and up the right side
	of the base."  Compares volume spikes on up-days (right side) vs
	down-days (left side) to gauge institutional demand.
	"""
	if not contractions:
		return {
			"right_side_up_spikes": 0,
			"left_side_down_spikes": 0,
			"demand_dominance": False,
			"post_shakeout_demand": False,
		}

	close_arr = closes.values.astype(float)
	vol_arr = volumes.values.astype(float)
	spike_threshold = vol_50d_avg * 1.5

	base_low_idx = min(c["low_idx"] for c in contractions)
	base_start = contractions[0]["high_idx"]
	base_end = contractions[-1]["low_idx"]

	# Left side: base_start to base_low -- count volume spikes on down-days
	left_down_spikes = 0
	for i in range(base_start + 1, min(base_low_idx + 1, len(close_arr))):
		if close_arr[i] < close_arr[i - 1] and vol_arr[i] >= spike_threshold:
			left_down_spikes += 1

	# Right side: base_low to base_end -- count volume spikes on up-days
	right_up_spikes = 0
	for i in range(base_low_idx + 1, min(base_end + 1, len(close_arr))):
		if close_arr[i] > close_arr[i - 1] and vol_arr[i] >= spike_threshold:
			right_up_spikes += 1

	demand_dominance = right_up_spikes > left_down_spikes

	# Post-shakeout demand: 1.5x+ volume up-day within 3 days after last shakeout
	post_shakeout_demand = False
	if shakeout_result.get("has_constructive_shakeout"):
		last_date = shakeout_result.get("last_shakeout_date")
		if last_date:
			dates = closes.index
			date_strs = [str(d.date()) for d in dates]
			if last_date in date_strs:
				shake_idx = date_strs.index(last_date)
				for k in range(shake_idx + 1, min(shake_idx + 4, len(close_arr))):
					if close_arr[k] > close_arr[k - 1] and vol_arr[k] >= spike_threshold:
						post_shakeout_demand = True
						break

	return {
		"right_side_up_spikes": right_up_spikes,
		"left_side_down_spikes": left_down_spikes,
		"demand_dominance": demand_dominance,
		"post_shakeout_demand": post_shakeout_demand,
	}


def _check_pivot_tightness(highs, lows, closes, volumes, pivot_idx, base_start_idx):
	"""Evaluate price and volume tightness near the pivot area.

	Per Minervini (p.203): "Tightness in price from absolute highs to lows
	and tight closes with little change in price from one day to the next."
	Tight, low-volume pivots produce more reliable breakouts.
	"""
	high_arr = highs.values.astype(float)
	low_arr = lows.values.astype(float)
	close_arr = closes.values.astype(float)
	vol_arr = volumes.values.astype(float)

	if pivot_idx < 5 or pivot_idx >= len(close_arr):
		return {
			"atr_ratio": None,
			"max_close_change_5d_pct": None,
			"pre_pivot_volume_percentile": None,
			"is_tight": False,
		}

	# 5-day ATR near pivot
	pivot_start = max(0, pivot_idx - 4)
	pivot_ranges = high_arr[pivot_start : pivot_idx + 1] - low_arr[pivot_start : pivot_idx + 1]
	atr_5d = float(np.mean(pivot_ranges))

	# 50-day ATR baseline (or full base if shorter)
	baseline_start = max(0, pivot_idx - 49)
	baseline_ranges = high_arr[baseline_start : pivot_idx + 1] - low_arr[baseline_start : pivot_idx + 1]
	atr_baseline = float(np.mean(baseline_ranges)) if len(baseline_ranges) > 0 else atr_5d
	atr_ratio = round(atr_5d / atr_baseline, 2) if atr_baseline > 0 else 1.0

	# Max close-to-close change in last 5 days (%)
	max_cc_change = 0.0
	for i in range(pivot_start + 1, pivot_idx + 1):
		if close_arr[i - 1] > 0:
			change = abs(close_arr[i] - close_arr[i - 1]) / close_arr[i - 1] * 100
			max_cc_change = max(max_cc_change, change)
	max_cc_change = round(max_cc_change, 2)

	# Pre-pivot volume percentile (5-day avg ranked within base rolling windows)
	pivot_vol_avg = float(np.mean(vol_arr[pivot_start : pivot_idx + 1]))
	base_span = pivot_idx - base_start_idx
	if base_span >= 10:
		window_avgs = []
		for w in range(base_start_idx, pivot_idx - 4):
			window_avgs.append(float(np.mean(vol_arr[w : w + 5])))
		if window_avgs:
			rank = sum(1 for v in window_avgs if v <= pivot_vol_avg)
			percentile = round(rank / len(window_avgs) * 100, 1)
		else:
			percentile = 50.0
	else:
		percentile = 50.0

	is_tight = atr_ratio < 0.5 and percentile < 30

	return {
		"atr_ratio": atr_ratio,
		"max_close_change_5d_pct": max_cc_change,
		"pre_pivot_volume_percentile": percentile,
		"is_tight": is_tight,
	}


def _detect_cup_and_handle(highs, lows, closes, volumes, vol_50d_avg):
	"""Detect Cup & Handle pattern independently.

	Identifies a U-shaped cup formation followed by a handle consolidation.
	Cup depth 12-35% ideal (up to 50% acceptable), handle depth < 50% of cup,
	and declining volume during handle.
	"""
	high_arr = highs.values.astype(float)
	low_arr = lows.values.astype(float)
	close_arr = closes.values.astype(float)
	vol_arr = volumes.values.astype(float)
	n = len(close_arr)

	if n < 60:
		return {"detected": False, "reason": "insufficient_data"}

	# Find left rim: highest high in data (excluding last 20 bars for handle space)
	search_end = max(20, n - 20)
	left_rim_idx = int(np.argmax(high_arr[:search_end]))
	left_rim_price = high_arr[left_rim_idx]

	# Find cup bottom: lowest low after left rim, at least 15 bars in
	cup_search_start = left_rim_idx + 10
	if cup_search_start >= n - 15:
		return {"detected": False, "reason": "no_room_for_cup"}

	cup_bottom_idx = cup_search_start + int(np.argmin(low_arr[cup_search_start : n - 10]))
	cup_bottom_price = low_arr[cup_bottom_idx]

	# Cup depth validation
	cup_depth_pct = round((left_rim_price - cup_bottom_price) / left_rim_price * 100, 2)
	if cup_depth_pct < 8 or cup_depth_pct > 50:
		return {"detected": False, "reason": f"cup_depth_{cup_depth_pct}pct_out_of_range"}

	# Shape assessment (U vs V): divide cup into thirds
	cup_length = cup_bottom_idx - left_rim_idx
	if cup_length < 15:
		return {"detected": False, "reason": "cup_too_short"}

	third = cup_length // 3
	middle_start = left_rim_idx + third
	middle_end = left_rim_idx + 2 * third
	middle_avg = float(np.mean(close_arr[middle_start:middle_end]))

	# Linear interpolation between rim and bottom at middle
	interp_price = left_rim_price - (left_rim_price - cup_bottom_price) * 0.5
	shape_ratio = (
		round(abs(middle_avg - interp_price) / (left_rim_price - cup_bottom_price), 2)
		if (left_rim_price - cup_bottom_price) > 0
		else 0
	)

	if shape_ratio < 0.15:
		shape = "v_shape"
	elif shape_ratio > 0.3:
		shape = "u_shape"
	else:
		shape = "moderate"

	# Right rim recovery: find where price returns near left rim level (within 5%)
	right_rim_idx = None
	for i in range(cup_bottom_idx + 5, n):
		if close_arr[i] >= left_rim_price * 0.95:
			right_rim_idx = i
			break

	if right_rim_idx is None:
		return {"detected": False, "reason": "right_rim_not_recovered"}

	# Handle detection: 5-25 day consolidation after right rim recovery
	handle_start = right_rim_idx
	handle_end = min(handle_start + 25, n - 1)
	handle_bars = handle_end - handle_start

	if handle_bars < 5:
		return {"detected": False, "reason": "no_handle_room"}

	handle_data = close_arr[handle_start : handle_end + 1]
	handle_high = float(np.max(handle_data))
	handle_low = float(np.min(handle_data))
	handle_depth_pct = round((handle_high - handle_low) / handle_high * 100, 2)

	# Handle depth < 50% of cup depth
	if handle_depth_pct > cup_depth_pct * 0.5:
		return {"detected": False, "reason": "handle_too_deep"}

	# Handle low should be in upper third of cup range
	cup_range = left_rim_price - cup_bottom_price
	upper_third_threshold = cup_bottom_price + cup_range * (2 / 3)
	handle_low_ok = handle_low >= upper_third_threshold

	# Volume declining during handle
	handle_vols = vol_arr[handle_start : handle_end + 1]
	if len(handle_vols) >= 4:
		first_half_vol = float(np.mean(handle_vols[: len(handle_vols) // 2]))
		second_half_vol = float(np.mean(handle_vols[len(handle_vols) // 2 :]))
		handle_vol_declining = second_half_vol < first_half_vol
	else:
		handle_vol_declining = True

	# Quality assessment
	ideal_depth = 12 <= cup_depth_pct <= 35
	if (
		ideal_depth
		and shape == "u_shape"
		and handle_low_ok
		and handle_vol_declining
		and handle_depth_pct < cup_depth_pct * 0.33
	):
		quality = "textbook"
	elif cup_depth_pct <= 50 and handle_low_ok and (handle_vol_declining or shape != "v_shape"):
		quality = "acceptable"
	else:
		quality = "flawed"

	return {
		"detected": True,
		"left_rim_price": round(left_rim_price, 2),
		"cup_bottom_price": round(cup_bottom_price, 2),
		"cup_depth_pct": cup_depth_pct,
		"cup_length_days": cup_length,
		"shape": shape,
		"shape_ratio": shape_ratio,
		"handle_depth_pct": handle_depth_pct,
		"handle_days": handle_bars,
		"handle_low_in_upper_third": handle_low_ok,
		"handle_volume_declining": handle_vol_declining,
		"quality": quality,
	}


def _detect_power_play(opens, highs, closes, volumes, vol_50d_avg):
	"""Detect Power Play pattern independently.

	A Power Play occurs when a stock gaps up on high volume then consolidates
	tightly.  The pivot is the highest high during the post-gap consolidation.
	"""
	open_arr = opens.values.astype(float)
	high_arr = highs.values.astype(float)
	close_arr = closes.values.astype(float)
	vol_arr = volumes.values.astype(float)
	n = len(close_arr)

	if n < 30:
		return {"detected": False, "reason": "insufficient_data"}

	# Scan for gap-up days in the last 60 bars
	scan_start = max(0, n - 60)
	best_gap = None

	for i in range(scan_start + 1, n - 5):
		gap_pct = (open_arr[i] - close_arr[i - 1]) / close_arr[i - 1] * 100
		vol_ratio = vol_arr[i] / vol_50d_avg if vol_50d_avg > 0 else 0

		if gap_pct >= 3.0 and vol_ratio >= 1.5:
			# Check post-gap consolidation (5-20 days)
			consol_end = min(i + 21, n)
			consol_bars = consol_end - (i + 1)
			if consol_bars < 5:
				continue

			consol_closes = close_arr[i + 1 : consol_end]
			consol_highs = high_arr[i + 1 : consol_end]
			consol_vols = vol_arr[i + 1 : consol_end]

			if len(consol_closes) < 5:
				continue

			consol_range_pct = round(
				(float(np.max(consol_closes)) - float(np.min(consol_closes))) / float(np.min(consol_closes)) * 100, 2
			)

			# Volume contracting during consolidation
			if len(consol_vols) >= 4:
				first_half = float(np.mean(consol_vols[: len(consol_vols) // 2]))
				second_half = float(np.mean(consol_vols[len(consol_vols) // 2 :]))
				vol_contracting = second_half < first_half
			else:
				vol_contracting = True

			if consol_range_pct <= 7.0 and vol_contracting:
				pivot = round(float(np.max(consol_highs)), 2)
				# Prefer the strongest gap
				if best_gap is None or gap_pct > best_gap["gap_pct"]:
					best_gap = {
						"gap_day_idx": i,
						"gap_pct": round(gap_pct, 2),
						"gap_volume_ratio": round(vol_ratio, 2),
						"consolidation_days": consol_bars,
						"consolidation_range_pct": consol_range_pct,
						"volume_contracting": vol_contracting,
						"pivot_price": pivot,
					}

	if best_gap is None:
		return {"detected": False, "reason": "no_qualifying_gap_up_consolidation"}

	# Quality assessment
	gp = best_gap["gap_pct"]
	vr = best_gap["gap_volume_ratio"]
	cr = best_gap["consolidation_range_pct"]

	if gp >= 5.0 and vr >= 2.0 and cr < 4.0:
		quality = "textbook"
	elif gp >= 3.0 and vr >= 1.5 and cr <= 7.0:
		quality = "acceptable"
	else:
		quality = "marginal"

	dates = closes.index
	gap_idx = best_gap["gap_day_idx"]
	best_gap["gap_date"] = str(dates[gap_idx].date()) if gap_idx < len(dates) else None
	best_gap["quality"] = quality
	best_gap["detected"] = True
	return best_gap


def _detect_3c_entry(closes, highs, lows, volumes, vol_50d_avg):
	"""Detect 3C (Cup Completion Cheat) entry point in cup formation recovery.

	The 3C entry is the earliest actionable entry within a forming cup pattern,
	occurring when the stock has recovered 33-50% from the cup bottom toward
	the peak, then pauses in a tight range on declining volume.

	Returns:
		dict: Detection result with cup geometry, recovery metrics, pause
		characteristics, and entry price.  If not detected, returns
		{"detected": False, "reason": "..."}.

	Notes:
		- Cup depth must be 15-50% to qualify
		- Recovery of 33-50% from bottom toward peak is ideal
		- Pause zone: 3-12% range lasting at least 5 days
		- Volume dryup in pause zone (below 80% of 50-day avg) confirms supply exhaustion
		- Shakeout within pause upgrades quality to textbook

	Example:
		>>> result = _detect_3c_entry(closes, highs, lows, volumes, vol_50d_avg)
		>>> result["detected"]
		True
	"""
	close_arr = closes.values.astype(float)
	high_arr = highs.values.astype(float)
	low_arr = lows.values.astype(float)
	vol_arr = volumes.values.astype(float)
	n = len(close_arr)

	if n < 60:
		return {"detected": False, "reason": "insufficient_data"}

	# Step 1: Cup formation detection
	# Find peak (highest high excluding last 20 bars)
	search_end = max(20, n - 20)
	peak_idx = int(np.argmax(high_arr[:search_end]))
	peak_price = high_arr[peak_idx]

	# Find cup bottom (lowest low after peak)
	if peak_idx + 5 >= n:
		return {"detected": False, "reason": "no_room_after_peak"}

	bottom_idx = peak_idx + int(np.argmin(low_arr[peak_idx:]))
	bottom_price = low_arr[bottom_idx]

	# Cup depth validation (15-50%)
	if peak_price <= 0:
		return {"detected": False, "reason": "invalid_peak_price"}

	cup_depth_pct = (peak_price - bottom_price) / peak_price * 100
	if cup_depth_pct < 15 or cup_depth_pct > 50:
		return {"detected": False, "reason": f"cup_depth_{round(cup_depth_pct, 1)}pct_out_of_range"}

	# Step 2: Recovery position (33-50% from bottom toward peak)
	cup_range = peak_price - bottom_price
	recovery_amount = close_arr[-1] - bottom_price
	recovery_pct = (recovery_amount / cup_range * 100) if cup_range > 0 else 0

	if recovery_pct < 25 or recovery_pct > 60:
		return {"detected": False, "reason": f"recovery_{round(recovery_pct, 1)}pct_outside_acceptable_range"}

	# Step 3: Pause/Plateau detection in last 30 bars
	pause_lookback = min(30, n - 1)
	pause_segment = close_arr[-pause_lookback:]
	pause_high = float(np.max(pause_segment))
	pause_low = float(np.min(pause_segment))
	pause_range_pct = (pause_high - pause_low) / pause_low * 100 if pause_low > 0 else 999

	if pause_range_pct < 3 or pause_range_pct > 12:
		return {"detected": False, "reason": f"pause_range_{round(pause_range_pct, 1)}pct_outside_3_12_range"}

	# Calculate pause duration (consecutive days within the range)
	pause_duration = 0
	for i in range(len(pause_segment) - 1, -1, -1):
		if pause_low <= pause_segment[i] <= pause_high:
			pause_duration += 1
		else:
			break

	if pause_duration < 5:
		return {"detected": False, "reason": f"pause_duration_{pause_duration}d_too_short"}

	# Step 4: Volume dryup in pause zone
	pause_vols = vol_arr[-pause_lookback:]
	pause_avg_vol = float(np.mean(pause_vols))
	pause_volume_dryup = pause_avg_vol < (vol_50d_avg * 0.80) if vol_50d_avg > 0 else False

	# Step 5: Shakeout bonus (undercut then recovery of pause low)
	has_shakeout = False
	for i in range(1, len(pause_segment)):
		if pause_segment[i] < pause_low * 0.995:
			# Check if it recovered above pause_low within 3 days
			for j in range(i + 1, min(i + 4, len(pause_segment))):
				if pause_segment[j] >= pause_low:
					has_shakeout = True
					break
			if has_shakeout:
				break

	# Step 6: Entry price
	entry_price = round(pause_high * 1.001, 2)

	# Quality assessment
	ideal_recovery = 33 <= recovery_pct <= 50
	ideal_range = 5 <= pause_range_pct <= 8
	wide_recovery = 25 <= recovery_pct <= 60
	wide_range = 3 <= pause_range_pct <= 12

	if ideal_recovery and ideal_range and pause_volume_dryup and has_shakeout:
		quality = "textbook"
	elif wide_recovery and wide_range and pause_volume_dryup:
		quality = "acceptable"
	else:
		quality = "marginal"

	return {
		"detected": True,
		"cup_peak_price": round(float(peak_price), 2),
		"cup_bottom_price": round(float(bottom_price), 2),
		"recovery_pct": round(recovery_pct, 1),
		"pause_range_pct": round(pause_range_pct, 1),
		"pause_duration_days": pause_duration,
		"pause_volume_dryup": pause_volume_dryup,
		"has_shakeout_in_pause": has_shakeout,
		"entry_price": entry_price,
		"quality": quality,
	}


def _volume_confirmation_grade(contraction_vol, dryup):
	"""Synthesize contraction volume analysis and dryup into a single grade.

	Returns one of: strongly_confirmed, confirmed, supportive, neutral,
	suspect, divergent.
	"""
	vol_declining = contraction_vol["declining"]
	vol_strongly = contraction_vol["strongly_declining"]
	vol_ratios = contraction_vol["vol_ratios"]
	dryup_detected = dryup["dryup_detected"]

	# divergent: volume increasing each contraction
	if len(vol_ratios) > 0 and all(r > 1.0 for r in vol_ratios):
		return "divergent"

	# suspect: volume mostly rising
	if len(vol_ratios) > 0 and sum(1 for r in vol_ratios if r > 1.0) > len(vol_ratios) / 2:
		return "suspect"

	# strongly_confirmed: strongly declining contraction volume AND dryup
	if vol_strongly and dryup_detected:
		return "strongly_confirmed"

	# confirmed: declining contraction volume AND dryup detected
	if vol_declining and dryup_detected:
		return "confirmed"

	# supportive: one of the two present
	if vol_declining or dryup_detected:
		return "supportive"

	return "neutral"


def _grade_contraction_ratios(contraction_ratios):
	"""Grade each contraction ratio individually.

	ideal: 0.4-0.6, acceptable: 0.3-0.75, poor: outside range.
	"""
	grades = []
	for r in contraction_ratios:
		if 0.4 <= r <= 0.6:
			grades.append("ideal")
		elif 0.3 <= r <= 0.75:
			grades.append("acceptable")
		else:
			grades.append("poor")
	return grades


def _classify_first_correction(depth_pct):
	"""Classify the first correction depth zone.

	shallow: <10%, constructive_shallow: 10-15%, constructive: 15-25%,
	deep_acceptable: 25-35%, excessive: >35%.
	"""
	if depth_pct < 10:
		return "shallow"
	elif depth_pct < 15:
		return "constructive_shallow"
	elif depth_pct <= 25:
		return "constructive"
	elif depth_pct <= 35:
		return "deep_acceptable"
	else:
		return "excessive"


def _calculate_setup_readiness(
	contraction_ratios,
	vol_grade,
	pivot_tightness,
	shakeout,
	time_symmetry,
	demand_evidence,
	cup_handle,
	power_play,
):
	"""Calculate VCP setup readiness composite score (0-100).

	Components:
	- Contraction quality (0-25)
	- Volume confirmation (0-20)
	- Pivot tightness (0-15)
	- Shakeout quality (0-15)
	- Time symmetry (0-10)
	- Demand evidence (0-10)
	- Pattern type bonus (0-5)
	"""
	score = 0

	# Contraction quality (0-25)
	if contraction_ratios:
		ideal_count = sum(1 for r in contraction_ratios if 0.4 <= r <= 0.6)
		acceptable_count = sum(1 for r in contraction_ratios if 0.3 <= r <= 0.75)
		ratio_pct = (ideal_count * 1.0 + (acceptable_count - ideal_count) * 0.6) / len(contraction_ratios)
		score += round(ratio_pct * 25, 1)

	# Volume confirmation (0-20)
	vol_scores = {
		"strongly_confirmed": 20,
		"confirmed": 16,
		"supportive": 12,
		"neutral": 8,
		"suspect": 4,
		"divergent": 0,
	}
	score += vol_scores.get(vol_grade, 8)

	# Pivot tightness (0-15)
	if pivot_tightness.get("is_tight"):
		score += 15
	elif pivot_tightness.get("atr_ratio") is not None:
		atr = pivot_tightness["atr_ratio"]
		if atr < 0.7:
			score += 10
		elif atr < 1.0:
			score += 5

	# Shakeout quality (0-15)
	sq = shakeout.get("shakeout_quality_score", 0)
	score += min(15, round(sq * 1.5, 1))

	# Time symmetry (0-10)
	ts_quality = time_symmetry.get("right_side_quality", "constructive")
	if ts_quality == "constructive":
		score += 10
	elif ts_quality == "compressed":
		score += 5
	else:
		score += 2

	# Demand evidence (0-10)
	if demand_evidence.get("demand_dominance"):
		score += 7
	if demand_evidence.get("post_shakeout_demand"):
		score += 3

	# Pattern type bonus (0-5)
	if cup_handle.get("detected") and cup_handle.get("quality") == "textbook":
		score += 5
	elif cup_handle.get("detected"):
		score += 3
	if power_play.get("detected") and power_play.get("quality") == "textbook":
		score += 5
	elif power_play.get("detected"):
		score += 3

	score = min(100, round(score, 1))

	# Classification
	if score >= 80:
		classification = "prime"
	elif score >= 60:
		classification = "actionable"
	elif score >= 40:
		classification = "developing"
	elif score >= 20:
		classification = "early"
	else:
		classification = "weak"

	return {"score": score, "classification": classification}


@safe_run
def cmd_detect(args):
	"""Detect VCP pattern in a ticker's price data."""
	symbol = args.symbol.upper()
	ticker = yf.Ticker(symbol)
	data = ticker.history(period=args.period, interval=args.interval)

	if args.interval == "1wk":
		swing_window = 3  # 3 weekly bars (~3 weeks)
		min_data_points = 26  # ~6 months weekly
	else:
		swing_window = 5
		min_data_points = 60

	if data.empty or len(data) < min_data_points:
		output_json(
			{
				"error": f"Insufficient data for {symbol}. Need at least {min_data_points} trading days.",
				"data_points": len(data),
			}
		)
		return

	closes = data["Close"]
	highs = data["High"]
	lows = data["Low"]
	volumes = data["Volume"]
	current_price = float(closes.iloc[-1])

	# Find swing points
	swing_highs, swing_lows = _find_swing_points(highs, lows, closes, window=swing_window)

	# Detect contractions
	contractions = _detect_contractions(swing_highs, swing_lows, closes)

	# Filter: only use recent contractions (within the base formation)
	# Look back from the highest recent swing high
	if contractions:
		# Find the highest swing high as the base start
		max_high = max(contractions, key=lambda c: c["high_price"])
		max_high_idx = contractions.index(max_high)
		# Use contractions from the highest point onward
		relevant_contractions = contractions[max_high_idx:]
	else:
		relevant_contractions = []

	# Check for progressive tightening
	correction_depths = [c["depth_pct"] for c in relevant_contractions]
	contraction_ratios = []
	is_tightening = True

	for i in range(1, len(correction_depths)):
		if correction_depths[i - 1] > 0:
			ratio = correction_depths[i] / correction_depths[i - 1]
			contraction_ratios.append(round(ratio, 2))
			if ratio >= 1.0:
				is_tightening = False

	# VCP detection criteria
	vcp_detected = (
		len(relevant_contractions) >= args.min_contractions
		and is_tightening
		and correction_depths[0] <= 60  # First correction not too deep
	)

	# Volume analysis (contraction volume; breakout volume computed after pivot)
	contraction_vol = _analyze_contraction_volume(volumes, relevant_contractions)

	# Classify failure pattern when VCP not detected
	failure_pattern = None
	if not is_tightening and len(correction_depths) >= 2:
		if correction_depths[-1] > correction_depths[-2]:
			failure_pattern = "distribution_pattern"
		else:
			failure_pattern = "inconclusive"

	# Base duration in weeks
	if relevant_contractions:
		start_idx = relevant_contractions[0]["high_idx"]
		end_idx = relevant_contractions[-1]["low_idx"]
		base_days = end_idx - start_idx
		base_weeks = max(1, base_days // 5)
	else:
		base_weeks = 0

	# Pivot price (high of the last contraction or recent resistance)
	if relevant_contractions:
		pivot_price = relevant_contractions[-1]["high_price"]
		pivot_idx = relevant_contractions[-1]["high_idx"]
	else:
		pivot_price = float(highs.tail(20).max())
		pivot_idx = len(closes) - 1

	# Breakout volume (pivot-aware: checks proximity to pivot price)
	breakout_vol = _assess_breakout_volume(volumes, closes, pivot_price=pivot_price)

	# Volume dryup near pivot (adaptive lookback scales with base duration)
	base_start = relevant_contractions[0]["high_idx"] if relevant_contractions else 0
	dryup_base_span = pivot_idx - base_start if relevant_contractions else 0
	dryup_lookback = max(10, dryup_base_span // 10)
	dryup = _check_volume_dryup(volumes, base_start, pivot_idx, lookback=dryup_lookback)

	# Volume confirmation grade
	vol_grade = _volume_confirmation_grade(contraction_vol, dryup)

	# Volume divergence as additional failure pattern
	if vol_grade == "divergent" and failure_pattern is None:
		failure_pattern = "volume_divergence"

	# Shakeout detection
	shakeout = _detect_shakeouts(lows, closes, volumes, swing_lows, relevant_contractions, breakout_vol["vol_50d_avg"])

	# Time symmetry / compression
	time_symmetry = _detect_time_symmetry(relevant_contractions)

	# Demand evidence (depends on shakeout result)
	demand_evidence = _detect_demand_evidence(
		closes, volumes, relevant_contractions, shakeout, breakout_vol["vol_50d_avg"]
	)

	# Pivot tightness
	pivot_tightness = _check_pivot_tightness(highs, lows, closes, volumes, pivot_idx, base_start)

	# Cup & Handle detection
	cup_handle = _detect_cup_and_handle(highs, lows, closes, volumes, breakout_vol["vol_50d_avg"])

	# Cup Completion Cheat (3C) entry detection
	cup_completion_cheat = _detect_3c_entry(closes, highs, lows, volumes, breakout_vol["vol_50d_avg"])

	# Power Play detection
	opens = data["Open"]
	power_play = _detect_power_play(opens, highs, closes, volumes, breakout_vol["vol_50d_avg"])

	# Contraction ratio grades
	ratio_grades = _grade_contraction_ratios(contraction_ratios)

	# Technical footprint notation: "XW Y/Z/... NT"
	if correction_depths:
		depths_str = "/".join(str(int(round(d))) for d in correction_depths)
		footprint = f"{base_weeks}W {depths_str} {len(relevant_contractions)}T"
	else:
		footprint = "N/A"

	# Pattern classification
	overall_depth = correction_depths[0] if correction_depths else 0
	pattern_type = _classify_pattern(relevant_contractions, base_weeks, overall_depth)

	# First correction zone classification
	first_correction_zone = _classify_first_correction(overall_depth)

	# Relative correction comparison vs SPY
	relative_correction = {"stock_correction_pct": 0, "spy_correction_pct": 0, "ratio": 0, "excessive_relative": False}
	if relevant_contractions:
		first_c = relevant_contractions[0]
		stock_corr = first_c["depth_pct"]
		try:
			spy_data = yf.Ticker("SPY").history(period=args.period, interval=args.interval)
			if not spy_data.empty and len(spy_data) >= len(data):
				# Map stock contraction indices to SPY data
				spy_closes = spy_data["Close"].values.astype(float)
				c_high_idx = first_c["high_idx"]
				c_low_idx = first_c["low_idx"]
				if c_high_idx < len(spy_closes) and c_low_idx < len(spy_closes):
					spy_high = float(np.max(spy_closes[c_high_idx : c_low_idx + 1]))
					spy_low = float(np.min(spy_closes[c_high_idx : c_low_idx + 1]))
					spy_corr = round((spy_high - spy_low) / spy_high * 100, 2) if spy_high > 0 else 0
					ratio = round(stock_corr / spy_corr, 2) if spy_corr > 0 else 0
					relative_correction = {
						"stock_correction_pct": round(stock_corr, 2),
						"spy_correction_pct": spy_corr,
						"ratio": ratio,
						"excessive_relative": ratio > 2.5,
					}
		except Exception:
			pass

	# Pattern quality assessment (volume-adjusted, shakeout-adjusted)
	if vcp_detected:
		if all(r <= 0.6 for r in contraction_ratios) and len(relevant_contractions) >= 3:
			quality = "high"
		elif all(r <= 0.75 for r in contraction_ratios):
			quality = "moderate"
		else:
			quality = "low"
		# Volume caps quality
		if vol_grade == "divergent":
			quality = "low"
		elif vol_grade == "suspect" and quality == "high":
			quality = "moderate"
		# Shakeout adjustment
		has_constructive = any(s.get("grade") == "constructive" for s in shakeout.get("shakeouts_detail", []))
		has_destructive = any(s.get("grade") == "destructive" for s in shakeout.get("shakeouts_detail", []))
		if has_constructive and quality == "moderate":
			quality = "high"
		if has_destructive and quality == "high":
			quality = "moderate"
	else:
		quality = "none"

	# Setup readiness composite score
	setup_readiness = _calculate_setup_readiness(
		contraction_ratios,
		vol_grade,
		pivot_tightness,
		shakeout,
		time_symmetry,
		demand_evidence,
		cup_handle,
		power_play,
	)

	output_json(
		{
			"symbol": symbol,
			"date": str(data.index[-1].date()),
			"interval": args.interval,
			"current_price": round(current_price, 2),
			"vcp_detected": vcp_detected,
			"contractions_count": len(relevant_contractions),
			"contraction_ratios": contraction_ratios,
			"contraction_ratio_grades": ratio_grades,
			"correction_depths": correction_depths,
			"base_duration_weeks": base_weeks,
			"pivot_price": round(pivot_price, 2),
			"technical_footprint": footprint,
			"pattern_type": pattern_type,
			"pattern_quality": quality,
			"is_tightening": is_tightening,
			"failure_pattern": failure_pattern,
			"first_correction_pct": round(overall_depth, 1),
			"first_correction_zone": first_correction_zone,
			"relative_correction": relative_correction,
			"setup_readiness": setup_readiness,
			"contractions_detail": relevant_contractions,
			"cup_and_handle": cup_handle,
			"cup_completion_cheat": cup_completion_cheat,
			"power_play": power_play,
			"shakeout": shakeout,
			"time_symmetry": time_symmetry,
			"demand_evidence": demand_evidence,
			"pivot_tightness": pivot_tightness,
			"volume": {
				"contraction_vol_declining": contraction_vol["declining"],
				"contraction_vol_strongly_declining": contraction_vol["strongly_declining"],
				"contraction_vol_ratios": contraction_vol["vol_ratios"],
				"contraction_avg_volumes": contraction_vol["avg_volumes"],
				"pivot_area_dryup": dryup["dryup_detected"],
				"pivot_vol_vs_base_pct": dryup["ratio_pct"],
				"vol_50d_avg": breakout_vol["vol_50d_avg"],
				"current_vol": breakout_vol["current_vol"],
				"current_vs_avg_pct": breakout_vol["current_vs_avg_pct"],
				"breakout_vol_target_min": breakout_vol["breakout_target_min"],
				"breakout_vol_target_ideal": breakout_vol["breakout_target_ideal"],
				"breakout_volume_confirmed": breakout_vol["breakout_volume_confirmed"],
				"volume_confirmation": vol_grade,
			},
		}
	)


def main():
	parser = argparse.ArgumentParser(description="Volatility Contraction Pattern (VCP) Detection")
	sub = parser.add_subparsers(dest="command", required=True)

	sp = sub.add_parser("detect", help="Detect VCP pattern for a ticker")
	sp.add_argument("symbol", help="Ticker symbol")
	sp.add_argument("--period", default="1y", help="Data period (default: 1y)")
	sp.add_argument(
		"--interval", default="1d", choices=["1d", "1wk"], help="Data interval: 1d (daily, default) or 1wk (weekly)"
	)
	sp.add_argument("--min-contractions", type=int, default=2, help="Minimum contractions (default: 2)")
	sp.set_defaults(func=cmd_detect)

	args = parser.parse_args()
	args.func(args)


if __name__ == "__main__":
	main()
