#!/usr/bin/env python3
"""Extract module-level docstrings from Python files.

Usage:
    python tools/extract_docstring.py scripts/dividend_yield.py scripts/cape.py
    python tools/extract_docstring.py scripts/data_sources/info.py --json
"""

import argparse
import ast
import json
import sys
from pathlib import Path

MARKETDATA_ROOT = Path(__file__).resolve().parent.parent


def extract_module_docstring(file_path: Path) -> str | None:
	"""Extract module docstring from Python file using ast."""
	try:
		content = file_path.read_text(encoding="utf-8")
		tree = ast.parse(content)
		return ast.get_docstring(tree)
	except Exception as e:
		print(f"Error parsing {file_path}: {e}", file=sys.stderr)
		return None


def resolve_path(raw: str) -> Path:
	"""Resolve file path relative to MarketData root or as absolute."""
	p = Path(raw)
	if p.is_absolute():
		return p
	candidate = MARKETDATA_ROOT / p
	if candidate.exists():
		return candidate
	return p


def main() -> None:
	parser = argparse.ArgumentParser(description="Extract module-level docstrings from Python files.")
	parser.add_argument("files", nargs="*", help="Python files to extract docstrings from")
	parser.add_argument("--json", action="store_true", dest="as_json", help="Output as JSON")
	args = parser.parse_args()

	if not args.files:
		parser.print_help()
		sys.exit(1)

	results: dict[str, str | None] = {}

	for raw_path in args.files:
		file_path = resolve_path(raw_path)
		if not file_path.exists():
			print(f"File not found: {raw_path}", file=sys.stderr)
			results[raw_path] = None
			continue
		results[raw_path] = extract_module_docstring(file_path)

	if args.as_json:
		print(json.dumps(results, indent=2, ensure_ascii=False))
	else:
		for path, doc in results.items():
			print(f"--- {path} ---")
			print(doc if doc else "(no docstring)")
			print()


if __name__ == "__main__":
	main()
