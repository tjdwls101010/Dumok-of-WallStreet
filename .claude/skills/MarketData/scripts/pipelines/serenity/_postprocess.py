"""Post-processing helpers for Serenity pipeline outputs.

Functions that compress, summarize, or trim raw module data
before it is included in the final pipeline response.
"""


def _summarize_insider_transactions(data):
	"""Summarize insider transactions: aggregate buy/sell counts and amounts,
	determine net direction, and keep only the most recent 20 transactions.
	"""
	transactions = data if isinstance(data, list) else data.get("transactions", [])
	if not isinstance(transactions, list):
		return data

	buy_count = 0
	sell_count = 0
	buy_amount = 0.0
	sell_amount = 0.0

	for txn in transactions:
		if not isinstance(txn, dict):
			continue
		txn_type = str(txn.get("type", "") or txn.get("transaction", "")).lower()
		value = txn.get("value") or txn.get("amount") or 0
		try:
			value = float(value)
		except (ValueError, TypeError):
			value = 0.0

		if "buy" in txn_type or "purchase" in txn_type:
			buy_count += 1
			buy_amount += value
		elif "sale" in txn_type or "sell" in txn_type:
			sell_count += 1
			sell_amount += value

	if buy_amount > sell_amount * 1.2:
		net_direction = "net_buying"
	elif sell_amount > buy_amount * 1.2:
		net_direction = "net_selling"
	else:
		net_direction = "mixed"

	return {
		"summary": {
			"total_transactions": len(transactions),
			"buy_count": buy_count,
			"sell_count": sell_count,
			"buy_amount": round(buy_amount, 2),
			"sell_amount": round(sell_amount, 2),
			"net_direction": net_direction,
			"net_value": round(buy_amount - sell_amount, 2),
		},
		"transactions": transactions[:20],
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

	Returns:
		dict with next_report, surprise_history, consecutive_beats,
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

	# Surprise history from earnings_surprise
	surprise = earnings_surprise if isinstance(earnings_surprise, dict) and not earnings_surprise.get("error") else {}
	history = surprise.get("history") or surprise.get("surprise_history") or []

	if isinstance(history, list):
		result["surprise_history"] = history[:8]
	else:
		result["surprise_history"] = []

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


def _clean_analyst_revisions(data):
	"""Merge eps_revisions, eps_trend, and growth_estimates into horizon-based structure.

	Converts column-oriented yfinance data into per-horizon objects with
	computed trend direction and net revision counts.
	"""
	if not isinstance(data, dict) or data.get("error"):
		return data

	eps_rev = data.get("eps_revisions") or {}
	eps_trend = data.get("eps_trend") or {}
	growth_est = data.get("growth_estimates") or {}

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

	# Pre-extract stockTrend (growth_estimates), excluding indexTrend
	stock_trend = growth_est.get("stockTrend", {}) if isinstance(growth_est, dict) else {}

	for h in horizons:
		entry = {}

		# eps_trend fields
		if isinstance(trend_current, dict) and h in trend_current:
			entry["eps_current"] = trend_current[h]
		if isinstance(trend_7d, dict) and h in trend_7d:
			entry["eps_7d_ago"] = trend_7d[h]
		if isinstance(trend_30d, dict) and h in trend_30d:
			entry["eps_30d_ago"] = trend_30d[h]
		if isinstance(trend_90d, dict) and h in trend_90d:
			entry["eps_90d_ago"] = trend_90d[h]

		# eps_revisions fields
		if isinstance(up7_col, dict) and h in up7_col:
			val = up7_col[h] or 0
			entry["up_7d"] = up7_col[h]
			total_up_7d += val
		if isinstance(down7_col, dict) and h in down7_col:
			val = down7_col[h] or 0
			entry["down_7d"] = down7_col[h]
			total_down_7d += val
		if isinstance(up30_col, dict) and h in up30_col:
			val = up30_col[h] or 0
			entry["up_30d"] = up30_col[h]
			total_up_30d += val
		if isinstance(down30_col, dict) and h in down30_col:
			val = down30_col[h] or 0
			entry["down_30d"] = down30_col[h]
			total_down_30d += val

		# growth_estimates.stockTrend
		if isinstance(stock_trend, dict) and h in stock_trend:
			entry["growth_pct"] = stock_trend[h]

		if entry:
			by_horizon[h] = entry

		# trend_direction: compare eps_current vs eps_30d_ago per horizon
		eps_cur = entry.get("eps_current")
		eps_30d_val = entry.get("eps_30d_ago")
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
		"thresholds": "trend_direction: rising(majority horizons eps_current > eps_30d_ago) | falling(majority <) | stable(mixed)",
	}
