"""Signal synthesis module for Minervini SEPA pipeline.

Combines entry signals (VCP, entry_patterns, pocket_pivot, low_cheat) and
exit signals (sell_signals, post_breakout) into unified signal verdicts.
Determines overall signal: BUY_READY / WATCH / HOLD / REDUCE / SELL.
"""


def _check_breakout_volume(results):
	"""Check breakout volume confirmation: 2+ days of heavy volume.

	Pipeline-level rule: look at volume_analysis for confirmation.
	"""
	vol = results.get("volume_analysis", {})
	if vol.get("error"):
		return {
			"confirmed": False,
			"reason": "volume_analysis_unavailable",
			"thresholds": "confirmed: 2+ days with volume >= 125% of 50d avg on up-close within 2% of pivot",
		}

	confirmed = vol.get("breakout_volume_confirmation", False)
	ratio = vol.get("volume_vs_50day_avg_pct", 0)

	# Also check VCP volume data
	vcp = results.get("vcp", {})
	vcp_vol = vcp.get("volume", {}) if not vcp.get("error") else {}
	vcp_confirmed = vcp_vol.get("volume_confirmation", "neutral")

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
	"""Combine entry signal sources into unified entry signal."""
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
			# Only include fields that have values (avoid null noise)
			if p.get("trigger_price") is not None:
				sig["trigger_price"] = p["trigger_price"]
			if p.get("stop_price") is not None:
				sig["stop_price"] = p["stop_price"]
			signals.append(sig)

	# Pocket pivot
	pp = results.get("pocket_pivot", {})
	if not pp.get("error") and pp.get("pocket_pivot_count", 0) > 0:
		recent = pp.get("most_recent_pp", {})
		signals.append({
			"source": "pocket_pivot",
			"days_ago": recent.get("days_ago"),
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
	"""Build lightweight exit signal references for signal section (A.3).

	Full sell signal detail lives in risk_assessment.sell_signals.
	Here we include only signal names + severity as cross-reference.
	"""
	refs = []

	# Sell signals reference
	sell = results.get("sell_signals", {})
	if not sell.get("error") and sell.get("signal_count", 0) > 0:
		refs.append({
			"source": "sell_signals",
			"signals": sell.get("active_sell_signals", []),
			"severity": sell.get("severity"),
		})

	# Post breakout
	post = results.get("post_breakout", {})
	if not post.get("error"):
		hold_sell = post.get("hold_sell_signal", "hold")
		if hold_sell != "hold":
			refs.append({
				"source": "post_breakout",
				"signal": hold_sell,
			})

	return refs


def determine_overall_signal(results, sepa_score_data, risk_data):
	"""Determine overall signal: BUY_READY / WATCH / HOLD / REDUCE / SELL.

	Args:
		results: dict of module outputs
		sepa_score_data: dict from compute_sepa_score
		risk_data: dict from compute_risk_assessment

	Returns:
		dict with signal, entry_signals, exit_signals (ref only),
		volume_confirmation, reasons, thresholds
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

	if sell_severity == "critical" or post_signal == "sell":
		overall = "SELL"
		reasons.append("critical sell signals or post-breakout sell signal active")
	elif sell_severity == "warning" or post_signal == "reduce":
		overall = "REDUCE"
		reasons.append("warning-level sell signals or post-breakout reduce")
	elif post_signal == "watch":
		overall = "HOLD"
		reasons.append("post-breakout watch signal — monitor closely")
	# --- Entry signals ---
	elif sepa_score_data.get("hard_gate_fail"):
		overall = "WATCH"
		reasons.append(f"hard gate fail: {sepa_score_data.get('hard_gate_reasons')}")
	elif sepa_score_data.get("sepa_score", 0) >= 60 and entry_signals and volume_check.get("confirmed"):
		overall = "BUY_READY"
		reasons.append(f"SEPA score {sepa_score_data.get('sepa_score')}, entry signals active, volume confirmed")
	elif sepa_score_data.get("sepa_score", 0) >= 60 and entry_signals:
		overall = "WATCH"
		reasons.append(f"SEPA score {sepa_score_data.get('sepa_score')}, entry signals active but volume not confirmed")
	elif sepa_score_data.get("sepa_score", 0) >= 40:
		overall = "WATCH"
		reasons.append(f"SEPA score {sepa_score_data.get('sepa_score')}, developing setup")
	else:
		overall = "WATCH"
		reasons.append(f"SEPA score {sepa_score_data.get('sepa_score', 0)}, not ready")

	return {
		"signal": overall,
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
