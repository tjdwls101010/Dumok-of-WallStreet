"""Macro regime classification for the Serenity pipeline.

Combines multiple macro signals (ERP, VIX curve, net liquidity,
fear/greed, Fed watch, yield curve, BDI, DXY, real rates) into
a single regime label with risk level and decision rules.
"""


def _classify_macro_regime(macro_results):
	"""Classify macro regime based on combined signals.

	Returns:
		dict with regime, risk_level, drain_count, decision_rules
	"""
	erp = macro_results.get("erp", {})
	vix = macro_results.get("vix_curve", {})
	net_liq = macro_results.get("net_liquidity", {})
	fear_greed = macro_results.get("fear_greed", {})
	fedwatch = macro_results.get("fedwatch", {})
	yield_curve = macro_results.get("yield_curve", {})

	# Signal extraction
	erp_healthy = False
	erp_danger = False
	erp_val = None
	if not erp.get("error"):
		erp_val = erp.get("current", {}).get("erp")
		if erp_val is not None:
			erp_healthy = erp_val > 3.0
			erp_danger = erp_val < 1.5

	vix_contango = False
	vix_backwardation = False
	if not vix.get("error"):
		structure = str(vix.get("structure_type", "")).lower()
		vix_contango = "contango" in structure
		vix_backwardation = "backwardation" in structure

	net_liq_positive = False
	if not net_liq.get("error"):
		net_liq_data = net_liq.get("net_liquidity", {})
		trend = str(net_liq_data.get("direction", "")).lower()
		net_liq_positive = "positive" in trend or "rising" in trend or "expanding" in trend

	fear_extreme = False
	fg_val = None
	if not fear_greed.get("error"):
		fg_val = fear_greed.get("current", {}).get("score")
		if fg_val is not None:
			try:
				fear_extreme = float(fg_val) < 25
			except (ValueError, TypeError):
				pass

	# Regime classification
	risk_on_signals = [erp_healthy, vix_contango, net_liq_positive]
	risk_off_signals = [erp_danger, vix_backwardation, fear_extreme]

	risk_on_count = sum(1 for s in risk_on_signals if s)
	risk_off_count = sum(1 for s in risk_off_signals if s)

	if risk_on_count >= 2 and risk_off_count == 0:
		regime = "risk_on"
	elif risk_off_count >= 2 and risk_on_count == 0:
		regime = "risk_off"
	else:
		regime = "transitional"

	# Count negative macro signals (drains)
	drain_count = 0
	decision_rules = []

	if erp.get("error"):
		decision_rules.append("ERP unavailable (script error)")
	elif erp_val is None:
		decision_rules.append("ERP data unavailable")
	elif not erp_healthy:
		drain_count += 1
		decision_rules.append(f"ERP at {erp_val:.2f}% — below healthy threshold (>3%)")
	else:
		decision_rules.append(f"ERP healthy at {erp_val:.2f}%")

	if vix_backwardation:
		drain_count += 1
		decision_rules.append("VIX in backwardation — elevated near-term fear")
	elif vix_contango:
		decision_rules.append("VIX contango — normal risk appetite")

	if not net_liq_positive and not net_liq.get("error"):
		drain_count += 1
		decision_rules.append("Net liquidity contracting or neutral")
	elif net_liq_positive:
		decision_rules.append("Net liquidity expanding — supportive for risk assets")

	if fear_greed.get("error"):
		decision_rules.append("Fear & Greed unavailable (script error)")
	elif fg_val is None:
		decision_rules.append("Fear & Greed data unavailable")
	elif fear_extreme:
		drain_count += 1
		decision_rules.append(f"Fear & Greed at {float(fg_val):.0f} — extreme fear levels (<25)")
	else:
		decision_rules.append(f"Sentiment at {float(fg_val):.0f} — within normal range")

	if not fedwatch.get("error"):
		decision_rules.append("Fed rate path data available for context")

	if not yield_curve.get("error"):
		inversion = yield_curve.get("inverted") or yield_curve.get("spread_10y_2y")
		if inversion is not None:
			if isinstance(inversion, bool) and inversion:
				drain_count += 1
				decision_rules.append("Yield curve inverted — recession signal")
			elif isinstance(inversion, (int, float)) and inversion < 0:
				drain_count += 1
				decision_rules.append(f"Yield curve inverted (10Y-2Y spread: {inversion:.2f}%)")
			else:
				decision_rules.append("Yield curve normal")

	# BDI signal (always included in v4.0)
	bdi = macro_results.get("bdi", {})
	if not bdi.get("error"):
		bdi_z = bdi.get("statistics", {}).get("z_score")
		if isinstance(bdi_z, (int, float)):
			if bdi_z < -2:
				drain_count += 1
				decision_rules.append(f"BDI z-score {bdi_z:.2f} — extreme shipping demand weakness")
			elif bdi_z < -1:
				decision_rules.append(f"BDI z-score {bdi_z:.2f} — below-average shipping demand")
			else:
				decision_rules.append(f"BDI z-score {bdi_z:.2f} — shipping demand normal/elevated")

	# DXY signal (always included in v4.0)
	dxy = macro_results.get("dxy", {})
	if not dxy.get("error"):
		dxy_z = dxy.get("statistics", {}).get("z_score")
		if isinstance(dxy_z, (int, float)):
			if dxy_z > 2:
				drain_count += 1
				decision_rules.append(f"DXY z-score {dxy_z:.2f} — extremely strong dollar pressures risk assets")
			elif dxy_z > 1:
				decision_rules.append(f"DXY z-score {dxy_z:.2f} — strong dollar")
			else:
				decision_rules.append(f"DXY z-score {dxy_z:.2f} — dollar within normal range")

	# Real rates signal
	real_rate = macro_results.get("real_rate")
	if isinstance(real_rate, (int, float)):
		if real_rate < 0:
			decision_rules.append(f"Real rate {real_rate:.2f}% — negative, liquidity supportive")
		else:
			decision_rules.append(f"Real rate {real_rate:.2f}% — positive, tighter conditions")

	# Risk level
	if drain_count == 0:
		risk_level = "low"
	elif drain_count <= 1:
		risk_level = "moderate"
	elif drain_count <= 3:
		risk_level = "elevated"
	else:
		risk_level = "high"

	return {
		"regime": regime,
		"risk_level": risk_level,
		"drain_count": drain_count,
		"decision_rules": decision_rules,
	}
