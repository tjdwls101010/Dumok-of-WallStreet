"""Market-cap string parsing helper for the Serenity pipeline."""


def _parse_mcap_string(mcap_str):
	"""Parse market cap string like '1.5B', '500M', '10B' to a numeric value.

	Returns:
		float or None if parsing fails
	"""
	if not mcap_str or not isinstance(mcap_str, str):
		return None
	mcap_str = mcap_str.strip().upper()
	multipliers = {"T": 1e12, "B": 1e9, "M": 1e6, "K": 1e3}
	for suffix, mult in multipliers.items():
		if mcap_str.endswith(suffix):
			try:
				return float(mcap_str[:-1]) * mult
			except ValueError:
				return None
	try:
		return float(mcap_str)
	except ValueError:
		return None
