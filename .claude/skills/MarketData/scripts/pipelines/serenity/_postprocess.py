"""Post-processing helpers for Serenity pipeline outputs.

Functions that compress, summarize, or trim raw module data
before it is included in the final pipeline response.
"""


def _summarize_insider_transactions(data):
	"""Summarize insider transactions: aggregate buy/sell counts and amounts,
	determine net direction, and keep only the most recent 20 transactions.

	Args:
		data: Raw insider transactions output (list or dict with transactions key)

	Returns:
		dict with summary (buy_count, sell_count, buy_amount, sell_amount,
		net_direction) and transactions (most recent 20)
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
		},
		"transactions": transactions[:20],
	}


def _extract_revenue_trajectory(financials_data):
	"""Extract quarterly revenue trajectory from income statement data.

	Args:
		financials_data: Raw income statement output from financials.py

	Returns:
		dict with revenue_by_quarter (list of {quarter, revenue} dicts, max 8)
	"""
	revenue_by_quarter = []

	# financials.py returns data in various formats; handle common structures
	if isinstance(financials_data, dict):
		# Try "data" key first (common wrapper)
		records = financials_data.get("data", financials_data)
		if isinstance(records, dict):
			# Column-oriented: {"TotalRevenue": {"2025-Q3": 203000000, ...}}
			rev_data = records.get("TotalRevenue") or records.get("Total Revenue")
			if isinstance(rev_data, dict):
				for quarter, revenue in list(rev_data.items())[:8]:
					revenue_by_quarter.append({
						"quarter": str(quarter),
						"revenue": revenue,
					})
			else:
				# Row-oriented: {date: {field: value, ...}, ...}
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
	"""Cap earnings_dates to the most recent N entries.

	yfinance get_earnings_dates may ignore the limit parameter,
	so this trims each column dict to the first `limit` entries
	(most recent dates first).

	Args:
		data: Raw earnings_dates output (dict-of-dicts from actions.py)
		limit: Maximum number of entries to keep (default 8)

	Returns:
		dict with each column trimmed to `limit` entries
	"""
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

	Retains pass/fail status flags and trims growth rate arrays
	to most recent 3 values.

	Args:
		data: Raw earnings_acceleration code33 output dict

	Returns:
		dict with symbol, code33_status, acceleration booleans,
		trimmed growth rates (3 most recent), and data_quality
	"""
	if not isinstance(data, dict) or data.get("error"):
		return data
	return {
		"symbol": data.get("symbol"),
		"code33_status": data.get("code33_status"),
		"eps_accelerating": data.get("eps_accelerating"),
		"sales_accelerating": data.get("sales_accelerating"),
		"margin_expanding": data.get("margin_expanding"),
		"eps_growth_rates": data.get("eps_growth_rates", [])[:3],
		"sales_growth_rates": data.get("sales_growth_rates", [])[:3],
		"data_quality": data.get("data_quality"),
	}


def _summarize_holders(data):
	"""Summarize institutional holders to top 5 with key fields only.

	Retains holder name, shares, and pctHeld. Drops date, value, and
	pctChange columns for token efficiency.

	Args:
		data: Raw institutional holders output (dict-of-lists format from holders.py)

	Returns:
		dict with top_holders (list of 5 dicts) and total_reported count
	"""
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
