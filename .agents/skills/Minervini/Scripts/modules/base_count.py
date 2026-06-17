#!/usr/bin/env python3
"""Base Counting: track base number within a Stage 2 advance.

Identifies and counts price bases (consolidation patterns) that form during
a stock's Stage 2 uptrend. Each base represents a distinct "step" in the
advance — the stock must make a meaningful new high (15%+ above prior
breakout) before a new pullback counts as a separate base.

Based on Minervini Chapter 10: bases are pauses within an uptrend where
supply is absorbed, forming VCP-like consolidation patterns before the
next advance.

Commands:
	count: Count bases and assess current base stage for a ticker

Args:
	symbol (str): Ticker symbol (e.g., "AAPL", "NVDA", "META")
	--period (str): Historical data period (default: "2y")
	--min-base-weeks (int): Minimum weeks for a formation to count as base (default: 3)

Returns:
	dict: {
		"current_base_number": int,
		"forming_base": dict|null,
		"base_history": [...],
		"cross_base_analysis": {"correction_trend": str, "depths": [float]},
		"risk_level": str,
		"base_count_reset_detected": bool,
		"thresholds": {...}
	}

Use Cases:
	- Determine if a stock is in early (base 1-2) or late (base 4+) stage
	- Adjust position sizing based on base number risk
	- Detect deepening corrections across bases (exhaustion signal)
	- Identify reset events that restart the base count

Notes:
	- Base 1-2: Most reliable breakouts, largest average gains
	- Base 3: Still tradeable but less reliable
	- Base 4+: Late stage, higher failure rate, smaller average gains
	- Base count resets to 1 when a fresh cycle begins after a Stage 4 decline (30+ of 40 days below 200MA)
	- Each new base's high must exceed the prior breakout (a higher step); no fixed % advance is required by the method
	- Correction depth ceiling is keyed to base length: <=3wk ->25%, <=25wk ->35%, >25wk ->50%; 60% is the absolute redline
	- Cross-base analysis: deepening corrections = late-stage exhaustion

See Also:
	- vcp.py: VCP detection within individual bases
	- stage_analysis.py: Stage classification for context
	- volume_analysis.py: Volume patterns during base formation
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import numpy as np
import yfinance as yf
from utils import output_json, safe_run, calculate_sma, max_constructive_depth_pct

# ── Constants ──────────────────────────────────────────────────────────
# A new base's high need only EXCEED the prior breakout (a higher step in the
# advance). The old fixed "15% above prior breakout" gate was not in the method —
# it's structure that separates bases, not a magic percentage. Kept as a knob
# (default 0 = off) for an analyst who wants to demand bigger steps; that is a
# non-canonical tightening, not Minervini's rule.
MIN_ADVANCE_PCT = 0.0     # New base high must exceed prior breakout (off = 0)
MIN_CORRECTION_PCT = 8.0  # Min correction depth to count as a base at all
REDLINE_DEPTH_PCT = 60.0  # Absolute redline — any base deeper than this fails outright
SWING_HIGH_WINDOW = 20    # Days to look back/forward for swing high (CLI: --swing-window)
MAX_BASE_WEEKS = 65       # Max base duration / breakout search horizon (CLI: --max-base-weeks)
FORMING_RECENCY_DAYS = 60  # A still-unbroken base counts as "forming" only if its low is this recent (CLI: --forming-recency-days)
RESET_WINDOW = 40         # Rolling window for reset detection (CLI: --reset-window)
RESET_THRESHOLD = 30      # Days below 200MA within window to trigger reset (CLI: --reset-days)
# Duration-keyed constructive depth ceiling lives in utils (max_constructive_depth_pct),
# shared with vcp so the two modules cannot drift apart on the spec rule.
# Relative-correction severity band: avoid a base falling >2–3x the market's own decline.
REL_CORRECTION_NORMAL_RATIO = 2.0    # <=2x SPY's drop = normal
REL_CORRECTION_ELEVATED_RATIO = 3.0  # <=3x = elevated; above = excessive


def _is_swing_high(highs_arr, idx, window=SWING_HIGH_WINDOW):
	"""Check if idx is a swing high within a symmetric window.

	A swing high is the highest point in a window of 2*window days
	centered on idx. This filters out minor peaks.
	"""
	start = max(0, idx - window)
	end = min(len(highs_arr), idx + window + 1)

	if end - start < window:  # Not enough data
		return False

	return highs_arr[idx] == np.max(highs_arr[start:end])


def _find_bases(closes, highs, lows, sma200, min_base_weeks=3,
				swing_window=SWING_HIGH_WINDOW, max_base_days=MAX_BASE_WEEKS * 5,
				forming_recency_days=FORMING_RECENCY_DAYS, min_advance_pct=MIN_ADVANCE_PCT):
	"""Identify bases within a Stage 2 advance.

	A base is a distinct step in the stock's advance:
	1. Stock must be above 200MA (Stage 2)
	2. A significant swing high forms (swing_window-day window)
	3. For base 2+: high must exceed the prior breakout (a higher step)
	4. Price corrects at least 8%, within the duration-keyed depth ceiling
	5. Price breaks out above the high (base complete)

	Returns:
		(list of completed bases, forming_base or None)
	"""
	closes_arr = closes.values.astype(float)
	highs_arr = highs.values.astype(float)
	lows_arr = lows.values.astype(float)
	sma200_arr = sma200.values.astype(float)
	dates = closes.index
	n = len(closes_arr)

	min_base_days = min_base_weeks * 5
	completed_bases = []
	forming_base = None
	last_breakout_price = 0.0

	i = 0
	while i < n - min_base_days:
		# Must be above 200MA (Stage 2)
		if np.isnan(sma200_arr[i]) or closes_arr[i] < sma200_arr[i]:
			i += 1
			continue

		# Check for swing high
		if not _is_swing_high(highs_arr, i, swing_window):
			i += 1
			continue

		base_high = highs_arr[i]
		base_start_idx = i

		# For base 2+: require minimum advance from prior breakout
		if last_breakout_price > 0:
			advance_pct = (base_high - last_breakout_price) / last_breakout_price * 100
			if advance_pct < min_advance_pct:
				i += 1
				continue

		# Find pullback low after the swing high
		search_end = min(i + max_base_days, n)
		if search_end <= i + min_base_days:
			i += 1
			continue

		# Find the lowest low in the base period
		segment_lows = lows_arr[i:search_end]
		low_offset = np.argmin(segment_lows)
		base_low_idx = i + low_offset
		base_low = lows_arr[base_low_idx]

		# Check correction depth
		correction_depth = (base_high - base_low) / base_high * 100

		if correction_depth < MIN_CORRECTION_PCT:
			# Too shallow — not a real base, skip past this high
			i += swing_window
			continue

		if correction_depth > REDLINE_DEPTH_PCT:
			# Past the absolute redline — failed outright, regardless of duration.
			# The duration-keyed constructive ceiling is applied below, once the
			# base's length is known.
			i += swing_window
			continue

		# Find breakout: close above base_high after the low
		breakout_idx = None
		for k in range(base_low_idx + 1, min(base_low_idx + max_base_days, n)):
			if closes_arr[k] > base_high:
				breakout_idx = k
				break

		if breakout_idx is None:
			# No breakout found — check if base is still forming
			duration_days = n - 1 - base_start_idx
			duration_weeks = max(1, duration_days // 5)
			if duration_weeks >= min_base_weeks and base_low_idx > n - forming_recency_days:
				# Recent base, still forming
				forming_base = {
					"start_date": str(dates[base_start_idx].date()),
					"duration_weeks": duration_weeks,
					"correction_depth_pct": round(correction_depth, 1),
					"high_price": round(float(base_high), 2),
					"low_price": round(float(base_low), 2),
					"status": "forming",
				}
			# Move past the low and continue searching
			i = base_low_idx + swing_window
			continue

		# Base completed — validate duration
		duration_days = breakout_idx - base_start_idx
		duration_weeks = max(1, duration_days // 5)

		if duration_weeks < min_base_weeks:
			# Too short to be a real base
			i = breakout_idx + 1
			continue

		# Duration-keyed depth ceiling: a correction that's deep for a base of this
		# LENGTH is non-constructive (deep-and-fast), even under the absolute redline.
		if correction_depth > max_constructive_depth_pct(duration_weeks):
			i = breakout_idx + 1
			continue

		# Record completed base
		completed_bases.append({
			"start_idx": base_start_idx,
			"end_idx": breakout_idx,
			"start_date": str(dates[base_start_idx].date()),
			"end_date": str(dates[breakout_idx].date()),
			"duration_weeks": duration_weeks,
			"correction_depth_pct": round(correction_depth, 1),
			"high_price": round(float(base_high), 2),
			"low_price": round(float(base_low), 2),
			"status": "completed",
		})

		# Update tracking — advance past breakout
		last_breakout_price = float(base_high)
		i = breakout_idx + 1

	return completed_bases, forming_base


def _classify_base_pattern(depth, duration_weeks):
	"""Classify base pattern type (Minervini terminology)."""
	if depth < 15 and duration_weeks >= 5:
		return "Flat Base"
	elif depth <= 35 and duration_weeks >= 5:
		return "Cup"
	elif depth < 20 and duration_weeks <= 3:
		return "Power Play"
	elif depth > 35:
		return "Deep Correction"
	else:
		return "Cup"  # Default for 8-35% depth, 3-5 week duration


def _check_base_reset(closes, sma200, reset_window=RESET_WINDOW, reset_threshold=RESET_THRESHOLD):
	"""Check if base count should reset (Stage 4 decline).

	Uses rolling window: reset_threshold+ of reset_window trading days below 200MA.
	This is more robust than consecutive-day counting — handles
	brief bounces during Stage 4 declines.
	"""
	closes_arr = closes.values.astype(float)
	sma200_arr = sma200.values.astype(float)

	# Build boolean array: 1 if below 200MA, 0 otherwise
	valid_mask = ~np.isnan(sma200_arr)
	below = np.zeros(len(closes_arr), dtype=int)
	below[valid_mask] = (closes_arr[valid_mask] < sma200_arr[valid_mask]).astype(int)

	if len(below) < reset_window:
		return []

	# Rolling sum of days below 200MA
	kernel = np.ones(reset_window, dtype=int)
	rolling_sum = np.convolve(below, kernel, mode="valid")

	# Find points where rolling sum exceeds threshold
	reset_indices = np.where(rolling_sum >= reset_threshold)[0]
	if len(reset_indices) == 0:
		return []

	# Convert to original index space and deduplicate (keep first of each cluster)
	reset_points = []
	last_reset = -reset_window
	for idx in reset_indices:
		original_idx = idx + reset_window - 1
		if original_idx - last_reset >= reset_window:
			reset_points.append(original_idx)
			last_reset = original_idx

	return reset_points


def _compute_relative_correction(dates, start_idx, end_idx, stock_correction_pct):
	"""Compute stock correction depth relative to SPY during the same period."""
	start_date = str(dates[start_idx].date())
	end_date = str(dates[end_idx].date())

	try:
		spy = yf.Ticker("SPY")
		spy_data = spy.history(start=start_date, end=end_date, interval="1d")
		if spy_data.empty or len(spy_data) < 5:
			return None, "unknown"

		spy_high = float(spy_data["High"].max())
		spy_low = float(spy_data["Low"].min())
		if spy_high <= 0:
			return None, "unknown"

		spy_correction = (spy_high - spy_low) / spy_high * 100
		if spy_correction < 0.5:
			return None, "unknown"

		ratio = round(stock_correction_pct / spy_correction, 2)

		if ratio <= REL_CORRECTION_NORMAL_RATIO:
			severity = "normal"
		elif ratio <= REL_CORRECTION_ELEVATED_RATIO:
			severity = "elevated"
		else:
			severity = "excessive"

		return ratio, severity
	except Exception:
		return None, "unknown"


def _compute_cross_base_analysis(bases):
	"""Analyze correction depth trend across bases.

	Deepening corrections = late-stage exhaustion signal.
	Shallowing corrections = healthy supply absorption.
	"""
	if len(bases) < 2:
		return None

	depths = [b["correction_depth_pct"] for b in bases]

	# Compare successive depths
	changes = [depths[i + 1] - depths[i] for i in range(len(depths) - 1)]
	avg_change = sum(changes) / len(changes)

	if avg_change > 3.0:
		trend = "deepening"
	elif avg_change < -3.0:
		trend = "shallowing"
	else:
		trend = "stable"

	return {
		"correction_trend": trend,
		"depths": depths,
	}


@safe_run
def cmd_count(args):
	"""Count bases and assess current base stage."""
	symbol = args.symbol.upper()
	ticker = yf.Ticker(symbol)
	data = ticker.history(period=args.period, interval="1d")
	data = data.dropna(subset=["Open", "High", "Low", "Close"])

	if data.empty or len(data) < 200:
		output_json({
			"error": f"Insufficient data for {symbol}. Need at least 200 trading days.",
			"data_points": len(data),
		})
		return

	closes = data["Close"]
	highs = data["High"]
	lows = data["Low"]
	sma200 = calculate_sma(closes, 200)

	# Check for base count resets
	reset_points = _check_base_reset(closes, sma200, args.reset_window, args.reset_days)

	# Find bases
	all_bases, forming_base = _find_bases(
		closes, highs, lows, sma200, args.min_base_weeks,
		swing_window=args.swing_window,
		max_base_days=args.max_base_weeks * 5,
		forming_recency_days=args.forming_recency_days,
		min_advance_pct=args.min_advance_pct,
	)

	# Apply reset: only count bases after the last reset
	if reset_points and all_bases:
		last_reset = reset_points[-1]
		all_bases = [b for b in all_bases if b["start_idx"] > last_reset]

	# Also check if forming base is before reset
	if reset_points and forming_base:
		# forming_base doesn't have start_idx, but if reset happened recently
		# and forming base started before, discard it
		pass  # forming_base is always recent by construction

	# Number bases, classify, compute relative correction
	dates = closes.index
	for i, base in enumerate(all_bases):
		base["base_number"] = i + 1
		base["pattern_type"] = _classify_base_pattern(
			base["correction_depth_pct"],
			base["duration_weeks"],
		)
		ratio, severity = _compute_relative_correction(
			dates, base["start_idx"], base["end_idx"], base["correction_depth_pct"]
		)
		base["relative_correction_ratio"] = ratio
		base["correction_severity"] = severity
		# Remove internal index fields
		base.pop("start_idx", None)
		base.pop("end_idx", None)

	current_base_number = len(all_bases)

	# Assessment based on base number
	if current_base_number == 0:
		assessment = "No bases detected"
		risk_level = "unknown"
	elif current_base_number <= 2:
		assessment = "Early stage - optimal entry zone"
		risk_level = "low"
	elif current_base_number == 3:
		assessment = "Mid stage - still tradeable but becoming obvious"
		risk_level = "moderate"
	elif current_base_number <= 5:
		assessment = "Late stage - higher failure rate"
		risk_level = "high"
	else:
		assessment = "Very late stage - most breakouts fail"
		risk_level = "very_high"

	# Correction severity adjustment
	if all_bases:
		latest_severity = all_bases[-1].get("correction_severity", "normal")
		if latest_severity == "excessive":
			severity_upgrade = {"low": "moderate", "moderate": "high", "high": "very_high"}
			if risk_level in severity_upgrade:
				risk_level = severity_upgrade[risk_level]

	# Cross-base analysis
	cross_base = _compute_cross_base_analysis(all_bases)

	output_json({
		"symbol": symbol,
		"date": str(data.index[-1].date()),
		"current_price": round(float(closes.iloc[-1]), 2),
		"current_base_number": current_base_number,
		"forming_base": forming_base,
		"base_history": all_bases,
		"cross_base_analysis": cross_base,
		"base_stage_assessment": assessment,
		"risk_level": risk_level,
		"base_count_reset_detected": len(reset_points) > 0,
		"thresholds": {
			"min_advance_between_bases": f"new high must exceed prior breakout (MIN_ADVANCE_PCT={MIN_ADVANCE_PCT}%, 0 = off; not a Minervini rule)",
			"correction_range": f">={MIN_CORRECTION_PCT}% deep, ceiling keyed to duration (<=3wk:25% / <=25wk:35% / >25wk:50%); {REDLINE_DEPTH_PCT}% redline",
			"risk_levels": "low: base 1-2 | moderate: base 3 | high: base 4-5 | very_high: base 6+",
			"reset_trigger": f"{args.reset_days}+ of {args.reset_window} trading days below 200MA",
			"cross_base_warning": "deepening corrections = late-stage exhaustion",
		},
	})


def main():
	parser = argparse.ArgumentParser(description="Base Counting for Stage 2 Advance")
	sub = parser.add_subparsers(dest="command", required=True)

	sp = sub.add_parser("count", help="Count bases and assess base stage")
	sp.add_argument("symbol", help="Ticker symbol")
	sp.add_argument("--period", default="2y", help="Data period (default: 2y)")
	sp.add_argument("--min-base-weeks", type=int, default=3, help="Minimum weeks per base (default: 3)")
	sp.add_argument("--swing-window", type=int, default=SWING_HIGH_WINDOW,
		help="Symmetric (+/-) window in days for swing-high detection (default: %(default)s). "
			 "A 'meaningful' swing high scales with the base's own timeframe — widen for longer "
			 "bases / weekly-scale work, narrow for tighter intraday-to-swing structures.")
	sp.add_argument("--max-base-weeks", type=int, default=MAX_BASE_WEEKS,
		help="Max base duration / breakout search horizon in WEEKS (default: %(default)s; ~%(default)s*5 days). "
			 "How long a consolidation still counts as a base vs dead money is context-dependent — "
			 "shorten for fast momentum names, lengthen for slow multi-quarter bases.")
	sp.add_argument("--forming-recency-days", type=int, default=FORMING_RECENCY_DAYS,
		help="Recency window in days for an unbroken base to still count as 'currently forming' "
			 "(default: %(default)s). Whether a still-open consolidation is live depends on the "
			 "timeframe — raise it for longer bases, lower it to demand a fresher pullback.")
	sp.add_argument("--reset-days", type=int, default=RESET_THRESHOLD,
		help="Days below 200MA (within --reset-window) that confirm a Stage-4 reset of the base count "
			 "(default: %(default)s). An arbitrary discretization of 'Stage-4 confirmed', not a canonical "
			 "constant — tune with --reset-window to make the reset stricter or looser.")
	sp.add_argument("--reset-window", type=int, default=RESET_WINDOW,
		help="Rolling window in days over which --reset-days is counted (default: %(default)s). "
			 "Pairs with --reset-days; the band, not either number alone, defines 'Stage-4 confirmed'.")
	sp.add_argument("--min-advance-pct", type=float, default=MIN_ADVANCE_PCT,
		help="Min %% a new base's high must exceed the prior breakout to count as a separate base "
			 "(default: %(default)s = off). HEURISTIC with no canonical value — not a Minervini rule; "
			 "bases are separated by structure, not a magic %%. Raise only to demand bigger steps.")
	sp.set_defaults(func=cmd_count)

	args = parser.parse_args()
	args.func(args)


if __name__ == "__main__":
	main()
