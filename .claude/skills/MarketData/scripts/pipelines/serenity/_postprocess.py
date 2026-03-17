"""Post-processing helpers for Serenity pipeline outputs.

Functions that compress, summarize, or trim raw module data
before it is included in the final pipeline response.
"""


def _summarize_insider_transactions(data):
	"""Summarize insider transactions with by_insider aggregation.

	Filters to Sale/Buy only (excludes Proposed Sale and Option Exercise),
	groups by insider name, and computes per-insider and overall summary.
	"""
	records = data if isinstance(data, list) else []
	if not records:
		return data

	# Filter: keep only Sale and Buy (removes Proposed Sale duplicates + Option Exercise noise)
	filtered = [r for r in records if isinstance(r, dict) and r.get("transaction") in ("Sale", "Buy")]

	# Aggregate by insider
	insiders = {}
	for txn in filtered:
		name = txn.get("insider", "")
		if not name:
			continue
		if name not in insiders:
			insiders[name] = {
				"insider": name,
				"relationship": txn.get("relationship", ""),
				"buy_count": 0, "buy_amount": 0,
				"sell_count": 0, "sell_amount": 0,
			}
		entry = insiders[name]
		value = txn.get("value") or 0
		# Pick the most specific (longest) relationship for this insider
		rel = txn.get("relationship", "")
		if len(rel) > len(entry["relationship"]):
			entry["relationship"] = rel

		if txn.get("transaction") == "Buy":
			entry["buy_count"] += 1
			entry["buy_amount"] += value
		elif txn.get("transaction") == "Sale":
			entry["sell_count"] += 1
			entry["sell_amount"] += value

	# Compute net_amount and sort by abs(net_amount) descending
	by_insider = []
	for entry in insiders.values():
		entry["net_amount"] = entry["buy_amount"] - entry["sell_amount"]
		by_insider.append(entry)
	by_insider.sort(key=lambda x: abs(x["net_amount"]), reverse=True)
	by_insider = by_insider[:15]

	# Overall summary
	total_buy_count = sum(e["buy_count"] for e in insiders.values())
	total_sell_count = sum(e["sell_count"] for e in insiders.values())
	total_buy_amount = sum(e["buy_amount"] for e in insiders.values())
	total_sell_amount = sum(e["sell_amount"] for e in insiders.values())

	if total_buy_amount > total_sell_amount * 1.2:
		net_direction = "net_buying"
	elif total_sell_amount > total_buy_amount * 1.2:
		net_direction = "net_selling"
	else:
		net_direction = "mixed"

	return {
		"summary": {
			"total_transactions": len(filtered),
			"buy_count": total_buy_count,
			"sell_count": total_sell_count,
			"buy_amount": total_buy_amount,
			"sell_amount": total_sell_amount,
			"net_direction": net_direction,
			"net_value": total_buy_amount - total_sell_amount,
			"thresholds": "net_buying: buy_amount > sell_amount \u00d7 1.2 | net_selling: sell_amount > buy_amount \u00d7 1.2 | mixed: otherwise",
		},
		"by_insider": by_insider,
	}


def _extract_revenue_trajectory(financials_data):
	"""Extract quarterly revenue trajectory from income statement data."""
	revenue_by_quarter = []

	if isinstance(financials_data, dict):
		records = financials_data.get("data", financials_data)
		if isinstance(records, dict):
			rev_data = records.get("TotalRevenue") or records.get("Total Revenue")
			if isinstance(rev_data, dict):
				for quarter, revenue in list(rev_data.items())[:8]:
					revenue_by_quarter.append({
						"quarter": str(quarter),
						"revenue": revenue,
					})
			else:
				for date_key, row in list(records.items())[:8]:
					if isinstance(row, dict):
						rev = row.get("TotalRevenue") or row.get("Total Revenue")
						if rev is not None:
							revenue_by_quarter.append({
								"quarter": str(date_key),
								"revenue": rev,
							})
	elif isinstance(financials_data, list):
		for record in financials_data[:8]:
			if isinstance(record, dict):
				quarter = record.get("quarter") or record.get("date") or record.get("period")
				rev = record.get("TotalRevenue") or record.get("Total Revenue") or record.get("revenue")
				if quarter and rev is not None:
					revenue_by_quarter.append({
						"quarter": str(quarter),
						"revenue": rev,
					})

	return {"revenue_by_quarter": revenue_by_quarter}


def _cap_earnings_dates(data, limit=8):
	"""Cap earnings_dates to the most recent N entries."""
	if not isinstance(data, dict) or data.get("error"):
		return data
	trimmed = {}
	for col, values in data.items():
		if isinstance(values, dict):
			trimmed[col] = dict(list(values.items())[:limit])
		else:
			trimmed[col] = values
	return trimmed


def _compress_earnings_acceleration(data):
	"""Compress earnings_acceleration output to essential metrics.

	Removes symbol and code33_status (Minervini terminology).
	"""
	if not isinstance(data, dict) or data.get("error"):
		return data
	result = {
		"eps_accelerating": data.get("eps_accelerating"),
		"margin_expanding": data.get("margin_expanding"),
		"eps_growth_rates": data.get("eps_growth_rates", [])[:3],
		"data_quality": data.get("data_quality"),
	}
	# Only include sales fields when data is available (yfinance quarterly_income_stmt
	# rarely provides enough quarters for YoY acceleration, so these are usually empty)
	sales_rates = data.get("sales_growth_rates", [])
	if sales_rates:
		result["sales_accelerating"] = data.get("sales_accelerating")
		result["sales_growth_rates"] = sales_rates[:3]
	return result


def _summarize_holders(data):
	"""Summarize institutional holders to top 5 with key fields only."""
	if not isinstance(data, dict) or data.get("error"):
		return data

	holders_list = []
	holder_names = data.get("Holder", {})
	pct_held = data.get("pctHeld", {})
	shares = data.get("Shares", {})

	if holder_names:
		for idx in sorted(holder_names.keys(), key=lambda x: int(x))[:5]:
			holders_list.append({
				"holder": holder_names.get(idx),
				"pctHeld": pct_held.get(idx),
				"shares": shares.get(idx),
			})

	return {
		"top_holders": holders_list,
		"total_reported": len(holder_names),
	}


def _merge_earnings(earnings_dates, earnings_surprise):
	"""Merge earnings_dates and earnings_surprise into unified earnings object.

	Restructures flat surprise entries from cmd_surprise into nested schema:
	- eps sub-object: estimate, actual, surprise_pct, pct_skipped_reason, beat, yoy_pct, qoq_pct
	- revenue sub-object: actual, yoy_pct, qoq_pct
	- post_er_* fields remain at top level

	Returns:
		dict with next_report, surprise_history (nested), consecutive_beats,
		avg_surprise_pct, cockroach_effect
	"""
	result = {}

	# Next report from earnings_dates
	if isinstance(earnings_dates, dict) and not earnings_dates.get("error"):
		dates_col = earnings_dates.get("Earnings Date", {})
		eps_est_col = earnings_dates.get("EPS Estimate", {})
		if isinstance(dates_col, dict) and dates_col:
			first_key = next(iter(dates_col), None)
			if first_key is not None:
				result["next_report"] = {
					"date": dates_col.get(first_key),
					"eps_estimate": eps_est_col.get(first_key) if isinstance(eps_est_col, dict) else None,
				}

	# Surprise history from earnings_surprise — restructure flat → nested
	surprise = earnings_surprise if isinstance(earnings_surprise, dict) and not earnings_surprise.get("error") else {}
	history = surprise.get("history") or surprise.get("surprise_history") or []

	nested_history = []
	if isinstance(history, list):
		for entry in history[:8]:
			if not isinstance(entry, dict):
				continue
			nested_entry = {
				"date": entry.get("date"),
				"eps": {
					"estimate": entry.get("estimate"),
					"actual": entry.get("actual"),
					"surprise_pct": entry.get("surprise_pct"),
					"pct_skipped_reason": entry.get("pct_skipped_reason"),
					"beat": entry.get("beat"),
					"yoy_pct": entry.get("eps_yoy_pct"),
					"qoq_pct": entry.get("eps_qoq_pct"),
				},
				"revenue": {
					"actual": entry.get("revenue"),
					"yoy_pct": entry.get("revenue_yoy_pct"),
					"qoq_pct": entry.get("revenue_qoq_pct"),
				},
				"post_er_gap": entry.get("post_er_gap"),
				"post_er_return_1d": entry.get("post_er_return_1d"),
				"post_er_return_5d": entry.get("post_er_return_5d"),
			}
			nested_history.append(nested_entry)

	result["surprise_history"] = nested_history
	result["consecutive_beats"] = surprise.get("consecutive_beats")
	result["avg_surprise_pct"] = surprise.get("avg_surprise_pct")

	# Cockroach effect classification
	beats = surprise.get("consecutive_beats")
	if isinstance(beats, (int, float)):
		if beats >= 4:
			result["cockroach_effect"] = "strong"
		elif beats >= 2:
			result["cockroach_effect"] = "moderate"
		else:
			result["cockroach_effect"] = "weak"
	else:
		result["cockroach_effect"] = "unknown"

	return result


def _reformat_analyst_recommendations(data):
	"""Reformat analyst_recommendations from column-oriented to row-oriented.

	Converts {"strongBuy": {"0": 6, "1": 5, ...}} format to
	[{"period": "current", "strongBuy": 6, "buy": 25, ...}, ...] format.
	"""
	if not isinstance(data, dict) or data.get("error"):
		return data

	period_labels = ["current", "-1m", "-2m", "-3m"]
	categories = ["strongBuy", "buy", "hold", "sell", "strongSell"]

	# Determine number of periods from any available category
	max_periods = 0
	for cat in categories:
		col = data.get(cat)
		if isinstance(col, dict):
			max_periods = max(max_periods, len(col))

	rows = []
	for i in range(min(max_periods, len(period_labels))):
		row = {"period": period_labels[i]}
		for cat in categories:
			col = data.get(cat, {})
			if isinstance(col, dict):
				row[cat] = col.get(str(i))
			else:
				row[cat] = None
		rows.append(row)

	return rows


def _clean_analyst_revisions(data, earnings_estimate=None, revenue_estimate=None):
	"""Merge eps_revisions, eps_trend, growth_estimates, earnings_estimate,
	and revenue_estimate into horizon-based structure with nested eps/revenue sub-objects.

	Converts column-oriented yfinance data into per-horizon objects with
	computed trend direction and net revision counts.

	Args:
		data: Raw analyst_revisions output (eps_revisions, eps_trend, growth_estimates)
		earnings_estimate: Optional earnings estimate data (avg, low, high, yearAgoEps, growth per horizon)
		revenue_estimate: Optional revenue estimate data (avg, low, high, yearAgoRevenue, growth per horizon)
	"""
	if not isinstance(data, dict) or data.get("error"):
		return data

	eps_rev = data.get("eps_revisions") or {}
	eps_trend = data.get("eps_trend") or {}

	# Normalize estimate data (handle error responses)
	if isinstance(earnings_estimate, dict) and earnings_estimate.get("error"):
		earnings_estimate = None
	if isinstance(revenue_estimate, dict) and revenue_estimate.get("error"):
		revenue_estimate = None

	horizons = ("0q", "+1q", "0y", "+1y")
	by_horizon = {}

	total_up_7d = 0
	total_down_7d = 0
	total_up_30d = 0
	total_down_30d = 0
	rising_count = 0
	falling_count = 0
	comparable_count = 0

	# Pre-extract column dicts (eps_trend)
	trend_current = eps_trend.get("current", {}) if isinstance(eps_trend, dict) else {}
	trend_7d = eps_trend.get("7daysAgo", {}) if isinstance(eps_trend, dict) else {}
	trend_30d = eps_trend.get("30daysAgo", {}) if isinstance(eps_trend, dict) else {}
	trend_90d = eps_trend.get("90daysAgo", {}) if isinstance(eps_trend, dict) else {}

	# Pre-extract column dicts (eps_revisions)
	up7_col = eps_rev.get("upLast7days", {}) if isinstance(eps_rev, dict) else {}
	down7_col = eps_rev.get("downLast7days", {}) if isinstance(eps_rev, dict) else {}
	up30_col = eps_rev.get("upLast30days", {}) if isinstance(eps_rev, dict) else {}
	down30_col = eps_rev.get("downLast30days", {}) if isinstance(eps_rev, dict) else {}

	# Pre-extract earnings_estimate columns
	ee_avg = earnings_estimate.get("avg", {}) if isinstance(earnings_estimate, dict) else {}
	ee_low = earnings_estimate.get("low", {}) if isinstance(earnings_estimate, dict) else {}
	ee_high = earnings_estimate.get("high", {}) if isinstance(earnings_estimate, dict) else {}
	ee_yago = earnings_estimate.get("yearAgoEps", {}) if isinstance(earnings_estimate, dict) else {}
	ee_growth = earnings_estimate.get("growth", {}) if isinstance(earnings_estimate, dict) else {}

	# Pre-extract revenue_estimate columns
	re_avg = revenue_estimate.get("avg", {}) if isinstance(revenue_estimate, dict) else {}
	re_low = revenue_estimate.get("low", {}) if isinstance(revenue_estimate, dict) else {}
	re_high = revenue_estimate.get("high", {}) if isinstance(revenue_estimate, dict) else {}
	re_growth = revenue_estimate.get("growth", {}) if isinstance(revenue_estimate, dict) else {}

	for h in horizons:
		# Build eps sub-object
		eps_entry = {}
		if isinstance(trend_current, dict) and h in trend_current:
			eps_entry["current"] = trend_current[h]
		if isinstance(trend_7d, dict) and h in trend_7d:
			eps_entry["7d_ago"] = trend_7d[h]
		if isinstance(trend_30d, dict) and h in trend_30d:
			eps_entry["30d_ago"] = trend_30d[h]
		if isinstance(trend_90d, dict) and h in trend_90d:
			eps_entry["90d_ago"] = trend_90d[h]

		# EPS low/high/yoy_pct from earnings_estimate
		if isinstance(ee_low, dict) and h in ee_low:
			eps_entry["low"] = ee_low[h]
		if isinstance(ee_high, dict) and h in ee_high:
			eps_entry["high"] = ee_high[h]
		if isinstance(ee_growth, dict) and h in ee_growth:
			g = ee_growth[h]
			eps_entry["yoy_pct"] = round(g * 100, 2) if isinstance(g, (int, float)) else None

		# eps_revisions fields
		if isinstance(up7_col, dict) and h in up7_col:
			val = up7_col[h] or 0
			eps_entry["up_7d"] = up7_col[h]
			total_up_7d += val
		if isinstance(down7_col, dict) and h in down7_col:
			val = down7_col[h] or 0
			eps_entry["down_7d"] = down7_col[h]
			total_down_7d += val
		if isinstance(up30_col, dict) and h in up30_col:
			val = up30_col[h] or 0
			eps_entry["up_30d"] = up30_col[h]
			total_up_30d += val
		if isinstance(down30_col, dict) and h in down30_col:
			val = down30_col[h] or 0
			eps_entry["down_30d"] = down30_col[h]
			total_down_30d += val

		# Build revenue sub-object from revenue_estimate
		rev_entry = {}
		if isinstance(re_avg, dict) and h in re_avg:
			rev_entry["avg"] = re_avg[h]
		if isinstance(re_low, dict) and h in re_low:
			rev_entry["low"] = re_low[h]
		if isinstance(re_high, dict) and h in re_high:
			rev_entry["high"] = re_high[h]
		if isinstance(re_growth, dict) and h in re_growth:
			g = re_growth[h]
			rev_entry["yoy_pct"] = round(g * 100, 2) if isinstance(g, (int, float)) else None

		# Build horizon entry with nested eps/revenue
		horizon_entry = {}
		if eps_entry:
			horizon_entry["eps"] = eps_entry
		if rev_entry:
			horizon_entry["revenue"] = rev_entry

		if horizon_entry:
			by_horizon[h] = horizon_entry

		# trend_direction: compare eps current vs 30d_ago per horizon
		eps_cur = eps_entry.get("current")
		eps_30d_val = eps_entry.get("30d_ago")
		if isinstance(eps_cur, (int, float)) and isinstance(eps_30d_val, (int, float)):
			comparable_count += 1
			if eps_cur > eps_30d_val:
				rising_count += 1
			elif eps_cur < eps_30d_val:
				falling_count += 1

	# Majority rule for trend_direction
	if comparable_count > 0 and rising_count > comparable_count / 2:
		trend_direction = "rising"
	elif comparable_count > 0 and falling_count > comparable_count / 2:
		trend_direction = "falling"
	else:
		trend_direction = "stable"

	return {
		"by_horizon": by_horizon,
		"trend_direction": trend_direction,
		"net_revisions_7d": total_up_7d - total_down_7d,
		"net_revisions_30d": total_up_30d - total_down_30d,
		"thresholds": "trend_direction: rising(majority horizons eps current > eps 30d_ago) | falling(majority <) | stable(mixed)",
	}
