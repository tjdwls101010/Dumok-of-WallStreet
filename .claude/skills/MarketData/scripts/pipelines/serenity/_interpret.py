"""Self-documenting interpretation helpers for Serenity pipeline outputs."""


def _interpret_institutional_flow(io_assessment, iv_regime, flow_assessment, insider_dir):
	"""Human-readable interpretation for institutional flow assessment."""
	context = f"IO quality: {io_assessment}, IV regime: {iv_regime}, insider direction: {insider_dir}"
	if flow_assessment == "positive":
		summary = "Accumulation signals present — institutional behavior aligns with bullish thesis."
	elif flow_assessment == "negative":
		summary = "Distribution signals detected — investigate whether active conviction reversal or mechanical flow."
	else:
		summary = "No clear directional signal from institutional data — rely on other evidence legs."
	return f"{summary} ({context})"
