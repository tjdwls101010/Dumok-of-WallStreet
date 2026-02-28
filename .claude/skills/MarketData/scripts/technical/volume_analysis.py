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
from utils import output_json, safe_run


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
		if pct_change <= -0.2 and recent_vol.iloc[i] > vol_50avg:
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
		if pct_change >= 0.2 and recent_vol.iloc[i] > vol_50avg:
			count += 1
			dates.append(str(recent_close.index[i].date()))

	return count, dates


def _grade_accumulation(up_down_ratio, acc_days, dist_days, vol_trend_ratio):
	"""Grade accumulation/distribution on A-E scale.

	A+: Strong accumulation (ratio > 1.8, acc >> dist)
	A:  Clear accumulation (ratio > 1.5)
	B+: Moderate accumulation (ratio > 1.3)
	B:  Slight accumulation (ratio > 1.15)
	C:  Neutral (ratio 0.85 - 1.15)
	D:  Slight distribution (ratio 0.7 - 0.85)
	E:  Heavy distribution (ratio < 0.7)
	"""
	if up_down_ratio > 1.8 and acc_days > dist_days * 2:
		return "A+"
	elif up_down_ratio > 1.5:
		return "A"
	elif up_down_ratio > 1.3:
		return "B+"
	elif up_down_ratio > 1.15:
		return "B"
	elif up_down_ratio > 0.85:
		return "C"
	elif up_down_ratio > 0.7:
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

	declining = second_half_avg < first_half_avg * 0.9 if first_half_avg > 0 else False
	return declining, "declining" if declining else "increasing"


def _detect_distribution_clusters(dist_dates, cluster_window=25, min_cluster_size=3):
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
		"cluster_warning": max_size >= min_cluster_size,
	}


def _detect_climactic_days(volumes, closes, vol_50avg, lookback=50):
	"""Identify days with volume >= 2x of 50-day average (climactic volume).

	Classifies direction and interpretation for institutional activity detection.
	"""
	recent_vol = volumes.tail(lookback)
	recent_close = closes.tail(lookback)
	threshold = vol_50avg * 2.0

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
	ratio_20, _, _ = _calc_up_down_ratio(volumes, closes, 20)
	ratio_50, up_vol_50, down_vol_50 = _calc_up_down_ratio(volumes, closes, 50)

	# Accumulation and distribution day counts
	acc_days, acc_dates = _count_accumulation_days(volumes, closes, vol_50avg, 50)
	dist_days, dist_dates = _count_distribution_days(volumes, closes, vol_50avg, 50)

	# Grade
	grade = _grade_accumulation(ratio_50, acc_days, dist_days, vol_vs_50avg_pct)

	# Breakout volume confirmation
	# Recent 5 days: any day with price up AND volume 25%+ above 50-day avg?
	breakout_confirmed = False
	recent_5_vol = volumes.tail(5)
	recent_5_close = closes.tail(5)
	recent_5_change = recent_5_close.diff()
	for i in range(1, len(recent_5_vol)):
		if recent_5_change.iloc[i] > 0 and recent_5_vol.iloc[i] > vol_50avg * 1.25:
			breakout_confirmed = True
			break

	# Pullback volume analysis
	pullback_declining, pullback_status = _check_pullback_volume(volumes, closes)

	# Volume trend
	if ratio_50 > 1.3:
		vol_trend = "accumulation"
	elif ratio_50 < 0.7:
		vol_trend = "distribution"
	else:
		vol_trend = "neutral"

	# Distribution day clustering
	distribution_clusters = _detect_distribution_clusters(dist_dates)

	# Climactic volume days
	climactic = _detect_climactic_days(volumes, closes, vol_50avg)

	# Volume direction summary (20-day)
	vol_summary = _volume_direction_summary(volumes, closes, lookback=20)

	output_json(
		{
			"symbol": symbol,
			"date": str(data.index[-1].date()),
			"current_price": round(current_price, 2),
			"accumulation_distribution_rating": grade,
			"up_down_volume_ratio_50d": ratio_50,
			"up_down_volume_ratio_20d": ratio_20,
			"volume_vs_50day_avg_pct": vol_vs_50avg_pct,
			"current_volume": int(current_vol),
			"avg_volume_50d": int(vol_50avg),
			"breakout_volume_confirmation": breakout_confirmed,
			"volume_trend": vol_trend,
			"accumulation_days_50d": acc_days,
			"distribution_days_50d": dist_days,
			"net_acc_dist": acc_days - dist_days,
			"pullback_volume_declining": pullback_declining,
			"pullback_status": pullback_status,
			"recent_distribution_dates": dist_dates[-5:] if dist_dates else [],
			"distribution_clusters": distribution_clusters,
			"climactic_volume": climactic,
			"volume_direction_summary_20d": vol_summary,
		}
	)


def main():
	parser = argparse.ArgumentParser(description="Volume Analysis: Accumulation/Distribution")
	sub = parser.add_subparsers(dest="command", required=True)

	sp = sub.add_parser("analyze", help="Full volume analysis")
	sp.add_argument("symbol", help="Ticker symbol")
	sp.add_argument("--period", default="6mo", help="Data period (default: 6mo)")
	sp.set_defaults(func=cmd_analyze)

	args = parser.parse_args()
	args.func(args)


if __name__ == "__main__":
	main()
