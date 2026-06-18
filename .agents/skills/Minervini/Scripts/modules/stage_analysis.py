#!/usr/bin/env python3
"""Stage analysis — where in the four-stage lifecycle a stock sits, decided
structurally, not scored.

A stock is in exactly ONE of Weinstein's four stages at a time, and which one is
a question of structure, not degree: price's position relative to a 200-day MA,
and whether that MA is actually turning up. So this module does NOT compute a
0-100 "stage score" and take an argmax. It used to, and that was a bug of the
same family the pipeline already killed: a weighted point-blend invents a
continuum where the reality is a switch. The old version handed Ford a higher
"Stage 2 advancing" number (60) than NVDA (35) and flipped Intel into a buyable
Stage 2 on a one-bucket plurality — because unanchored point-weights, summed and
argmax'd, drift toward whatever factor the stock happens to have, not toward the
lifecycle truth. A boolean cascade can't drift: it asks the structural questions
in the order that resolves the lifecycle, and the first matching signature wins.

The signatures, straight from the method (book Ch. 5; the Trend-Template
climax lines):

- Stage 4 (Declining): price BELOW a 200-day MA that is itself in a definite
  downtrend. Checked first — a broken stock must never be mistaken for a base.
- Stage 2 (Advancing): price ABOVE a 200-day MA that is RISING (same 1-month test
  trend_template.py uses for its criterion 3, so stage and gate cannot disagree
  on "rising"), with the trend confirmed by a bullish MA stack OR an intact
  higher-high/higher-low structure. The only buyable stage.
- Stage 3 (Topping): still above the 200-day MA, but it has stopped rising (or the
  stack has rolled) AND the uptrend structure is gone — price whipsawing across a
  flattening MA after an advance.
- Stage 1 (Basing): the residual. Below a non-declining MA, or oscillating near a
  flat one. Not actionable; the safe default when nothing else matches.

The classifier decides the lifecycle phase ONLY. It is deliberately NOT a quality
filter — a sleepy value name can be structurally in a Stage-2 uptrend. That is
correct and not a contradiction: the qualify gate ANDs this with the full Trend
Template (RS >=70, >=30% off the low, within 25% of the high), and THAT is where
quality-poor uptrends are rejected. Asking the stage classifier to also judge
quality is how you get the old score's incoherence back.

Commands:
    classify     Deterministic Stage 1-4 + the structural reads that decided it.
    transitions  Stage 1 -> Stage 2 early-turn signals.
    risk         Diagnostic sell-tells for a name already in an advance
                 (largest decline since the Stage-2 began, climax extension,
                 tennis-ball vs egg character). No distribution-day tally, no
                 key-reversal, no sizing — those were generic-TA fabrications.

Args:
    symbol (str): Ticker (e.g. "AAPL", "NVDA").
    --period (str): History to pull (default "2y").
    --swing-bars (int): N-bar confirmation for swing-point detection (default 5).
        Flexible: a 7-week power-play and an 18-month cup swing on different
        scales, so this is yours to widen for longer bases.
    --ma-uptrend-days (int): Lookback for the "200-day MA rising" test
        (default 22 = ~1 month, matching trend_template). The method prefers
        4-5 months of rise; widen to demand a longer-confirmed turn.

Returns (classify):
    {"symbol", "date", "current_price", "stage", "stage_name",
     "structural_reads": {price_vs_200ma, sma200_trend, ma_stack, trend_structure,
                          pct_above_52w_low, pct_below_52w_high}}
    No "scores", no "max_scores" — the stage is the structure, read it directly.

See Also:
    - trend_template.py: the 8-criteria gate; Stage 2 is its lifecycle twin.
    - rs_ranking.py: relative strength — the scarcity the stack can't show.
    - volume_analysis.py: accumulation/distribution footprint behind the structure.
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import numpy as np
import yfinance as yf
from volume_analysis import _calc_up_down_ratio
from utils import output_json, safe_run, calculate_sma

STAGE_NAMES = {
	1: "Basing / Neglect (Consolidation)",
	2: "Advancing (Accumulation)",
	3: "Topping (Distribution)",
	4: "Declining (Capitulation)",
}

# --- Diagnostic windows & conviction floors (transitions / risk) -----------
# These drive the early-turn and sell-tell DIAGNOSTICS, never the classify gate
# path (that path is fully governed by --ma-uptrend-days and --swing-bars; the
# 50/150/200 MA periods and the 252-day year are definitional, not tunable).
# They are named here, with their reason, rather than buried as bare literals so
# the number — and why it is what it is — is visible where a reader would
# question it. The conviction multipliers encode what a signal MEANS (what counts
# as volume "expanding", ranges "widening"), which is canonical to the method and
# constant across stocks; the lookbacks are short diagnostic windows that rarely
# need per-run tuning. The one number an analyst genuinely re-defines per stock —
# how long an advance must run before a parabolic move reads as a climax — is a
# CLI arg (--min-advance-weeks) below.
_SMA50_SLOPE_LOOKBACK = 20      # bars to read the 50-day MA's slope (short-trend re-engagement)
_VOL_AVG_LOOKBACK = 50          # baseline volume window — a "normal" session's volume
_VOL_RECENT_LOOKBACK = 5        # recent window compared against that baseline
_VOL_EXPANSION_MULT = 1.25      # 1.25x the 50d average = volume genuinely expanding, not noise
_UD_LOOKBACK = 30               # up/down-volume accumulation window
_UD_RATIO_BULLISH = 1.15        # up-vol must lead down-vol by 15% to read as accumulation
_FLATTENING_FLOOR = -0.5        # SMA200 %change > -0.5 counts as "flattening", not still-falling
_RS_LOOKBACK_DAYS = 63          # ~3 months — the relative-strength comparison window vs SPY
_ADR_FAST = 5                   # recent average-daily-range window
_ADR_SLOW = 60                  # baseline ADR window the recent one is judged against
_RANGE_EXPANSION_MULT = 1.3     # recent ADR > 1.3x baseline = ranges widening (a climax tell)
_ATR_RECENT = 15                # recent volatility window (tennis-ball vs egg)
_ATR_BASE = 60                  # baseline volatility window
_ATR_EXPANSION_MULT = 1.15      # 1.15x = volatility genuinely expanding, not drifting
_RECENT_HIGH_WINDOW = 40        # window defining "the recent high" price must snap back to
_NEAR_HIGH_BAND = 0.95          # within 5% of that high = still making / holding highs
_DEFAULT_MIN_ADVANCE_WEEKS = 8  # a climax only ENDS a trend after a long advance; "long" >= ~8wk


def _ma_slope(series, lookback=20):
	"""Normalized slope (percent per day) of a moving average over `lookback`."""
	if len(series) < lookback:
		return 0.0
	recent = series.dropna().tail(lookback)
	if len(recent) < 2:
		return 0.0
	x = np.arange(len(recent))
	y = recent.values.astype(float)
	slope = np.polyfit(x, y, 1)[0]
	mean_val = np.mean(y)
	if mean_val == 0:
		return 0.0
	return (slope / mean_val) * 100


def _sma200_trend_pct(sma200, lookback_days):
	"""Percent change of the 200-day MA over `lookback_days` (the rising test).

	Returns the percent change of SMA200 now vs `lookback_days` ago. Positive ==
	rising (== trend_template criterion 3). Falls back to the earliest available
	SMA200 value when history is short, mirroring trend_template.
	"""
	s = sma200.dropna()
	if len(s) < 2:
		return 0.0
	now = float(s.iloc[-1])
	ago = float(s.iloc[-1 - lookback_days]) if len(s) > lookback_days else float(s.iloc[0])
	if ago == 0:
		return 0.0
	return (now / ago - 1) * 100


def _find_swing_points(series, confirmation_bars=5):
	"""Swing highs/lows by N-bar confirmation.

	A swing high is a local max with `confirmation_bars` lower bars on each side
	(swing low symmetric). Returns (swing_highs, swing_lows) as lists of
	(index, value), chronological.
	"""
	values = series.values.astype(float)
	n = len(values)
	swing_highs = []
	swing_lows = []

	for i in range(confirmation_bars, n - confirmation_bars):
		is_high = True
		for j in range(1, confirmation_bars + 1):
			if values[i] < values[i - j] or values[i] < values[i + j]:
				is_high = False
				break
		if is_high:
			swing_highs.append((i, float(values[i])))

		is_low = True
		for j in range(1, confirmation_bars + 1):
			if values[i] > values[i - j] or values[i] > values[i + j]:
				is_low = False
				break
		if is_low:
			swing_lows.append((i, float(values[i])))

	return swing_highs, swing_lows


def _trend_structure(highs, lows, confirmation_bars=5):
	"""Read the swing structure into four booleans.

	HH/HL = last two swing highs/lows ascending (uptrend intact).
	LH/LL = last two descending (downtrend). Needs enough bars to find two of
	each; returns all-False when it can't (structure unknown, not absent).
	"""
	min_bars = confirmation_bars * 2 * 3  # room for >=2 confirmed swings each side
	if len(highs) < min_bars:
		return False, False, False, False

	swing_highs, _ = _find_swing_points(highs, confirmation_bars)
	_, swing_lows = _find_swing_points(lows, confirmation_bars)

	hh = lh = hl = ll = False
	if len(swing_highs) >= 2:
		a, b = swing_highs[-2][1], swing_highs[-1][1]
		hh = b > a
		lh = b < a
	if len(swing_lows) >= 2:
		a, b = swing_lows[-2][1], swing_lows[-1][1]
		hl = b > a
		ll = b < a
	return hh, hl, lh, ll


def _largest_decline_since_stage2(closes, sma200):
	"""Largest peak-to-trough drawdown since price first reclaimed the 200-day MA.

	Approximates the Stage-2 start as the first close above SMA200, then measures
	the deepest pullback since. This is the method's headline sell tell: the
	largest decline since the advance began, judged against the stock's own move.
	"""
	above = closes > sma200
	crossover = above.astype(int).diff()
	cross_up = crossover[crossover == 1]
	if len(cross_up) == 0:
		segment = closes
	else:
		segment = closes.iloc[closes.index.get_loc(cross_up.index[0]):]
	if len(segment) < 2:
		return 0.0
	running_max = segment.expanding().max()
	drawdowns = (segment / running_max - 1) * 100
	return float(drawdowns.min())


def _decline_band(decline_pct):
	"""Map a drawdown to the method's healthy-leader correction bands (spec §Risk).

	25-35% healthy / >50% generally fails / >60% redline. Diagnostic only.
	"""
	d = abs(decline_pct)
	if d < 25:
		return "normal_pullback"
	if d <= 35:
		return "healthy_leader_band"
	if d <= 50:
		return "caution_exceeds_healthy_band"
	if d <= 60:
		return "failing_over_50pct"
	return "redline_over_60pct"


def _atr(highs, lows, closes, window):
	"""Average true range over the last `window` bars."""
	tr = np.maximum(
		highs.values - lows.values,
		np.maximum(
			np.abs(highs.values - np.roll(closes.values, 1)),
			np.abs(lows.values - np.roll(closes.values, 1)),
		),
	)
	if len(tr) < window:
		return float(np.mean(tr[1:])) if len(tr) > 1 else 0.0
	return float(np.mean(tr[-window:]))


# ---------------------------------------------------------------------------
# The classifier — a boolean cascade, no points
# ---------------------------------------------------------------------------

def _classify_stage(price, s50, s150, s200, sma200_trend_pct, hh, hl, lh, ll):
	"""Place the lifecycle stage by structural signature, first match wins.

	Order is the point: Stage 4 (the broken case) is ruled out first so it can
	never be mistaken for a base; Stage 2 (the only buyable case) is then the
	clean above-a-rising-MA structure; Stage 3 is what's left above the MA once
	the rise has stalled; Stage 1 absorbs the rest.
	"""
	above_200 = price > s200
	s200_rising = sma200_trend_pct > 0       # == trend_template criterion 3
	s200_declining = sma200_trend_pct < 0
	bull_stack = s50 > s150 > s200
	bear_stack = s50 < s150
	uptrend_structure = hh and hl

	# Stage 4 — price below a definitively declining 200-day MA.
	if (not above_200) and s200_declining:
		return 4
	# Stage 2 — above a rising 200-day MA, trend confirmed by the stack or by an
	# intact higher-high/higher-low structure.
	if above_200 and s200_rising and (bull_stack or uptrend_structure):
		return 2
	# Stage 3 — still above the MA, but the rise has stalled (or the stack rolled)
	# and the uptrend structure is gone: distribution after an advance.
	if above_200 and (not s200_rising or bear_stack) and (not uptrend_structure):
		return 3
	# Stage 1 — basing / neglect / unconfirmed. The safe residual.
	return 1


@safe_run
def cmd_classify(args):
	"""Classify a stock into Stage 1-4 by structure."""
	symbol = args.symbol.upper()
	ticker = yf.Ticker(symbol)
	data = ticker.history(period=args.period, interval="1d")
	# Drop incomplete bars: yfinance appends a partial current-session row mid-day
	# whose OHLC can be NaN, which would poison every downstream comparison.
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
	current_price = float(closes.iloc[-1])
	date_str = str(data.index[-1].date())

	sma50 = calculate_sma(closes, 50)
	sma150 = calculate_sma(closes, 150)
	sma200 = calculate_sma(closes, 200)
	c_sma50 = float(sma50.iloc[-1])
	c_sma150 = float(sma150.iloc[-1])
	c_sma200 = float(sma200.iloc[-1])

	sma200_trend_pct = _sma200_trend_pct(sma200, args.ma_uptrend_days)
	hh, hl, lh, ll = _trend_structure(highs, lows, args.swing_bars)

	week52_low = float(lows.tail(252).min()) if len(lows) >= 252 else float(lows.min())
	week52_high = float(highs.tail(252).max()) if len(highs) >= 252 else float(highs.max())
	pct_above_52w_low = (current_price / week52_low - 1) * 100 if week52_low > 0 else 0.0
	pct_below_52w_high = (current_price / week52_high - 1) * 100 if week52_high > 0 else 0.0

	stage = _classify_stage(
		current_price, c_sma50, c_sma150, c_sma200, sma200_trend_pct, hh, hl, lh, ll
	)

	if sma200_trend_pct > 0:
		trend_label = "rising"
	elif sma200_trend_pct < 0:
		trend_label = "declining"
	else:
		trend_label = "flat"

	if c_sma50 > c_sma150 > c_sma200:
		stack_label = "bullish (50>150>200)"
	elif c_sma50 < c_sma150:
		stack_label = "bearish (50<150)"
	else:
		stack_label = "mixed"

	output_json({
		"symbol": symbol,
		"date": date_str,
		"current_price": round(current_price, 2),
		"stage": stage,
		"stage_name": STAGE_NAMES[stage],
		"structural_reads": {
			"price_vs_200ma": "above" if current_price > c_sma200 else "below",
			"sma200_trend": {
				"label": trend_label,
				"pct_change": round(sma200_trend_pct, 2),
				"lookback_days": args.ma_uptrend_days,
			},
			"ma_stack": stack_label,
			"trend_structure": {
				"higher_highs": hh, "higher_lows": hl,
				"lower_highs": lh, "lower_lows": ll,
				"swing_bars": args.swing_bars,
			},
			"pct_above_52w_low": round(pct_above_52w_low, 1),
			"pct_below_52w_high": round(pct_below_52w_high, 1),
		},
		"doctrine": (
			"A stock is in exactly ONE stage at a time — a question of structure, not degree. "
			"The classification is a boolean cascade, not a weighted score, precisely because a "
			"point-blend would invent a continuum where the reality is a switch, and would let a "
			"strong factor paper over a disqualifying one. Read the stage as a gate, not a grade."
		),
	})


@safe_run
def cmd_transitions(args):
	"""Detect Stage 1 -> Stage 2 early-turn signals.

	The early read the gate can't give you: a name still basing but starting to
	turn. No Golden Cross here — a 50/200 crossover is a lagging generic-TA
	artifact the method does not time off; the structural turn (reclaiming the
	200-day on volume, the MA flattening, higher highs/lows forming) leads it by
	weeks.
	"""
	symbol = args.symbol.upper()
	ticker = yf.Ticker(symbol)
	data = ticker.history(period=args.period, interval="1d")
	data = data.dropna(subset=["Open", "High", "Low", "Close"])

	if data.empty or len(data) < 200:
		output_json({
			"error": f"Insufficient data for {symbol}.",
			"data_points": len(data),
		})
		return

	closes = data["Close"]
	highs = data["High"]
	lows = data["Low"]
	volumes = data["Volume"]
	current_price = float(closes.iloc[-1])

	sma50 = calculate_sma(closes, 50)
	sma200 = calculate_sma(closes, 200)
	c_sma200 = float(sma200.iloc[-1])
	sma200_trend_pct = _sma200_trend_pct(sma200, args.ma_uptrend_days)

	vol_50avg = float(volumes.tail(_VOL_AVG_LOOKBACK).mean())
	recent_vol = float(volumes.tail(_VOL_RECENT_LOOKBACK).mean())
	vol_expansion = recent_vol > vol_50avg * _VOL_EXPANSION_MULT

	week52_high = float(highs.tail(252).max()) if len(highs) >= 252 else float(highs.max())

	signals = []

	# 1. Price reclaims the 200-day MA on expanding volume.
	price_above_200 = current_price > c_sma200
	signals.append({
		"signal": "Price reclaims 200-day MA on volume",
		"detected": price_above_200 and vol_expansion,
		"detail": f"Price {'>' if price_above_200 else '<'} SMA200, vol {'expanded' if vol_expansion else 'normal'}",
	})

	# 2. 200-day MA flattening or turning up (the long trend stops falling).
	flattening_or_rising = sma200_trend_pct > _FLATTENING_FLOOR
	signals.append({
		"signal": "200-day MA flattening or turning up",
		"detected": flattening_or_rising,
		"detail": f"SMA200 {args.ma_uptrend_days}d change: {sma200_trend_pct:+.2f}%",
	})

	# 3. Higher highs and higher lows forming.
	hh, hl, _, _ = _trend_structure(highs, lows, args.swing_bars)
	signals.append({
		"signal": "Higher highs and higher lows forming",
		"detected": hh and hl,
		"detail": f"HH: {hh}, HL: {hl}",
	})

	# 4. 50-day MA turning up (short trend re-engaging).
	sma50_rising = _ma_slope(sma50, _SMA50_SLOPE_LOOKBACK) > 0
	signals.append({
		"signal": "50-day MA turning up",
		"detected": sma50_rising,
		"detail": f"SMA50 slope {'rising' if sma50_rising else 'flat/falling'}",
	})

	# 5. Up-volume exceeds down-volume (accumulation footprint).
	ratio, _, _ = _calc_up_down_ratio(volumes, closes, _UD_LOOKBACK)
	signals.append({
		"signal": "Up-volume exceeds down-volume",
		"detected": ratio > _UD_RATIO_BULLISH,
		"detail": f"Up/Down volume ratio: {ratio:.2f}",
	})

	# 6. Price within 25% of the 52-week high (overhead supply thinning).
	within_25 = current_price >= week52_high * 0.75
	signals.append({
		"signal": "Price within 25% of 52-week high",
		"detected": within_25,
		"detail": f"{((current_price / week52_high - 1) * 100):.1f}% from 52w high",
	})

	# 7. Relative strength improving vs S&P 500.
	try:
		spy = yf.Ticker("SPY").history(period="3mo")
		spy_ret = (float(spy["Close"].iloc[-1]) / float(spy["Close"].iloc[0]) - 1) * 100
		stk = closes.tail(_RS_LOOKBACK_DAYS)
		stk_ret = (float(stk.iloc[-1]) / float(stk.iloc[0]) - 1) * 100
		rs_improving = stk_ret > spy_ret
		rs_detail = f"Stock 3m: {stk_ret:.1f}%, SPY 3m: {spy_ret:.1f}%"
	except Exception:
		rs_improving = False
		rs_detail = "Unable to calculate"
	signals.append({
		"signal": "Relative strength improving vs S&P 500",
		"detected": rs_improving,
		"detail": rs_detail,
	})

	detected = sum(1 for s in signals if s["detected"])
	output_json({
		"symbol": symbol,
		"date": str(data.index[-1].date()),
		"current_price": round(current_price, 2),
		"transition_type": "Stage 1 -> Stage 2",
		"signals": signals,
		"detected_count": detected,
		"total_signals": len(signals),
		"transition_strength": "strong" if detected >= 5 else "moderate" if detected >= 3 else "weak",
	})


@safe_run
def cmd_risk(args):
	"""Diagnostic sell-tells for a name already in an advance.

	Reads the three character signals the method actually sells on — NOT a
	distribution-day count (an O'Neil mechanism the method does not use) and NOT
	a fabricated multi-criteria "key reversal." Diagnostic only: no stop, no
	size, no verdict. The analyst weighs these against the stock's own move.

	1. Largest decline since the Stage 2 began — the headline tell. Judged
	   against the method's healthy-leader correction bands, because magnitude is
	   read relative to the stock's own advance, not an absolute percent.
	2. Climax extension — price stretched far above the 50-day MA with ranges
	   expanding after a long advance: a parabolic move ENDS a trend.
	3. Tennis ball vs egg — healthy pullbacks snap back to new highs with volume
	   contracting on the dip and expanding on the recovery; widening two-way
	   swings are an egg, not a ball.
	"""
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
	volumes = data["Volume"]
	current_price = float(closes.iloc[-1])

	sma50 = calculate_sma(closes, 50)
	sma200 = calculate_sma(closes, 200)
	c_sma50 = float(sma50.iloc[-1])

	# 1. Largest decline since Stage 2 began.
	largest_decline = _largest_decline_since_stage2(closes, sma200)
	decline_band = _decline_band(largest_decline)

	# 2. Climax extension above the 50-day MA + range expansion + length of run.
	extension_pct = (current_price / c_sma50 - 1) * 100 if c_sma50 > 0 else 0.0
	adr = ((highs - lows) / closes * 100).astype(float)
	adr_5d = float(adr.iloc[-_ADR_FAST:].mean())
	adr_60d = float(adr.iloc[-_ADR_SLOW:].mean()) if len(adr) >= _ADR_SLOW else adr_5d
	range_expanding = adr_5d > _RANGE_EXPANSION_MULT * adr_60d if adr_60d > 0 else False
	days_since_50ma = 0
	for i in range(len(closes) - 1, -1, -1):
		if float(closes.iloc[i]) <= float(sma50.iloc[i]):
			break
		days_since_50ma += 1
	weeks_of_advance = days_since_50ma // 5
	climactic = extension_pct > args.climax_extension_pct and range_expanding and weeks_of_advance >= args.min_advance_weeks

	# 3. Tennis ball vs egg: volatility trend + whether price still makes new highs.
	atr_recent = _atr(highs, lows, closes, _ATR_RECENT)
	atr_base = _atr(highs, lows, closes, _ATR_BASE)
	vol_expanding = atr_recent > atr_base * _ATR_EXPANSION_MULT if atr_base > 0 else False
	recent_high = float(highs.tail(_RECENT_HIGH_WINDOW).max())
	near_recent_high = current_price >= recent_high * _NEAR_HIGH_BAND
	if near_recent_high and not vol_expanding:
		character = "tennis_ball"
	elif vol_expanding and not near_recent_high:
		character = "egg"
	else:
		character = "mixed"

	output_json({
		"symbol": symbol,
		"date": str(data.index[-1].date()),
		"current_price": round(current_price, 2),
		"largest_decline_since_stage2": {
			"pct": round(largest_decline, 1),
			"band": decline_band,
			"note": "headline sell tell; judged vs the stock's own advance, not an absolute %",
		},
		"climax_extension": {
			"pct_above_50ma": round(extension_pct, 1),
			"range_expanding": bool(range_expanding),
			"weeks_of_advance": weeks_of_advance,
			"climactic": bool(climactic),
			"threshold_pct": args.climax_extension_pct,
			"min_advance_weeks": args.min_advance_weeks,
		},
		"character": {
			"read": character,
			"volatility_expanding": bool(vol_expanding),
			"near_recent_high": bool(near_recent_high),
			"note": "tennis_ball = snaps back to highs, volatility contained; egg = widening two-way swings",
		},
		"interpretation": "diagnostic only — no stop, no size, no verdict",
		"doctrine": (
			"These are character reads, not stops. The single largest decline SINCE Stage 2 "
			"began is the footprint of institutions exiting ahead of a deceleration they can see "
			"and you can't yet — read it relative to the stock's OWN advance; the 'overreaction, "
			"buy the dip' instinct fails precisely because the sellers know something not-yet-public. "
			"Sell on NON-confirmation, not just on loss: a momentum entry predicts movement, so a "
			"stock that just sits has falsified the thesis as surely as one that drops. Tennis-ball "
			"vs egg — healthy pullbacks snap back fast on contracting volume; widening two-way swings "
			"mean the supply/demand fight has turned contested."
		),
	})


def main():
	parser = argparse.ArgumentParser(description="Stage analysis (Weinstein/Minervini Stage 1-4)")
	sub = parser.add_subparsers(dest="command", required=True)

	def add_common(sp):
		sp.add_argument("symbol", help="Ticker symbol")
		sp.add_argument("--period", default="2y", help="Data period (default: 2y)")
		sp.add_argument("--swing-bars", type=int, default=5, dest="swing_bars",
						help="N-bar swing confirmation (default 5; widen for longer bases)")
		sp.add_argument("--ma-uptrend-days", type=int, default=22, dest="ma_uptrend_days",
						help="Lookback for the 200-day MA rising test (default 22 = ~1mo)")

	sp = sub.add_parser("classify", help="Classify stock into Stage 1-4 (structural, no score)")
	add_common(sp)
	sp.set_defaults(func=cmd_classify)

	sp = sub.add_parser("transitions", help="Detect Stage 1->2 early-turn signals")
	add_common(sp)
	sp.set_defaults(func=cmd_transitions)

	sp = sub.add_parser("risk", help="Diagnostic sell-tells (decline-since-S2, climax, character)")
	sp.add_argument("symbol", help="Ticker symbol")
	sp.add_argument("--period", default="2y", help="Data period (default: 2y)")
	sp.add_argument("--climax-extension-pct", type=float, default=25.0, dest="climax_extension_pct",
					help="Extension above 50-day MA flagged climactic (default 25; diagnostic)")
	sp.add_argument("--min-advance-weeks", type=int, default=_DEFAULT_MIN_ADVANCE_WEEKS,
					dest="min_advance_weeks",
					help="Weeks of advance required before a stretched move reads as a climax "
						 "(default 8). 'Long' is yours to redefine: a fast leader can top in fewer, "
						 "a slow grinder needs more.")
	sp.set_defaults(func=cmd_risk)

	args = parser.parse_args()
	args.func(args)


if __name__ == "__main__":
	main()
