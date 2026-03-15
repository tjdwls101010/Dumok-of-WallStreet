"""Health-gate extraction and fundamental readiness code builders."""


def _extract_health_gates(results):
	"""Extract 4 health gates from L4 script results with 3-level severity.

	Severity levels: PASS (1.0), CAUTION (0.5), FLAG (0.0)

	Gates:
	1. Bear-Bull Paradox: debt grade + interest coverage
	2. Active Dilution: shares change percentage
	3. No-Growth Fail: margin of safety percentage
	4. Margin Collapse: margin trajectory

	Returns:
		dict with gate statuses, severity_score (0-4.0), total_pass, total_gates, flags
	"""
	gates = {
		"bear_bull_paradox": "PASS",
		"active_dilution": "PASS",
		"no_growth_fail": "PASS",
		"margin_collapse": "PASS",
	}
	severity = {
		"bear_bull_paradox": 1.0,
		"active_dilution": 1.0,
		"no_growth_fail": 1.0,
		"margin_collapse": 1.0,
	}
	flags = []

	# Bear-Bull Paradox: PASS (A-B + coverage > 3x), CAUTION (C OR 1-3x), FLAG (D OR < 1x)
	debt = results.get("debt_structure", {})
	bbp_detail = {}
	if not debt.get("error"):
		grade = str(debt.get("debt_quality_grade", "")).upper()[:1]
		coverage = debt.get("interest_coverage_ratio")
		bbp_detail = {
			"debt_quality_grade": debt.get("debt_quality_grade"),
			"interest_coverage_ratio": coverage,
			"total_debt": debt.get("total_debt"),
			"cash_and_equivalents": debt.get("cash_and_equivalents"),
			"net_debt": debt.get("net_debt"),
			"debt_to_equity": debt.get("debt_to_equity"),
			"thresholds": "FLAG: grade D or coverage < 1x | CAUTION: grade C or 1-3x | PASS: grade A-B and coverage > 3x",
		}
		if grade == "D" or (coverage is not None and coverage < 1.0):
			gates["bear_bull_paradox"] = "FLAG"
			severity["bear_bull_paradox"] = 0.0
			flags.append("bear_bull_paradox")
		elif grade == "C" or (coverage is not None and 1.0 <= coverage <= 3.0):
			gates["bear_bull_paradox"] = "CAUTION"
			severity["bear_bull_paradox"] = 0.5

	# Active Dilution: shares dilution + FCF optical illusion + SBC health
	# V2 Dilution Quality: high-growth dilution (contract-backed deployment) is less
	# concerning than low/no-growth dilution (value destruction). Revenue growth
	# modifies severity — a company diluting while growing >25% gets a one-tier discount.
	sbc = results.get("sbc_analyzer", {})
	fpe = results.get("forward_pe", {})
	ad_detail = {}
	if not sbc.get("error"):
		shares_change = sbc.get("shares_change_qoq_pct")
		real_fcf = sbc.get("real_fcf")
		reported_fcf = sbc.get("reported_fcf")
		sbc_flag = sbc.get("flag")  # "healthy" / "warning" / "toxic"

		# Revenue growth modifier: high growth softens dilution severity by one tier
		rev_growth = None
		if isinstance(fpe, dict) and not fpe.get("error"):
			rg = fpe.get("revenue_growth_yoy")
			if isinstance(rg, (int, float)):
				rev_growth = rg * 100 if rg < 1 else rg
		high_growth = isinstance(rev_growth, (int, float)) and rev_growth > 25

		ad_detail = {
			"shares_change_qoq_pct": shares_change,
			"dilution_flag": sbc.get("dilution_flag"),
			"sbc_pct_revenue": sbc.get("sbc_pct_revenue"),
			"real_fcf": real_fcf,
			"reported_fcf": reported_fcf,
			"sbc_flag": sbc_flag,
			"revenue_growth_yoy_pct": rev_growth,
			"high_growth_dilution_discount": high_growth,
			"thresholds": (
				"FLAG: shares_qoq > 2% | reported_fcf > 0 but real_fcf < 0 | sbc toxic (>30% rev) "
				"| CAUTION: shares_qoq 1-2% | sbc warning (10-30% rev) | PASS: otherwise "
				"| high_growth_discount: revenue_growth > 25% softens severity by one tier (V2 dilution quality)"
			),
		}

		# Priority 1: Direct share dilution (when data available)
		if isinstance(shares_change, (int, float)):
			if shares_change > 2:
				if high_growth:
					gates["active_dilution"] = "CAUTION"
					severity["active_dilution"] = 0.5
				else:
					gates["active_dilution"] = "FLAG"
					severity["active_dilution"] = 0.0
					flags.append("active_dilution")
			elif shares_change > 1:
				if not high_growth:
					gates["active_dilution"] = "CAUTION"
					severity["active_dilution"] = 0.5

		# Priority 2: FCF Optical Illusion (Serenity core insight)
		# reported FCF positive but real FCF (after SBC) negative = masked dilution
		elif (isinstance(real_fcf, (int, float)) and isinstance(reported_fcf, (int, float))
			  and reported_fcf > 0 and real_fcf < 0):
			if high_growth:
				gates["active_dilution"] = "CAUTION"
				severity["active_dilution"] = 0.5
			else:
				gates["active_dilution"] = "FLAG"
				severity["active_dilution"] = 0.0
				flags.append("active_dilution")

		# Priority 3: SBC health flag from sbc_analyzer module
		elif sbc_flag == "toxic":
			if high_growth:
				gates["active_dilution"] = "CAUTION"
				severity["active_dilution"] = 0.5
			else:
				gates["active_dilution"] = "FLAG"
				severity["active_dilution"] = 0.0
				flags.append("active_dilution")
		elif sbc_flag == "warning":
			gates["active_dilution"] = "CAUTION"
			severity["active_dilution"] = 0.5

		# Priority 4: Original dilution_flag fallback
		elif sbc.get("dilution_flag") == "active_dilution":
			gates["active_dilution"] = "FLAG"
			severity["active_dilution"] = 0.0
			flags.append("active_dilution")

	# No-Growth Fail: PASS (MoS > 20%), CAUTION (0-20%), FLAG (< 0%)
	ngv = results.get("no_growth_valuation", {})
	ngf_detail = {}
	if not ngv.get("error"):
		mos = ngv.get("margin_of_safety_pct")
		ngf_detail = {
			"margin_of_safety_pct": mos,
			"no_growth_fair_value": ngv.get("no_growth_fair_value"),
			"current_market_cap": ngv.get("current_market_cap"),
			"implied_earnings": ngv.get("implied_earnings"),
			"net_margin_pct": ngv.get("net_margin_pct"),
			"thresholds": "FLAG: MoS < 0% | CAUTION: 0-20% | PASS: > 20%",
		}
		if mos is not None:
			if mos < 0:
				gates["no_growth_fail"] = "FLAG"
				severity["no_growth_fail"] = 0.0
				flags.append("no_growth_fail")
			elif mos <= 20:
				gates["no_growth_fail"] = "CAUTION"
				severity["no_growth_fail"] = 0.5

	# Margin Collapse: PASS (expanding), CAUTION (stable/compression), FLAG (collapse)
	margin = results.get("margin_tracker", {})
	mc_detail = {}
	if not margin.get("error"):
		margin_flag = str(margin.get("flag", "")).upper()
		latest_q = margin.get("latest_quarter", {})
		mc_detail = {
			"flag": margin.get("flag"),
			"gross_margin": latest_q.get("gross_margin") if isinstance(latest_q, dict) else None,
			"operating_margin": latest_q.get("operating_margin") if isinstance(latest_q, dict) else None,
			"net_margin": latest_q.get("net_margin") if isinstance(latest_q, dict) else None,
			"gross_margin_qoq_change": margin.get("gross_margin_qoq_change"),
			"operating_margin_qoq_change": margin.get("operating_margin_qoq_change"),
			"thresholds": "FLAG: collapse | CAUTION: stable/compression/contracting | PASS: expanding",
		}
		if "COLLAPSE" in margin_flag:
			gates["margin_collapse"] = "FLAG"
			severity["margin_collapse"] = 0.0
			flags.append("margin_collapse")
		elif "COMPRESSION" in margin_flag or "CONTRACTING" in margin_flag or "STABLE" in margin_flag:
			gates["margin_collapse"] = "CAUTION"
			severity["margin_collapse"] = 0.5

	# IO Quality: CAUTION only (never FLAG) — H2/H8 TacitKnowledge Audit
	gates["io_quality_concern"] = "PASS"
	severity["io_quality_concern"] = 1.0
	iq_detail = {}
	io_data = results.get("institutional_quality", {})
	if not io_data.get("error"):
		io_score = io_data.get("io_quality_score")
		quant_mm_pct = io_data.get("quant_mm_pct")
		iq_detail = {
			"io_quality_score": io_score,
			"quant_mm_pct": quant_mm_pct,
			"thresholds": "CAUTION: quant_mm_pct > 30% or io_score <= 3 | PASS: otherwise | never FLAG",
		}
		if (isinstance(quant_mm_pct, (int, float)) and quant_mm_pct > 30) or \
		   (isinstance(io_score, (int, float)) and io_score <= 3):
			gates["io_quality_concern"] = "CAUTION"
			severity["io_quality_concern"] = 0.5

	severity_score = sum(severity.values())

	return {
		"bear_bull_paradox": gates["bear_bull_paradox"],
		"active_dilution": gates["active_dilution"],
		"no_growth_fail": gates["no_growth_fail"],
		"margin_collapse": gates["margin_collapse"],
		"io_quality_concern": gates["io_quality_concern"],
		"severity_score": severity_score,
		"detail": {
			"bear_bull_paradox": bbp_detail,
			"active_dilution": ad_detail,
			"no_growth_fail": ngf_detail,
			"margin_collapse": mc_detail,
			"io_quality_concern": iq_detail,
		},
	}


def _build_readiness_codes(health_gates, valuation_summary, l4_results, l5_results=None, sec_result=None, sec_sc_results=None, bottleneck_pre_score=None, composite_signal=None):
	"""Build standardized fundamental readiness codes for auditability.

	Returns:
		list of str codes summarizing automated assessment
	"""
	codes = []

	# Health gates
	codes.append(f"HEALTH_GATES_{health_gates['total_pass']}_{health_gates['total_gates']}")

	# Health severity score
	sev_score = health_gates.get("severity_score")
	if sev_score is not None:
		codes.append(f"HEALTH_SEVERITY_{sev_score}")

	# Dilution status
	sbc = l4_results.get("sbc_analyzer", {})
	if sec_result and not sec_result.get("error"):
		codes.append("DILUTION_sec_confirmed_atm")
	elif not sbc.get("error"):
		dilution = sbc.get("dilution_flag", "clean")
		codes.append(f"DILUTION_{dilution}")

	# Valuation floor
	upside = valuation_summary.get("no_growth_upside_pct")
	if upside is not None:
		codes.append(f"VALUATION_FLOOR_{upside:.0f}PCT")

	# Forward PE
	fpe = valuation_summary.get("forward_pe")
	if fpe is not None:
		codes.append(f"FWD_PE_{fpe:.1f}")

	# Margin trajectory
	margin = valuation_summary.get("margin_status")
	if margin:
		codes.append(f"MARGIN_{margin}")

	# Debt quality
	debt = valuation_summary.get("debt_quality_grade")
	if debt:
		codes.append(f"DEBT_GRADE_{debt}")

	# IO quality
	io = valuation_summary.get("io_quality_score")
	if io is not None:
		codes.append(f"IO_QUALITY_{io}")

	# Code 33 status
	ea = l4_results.get("earnings_acceleration", {})
	if not ea.get("error"):
		c33 = ea.get("code33_status")
		if c33 is not None:
			codes.append(f"CODE33_{str(c33).upper()}")

	# Consecutive beats
	if l5_results:
		es = l5_results.get("earnings_surprise", {})
		if not es.get("error"):
			beats = es.get("consecutive_beats")
			if beats is not None:
				codes.append(f"BEATS_{beats}")

	# SBC health
	if not sbc.get("error"):
		sbc_flag = sbc.get("flag")
		if sbc_flag:
			codes.append(f"SBC_{sbc_flag}")

	# CapEx direction (from L2 company_capex if available)
	# capex_data is passed separately as it's popped from l4_results

	# SEC supply chain data availability
	if sec_sc_results:
		sc_data = sec_sc_results.get("sec_supply_chain", {})
		if sc_data and not sc_data.get("error") and sc_data.get("data"):
			matches = sc_data["data"].get("extraction_stats", {}).get("total_matches", 0)
			if matches > 0:
				codes.append("SEC_SC_available")
			else:
				codes.append("SEC_SC_partial")
		else:
			codes.append("SEC_SC_unavailable")

	# Bottleneck pre-score
	if bottleneck_pre_score and not bottleneck_pre_score.get("error"):
		bn_score = bottleneck_pre_score.get("pre_score", 0)
		bn_max = bottleneck_pre_score.get("pre_score_max", 4.25)
		codes.append(f"BOTTLENECK_PRE_{bn_score}_{bn_max}")

	# Composite signal grade
	if composite_signal and not composite_signal.get("error"):
		grade = composite_signal.get("grade")
		score = composite_signal.get("composite_score")
		if grade:
			codes.append(f"COMPOSITE_{grade}_{score}")

	return codes
