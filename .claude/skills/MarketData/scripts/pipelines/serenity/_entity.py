"""Entity name normalization utilities for cross-chain supply chain analysis."""

import re


_ENTITY_SUFFIXES = re.compile(
	r",?\s*\b(?:Inc\.?|Corp\.?|Corporation|LLC|Ltd\.?|Limited|Co\.?|Company|"
	r"Group|Holdings|Plc\.?|SE|N\.?V\.?|S\.?A\.?|A\.?G\.?|GmbH|KK|"
	r"Kabushiki\s+Kaisha)\b\.?\s*$",
	re.IGNORECASE,
)

_ENTITY_ALIAS_MAP = {
	"tsmc": "taiwan semiconductor manufacturing",
	"taiwan semiconductor manufacturing company": "taiwan semiconductor manufacturing",
	"taiwan semiconductor": "taiwan semiconductor manufacturing",
	"foxconn": "hon hai precision industry",
	"hon hai": "hon hai precision industry",
	"ibm": "international business machines",
	"sk hynix inc": "sk hynix",
	"micron technology inc": "micron technology",
	"samsung electronics co": "samsung electronics",
	"alphabet": "google",
	"alphabet inc": "google",
	"meta platforms": "meta",
	"meta platforms inc": "meta",
	"advanced micro devices": "amd",
	"broadcom inc": "broadcom",
	"texas instruments incorporated": "texas instruments",
	"applied materials inc": "applied materials",
	"lam research corp": "lam research",
	"asml holding": "asml",
	"tokyo electron": "tokyo electron",
}


def _normalize_entity_name(name):
	"""Normalize a company/entity name for fuzzy matching."""
	if not name or not isinstance(name, str):
		return ""
	normalized = name.strip()
	# Remove suffixes (up to 3 iterations for nested suffixes)
	for _ in range(3):
		prev = normalized
		normalized = _ENTITY_SUFFIXES.sub("", normalized).strip()
		if normalized == prev:
			break
	# Lowercase + whitespace normalization
	normalized = re.sub(r"\s+", " ", normalized.lower().strip()).rstrip(".,;:")
	# Apply alias mapping
	return _ENTITY_ALIAS_MAP.get(normalized, normalized)
