"""Valuation summary builder for Serenity pipeline."""


def _build_valuation_summary(results):
	"""Build valuation summary from L4 script results.

	Includes dual_valuation object combining no-growth floor and growth upside
	(TacitKnowledge Audit H4: Dual-Valuation Anchor).
	"""
	forward_pe_data = results.get("forward_pe", {})
	ngv_data = results.get("no_growth_valuation", {})
	margin_data = results.get("margin_tracker", {})
	io_data = results.get("institutional_quality", {})
	debt_data = results.get("debt_structure", {})

	# Dual-Valuation: no-growth floor + growth upside (H4)
	dual_valuation = {}
	if not ngv_data.get("error"):
		dual_valuation["no_growth_floor"] = {
			"fair_value": ngv_data.get("no_growth_fair_value"),
			"market_cap": ngv_data.get("current_market_cap"),
			"margin_of_safety_pct": ngv_data.get("margin_of_safety_pct"),
		}
	if not forward_pe_data.get("error"):
		dual_valuation["growth_upside"] = {
			"forward_1y_pe": forward_pe_data.get("forward_1y_pe"),
			"forward_2y_pe": forward_pe_data.get("forward_2y_pe"),
			"revenue_based_fair_value_low": forward_pe_data.get("revenue_based_fair_value_low"),
			"revenue_based_fair_value_high": forward_pe_data.get("revenue_based_fair_value_high"),
			"primary_valuation_method": forward_pe_data.get("primary_valuation_method"),
			"assessment": forward_pe_data.get("assessment"),
		}

	return {
		"forward_pe": forward_pe_data.get("forward_1y_pe") if not forward_pe_data.get("error") else None,
		"no_growth_upside_pct": ngv_data.get("margin_of_safety_pct") if not ngv_data.get("error") else None,
		"margin_status": margin_data.get("flag") if not margin_data.get("error") else None,
		"io_quality_score": io_data.get("io_quality_score") if not io_data.get("error") else None,
		"debt_quality_grade": debt_data.get("debt_quality_grade") if not debt_data.get("error") else None,
		"dual_valuation": dual_valuation,
	}
