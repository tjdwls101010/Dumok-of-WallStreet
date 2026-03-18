"""Signal synthesis module for Minervini SEPA pipeline.

Combines entry signals (VCP, entry_patterns, pocket_pivot, low_cheat) and
exit signals (sell_signals, post_breakout) into unified signal verdicts.
Determines overall action: BUY_READY / WATCH / HOLD / REDUCE / SELL.
"""


def _check_breakout_volume(results):
	"""Check breakout volume confirmation: 2+ days of heavy volume."""
	vol = results.get("volume_analysis", {})
	if vol.get("error"):
		return {
			"confirmed": False,
			"reason": "volume_analysis_unavailable",
			"thresholds": "confirmed: 2+ days with volume >= 125% of 50d avg on up-close within 2% of pivot",
		}

	confirmed = vol.get("breakout_volume_confirmation", False)
	ratio = vol.get("volume_vs_50day_avg_pct", 0)

	# VCP volume — not_applicable if VCP not detected
	vcp = results.get("vcp", {})
	vcp_detected = vcp.get("vcp_detected", False) if not vcp.get("error") else False
	if vcp_detected:
		vcp_confirmed = vcp.get("volume", {}).get("volume_confirmation", "neutral")
	else:
		vcp_confirmed = "not_applicable"

	if confirmed or vcp_confirmed in ("strongly_confirmed", "confirmed"):
		return {
			"confirmed": True,
			"volume_vs_avg_pct": ratio,
			"vcp_confirmation": vcp_confirmed,
			"thresholds": "confirmed: 2+ days with volume >= 125% of 50d avg on up-close within 2% of pivot",
		}

	return {
		"confirmed": False,
		"volume_vs_avg_pct": ratio,
		"vcp_confirmation": vcp_confirmed,
		"thresholds": "confirmed: 2+ days with volume >= 125% of 50d avg on up-close within 2% of pivot",
	}


def synthesize_entry_signals(results):
	"""Combine entry signal sources into unified entry signal list."""
	signals = []

	# VCP
	vcp = results.get("vcp", {})
	if not vcp.get("error") and vcp.get("vcp_detected"):
		signals.append({
			"source": "vcp",
			"pattern_type": vcp.get("pattern_type"),
			"quality": vcp.get("pattern_quality"),
			"pivot_price": vcp.get("pivot_price"),
			"readiness": vcp.get("setup_readiness", {}).get("classification"),
			"footprint": vcp.get("technical_footprint"),
		})

	# Entry patterns
	entry = results.get("entry_patterns", {})
	if not entry.get("error") and entry.get("pattern_count", 0) > 0:
		for p in entry.get("active_patterns", []):
			sig = {
				"source": "entry_pattern",
				"pattern": p.get("pattern"),
				"quality": p.get("quality"),
			}
			if p.get("trigger_price") is not None:
				sig["trigger_price"] = p["trigger_price"]
			if p.get("stop_price") is not None:
				sig["stop_price"] = p["stop_price"]
			signals.append(sig)

	# Pocket pivot — only if recent (≤15 days)
	pp = results.get("pocket_pivot", {})
	if not pp.get("error") and pp.get("pocket_pivot_count", 0) > 0:
		recent = pp.get("most_recent_pp", {})
		days_ago = recent.get("days_ago", 999)
		if days_ago <= 15:
			signals.append({
				"source": "pocket_pivot",
				"days_ago": days_ago,
				"quality": recent.get("quality"),
				"count": pp.get("pocket_pivot_count"),
			})

	# Low cheat
	lc = results.get("low_cheat", {})
	if not lc.get("error") and lc.get("low_cheat_detected"):
		signals.append({
			"source": "low_cheat",
			"quality": lc.get("quality"),
			"entry_price": lc.get("entry_analysis", {}).get("low_cheat_entry"),
			"risk_reduction_pct": lc.get("entry_analysis", {}).get("risk_reduction_pct"),
		})

	# Cup completion cheat (3C) from VCP
	if not vcp.get("error"):
		ccc = vcp.get("cup_completion_cheat", {})
		if ccc.get("detected"):
			signals.append({
				"source": "cup_completion_cheat",
				"quality": ccc.get("quality"),
				"entry_price": ccc.get("entry_price"),
				"recovery_pct": ccc.get("recovery_pct"),
			})

	return signals


def synthesize_exit_signals_ref(results):
	"""Lightweight exit signal references (full detail in risk section)."""
	refs = []

	sell = results.get("sell_signals", {})
	if not sell.get("error") and sell.get("signal_count", 0) > 0:
		refs.append({
			"source": "sell_signals",
			"signals": sell.get("active_sell_signals", []),
			"severity": sell.get("severity"),
		})

	post = results.get("post_breakout", {})
	if not post.get("error"):
		hold_sell = post.get("hold_sell_signal", "hold")
		if hold_sell != "hold":
			refs.append({
				"source": "post_breakout",
				"signal": hold_sell,
			})

	return refs


def determine_overall_signal(results, sepa_total, classification, hard_gate_fail, hard_gates, risk_data):
	"""Determine overall action: BUY_READY / WATCH / HOLD / REDUCE / SELL.

	Args:
		results: dict of module outputs
		sepa_total: int (0-100)
		classification: str
		hard_gate_fail: bool
		hard_gates: list of gate dicts
		risk_data: dict from compute_risk_assessment

	Returns:
		dict with action, entry_signals, exit_signals, volume_confirmation,
		reasons, thresholds
	"""
	entry_signals = synthesize_entry_signals(results)
	exit_signals_ref = synthesize_exit_signals_ref(results)
	volume_check = _check_breakout_volume(results)

	reasons = []

	# --- Exit signals take priority ---
	sell_severity = "healthy"
	sell = results.get("sell_signals", {})
	if not sell.get("error"):
		sell_severity = sell.get("severity", "healthy")

	post = results.get("post_breakout", {})
	post_signal = post.get("hold_sell_signal", "hold") if not post.get("error") else "hold"

	sell_count = sell.get("signal_count", 0) if not sell.get("error") else 0

	if sell_severity == "critical" or post_signal == "sell":
		action = "SELL"
		reasons.append(f"{sell_count} active sell signals ({sell_severity} severity) override all other factors")
	elif sell_severity == "warning" or post_signal == "reduce":
		action = "REDUCE"
		reasons.append(f"sell signals at {sell_severity} severity — reduce exposure")
	elif post_signal == "watch":
		action = "HOLD"
		reasons.append("post-breakout watch signal — monitor closely")
	# --- Entry signals ---
	elif hard_gate_fail:
		failed_gates = [g["gate"] for g in hard_gates if not g["passed"]]
		action = "WATCH"
		reasons.append(f"hard gate fail ({', '.join(failed_gates)}) prevents BUY_READY; sell severity below SELL threshold")
	elif sepa_total >= 60 and entry_signals and volume_check.get("confirmed"):
		action = "BUY_READY"
		reasons.append(f"SEPA {classification} ({sepa_total}), entry pattern active, no sell signals, volume confirmed")
	elif sepa_total >= 60 and entry_signals:
		action = "WATCH"
		reasons.append(f"SEPA {classification} ({sepa_total}), entry signals active but volume not confirmed — wait for breakout volume")
	elif sepa_total >= 40:
		action = "WATCH"
		reasons.append(f"SEPA {classification} ({sepa_total}) — setup developing, not yet actionable")
	else:
		action = "WATCH"
		reasons.append(f"SEPA score {sepa_total} — not ready")

	return {
		"action": action,
		"entry_signals": entry_signals,
		"exit_signals": exit_signals_ref,
		"volume_confirmation": volume_check,
		"reasons": reasons,
		"thresholds": {
			"BUY_READY": "SEPA prime/actionable + entry pattern active + no sell signals + volume confirmed",
			"WATCH": "SEPA developing or entry not ready",
			"HOLD": "position exists + no sell signals",
			"REDUCE": "moderate sell signals OR egg behavior",
			"SELL": "critical sell signals OR hard stop hit",
		},
	}
