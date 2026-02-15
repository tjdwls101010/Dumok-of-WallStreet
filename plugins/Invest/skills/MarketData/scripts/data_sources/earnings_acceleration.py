#!/usr/bin/env python3
"""Earnings Acceleration Analysis: Code 33 validation and earnings pattern detection.

Analyzes earnings acceleration patterns based on Mark Minervini's SEPA methodology.
Detects Code 33 (Triple Acceleration: EPS + Sales + Margins all accelerating for 3 quarters),
earnings surprise history, and analyst revision trends.

Commands:
	code33: Check for Code 33 (Triple Acceleration) pattern
	acceleration: Analyze quarterly EPS and sales growth trends
	surprise: Get earnings surprise history and post-earnings drift signals
	revisions: Track analyst estimate revision trends

Args:
	symbol (str): Ticker symbol (e.g., "AAPL", "NVDA", "META")

Returns:
	For code33:
		dict: {
			"symbol": str,
			"code33_status": str,
			"eps_accelerating": bool,
			"sales_accelerating": bool,
			"margin_expanding": bool,
			"quarters_analyzed": int,
			"eps_growth_rates": [float],
			"sales_growth_rates": [float],
			"margin_trend": [float],
			"eps_quarters_available": int,
			"sales_quarters_available": int,
			"data_quality": str
		}

	For acceleration:
		dict: {
			"symbol": str,
			"eps_acceleration": [{"quarter": str, "growth_rate": float, "accelerating": bool}],
			"sales_acceleration": [{"quarter": str, "growth_rate": float, "accelerating": bool}],
			"overall_trend": str
		}

	For surprise:
		dict: {
			"symbol": str,
			"surprise_history": [{
				"date": str, "estimate": float, "actual": float,
				"surprise_pct": float, "pct_skipped_reason": str,
				"post_er_return_1d": float,
				"post_er_return_5d": float, "post_er_gap": float
			}],
			"consecutive_beats": int,
			"avg_surprise_pct": float,
			"avg_surprise_method": str,
			"cockroach_effect": str
		}

	For revisions:
		dict: {
			"symbol": str,
			"revision_direction": str,
			"current_quarter_revisions": dict,
			"next_quarter_revisions": dict
		}

Example:
	>>> python earnings_acceleration.py code33 NVDA
	{
		"symbol": "NVDA",
		"code33_status": "PASS",
		"eps_accelerating": true,
		"sales_accelerating": true,
		"margin_expanding": true,
		"eps_growth_rates": [25.3, 38.5, 52.1],
		"sales_growth_rates": [18.2, 28.7, 42.3]
	}

	>>> python earnings_acceleration.py acceleration AAPL
	{
		"symbol": "AAPL",
		"eps_acceleration": [
			{"quarter": "2025Q4", "growth_rate": 12.5, "accelerating": true},
			{"quarter": "2025Q3", "growth_rate": 8.2, "accelerating": false}
		],
		"overall_trend": "accelerating"
	}

	>>> python earnings_acceleration.py surprise NVDA
	{
		"symbol": "NVDA",
		"surprise_history": [
			{
				"date": "2025-11-20",
				"estimate": 0.81,
				"actual": 0.89,
				"surprise_pct": 9.88,
				"beat": true,
				"post_er_return_1d": 3.25,
				"post_er_return_5d": 5.12,
				"post_er_gap": 2.10
			}
		],
		"consecutive_beats": 4,
		"avg_surprise_pct": 8.45,
		"cockroach_effect": "strong",
		"total_quarters_analyzed": 8
	}

Use Cases:
	- Validate Code 33 for SEPA methodology stock selection
	- Track earnings momentum for position management
	- Identify cockroach effect (one surprise predicts more)
	- Monitor analyst revisions for sentiment shifts

Notes:
	- Code 33 requires 3 consecutive quarters of acceleration in ALL three metrics
	- EPS growth rates compare to same quarter prior year (YoY)
	- Margin expansion uses gross or operating margin trend
	- Analyst revisions of 5%+ are significant per Minervini
	- Post-Earnings Drift: market underreacts to earnings surprises
	- Data quality levels: full (3+ quarters), partial (2 quarters), minimal (0-1 quarters)
	- Surprise % set to null when |estimate| < 0.05 (near-zero denominator floor)
	- Average surprise uses trimmed mean (top/bottom 10% removed) when 5+ data points available

See Also:
	- trend_template.py: Trend Template check (price-based qualification)
	- stage_analysis.py: Stage classification (technical context)
	- sepa_pipeline.py: Full SEPA pipeline integrating all checks
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import yfinance as yf
from utils import error_json, output_json, safe_run


def _get_quarterly_financials(symbol):
	"""Retrieve quarterly income statement data and earnings dates.

	Tries ticker.quarterly_income_stmt first for broader historical coverage
	(8+ quarters), falls back to get_income_stmt(freq="quarterly") if unavailable.
	"""
	ticker = yf.Ticker(symbol)

	# Try quarterly_income_stmt for more historical quarters
	income = None
	try:
		qi = ticker.quarterly_income_stmt
		if qi is not None and not qi.empty and len(qi.columns) >= 4:
			income = qi
	except Exception:
		pass

	# Fallback to standard API
	if income is None or income.empty:
		income = ticker.get_income_stmt(freq="quarterly")

	return ticker, income


def _get_eps_growth_from_earnings_dates(ticker, limit=12):
	"""Extract YoY EPS growth from earnings_dates (up to 12 quarters).

	earnings_dates provides more historical EPS data than income statements.
	Returns list of (quarter_label, growth_rate) tuples, most recent first.
	"""
	try:
		ed = ticker.get_earnings_dates(limit=limit)
	except Exception:
		return []

	if ed is None or ed.empty or "Reported EPS" not in ed.columns:
		return []

	# Filter rows with actual reported EPS
	ed = ed.dropna(subset=["Reported EPS"])
	if len(ed) < 5:  # Need at least 5 quarters for 1 YoY comparison
		return []

	# Sort by date descending
	ed = ed.sort_index(ascending=False)
	eps_values = list(zip(ed.index, ed["Reported EPS"]))

	results = []
	for i in range(len(eps_values)):
		current_date, current_eps = eps_values[i]
		# Find same quarter prior year (4 quarters back)
		yoy_idx = i + 4
		if yoy_idx < len(eps_values):
			prior_date, prior_eps = eps_values[yoy_idx]
			if prior_eps != 0:
				growth = ((current_eps / prior_eps) - 1) * 100
				label = str(current_date.date()) if hasattr(current_date, "date") else str(current_date)
				results.append((label, round(growth, 2)))

	return results


def _extract_growth_series(income_df, metric_name):
	"""Extract YoY growth rates for a metric across quarters.

	Returns list of (quarter_label, growth_rate) tuples, most recent first.
	"""
	if income_df is None or income_df.empty:
		return []

	# income_df columns are dates, rows are metrics
	if metric_name not in income_df.index:
		return []

	values = income_df.loc[metric_name]
	# Sort by date descending (most recent first)
	values = values.sort_index(ascending=False)

	results = []
	dates = list(values.index)

	for i, date in enumerate(dates):
		current_val = values[date]
		if current_val is None or (hasattr(current_val, "__class__") and current_val != current_val):
			continue

		# Find same quarter from prior year (4 quarters back)
		yoy_idx = i + 4
		if yoy_idx < len(dates):
			prior_val = values[dates[yoy_idx]]
			if (
				prior_val is not None
				and prior_val != 0
				and not (hasattr(prior_val, "__class__") and prior_val != prior_val)
			):
				growth = ((float(current_val) / float(prior_val)) - 1) * 100
				quarter_label = str(date.date()) if hasattr(date, "date") else str(date)
				results.append((quarter_label, round(growth, 2)))

	return results


def _is_accelerating(growth_rates, min_quarters=3):
	"""Check if growth rates are accelerating (each quarter faster than prior).

	growth_rates: list of (quarter, rate) tuples, most recent first.
	Returns (is_accelerating, rates_used).
	"""
	if len(growth_rates) < min_quarters:
		return False, []

	# Take most recent min_quarters
	recent = growth_rates[:min_quarters]
	rates = [r[1] for r in recent]

	# Accelerating means each quarter's growth > the previous quarter's growth
	# Since list is most-recent-first, rates[0] > rates[1] > rates[2]
	accelerating = all(rates[i] > rates[i + 1] for i in range(len(rates) - 1))
	# Also all positive
	all_positive = all(r > 0 for r in rates)

	return accelerating and all_positive, rates


def _assess_data_quality(eps_count, sales_count):
	"""Assess earnings data completeness for analysis reliability."""
	min_count = min(eps_count, sales_count)
	if min_count >= 3:
		return "full"
	elif min_count >= 2:
		return "partial"
	else:
		return "minimal"


@safe_run
def cmd_code33(args):
	"""Check for Code 33 (Triple Acceleration) pattern."""
	symbol = args.symbol.upper()
	ticker, income = _get_quarterly_financials(symbol)

	if income is None or income.empty:
		error_json(f"No quarterly financial data available for {symbol}")

	# EPS acceleration: prefer earnings_dates (12+ quarters) over income statement (5 quarters)
	eps_growth = _get_eps_growth_from_earnings_dates(ticker)
	eps_metric = "Reported EPS (earnings_dates)"
	if not eps_growth:
		# Fallback to income statement
		eps_metric = next(
			(
				m
				for m in ["DilutedEPS", "Diluted EPS", "BasicEPS", "Basic EPS", "NetIncome", "Net Income"]
				if m in income.index
			),
			"NetIncome",
		)
		eps_growth = _extract_growth_series(income, eps_metric)
	eps_acc, eps_rates = _is_accelerating(eps_growth)

	# Sales acceleration
	sales_metric = next(
		(m for m in ["TotalRevenue", "Total Revenue", "OperatingRevenue", "Operating Revenue"] if m in income.index),
		"TotalRevenue",
	)
	sales_growth = _extract_growth_series(income, sales_metric)
	sales_acc, sales_rates = _is_accelerating(sales_growth)

	# Margin expansion (gross margin or operating margin)
	margin_expanding = False
	margin_values = []
	gp_metric = next((m for m in ["GrossProfit", "Gross Profit"] if m in income.index), None)
	if gp_metric is not None and sales_metric in income.index:
		gross_profit = income.loc[gp_metric].sort_index(ascending=False)
		revenue = income.loc[sales_metric].sort_index(ascending=False)
		for i in range(min(4, len(gross_profit))):
			gp = gross_profit.iloc[i]
			rev = revenue.iloc[i]
			if gp is not None and rev is not None and rev != 0:
				gp_f = float(gp) if not (hasattr(gp, "__class__") and gp != gp) else 0
				rev_f = float(rev) if not (hasattr(rev, "__class__") and rev != rev) else 1
				if rev_f != 0:
					margin_values.append(round(gp_f / rev_f * 100, 2))

		if len(margin_values) >= 3:
			# Expanding means most recent > prior quarters
			margin_expanding = all(
				margin_values[i] > margin_values[i + 1] for i in range(min(2, len(margin_values) - 1))
			)

	code33_pass = eps_acc and sales_acc and margin_expanding

	output_json(
		{
			"symbol": symbol,
			"code33_status": "PASS" if code33_pass else "FAIL",
			"eps_accelerating": eps_acc,
			"eps_metric_used": eps_metric,
			"eps_growth_rates": eps_rates,
			"eps_quarters": [q[0] for q in eps_growth[:3]] if eps_growth else [],
			"sales_accelerating": sales_acc,
			"sales_metric_used": sales_metric,
			"sales_growth_rates": sales_rates,
			"sales_quarters": [q[0] for q in sales_growth[:3]] if sales_growth else [],
			"margin_expanding": margin_expanding,
			"margin_values_pct": margin_values[:4] if margin_values else [],
			"quarters_analyzed": min(len(eps_growth), len(sales_growth)),
			"eps_quarters_available": len(eps_growth),
			"sales_quarters_available": len(sales_growth),
			"data_quality": _assess_data_quality(len(eps_growth), len(sales_growth)),
		}
	)


@safe_run
def cmd_acceleration(args):
	"""Analyze quarterly EPS and sales growth acceleration trends."""
	symbol = args.symbol.upper()
	ticker, income = _get_quarterly_financials(symbol)

	if income is None or income.empty:
		error_json(f"No quarterly financial data available for {symbol}")

	# EPS acceleration: prefer earnings_dates (12+ quarters) over income statement
	eps_growth = _get_eps_growth_from_earnings_dates(ticker)
	eps_metric = "Reported EPS (earnings_dates)"
	if not eps_growth:
		eps_metric = next(
			(
				m
				for m in ["DilutedEPS", "Diluted EPS", "BasicEPS", "Basic EPS", "NetIncome", "Net Income"]
				if m in income.index
			),
			"NetIncome",
		)
		eps_growth = _extract_growth_series(income, eps_metric)

	eps_results = []
	for i, (quarter, rate) in enumerate(eps_growth):
		acc = rate > eps_growth[i + 1][1] if i + 1 < len(eps_growth) else None
		eps_results.append(
			{
				"quarter": quarter,
				"growth_rate_yoy": rate,
				"accelerating": acc,
			}
		)

	# Sales acceleration
	sales_metric = next(
		(m for m in ["TotalRevenue", "Total Revenue", "OperatingRevenue", "Operating Revenue"] if m in income.index),
		"TotalRevenue",
	)
	sales_growth = _extract_growth_series(income, sales_metric)

	sales_results = []
	for i, (quarter, rate) in enumerate(sales_growth):
		acc = rate > sales_growth[i + 1][1] if i + 1 < len(sales_growth) else None
		sales_results.append(
			{
				"quarter": quarter,
				"growth_rate_yoy": rate,
				"accelerating": acc,
			}
		)

	# Overall trend
	if len(eps_results) >= 2:
		recent_eps_acc = eps_results[0].get("accelerating", False)
		recent_sales_acc = sales_results[0].get("accelerating", False) if sales_results else False
		if recent_eps_acc and recent_sales_acc:
			overall = "strongly_accelerating"
		elif recent_eps_acc or recent_sales_acc:
			overall = "accelerating"
		elif eps_results[0]["growth_rate_yoy"] > 0:
			overall = "growing_but_decelerating"
		else:
			overall = "declining"
	else:
		overall = "insufficient_data"

	output_json(
		{
			"symbol": symbol,
			"eps_metric_used": eps_metric,
			"eps_acceleration": eps_results,
			"sales_metric_used": sales_metric,
			"sales_acceleration": sales_results,
			"overall_trend": overall,
		}
	)


def _enrich_post_er_reactions(ticker, surprises):
	"""Add post-earnings price reaction fields to each surprise entry.

	For each earnings date, fetches surrounding price data and calculates:
	- post_er_return_1d: return from pre-ER close to next day close (%)
	- post_er_return_5d: return from pre-ER close to 5th trading day close (%)
	- post_er_gap: gap from pre-ER close to next day open (%)

	Modifies surprises list in-place. Sets fields to None if data unavailable.
	"""
	from datetime import timedelta

	import pandas as pd

	if not surprises:
		return

	# Parse all earnings dates
	er_dates = []
	for s in surprises:
		try:
			dt = pd.Timestamp(s["date"])
			er_dates.append(dt)
		except (ValueError, TypeError):
			er_dates.append(None)

	# Find date range for a single batch history fetch
	valid_dates = [d for d in er_dates if d is not None]
	if not valid_dates:
		for s in surprises:
			s["post_er_return_1d"] = None
			s["post_er_return_5d"] = None
			s["post_er_gap"] = None
		return

	earliest = min(valid_dates) - timedelta(days=5)
	latest = max(valid_dates) + timedelta(days=15)

	# Fetch price history in one batch call
	try:
		hist = ticker.history(start=earliest, end=latest, auto_adjust=False)
	except Exception:
		hist = None

	if hist is None or hist.empty:
		for s in surprises:
			s["post_er_return_1d"] = None
			s["post_er_return_5d"] = None
			s["post_er_gap"] = None
		return

	# Normalize index to date-only for reliable comparison
	hist.index = hist.index.normalize()
	if hist.index.tz is not None:
		hist.index = hist.index.tz_localize(None)

	for i, s in enumerate(surprises):
		er_dt = er_dates[i]
		if er_dt is None:
			s["post_er_return_1d"] = None
			s["post_er_return_5d"] = None
			s["post_er_gap"] = None
			continue

		try:
			er_dt_norm = pd.Timestamp(er_dt).normalize()

			# Find pre-ER close: last trading day on or before earnings date
			mask_on_or_before = hist.index <= er_dt_norm
			if not mask_on_or_before.any():
				s["post_er_return_1d"] = None
				s["post_er_return_5d"] = None
				s["post_er_gap"] = None
				continue

			pre_er_idx = hist.index[mask_on_or_before][-1]
			pre_er_close = float(hist.loc[pre_er_idx, "Close"])

			if pre_er_close <= 0:
				s["post_er_return_1d"] = None
				s["post_er_return_5d"] = None
				s["post_er_gap"] = None
				continue

			# Trading days after earnings date
			mask_after = hist.index > er_dt_norm
			days_after = hist.index[mask_after]

			# post_er_gap: next trading day open vs pre-ER close
			if len(days_after) >= 1:
				next_day = days_after[0]
				next_open = float(hist.loc[next_day, "Open"])
				s["post_er_gap"] = round((next_open / pre_er_close - 1) * 100, 2)
			else:
				s["post_er_gap"] = None

			# post_er_return_1d: next trading day close vs pre-ER close
			if len(days_after) >= 1:
				next_day = days_after[0]
				next_close = float(hist.loc[next_day, "Close"])
				s["post_er_return_1d"] = round((next_close / pre_er_close - 1) * 100, 2)
			else:
				s["post_er_return_1d"] = None

			# post_er_return_5d: 5th trading day close vs pre-ER close
			if len(days_after) >= 5:
				day5 = days_after[4]
				day5_close = float(hist.loc[day5, "Close"])
				s["post_er_return_5d"] = round((day5_close / pre_er_close - 1) * 100, 2)
			else:
				s["post_er_return_5d"] = None

		except (KeyError, IndexError, TypeError, ValueError):
			s["post_er_return_1d"] = None
			s["post_er_return_5d"] = None
			s["post_er_gap"] = None


@safe_run
def cmd_surprise(args):
	"""Get earnings surprise history and post-earnings drift signals."""
	symbol = args.symbol.upper()
	ticker = yf.Ticker(symbol)

	# Get earnings history (includes estimate vs actual)
	earnings_hist = ticker.get_earnings_history()

	if earnings_hist is None or (hasattr(earnings_hist, "empty") and earnings_hist.empty):
		error_json(f"No earnings history available for {symbol}")

	# Process earnings history
	surprises = []
	if isinstance(earnings_hist, dict):
		# Dict format from yfinance
		for date_key, row in earnings_hist.items():
			if isinstance(row, dict):
				estimate = row.get("epsEstimate") or row.get("Estimate")
				actual = row.get("epsActual") or row.get("Reported EPS") or row.get("Actual")
				if estimate is not None and actual is not None:
					try:
						est_f = float(estimate)
						act_f = float(actual)
						if abs(est_f) < 0.05:
							surprise_pct = None
							pct_skipped_reason = "estimate_near_zero"
						else:
							surprise_pct = round(((act_f - est_f) / abs(est_f) * 100), 2)
							pct_skipped_reason = None
						surprises.append(
							{
								"date": str(date_key),
								"estimate": est_f,
								"actual": act_f,
								"surprise_pct": surprise_pct,
								"pct_skipped_reason": pct_skipped_reason,
								"beat": act_f > est_f,
							}
						)
					except (ValueError, TypeError):
						pass
	else:
		# DataFrame format
		import pandas as pd

		if isinstance(earnings_hist, pd.DataFrame) and not earnings_hist.empty:
			for idx, row in earnings_hist.iterrows():
				estimate = row.get("epsEstimate", row.get("Estimate"))
				actual = row.get("epsActual", row.get("Reported EPS"))
				if estimate is not None and actual is not None:
					try:
						est_f = float(estimate)
						act_f = float(actual)
						if est_f != est_f or act_f != act_f:
							continue
						if abs(est_f) < 0.05:
							surprise_pct = None
							pct_skipped_reason = "estimate_near_zero"
						else:
							surprise_pct = round(((act_f - est_f) / abs(est_f) * 100), 2)
							pct_skipped_reason = None
						surprises.append(
							{
								"date": str(idx.date()) if hasattr(idx, "date") else str(idx),
								"estimate": est_f,
								"actual": act_f,
								"surprise_pct": surprise_pct,
								"pct_skipped_reason": pct_skipped_reason,
								"beat": act_f > est_f,
							}
						)
					except (ValueError, TypeError):
						pass

	# Sort most recent first
	surprises.sort(key=lambda x: x["date"], reverse=True)

	# Enrich with post-ER price reaction data
	_enrich_post_er_reactions(ticker, surprises)

	# Consecutive beats
	consecutive_beats = 0
	for s in surprises:
		if s["beat"]:
			consecutive_beats += 1
		else:
			break

	# Average surprise
	valid_surprises = [s["surprise_pct"] for s in surprises if s["surprise_pct"] is not None]
	if len(valid_surprises) >= 5:
		# Trimmed mean: remove top and bottom 10%
		sorted_vals = sorted(valid_surprises)
		trim_count = max(1, len(sorted_vals) // 10)
		trimmed = sorted_vals[trim_count:-trim_count]
		avg_surprise = round(sum(trimmed) / len(trimmed), 2) if trimmed else 0
		avg_surprise_method = "trimmed_mean"
	else:
		avg_surprise = round(sum(valid_surprises) / len(valid_surprises), 2) if valid_surprises else 0
		avg_surprise_method = "simple_mean"

	# Cockroach effect assessment
	if consecutive_beats >= 4:
		cockroach = "strong"
	elif consecutive_beats >= 2:
		cockroach = "moderate"
	else:
		cockroach = "none"

	output_json(
		{
			"symbol": symbol,
			"surprise_history": surprises[:8],
			"consecutive_beats": consecutive_beats,
			"avg_surprise_pct": avg_surprise,
			"avg_surprise_method": avg_surprise_method,
			"cockroach_effect": cockroach,
			"total_quarters_analyzed": len(surprises),
		}
	)


@safe_run
def cmd_revisions(args):
	"""Track analyst estimate revision trends."""
	symbol = args.symbol.upper()
	ticker = yf.Ticker(symbol)

	# EPS revisions
	eps_revisions = ticker.get_eps_revisions()
	eps_trend = ticker.get_eps_trend()
	growth_estimates = ticker.get_growth_estimates()

	output_json(
		{
			"symbol": symbol,
			"eps_revisions": eps_revisions,
			"eps_trend": eps_trend,
			"growth_estimates": growth_estimates,
			"interpretation": {
				"upward_revisions": "Positive - analysts raising estimates indicates strengthening fundamentals",
				"downward_revisions": "Negative - analysts cutting estimates signals potential weakness",
				"significance_threshold": "5%+ revision is meaningful per Minervini methodology",
			},
		}
	)


def main():
	parser = argparse.ArgumentParser(description="Earnings Acceleration Analysis")
	sub = parser.add_subparsers(dest="command", required=True)

	# code33
	sp = sub.add_parser("code33", help="Check Code 33 (Triple Acceleration)")
	sp.add_argument("symbol", help="Ticker symbol")
	sp.set_defaults(func=cmd_code33)

	# acceleration
	sp = sub.add_parser("acceleration", help="Analyze earnings acceleration trends")
	sp.add_argument("symbol", help="Ticker symbol")
	sp.set_defaults(func=cmd_acceleration)

	# surprise
	sp = sub.add_parser("surprise", help="Get earnings surprise history")
	sp.add_argument("symbol", help="Ticker symbol")
	sp.set_defaults(func=cmd_surprise)

	# revisions
	sp = sub.add_parser("revisions", help="Track analyst estimate revisions")
	sp.add_argument("symbol", help="Ticker symbol")
	sp.set_defaults(func=cmd_revisions)

	args = parser.parse_args()
	args.func(args)


if __name__ == "__main__":
	main()
