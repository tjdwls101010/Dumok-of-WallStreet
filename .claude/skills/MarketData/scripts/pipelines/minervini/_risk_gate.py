"""Risk assessment module for Minervini SEPA pipeline.

Calculates stop-loss levels from VCP pivot/low, R:R ratio, integrates
position_sizing.calculate results. Sell signal detail is provided by
risk_assessment.sell_signals (not duplicated here).
"""


def compute_risk_assessment(results, account_size=100000):
	"""Compute risk assessment from module results.

	Args:
		results: dict of module name -> module output
		account_size: account value for position sizing (default: 100000)

	Returns:
		dict with stop_loss, risk_reward_ratio (+ thresholds), position_sizing.
		Does NOT include sell_signals_summary (D.2 — canonical location
		is risk_assessment.sell_signals).
	"""
	vcp = results.get("vcp", {})
	pos_sizing = results.get("position_sizing", {})

	# --- Stop-loss calculation ---
	stop_loss = None
	pivot_price = None
	stop_pct = 7.0  # default

	if not vcp.get("error") and vcp.get("vcp_detected"):
		pivot_price = vcp.get("pivot_price")
		# Use the lowest low from the last contraction as stop reference
		corrections = vcp.get("correction_depths", [])
		if pivot_price and corrections:
			last_depth = corrections[-1]
			# Stop is below the bottom of the last contraction
			stop_loss = round(pivot_price * (1 - last_depth / 100), 2)
			if pivot_price > 0:
				stop_pct = round((pivot_price - stop_loss) / pivot_price * 100, 2)

	# Fallback: use entry_patterns stop if VCP not available
	if stop_loss is None:
		entry = results.get("entry_patterns", {})
		if not entry.get("error"):
			patterns = entry.get("active_patterns", [])
			if patterns:
				best = patterns[0]
				stop_loss = best.get("stop_price")
				pivot_price = best.get("trigger_price")
				stop_pct = best.get("stop_pct", 7.0)

	# Fallback: use low_cheat if available
	if stop_loss is None:
		lc = results.get("low_cheat", {})
		if not lc.get("error") and lc.get("low_cheat_detected"):
			ea = lc.get("entry_analysis", {})
			stop_loss = ea.get("stop_loss")
			pivot_price = ea.get("low_cheat_entry")
			stop_pct = ea.get("risk_pct", 7.0)

	# --- R:R ratio ---
	risk_reward_ratio = None
	target_price = None
	if pivot_price and stop_loss and pivot_price > stop_loss:
		# Target = 3x the risk (standard SEPA target)
		risk_per_share = pivot_price - stop_loss
		# Use RS ranking to estimate target: higher RS -> higher target
		rs = results.get("rs_ranking", {})
		rs_score = rs.get("rs_score", 50) if not rs.get("error") else 50
		# Target multiplier: 2-4x based on RS and base count
		base = results.get("base_count", {})
		base_num = base.get("current_base_number", 2) if not base.get("error") else 2
		if base_num <= 2 and rs_score >= 80:
			target_mult = 4.0
		elif base_num <= 2 and rs_score >= 60:
			target_mult = 3.0
		elif base_num <= 3:
			target_mult = 2.5
		else:
			target_mult = 2.0
		target_gain = risk_per_share * target_mult
		target_price = round(pivot_price + target_gain, 2)
		risk_reward_ratio = round(target_mult, 1)

	# --- Position sizing ---
	position_suggestion = None
	if not pos_sizing.get("error"):
		position_suggestion = {
			"position_size_shares": pos_sizing.get("position_size_shares"),
			"position_value": pos_sizing.get("position_value"),
			"risk_amount": pos_sizing.get("risk_amount"),
			"portfolio_pct": pos_sizing.get("portfolio_pct"),
		}
	elif pivot_price and stop_pct > 0:
		# Inline calculation if module failed
		risk_per_trade = 0.005  # 0.5%
		risk_amount = account_size * risk_per_trade
		risk_per_share = pivot_price * stop_pct / 100
		if risk_per_share > 0:
			shares = int(risk_amount / risk_per_share)
			position_suggestion = {
				"position_size_shares": shares,
				"position_value": round(shares * pivot_price, 2),
				"risk_amount": round(risk_amount, 2),
				"portfolio_pct": round((shares * pivot_price) / account_size * 100, 2),
			}

	return {
		"stop_loss": stop_loss,
		"stop_pct": stop_pct,
		"pivot_price": pivot_price,
		"target_price": target_price,
		"risk_reward_ratio": risk_reward_ratio,
		"risk_reward_thresholds": "excellent: >=4:1 | good: 3:1 | acceptable: 2:1 | poor: <2:1",
		"position_sizing": position_suggestion,
	}
