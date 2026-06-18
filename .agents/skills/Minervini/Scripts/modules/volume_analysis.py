#!/usr/bin/env python3
"""Volume Analysis: institutional accumulation/distribution pattern detection.

Analyzes volume patterns to identify institutional buying (accumulation) or
selling (distribution) activity. Key component of Minervini's SEPA methodology
for confirming breakout validity and assessing institutional participation.

Includes distribution day clustering detection, climactic volume day
identification, and 20-day volume direction summary for early transition
signal detection.

Commands:
	analyze: Full volume analysis with accumulation/distribution rating
	demand-days: Scan for institutional demand days inside the base (up-day volume
		dwarfing the max prior down-day volume — accumulation's footprint before
		the breakout; absorbs the former pocket_pivot module)

Args:
	symbol (str): Ticker symbol (e.g., "AAPL", "NVDA", "META")
	--period (str): Historical data period (default: "6mo")

Returns:
	dict: {
		"symbol": str,
		"accumulation_distribution_rating": str,
		"up_down_volume_ratio_50d": float,
		"up_down_volume_ratio_20d": float,
		"volume_vs_50day_avg_pct": float,
		"breakout_volume_confirmation": bool,
		"volume_trend": str,
		"distribution_clusters": dict,
		"climactic_volume": dict,
		"volume_direction_summary_20d": dict
	}

Example:
	>>> python volume_analysis.py analyze NVDA --period 6mo
	{
		"symbol": "NVDA",
		"accumulation_distribution_rating": "B+",
		"up_down_volume_ratio_50d": 1.45,
		"up_down_volume_ratio_20d": 1.32,
		"volume_vs_50day_avg_pct": 115.3,
		"breakout_volume_confirmation": true,
		"volume_trend": "accumulation",
		"pullback_volume_declining": true,
		"distribution_clusters": {"clusters_found": 0, "cluster_warning": false},
		"climactic_volume": {"net_climactic": 1}
	}

Use Cases:
	- Confirm institutional accumulation before breakout entry
	- Validate breakout with volume surge (25%+ above 50-day avg)
	- Detect distribution days signaling potential exit
	- Detect distribution day clustering (3+ within 25 trading days)
	- Identify climactic volume days (2x+ average) for institutional activity
	- Monitor pullback quality (declining volume = healthy)
	- Grade overall accumulation/distribution (A-E scale)
	- Compare 20d vs 50d volume ratios for early transition detection

Notes:
	- A/B ratings indicate net accumulation (bullish)
	- D/E ratings indicate net distribution (bearish)
	- C rating is neutral
	- Breakout confirmation requires 25%+ above 50-day avg volume
	- Ideal breakout shows 100-200% above average volume
	- Pullback on declining volume is constructive (supply drying up)
	- Distribution days: price down >= 0.2% on above-average volume
	- Accumulation days: price up >= 0.2% on above-average volume
	- Climactic days: volume >= 2x 50-day average (institutional footprint)
	- Distribution clusters: 3+ dist days within 25 trading days = warning

See Also:
	- vcp.py: VCP detection (volume confirms tightening)
	- base_count.py: Volume patterns during base formation
	- trend_template.py: Volume context for Trend Template assessment
	- stage_analysis.py: Uses volume ratios for stage classification scoring
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import numpy as np
import yfinance as yf
from utils import calculate_sma, output_json, safe_run

# --- analyze: tunable lookback horizons (CLI-overridable defaults) ---
# The institutional supply/demand window; scales with how much base history matters.
ACCDIST_LOOKBACK = 50
# Recent-pressure window; a shorter horizon for the secondary ratio.
SHORT_LOOKBACK = 20
# How many sessions define a "cluster" of distribution/accumulation days.
CLUSTER_WINDOW = 25
# How recent a breakout-volume confirmation day must be.
BREAKOUT_WINDOW = 5
# How long the pullback being assessed is.
PULLBACK_WINDOW = 20

# --- analyze: definitional conviction floors (canonical, not tuned per-run) ---
# Price move that marks a genuine up/down day; below this is noise, not direction.
DIST_ACC_PRICE_THRESHOLD_PCT = 0.2
# How many distribution days within the window constitute a cluster.
MIN_CLUSTER_SIZE = 3
# Volume multiple of the 50d avg that marks a climactic/exhaustion spike.
CLIMACTIC_VOL_MULT = 2.0
# Up-day volume floor (x 50d avg) that confirms a breakout.
BREAKOUT_VOL_MULT = 1.25
# Inner down-day decline factor: pullback volume is "declining" below this.
PULLBACK_DECLINE_FACTOR = 0.9

# --- analyze: accumulation/distribution grade bands (A-E) ---
# DOCTRINE — read before touching these numbers.
# Graded off up_down_volume_ratio_50d: a 50-day AGGREGATE of sum(up-day vol)/sum(down-day vol).
# It reads the LEVEL of net accumulation, smoothed over the base — a bounded
# average. A real Stage-2 leader still prints ~40-45% down-days, so the down-vol
# denominator never collapses and this ratio physically tops out around ~1.6-1.9
# (observed basket max AMD ~1.87, MU ~1.51; the neutral mega-cap cluster ~1.0).
# The bands are calibrated to THAT range: A isolates the strongest, B+/B the
# strong-but-not-dwarfing, C the neutral ~1.0 cluster, D/E the real decliners.
#
# DO NOT re-point these at the method's "several hundred to ~1,000%" (3-10x)
# surge figure. That figure (the single-day demand-surge standard; book Ch.10-11:
# "a surge of several hundred percent or even as much as 1,000 percent compared
# with the AVERAGE volume") is the magnitude of a SINGLE demand DAY's volume vs
# its own average — a per-bar surge, with a "the day FOLLOWED by a bigger down
# day disqualifies" rule that only parses against one bar. An aggregate has no
# surge and no next-day: a lone 8x demand day on a neutral 24up/25down baseline
# lifts this aggregate only to ~1.28. Demanding 3x here would make every real
# leader fail and collapse all grades into D/E. (An audit recommended exactly
# this; it was a metric-mismatch. This comment exists to stop the next one.)
# The 3-10x surge standard lives on the `demand-days` per-bar volume_ratio
# (up-day vol / max prior down-day vol), NOT here. The book's hard ratios
# (Nasdaq 9:1, NYSE 21:1) are MARKET-breadth reads, not per-stock aggregates.
#
# NO DISTRIBUTION-DAY COUNTING. Down-side pressure is already priced into this
# grade through down-day VOLUME (the denominator) — the faithful asymmetry. We
# do NOT add a "N distribution days -> cap the grade" tally: that is the O'Neil
# distribution-day / follow-through mechanism the method rejects (the source
# counts no distribution days). The forward
# "bigger-down-day-follows" disqualifier in demand-days is a magnitude rule, not
# a count, and stays.
ACCDIST_GRADE_A_PLUS_RATIO = 1.8   # strong accumulation (top up/down-volume tier)
ACCDIST_GRADE_A_RATIO = 1.5        # clear accumulation
ACCDIST_GRADE_B_PLUS_RATIO = 1.3   # moderate
ACCDIST_GRADE_B_RATIO = 1.15       # slight
ACCDIST_GRADE_C_RATIO = 0.85       # neutral floor (0.85-1.15 = neutral)
ACCDIST_GRADE_D_RATIO = 0.7        # slight-distribution floor (below this = heavy, grade E)


def _calc_up_down_ratio(volumes, closes, lookback):
	"""Calculate up-day volume to down-day volume ratio."""
	recent_vol = volumes.tail(lookback)
	recent_close = closes.tail(lookback)
	price_change = recent_close.diff()

	up_vol = float(recent_vol[price_change > 0].sum())
	down_vol = float(recent_vol[price_change < 0].sum())

	if down_vol == 0:
		return 2.0, up_vol, down_vol
	return round(up_vol / down_vol, 3), up_vol, down_vol


def _count_distribution_days(volumes, closes, vol_50avg, lookback=50):
	"""Count distribution days in the last N trading days.

	Distribution day: price declines on above-average volume.
	"""
	recent_vol = volumes.tail(lookback)
	recent_close = closes.tail(lookback)
	price_change = recent_close.diff()

	count = 0
	dates = []
	for i in range(1, len(recent_vol)):
		pct_change = (recent_close.iloc[i] / recent_close.iloc[i - 1] - 1) * 100 if recent_close.iloc[i - 1] != 0 else 0
		if pct_change <= -DIST_ACC_PRICE_THRESHOLD_PCT and recent_vol.iloc[i] > vol_50avg:
			count += 1
			dates.append(str(recent_close.index[i].date()))

	return count, dates


def _count_accumulation_days(volumes, closes, vol_50avg, lookback=50):
	"""Count accumulation days in the last N trading days.

	Accumulation day: price rises on above-average volume.
	"""
	recent_vol = volumes.tail(lookback)
	recent_close = closes.tail(lookback)
	price_change = recent_close.diff()

	count = 0
	dates = []
	for i in range(1, len(recent_vol)):
		pct_change = (recent_close.iloc[i] / recent_close.iloc[i - 1] - 1) * 100 if recent_close.iloc[i - 1] != 0 else 0
		if pct_change >= DIST_ACC_PRICE_THRESHOLD_PCT and recent_vol.iloc[i] > vol_50avg:
			count += 1
			dates.append(str(recent_close.index[i].date()))

	return count, dates


def _calc_count_ratio(closes, lookback):
	"""Up-DAY count / down-DAY count over the lookback.

	This is the genuine second volume signal, distinct from the up/down *volume*
	ratio (which weights by magnitude). A former `_calc_volume_weighted_ratio`
	also returned a "volume-weighted" ratio, but the weighting (each day scaled
	by v / vol_50avg, a window-constant) cancels in the quotient, making it
	algebraically identical to `_calc_up_down_ratio` — so it was removed as a
	redundant field and the grade now reads `_calc_up_down_ratio` directly.
	"""
	recent_close = closes.tail(lookback)
	price_change = recent_close.diff()

	count_up = 0
	count_down = 0
	for i in range(1, len(recent_close)):
		if price_change.iloc[i] > 0:
			count_up += 1
		elif price_change.iloc[i] < 0:
			count_down += 1

	return round(count_up / count_down, 3) if count_down > 0 else 2.0


def _grade_accumulation(up_down_ratio):
	"""Grade accumulation/distribution A-E on the up/down *volume* ratio alone.

	The up/down volume ratio already carries the institutional footprint — down
	volume is its denominator — so the grade reads it directly. It deliberately
	does NOT layer an accumulation-day vs distribution-day *count* test on top:
	tallying distribution days is the index-timing mechanic this methodology does
	not use, and gating the top grade on it double-counts what the ratio already
	reflects. The raw acc/dist day counts stay in the output for the analyst to
	weigh; they just don't gate the grade.

	A+: ratio > 1.8   A: > 1.5   B+: > 1.3   B: > 1.15
	C:  0.85-1.15     D: 0.7-0.85   E: < 0.7
	"""
	if up_down_ratio > ACCDIST_GRADE_A_PLUS_RATIO:
		return "A+"
	elif up_down_ratio > ACCDIST_GRADE_A_RATIO:
		return "A"
	elif up_down_ratio > ACCDIST_GRADE_B_PLUS_RATIO:
		return "B+"
	elif up_down_ratio > ACCDIST_GRADE_B_RATIO:
		return "B"
	elif up_down_ratio > ACCDIST_GRADE_C_RATIO:
		return "C"
	elif up_down_ratio > ACCDIST_GRADE_D_RATIO:
		return "D"
	else:
		return "E"


def _check_pullback_volume(volumes, closes, lookback=20):
	"""Check if recent pullback shows declining volume (healthy)."""
	recent_vol = volumes.tail(lookback)
	recent_close = closes.tail(lookback)
	price_change = recent_close.diff()

	# Find if we're in a pullback (recent price decline)
	last_5_change = float(recent_close.iloc[-1] / recent_close.iloc[-5] - 1) * 100
	if last_5_change >= 0:
		return None, "not_in_pullback"

	# During pullback, is volume declining?
	down_days_vol = []
	for i in range(len(recent_vol) - 10, len(recent_vol)):
		if i >= 0 and price_change.iloc[i] < 0:
			down_days_vol.append(float(recent_vol.iloc[i]))

	if len(down_days_vol) < 2:
		return None, "insufficient_data"

	# Compare first half vs second half of down-day volumes
	mid = len(down_days_vol) // 2
	first_half_avg = np.mean(down_days_vol[:mid]) if mid > 0 else 0
	second_half_avg = np.mean(down_days_vol[mid:]) if mid < len(down_days_vol) else 0

	declining = second_half_avg < first_half_avg * PULLBACK_DECLINE_FACTOR if first_half_avg > 0 else False
	return declining, "declining" if declining else "increasing"


def _detect_distribution_clusters(dist_dates, cluster_window=CLUSTER_WINDOW, min_cluster_size=MIN_CLUSTER_SIZE):
	"""Detect clustering of Distribution Days within a sliding window.

	Clustered distribution days are more bearish than evenly spread ones.
	"""
	if len(dist_dates) < min_cluster_size:
		return {
			"clusters_found": 0,
			"clusters": [],
			"max_cluster_size": 0,
			"cluster_warning": False,
		}

	from datetime import datetime, timedelta

	parsed = sorted(datetime.strptime(d, "%Y-%m-%d") for d in dist_dates)
	clusters = []
	current_cluster = [parsed[0]]

	for i in range(1, len(parsed)):
		if (parsed[i] - current_cluster[0]).days <= cluster_window:
			current_cluster.append(parsed[i])
		else:
			if len(current_cluster) >= min_cluster_size:
				clusters.append(
					{
						"start": current_cluster[0].strftime("%Y-%m-%d"),
						"end": current_cluster[-1].strftime("%Y-%m-%d"),
						"count": len(current_cluster),
					}
				)
			current_cluster = [parsed[i]]

	if len(current_cluster) >= min_cluster_size:
		clusters.append(
			{
				"start": current_cluster[0].strftime("%Y-%m-%d"),
				"end": current_cluster[-1].strftime("%Y-%m-%d"),
				"count": len(current_cluster),
			}
		)

	max_size = max((c["count"] for c in clusters), default=0)
	return {
		"clusters_found": len(clusters),
		"clusters": clusters,
		"max_cluster_size": max_size,
		"cluster_warning": max_size >= 5,
	}


def _detect_climactic_days(volumes, closes, vol_50avg, lookback=50):
	"""Identify days with volume >= 2x of 50-day average (climactic volume).

	Classifies direction and interpretation for institutional activity detection.
	"""
	recent_vol = volumes.tail(lookback)
	recent_close = closes.tail(lookback)
	threshold = vol_50avg * CLIMACTIC_VOL_MULT

	climactic_days = []
	buy_count = 0
	sell_count = 0

	for i in range(1, len(recent_vol)):
		if recent_vol.iloc[i] >= threshold:
			price_chg = float(recent_close.iloc[i] - recent_close.iloc[i - 1])
			pct_chg = (price_chg / float(recent_close.iloc[i - 1])) * 100 if recent_close.iloc[i - 1] != 0 else 0
			vol_multiple = round(float(recent_vol.iloc[i]) / vol_50avg, 1)

			if price_chg > 0:
				direction = "up"
				interpretation = "institutional_buying"
				buy_count += 1
			else:
				direction = "down"
				interpretation = "institutional_selling" if abs(pct_chg) < 5 else "capitulation"
				sell_count += 1

			climactic_days.append(
				{
					"date": str(recent_close.index[i].date()),
					"direction": direction,
					"interpretation": interpretation,
					"price_change_pct": round(pct_chg, 2),
					"volume_multiple": vol_multiple,
				}
			)

	return {
		"climactic_days": climactic_days,
		"climactic_buy_days": buy_count,
		"climactic_sell_days": sell_count,
		"net_climactic": buy_count - sell_count,
	}


def _volume_direction_summary(volumes, closes, lookback=20):
	"""Summary statistics for recent volume direction (up vs down).

	Lightweight summary without daily detail to avoid token waste.
	"""
	recent_vol = volumes.tail(lookback)
	recent_close = closes.tail(lookback)
	price_change = recent_close.diff()
	vol_50avg = float(volumes.tail(50).mean()) if len(volumes) >= 50 else float(volumes.mean())

	up_vol_total = float(recent_vol[price_change > 0].sum())
	down_vol_total = float(recent_vol[price_change < 0].sum())
	ratio = round(up_vol_total / down_vol_total, 3) if down_vol_total > 0 else 2.0

	heavy_dist = 0
	heavy_acc = 0
	for i in range(1, len(recent_vol)):
		if recent_vol.iloc[i] > vol_50avg:
			if price_change.iloc[i] > 0:
				heavy_acc += 1
			elif price_change.iloc[i] < 0:
				heavy_dist += 1

	return {
		"up_volume_total": int(up_vol_total),
		"down_volume_total": int(down_vol_total),
		"up_down_volume_ratio_by_total": ratio,
		"heavy_dist_days": heavy_dist,
		"heavy_acc_days": heavy_acc,
	}


@safe_run
def cmd_analyze(args):
	"""Full volume analysis with accumulation/distribution rating."""
	symbol = args.symbol.upper()
	ticker = yf.Ticker(symbol)
	data = ticker.history(period=args.period, interval="1d")
	# yfinance appends a partial in-session bar whose OHLC can be NaN; that NaN
	# poisons closes.iloc[-1] and every comparison downstream. Drop it first.
	data = data.dropna(subset=["Open", "High", "Low", "Close"])

	if data.empty or len(data) < 50:
		output_json(
			{
				"error": f"Insufficient data for {symbol}. Need at least 50 trading days.",
				"data_points": len(data),
			}
		)
		return

	closes = data["Close"]
	volumes = data["Volume"]
	current_price = float(closes.iloc[-1])

	# 50-day average volume
	vol_50avg = float(volumes.tail(50).mean())
	current_vol = float(volumes.iloc[-1])
	vol_vs_50avg_pct = round(current_vol / vol_50avg * 100, 1) if vol_50avg > 0 else 0

	# Up/Down volume ratios at different lookbacks
	ratio_20, _, _ = _calc_up_down_ratio(volumes, closes, args.short_lookback)
	ratio_50, up_vol_50, down_vol_50 = _calc_up_down_ratio(volumes, closes, args.lookback)

	# Accumulation and distribution day counts
	acc_days, acc_dates = _count_accumulation_days(volumes, closes, vol_50avg, args.lookback)
	dist_days, dist_dates = _count_distribution_days(volumes, closes, vol_50avg, args.lookback)

	# Up/down DAY-count ratio (the genuine second signal; the volume ratio is ratio_50)
	count_ratio_50 = _calc_count_ratio(closes, args.lookback)
	count_ratio_20 = _calc_count_ratio(closes, args.short_lookback)

	# Grade on the up/down volume ratio
	grade = _grade_accumulation(ratio_50)

	# Breakout volume confirmation
	# Recent N days: any day with price up AND volume 25%+ above 50-day avg?
	breakout_confirmed = False
	recent_5_vol = volumes.tail(args.breakout_window)
	recent_5_close = closes.tail(args.breakout_window)
	recent_5_change = recent_5_close.diff()
	for i in range(1, len(recent_5_vol)):
		if recent_5_change.iloc[i] > 0 and recent_5_vol.iloc[i] > vol_50avg * BREAKOUT_VOL_MULT:
			breakout_confirmed = True
			break

	# Pullback volume analysis
	pullback_declining, pullback_status = _check_pullback_volume(volumes, closes, args.pullback_window)

	# Volume trend
	if ratio_50 > 1.3:
		vol_trend = "accumulation"
	elif ratio_50 < 0.7:
		vol_trend = "distribution"
	else:
		vol_trend = "neutral"

	# Distribution day clustering
	distribution_clusters = _detect_distribution_clusters(dist_dates, args.cluster_window)

	# Climactic volume days
	climactic = _detect_climactic_days(volumes, closes, vol_50avg, args.lookback)

	# Volume direction summary (20-day)
	vol_summary = _volume_direction_summary(volumes, closes, lookback=args.short_lookback)

	full_result = {
		"symbol": symbol,
		"date": str(data.index[-1].date()),
		"current_price": round(current_price, 2),
		"accumulation_distribution_rating": grade,
		"up_down_volume_ratio_50d": ratio_50,
		"up_down_volume_ratio_50d_unit": "sum(up-day vol) / sum(down-day vol) over 50d",
		"up_down_volume_ratio_20d": ratio_20,
		"volume_vs_50day_avg_pct": vol_vs_50avg_pct,
		"volume_vs_50day_avg_pct_unit": "current vol / 50d avg vol * 100",
		"current_volume": int(current_vol),
		"avg_volume_50d": int(vol_50avg),
		"breakout_volume_confirmation": breakout_confirmed,
		"volume_trend": vol_trend,
		"count_based_ratio_50d": count_ratio_50,
		"count_based_ratio_20d": count_ratio_20,
		"accumulation_days_50d": acc_days,
		"distribution_days_50d": dist_days,
		"net_acc_dist": acc_days - dist_days,
		"pullback_volume_declining": pullback_declining,
		"pullback_status": pullback_status,
		"recent_distribution_dates": dist_dates[-5:] if dist_dates else [],
		"distribution_clusters": distribution_clusters,
		"climactic_volume": climactic,
		"volume_direction_summary_20d": vol_summary,
		"thresholds": {
			"A+": "up_down_volume_ratio_50d > 1.8",
			"A": "up_down_volume_ratio_50d > 1.5",
			"B+": "up_down_volume_ratio_50d > 1.3",
			"B": "up_down_volume_ratio_50d > 1.15",
			"C": "up_down_volume_ratio_50d 0.85-1.15 (neutral)",
			"D": "up_down_volume_ratio_50d 0.7-0.85 (slight distribution)",
			"E": "up_down_volume_ratio_50d < 0.7 (heavy distribution)",
			"grade_input": "up_down_volume_ratio_50d (acc/dist day counts are informational, not graded)",
			"cluster_warning": "max_cluster_size >= 5 distribution days in a cluster",
			"breakout_confirmation": "volume 25%+ above 50d avg on up day in last 5 days",
		},
		"doctrine": (
			"Price is the aggregate of better-informed hands, so a failure to RALLY "
			"on unambiguously good news (a beat or a guidance raise) is smart money "
			"using the good-news liquidity to distribute — the dog that doesn't bark "
			"front-runs deterioration that becomes public later; the DEPTH of the "
			"sell-off separates healthy profit-taking from broken. And tape strength "
			"here is only HALF of catalyst confirmation: it must be paired with the "
			"numbers coming in strong, or it's a narrative with no earnings."
		),
	}

	# Compressed view for pipeline consumption
	full_result["compressed"] = {
		"accumulation_distribution_rating": full_result.get("accumulation_distribution_rating"),
		"up_down_volume_ratio_50d": full_result.get("up_down_volume_ratio_50d"),
		"up_down_volume_ratio_50d_unit": full_result.get("up_down_volume_ratio_50d_unit"),
		"up_down_volume_ratio_20d": full_result.get("up_down_volume_ratio_20d"),
		"volume_vs_50day_avg_pct": full_result.get("volume_vs_50day_avg_pct"),
		"breakout_volume_confirmation": full_result.get("breakout_volume_confirmation"),
		"volume_trend": full_result.get("volume_trend"),
		"pullback_volume_declining": full_result.get("pullback_volume_declining"),
		"distribution_clusters": full_result.get("distribution_clusters"),
		"thresholds": full_result.get("thresholds"),
	}

	# Recheck view: minimal fields for recheck command
	_clusters = full_result.get("distribution_clusters", {})
	full_result["recheck"] = {
		"grade": full_result.get("accumulation_distribution_rating"),
		"weighted_ratio_50d": full_result.get("up_down_volume_ratio_50d"),
		"cluster_warning": _clusters.get("cluster_warning") if isinstance(_clusters, dict) else None,
		"breakout_volume_confirmation": full_result.get("breakout_volume_confirmation"),
	}

	output_json(full_result)


# ---------------------------------------------------------------------------
# Demand days  (folded in from the former pocket_pivot module)
#
# A demand day is an up-day whose volume DWARFS the largest down-day volume in
# the prior window. It is the same up-dwarfs-down asymmetry the A/D grade above
# measures, but read on a single bar while price is still INSIDE the base —
# accumulation leaving a footprint before the breakout. It lives here, not in
# its own module, because it answers the identical funnel question ("is there
# demand-volume asymmetry in this base?") over the same OHLCV; a separate module
# only invites running one and skipping the other. The label "pocket pivot" is
# O'Neil/Morales vocabulary, absent from this method's source — so the public
# output speaks the method's own word, "demand day."
# ---------------------------------------------------------------------------

# Extension cutoffs vs the 10MA: beyond _EXTENDED a demand day is a chase, not a
# base entry; within _RIGHT_SIDE it sits in the constructive accumulation zone.
_EXTENDED_ABOVE_10MA_PCT = 10.0
_RIGHT_SIDE_ABOVE_10MA_PCT = 5.0

# Demand-day quality floors. THIS is where the method's per-bar surge standard
# lives: volume_ratio = up-day vol / max prior down-day vol (a pocket-pivot
# relative asymmetry). The book's "several hundred to ~1,000%" (3-10x) is the
# IDEAL surge magnitude, but it is a relationship/ceiling, not a copyable floor
# (a relationship, not a copyable digit): for liquid names the max-prior-down-day denominator never
# approaches zero, so even textbook footprints top out ~2.5-3x (observed basket
# max ~2.71). 2.0x is the deliberately conservative-but-reached "high" bar — one
# leg of a three-way AND (>=2.0 AND close in upper 70% of range AND above 50MA).
DEMAND_DAY_HIGH_VOL_RATIO = 2.0
DEMAND_DAY_MODERATE_VOL_RATIO = 1.5
DEMAND_DAY_HIGH_CLOSE_RANGE = 0.7
DEMAND_DAY_MODERATE_CLOSE_RANGE = 0.5


def _close_range_pct(close, high, low):
	"""Where the close sits in the day's range: 0.0 = at the low, 1.0 = at the high.

	A demand day that closes in the lower half of its range is buying that met
	immediate supply — conviction unconfirmed. Closing high is the tell the bid
	held into the close.
	"""
	rng = high - low
	if rng <= 0:
		return 0.5
	return round((close - low) / rng, 2)


def _max_down_volume(closes, volumes, idx, lookback, min_decline_pct):
	"""Largest volume among genuine down-days in the `lookback` sessions before idx.

	The bar a demand day must clear is the MAX prior down-day volume, not the
	mean: one real institutional down-day is the supply genuine demand has to
	overwhelm. A trivial down-tick (< min_decline_pct) is filtered as noise.
	"""
	start = max(1, idx - lookback)
	decline_threshold = 1.0 - min_decline_pct / 100.0
	max_down_vol = 0.0
	for i in range(start, idx):
		if closes[i] < closes[i - 1] * decline_threshold and volumes[i] > max_down_vol:
			max_down_vol = volumes[i]
	return max_down_vol


def _bigger_down_follows(closes, volumes, idx, demand_vol, lookahead, min_decline_pct):
	"""True if a down-day with volume > demand_vol occurs within `lookahead` of idx.

	The disqualifier half of the rule: demand that is immediately overwhelmed by a
	larger down-volume day was never accumulation. Reading only backward would
	stamp 'demand' on a footprint the method explicitly voids, so we look forward
	too. Near the right edge the lookahead is simply whatever bars exist.
	"""
	decline_threshold = 1.0 - min_decline_pct / 100.0
	end = min(len(closes), idx + lookahead + 1)
	for i in range(idx + 1, end):
		if closes[i] < closes[i - 1] * decline_threshold and volumes[i] > demand_vol:
			return True
	return False


def _demand_location(pct_above_50ma, pct_above_10ma, in_base):
	"""right_side (constructive) / handle (late-base) / extended (chase)."""
	if not in_base:
		return "extended"
	if pct_above_50ma >= 0 and pct_above_10ma <= _RIGHT_SIDE_ABOVE_10MA_PCT:
		return "right_side"
	return "handle"


def _grade_demand_day(volume_ratio, close_range_pct, above_50ma):
	"""high / moderate / low on vol-asymmetry x close-conviction x above-50MA."""
	if volume_ratio >= DEMAND_DAY_HIGH_VOL_RATIO and close_range_pct >= DEMAND_DAY_HIGH_CLOSE_RANGE and above_50ma:
		return "high"
	if volume_ratio >= DEMAND_DAY_MODERATE_VOL_RATIO and close_range_pct >= DEMAND_DAY_MODERATE_CLOSE_RANGE and above_50ma:
		return "moderate"
	return "low"


@safe_run
def cmd_demand_days(args):
	"""Scan for institutional demand days inside the base."""
	symbol = args.symbol.upper()
	ticker = yf.Ticker(symbol)
	data = ticker.history(period=args.period, interval="1d")
	data = data.dropna(subset=["Open", "High", "Low", "Close"])

	if data.empty or len(data) < 60:
		output_json({
			"error": f"Insufficient data for {symbol}. Need >= 60 trading days.",
			"data_points": len(data),
		})
		return

	closes = data["Close"].values.astype(float)
	highs = data["High"].values.astype(float)
	lows = data["Low"].values.astype(float)
	volumes = data["Volume"].values.astype(float)
	dates = data.index
	n = len(closes)

	sma50 = calculate_sma(data["Close"], 50).values
	sma10 = calculate_sma(data["Close"], 10).values
	current_price = round(float(closes[-1]), 2)

	lookback = args.down_vol_lookback
	min_decline = args.min_down_decline_pct
	stale_days = args.stale_days
	scan_start = max(lookback + 1, n - args.scan_days)

	demand_days = []
	disqualified = 0
	for i in range(scan_start, n):
		# Must be an up-day.
		if closes[i] <= closes[i - 1]:
			continue
		max_down_vol = _max_down_volume(closes, volumes, i, lookback, min_decline)
		# Up-volume must dwarf the largest prior down-volume.
		if max_down_vol <= 0 or volumes[i] <= max_down_vol:
			continue
		crp = _close_range_pct(closes[i], highs[i], lows[i])
		if crp < 0.5:
			continue
		# Forward disqualifier: voided if an even-bigger down-volume day follows.
		if _bigger_down_follows(closes, volumes, i, volumes[i], lookback, min_decline):
			disqualified += 1
			continue

		volume_ratio = round(volumes[i] / max_down_vol, 2)
		s50 = sma50[i]
		s10 = sma10[i]
		above_50ma = bool(s50 == s50 and closes[i] > s50)
		pct_above_50ma = round((closes[i] - s50) / s50 * 100, 2) if s50 == s50 and s50 > 0 else 0.0
		pct_above_10ma = round((closes[i] - s10) / s10 * 100, 2) if s10 == s10 and s10 > 0 else 0.0
		in_base = pct_above_10ma <= _EXTENDED_ABOVE_10MA_PCT
		days_ago = n - 1 - i

		demand_days.append({
			"date": str(dates[i].date()),
			"days_ago": days_ago,
			"actionable": days_ago <= stale_days,
			"close": round(float(closes[i]), 2),
			"volume": int(volumes[i]),
			"max_down_vol_window": int(max_down_vol),
			"volume_ratio": volume_ratio,
			"volume_ratio_unit": "up-day vol / max down-day vol in lookback window",
			"close_range_pct": crp,
			"above_50ma": above_50ma,
			"in_base": in_base,
			"location": _demand_location(pct_above_50ma, pct_above_10ma, in_base),
			"quality": _grade_demand_day(volume_ratio, crp, above_50ma),
		})

	most_recent = None
	if demand_days:
		last = demand_days[-1]
		most_recent = {
			"date": last["date"],
			"days_ago": last["days_ago"],
			"quality": last["quality"],
			"actionable": last["actionable"],
		}
	actionable_count = sum(1 for d in demand_days if d["actionable"])

	# Current base context (NaN-guarded so a missing SMA reports null, not a crash).
	s50c = sma50[-1]
	s10c = sma10[-1]
	pct_above_10ma_now = round((current_price - s10c) / s10c * 100, 2) if s10c == s10c and s10c > 0 else None
	base_context = {
		"above_50ma": bool(s50c == s50c and current_price > s50c),
		"pct_above_50ma": round((current_price - s50c) / s50c * 100, 2) if s50c == s50c and s50c > 0 else None,
		"pct_above_10ma": pct_above_10ma_now,
		"in_base": pct_above_10ma_now is not None and pct_above_10ma_now <= _EXTENDED_ABOVE_10MA_PCT,
	}

	full_result = {
		"symbol": symbol,
		"date": str(dates[-1].date()),
		"current_price": current_price,
		"demand_days": demand_days,
		"demand_day_count": len(demand_days),
		"actionable_count": actionable_count,
		"disqualified_count": disqualified,
		"most_recent": most_recent,
		"base_context": base_context,
		"params": {
			"down_vol_lookback": lookback,
			"scan_days": args.scan_days,
			"min_down_decline_pct": min_decline,
			"stale_days": stale_days,
		},
		"thresholds": {
			"demand_day": "up-day whose volume exceeds the MAX down-day volume in the prior lookback window",
			"disqualifier": "voided if a larger down-volume day follows within the lookback (supply overwhelmed the demand)",
			"actionable": f"days_ago <= {stale_days} (older footprints are history, not a present entry)",
			"quality_high": "vol_ratio >= 2.0 AND close in upper 70% of range AND above 50MA",
			"quality_moderate": "vol_ratio >= 1.5 AND close in upper 50% of range AND above 50MA",
			"location": "right_side (constructive) / handle (late-base) / extended (chase, >10% above 10MA)",
		},
		"doctrine": (
			"Institutional accumulation can't hide its footprint — it shows as "
			"outsized up-volume with a conspicuous absence of down-spikes; the "
			"ASYMMETRY, not the absolute level, distinguishes real sponsorship from a "
			"crowd bounce. A big demand day FOLLOWED by an even bigger down-volume day "
			"voids it — the supply came right back."
		),
	}

	full_result["compressed"] = {
		"demand_day_count": len(demand_days),
		"actionable_count": actionable_count,
		"disqualified_count": disqualified,
		"most_recent": most_recent,
		"base_context": base_context,
		"thresholds": full_result["thresholds"],
	}

	output_json(full_result)


def main():
	parser = argparse.ArgumentParser(description="Volume Analysis: Accumulation/Distribution")
	sub = parser.add_subparsers(dest="command", required=True)

	sp = sub.add_parser("analyze", help="Full volume analysis")
	sp.add_argument("symbol", help="Ticker symbol")
	sp.add_argument("--period", default="6mo", help="Data period (default: 6mo)")
	sp.add_argument("--lookback", type=int, default=ACCDIST_LOOKBACK,
					help="up/down ratio + acc/dist day window (default %d). The institutional "
						 "supply/demand window scales with how much base history is relevant — "
						 "widen for a long base, tighten to read only the most recent leg."
						 % ACCDIST_LOOKBACK)
	sp.add_argument("--short-lookback", type=int, default=SHORT_LOOKBACK,
					help="secondary short-ratio window (default %d). Recent-pressure horizon; "
						 "shorten to catch a fresh shift, lengthen to smooth noise." % SHORT_LOOKBACK)
	sp.add_argument("--cluster-window", type=int, default=CLUSTER_WINDOW,
					help="sessions that define a distribution 'cluster' (default %d). How tightly "
						 "dist days must bunch to count as concentrated selling." % CLUSTER_WINDOW)
	sp.add_argument("--breakout-window", type=int, default=BREAKOUT_WINDOW,
					help="recent days scanned for breakout-volume confirmation (default %d). How "
						 "recent a confirming volume day must be to still count." % BREAKOUT_WINDOW)
	sp.add_argument("--pullback-window", type=int, default=PULLBACK_WINDOW,
					help="pullback analysis lookback (default %d). Match to how long the pullback "
						 "being assessed has run." % PULLBACK_WINDOW)
	sp.set_defaults(func=cmd_analyze)

	sp = sub.add_parser("demand-days", help="Scan for institutional demand days inside the base")
	sp.add_argument("symbol", help="Ticker symbol")
	sp.add_argument("--period", default="1y", help="Data period (default: 1y)")
	sp.add_argument("--down-vol-lookback", type=int, default=10,
					help="sessions of prior down-days the demand day must dwarf (default 10). "
						 "A tight 5-week handle and a 26-week base warrant different horizons.")
	sp.add_argument("--scan-days", type=int, default=60,
					help="how far back to surface demand days (default 60). Scales with base length.")
	sp.add_argument("--min-down-decline-pct", type=float, default=0.3,
					help="min %% decline for a day to count as a genuine down-day (default 0.3). "
						 "The noise floor scales with the stock's own volatility.")
	sp.add_argument("--stale-days", type=int, default=15,
					help="demand days older than this are flagged not-actionable (default 15)")
	sp.set_defaults(func=cmd_demand_days)

	args = parser.parse_args()
	args.func(args)


if __name__ == "__main__":
	main()
