#!/usr/bin/env python3
"""Volume Edge Detection: extreme volume events for breakout confirmation.

Detects rare, high-conviction volume events that signal major institutional
participation — the kind that precedes sustained moves in leading stocks.
Based on TraderLion's methodology where the most powerful breakouts are
accompanied by historically significant volume.

Volume edge events are hierarchical: HVE (Highest Volume Ever) is the
strongest signal, followed by HVIPO and HV1. When multiple edge types
fire simultaneously, conviction increases.

Commands:
	detect: Single stock comprehensive volume edge analysis
	screen: Multiple stocks recent volume edge occurrence filter

Args:
	symbol (str): Ticker symbol (e.g., "AAPL", "NVDA", "META")
	symbols (list[str]): Multiple ticker symbols for screening
	--period (str): Historical data period (default: "2y")
	--lookback (int): Days to check for recent edges (default: 20)

Returns:
	For detect:
	dict: {
		"symbol": str,
		"date": str,
		"current_price": float,
		"edges_detected": list[str],
		"edge_count": int,
		"hve": {
			"detected": bool,
			"date": str,
			"volume": int,
			"previous_high": int,
			"multiple": float
		},
		"hvipo": {
			"detected": bool,
			"date": str,
			"volume": int,
			"ipo_week_high": int,
			"multiple": float
		},
		"hv1": {
			"detected": bool,
			"date": str,
			"volume": int,
			"year_high": int,
			"multiple": float
		},
		"increasing_avg_volume": {
			"detected": bool,
			"periods": list[dict],
			"stepwise_increase": bool
		},
		"volume_run_rate": {
			"current_run_rate": int,
			"ratio_vs_20d_avg": float,
			"ratio_vs_50d_avg": float,
			"interpretation": str
		},
		"conviction_level": str,
		"price_context": {
			"price_change_on_edge_day": float,
			"closing_range_pct": float,
			"direction": str
		}
	}

	For screen:
	dict: {
		"results": [
			{
				"symbol": str,
				"edges_detected": list[str],
				"edge_count": int,
				"conviction_level": str,
				"latest_edge_date": str,
				"latest_edge_type": str
			}
		],
		"ranked_by": str
	}

Example:
	>>> python volume_edge.py detect NVDA --period 2y --lookback 20
	{
		"symbol": "NVDA",
		"date": "2026-02-19",
		"current_price": 142.50,
		"edges_detected": ["HV1"],
		"edge_count": 1,
		"hve": {"detected": false},
		"hvipo": {"detected": false},
		"hv1": {
			"detected": true,
			"date": "2026-02-15",
			"volume": 98000000,
			"year_high": 85000000,
			"multiple": 1.15
		},
		"increasing_avg_volume": {
			"detected": true,
			"stepwise_increase": true
		},
		"volume_run_rate": {
			"current_run_rate": 72000000,
			"ratio_vs_20d_avg": 1.35,
			"ratio_vs_50d_avg": 1.22,
			"interpretation": "elevated"
		},
		"conviction_level": "moderate"
	}

	>>> python volume_edge.py screen AAPL NVDA MSFT META GOOGL --lookback 10
	{
		"results": [
			{"symbol": "NVDA", "edges_detected": ["HV1"], "edge_count": 1, ...},
			{"symbol": "META", "edges_detected": [], "edge_count": 0, ...}
		],
		"ranked_by": "edge_count"
	}

Use Cases:
	- Confirm breakout validity with historically significant volume
	- Screen multiple stocks for recent volume edge events
	- Detect HVE/HVIPO as highest-conviction institutional entry signals
	- Monitor increasing average volume as stealth accumulation indicator
	- Use volume run rate intraday to project whether volume edge is forming

Notes:
	- HVE (Highest Volume Ever): current/recent volume > all-time highest volume
	- HVIPO (Highest Volume since IPO): volume > highest since first week of trading
	- HV1 (Highest Volume in 1 Year): volume > highest in last 252 trading days
	- Hierarchy: HVE > HVIPO > HV1 in signal strength
	- HVE on price advance = extremely rare and bullish (major institutional entry)
	- HVE on price decline = potential capitulation or distribution climax
	- Increasing average volume over 3+ periods indicates stealth accumulation
	- Volume run rate extrapolates partial-day volume to full-session estimate
	- Edge events are most meaningful when accompanied by price breakout above pivot
	- Data period affects detection: use "max" for HVE, "2y" for HV1

See Also:
	- volume_analysis.py: Accumulation/distribution grading and up/down ratio
	- closing_range.py: Bar quality classification complements volume edge
	- vcp.py: VCP detection where volume contraction precedes edge events
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import yfinance as yf
from utils import output_json, safe_run


def _detect_hve(volumes, lookback):
	"""Detect Highest Volume Ever within the lookback window.

	Compares recent volume bars against the all-time high volume
	across the entire dataset.
	"""
	if len(volumes) < 2:
		return {"detected": False}

	recent = volumes.tail(lookback)
	# All-time high volume BEFORE the lookback window
	prior = volumes.iloc[:-lookback] if len(volumes) > lookback else volumes.iloc[:1]
	prior_max = float(prior.max()) if len(prior) > 0 else 0

	for i in range(len(recent) - 1, -1, -1):
		vol = float(recent.iloc[i])
		# Must exceed ALL prior volume including within lookback
		all_other_max = max(prior_max, float(volumes.iloc[:volumes.index.get_loc(recent.index[i])].max())) if volumes.index.get_loc(recent.index[i]) > 0 else 0
		if vol > all_other_max and all_other_max > 0:
			return {
				"detected": True,
				"date": str(recent.index[i].date()),
				"volume": int(vol),
				"previous_high": int(all_other_max),
				"multiple": round(vol / all_other_max, 2),
			}

	return {"detected": False}


def _detect_hvipo(volumes, lookback, ipo_window=5):
	"""Detect Highest Volume since IPO week.

	Compares recent volume against highest volume excluding
	the first trading week (IPO week often has anomalous volume).
	"""
	if len(volumes) <= ipo_window:
		return {"detected": False}

	ipo_week_max = float(volumes.iloc[:ipo_window].max())
	post_ipo = volumes.iloc[ipo_window:]

	if len(post_ipo) < lookback:
		return {"detected": False}

	recent = post_ipo.tail(lookback)
	prior_post_ipo = post_ipo.iloc[:-lookback] if len(post_ipo) > lookback else post_ipo.iloc[:1]
	prior_max = float(prior_post_ipo.max()) if len(prior_post_ipo) > 0 else 0

	for i in range(len(recent) - 1, -1, -1):
		vol = float(recent.iloc[i])
		# Find max of all post-IPO volume before this bar
		idx_in_post_ipo = post_ipo.index.get_loc(recent.index[i])
		all_prior = float(post_ipo.iloc[:idx_in_post_ipo].max()) if idx_in_post_ipo > 0 else 0
		if vol > all_prior and all_prior > 0:
			return {
				"detected": True,
				"date": str(recent.index[i].date()),
				"volume": int(vol),
				"ipo_week_high": int(ipo_week_max),
				"post_ipo_previous_high": int(all_prior),
				"multiple": round(vol / all_prior, 2),
			}

	return {"detected": False}


def _detect_hv1(volumes, lookback, year_days=252):
	"""Detect Highest Volume in 1 Year within the lookback window.

	Compares recent volume against the highest volume in
	the last 252 trading days (1 year).
	"""
	if len(volumes) < year_days:
		# Use all available data if less than 1 year
		year_data = volumes
	else:
		year_data = volumes.tail(year_days)

	recent = year_data.tail(lookback)
	prior = year_data.iloc[:-lookback] if len(year_data) > lookback else year_data.iloc[:1]
	prior_max = float(prior.max()) if len(prior) > 0 else 0

	for i in range(len(recent) - 1, -1, -1):
		vol = float(recent.iloc[i])
		idx_in_year = year_data.index.get_loc(recent.index[i])
		all_prior_year = float(year_data.iloc[:idx_in_year].max()) if idx_in_year > 0 else 0
		if vol > all_prior_year and all_prior_year > 0:
			return {
				"detected": True,
				"date": str(recent.index[i].date()),
				"volume": int(vol),
				"year_high": int(all_prior_year),
				"multiple": round(vol / all_prior_year, 2),
			}

	return {"detected": False}


def _detect_increasing_avg_volume(volumes, periods=(10, 20, 50)):
	"""Detect stepwise increase in average volume across periods.

	Checks if shorter-period averages are higher than longer-period averages,
	indicating building volume momentum (stealth accumulation).
	"""
	if len(volumes) < max(periods):
		return {"detected": False, "periods": [], "stepwise_increase": False}

	avgs = []
	for p in sorted(periods):
		avg = float(volumes.tail(p).mean())
		avgs.append({"period": p, "avg_volume": int(avg)})

	# Stepwise: each shorter period avg > longer period avg
	stepwise = True
	for i in range(len(avgs) - 1):
		if avgs[i]["avg_volume"] <= avgs[i + 1]["avg_volume"]:
			stepwise = False
			break

	return {
		"detected": stepwise,
		"periods": avgs,
		"stepwise_increase": stepwise,
	}


def _calc_volume_run_rate(current_volume, volumes):
	"""Calculate volume run rate and compare to averages.

	Run rate estimates full-day volume based on current volume.
	Since we use daily data (end-of-day), current_volume IS the full day.
	We compare it against 20-day and 50-day averages.
	"""
	avg_20 = float(volumes.tail(20).mean()) if len(volumes) >= 20 else float(volumes.mean())
	avg_50 = float(volumes.tail(50).mean()) if len(volumes) >= 50 else float(volumes.mean())

	ratio_20 = round(current_volume / avg_20, 2) if avg_20 > 0 else 0
	ratio_50 = round(current_volume / avg_50, 2) if avg_50 > 0 else 0

	if ratio_20 >= 2.0:
		interpretation = "extreme"
	elif ratio_20 >= 1.5:
		interpretation = "very_elevated"
	elif ratio_20 >= 1.2:
		interpretation = "elevated"
	elif ratio_20 >= 0.8:
		interpretation = "normal"
	else:
		interpretation = "below_average"

	return {
		"current_volume": int(current_volume),
		"avg_20d": int(avg_20),
		"avg_50d": int(avg_50),
		"ratio_vs_20d_avg": ratio_20,
		"ratio_vs_50d_avg": ratio_50,
		"interpretation": interpretation,
	}


def _price_context(data, edge_date=None):
	"""Get price context for the edge day or latest bar."""
	if edge_date:
		try:
			idx = data.index.get_loc(edge_date)
		except KeyError:
			idx = -1
	else:
		idx = -1

	h = float(data["High"].iloc[idx])
	l = float(data["Low"].iloc[idx])
	c = float(data["Close"].iloc[idx])

	cr = round((c - l) / (h - l) * 100, 1) if h != l else 50.0

	if idx > 0:
		prev_c = float(data["Close"].iloc[idx - 1])
		price_chg = round((c / prev_c - 1) * 100, 2) if prev_c != 0 else 0
	else:
		price_chg = 0

	direction = "up" if price_chg > 0.2 else ("down" if price_chg < -0.2 else "flat")

	return {
		"price_change_on_edge_day": price_chg,
		"closing_range_pct": cr,
		"direction": direction,
	}


def _conviction_level(edges_detected, hve, hvipo, hv1, inc_avg, run_rate):
	"""Determine overall conviction level from detected edges."""
	if hve.get("detected"):
		return "very_high"
	if hvipo.get("detected"):
		if inc_avg.get("stepwise_increase"):
			return "very_high"
		return "high"
	if hv1.get("detected"):
		if inc_avg.get("stepwise_increase"):
			return "high"
		return "moderate"
	if inc_avg.get("stepwise_increase"):
		return "moderate"
	if run_rate.get("ratio_vs_20d_avg", 0) >= 1.5:
		return "low_moderate"
	return "none"


@safe_run
def cmd_detect(args):
	"""Single stock comprehensive volume edge analysis."""
	symbol = args.symbol.upper()
	ticker = yf.Ticker(symbol)
	data = ticker.history(period=args.period, interval="1d")

	if data.empty or len(data) < 50:
		output_json({
			"error": f"Insufficient data for {symbol}. Need at least 50 trading days.",
			"data_points": len(data),
		})
		return

	volumes = data["Volume"]
	current_vol = float(volumes.iloc[-1])

	# Detect edge events
	hve = _detect_hve(volumes, args.lookback)
	hvipo = _detect_hvipo(volumes, args.lookback)
	hv1 = _detect_hv1(volumes, args.lookback)
	inc_avg = _detect_increasing_avg_volume(volumes)
	run_rate = _calc_volume_run_rate(current_vol, volumes.iloc[:-1])

	# Collect detected edge types
	edges = []
	if hve.get("detected"):
		edges.append("HVE")
	if hvipo.get("detected"):
		edges.append("HVIPO")
	if hv1.get("detected"):
		edges.append("HV1")
	if inc_avg.get("stepwise_increase"):
		edges.append("INCREASING_AVG")

	# Find the most significant edge date for price context
	edge_date = None
	for edge in [hve, hvipo, hv1]:
		if edge.get("detected") and edge.get("date"):
			edge_date = edge["date"]
			break

	price_ctx = _price_context(data, edge_date=None)
	conviction = _conviction_level(edges, hve, hvipo, hv1, inc_avg, run_rate)

	output_json({
		"symbol": symbol,
		"date": str(data.index[-1].date()),
		"current_price": round(float(data["Close"].iloc[-1]), 2),
		"lookback_days": args.lookback,
		"edges_detected": edges,
		"edge_count": len(edges),
		"hve": hve,
		"hvipo": hvipo,
		"hv1": hv1,
		"increasing_avg_volume": inc_avg,
		"volume_run_rate": run_rate,
		"conviction_level": conviction,
		"price_context": price_ctx,
	})


@safe_run
def cmd_screen(args):
	"""Multiple stocks recent volume edge occurrence filter."""
	results = []

	for sym in args.symbols:
		sym = sym.upper()
		try:
			ticker = yf.Ticker(sym)
			data = ticker.history(period=args.period, interval="1d")

			if data.empty or len(data) < 50:
				results.append({"symbol": sym, "error": "Insufficient data"})
				continue

			volumes = data["Volume"]
			current_vol = float(volumes.iloc[-1])

			hve = _detect_hve(volumes, args.lookback)
			hvipo = _detect_hvipo(volumes, args.lookback)
			hv1 = _detect_hv1(volumes, args.lookback)
			inc_avg = _detect_increasing_avg_volume(volumes)
			run_rate = _calc_volume_run_rate(current_vol, volumes.iloc[:-1])

			edges = []
			latest_date = None
			latest_type = None
			for label, edge in [("HVE", hve), ("HVIPO", hvipo), ("HV1", hv1)]:
				if edge.get("detected"):
					edges.append(label)
					if latest_date is None:
						latest_date = edge.get("date")
						latest_type = label
			if inc_avg.get("stepwise_increase"):
				edges.append("INCREASING_AVG")

			conviction = _conviction_level(edges, hve, hvipo, hv1, inc_avg, run_rate)

			results.append({
				"symbol": sym,
				"current_price": round(float(data["Close"].iloc[-1]), 2),
				"edges_detected": edges,
				"edge_count": len(edges),
				"conviction_level": conviction,
				"latest_edge_date": latest_date,
				"latest_edge_type": latest_type,
				"volume_vs_20d_avg": run_rate.get("ratio_vs_20d_avg", 0),
			})
		except Exception as e:
			results.append({
				"symbol": sym,
				"error": f"{type(e).__name__}: {e}",
			})

	# Sort by edge_count descending, then conviction
	conviction_order = {"very_high": 4, "high": 3, "moderate": 2, "low_moderate": 1, "none": 0}
	valid = [r for r in results if "edge_count" in r]
	errors = [r for r in results if "edge_count" not in r]
	valid.sort(
		key=lambda x: (x["edge_count"], conviction_order.get(x.get("conviction_level", "none"), 0)),
		reverse=True,
	)

	output_json({
		"results": valid + errors,
		"ranked_by": "edge_count",
		"period": args.period,
		"lookback_days": args.lookback,
		"symbols_analyzed": len(results),
	})


def main():
	parser = argparse.ArgumentParser(
		description="Volume Edge Detection: extreme volume events"
	)
	sub = parser.add_subparsers(dest="command", required=True)

	# detect
	sp = sub.add_parser("detect", help="Single stock volume edge analysis")
	sp.add_argument("symbol", help="Ticker symbol")
	sp.add_argument("--period", default="2y", help="Data period (default: 2y)")
	sp.add_argument(
		"--lookback", type=int, default=20,
		help="Days to check for recent edges (default: 20)",
	)
	sp.set_defaults(func=cmd_detect)

	# screen
	sp = sub.add_parser("screen", help="Multi-stock volume edge screening")
	sp.add_argument("symbols", nargs="+", help="Ticker symbols to screen")
	sp.add_argument("--period", default="2y", help="Data period (default: 2y)")
	sp.add_argument(
		"--lookback", type=int, default=20,
		help="Days to check for recent edges (default: 20)",
	)
	sp.set_defaults(func=cmd_screen)

	args = parser.parse_args()
	args.func(args)


if __name__ == "__main__":
	main()
