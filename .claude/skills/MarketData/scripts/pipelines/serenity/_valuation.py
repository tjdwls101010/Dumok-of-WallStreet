"""Valuation frame builder for Serenity pipeline verdict section."""


def _build_valuation_frame(results):
	"""Build valuation frame for verdict section.

	Dual-valuation: no-growth floor + growth upside (H4).
	"""
	forward_pe_data = results.get("forward_pe", {})
	ngv_data = results.get("no_growth_valuation", {})

	frame = {}

	if not ngv_data.get("error"):
		frame["no_growth_floor"] = {
			"fair_value": ngv_data.get("no_growth_fair_value"),
			"margin_of_safety_pct": ngv_data.get("margin_of_safety_pct"),
			"stress_test": "pass" if isinstance(ngv_data.get("margin_of_safety_pct"), (int, float)) and ngv_data["margin_of_safety_pct"] > 0 else "fail",
		}

	if not forward_pe_data.get("error"):
		frame["growth_upside"] = {
			"forward_1y_pe": forward_pe_data.get("forward_1y_pe"),
			"forward_2y_pe": forward_pe_data.get("forward_2y_pe"),
			"revenue_growth_yoy": forward_pe_data.get("revenue_growth_yoy"),
			"assessment": forward_pe_data.get("assessment"),
		}

	return frame
