"""Market breadth from Finviz homepage (~1-2s, single HTTP request).

Scrapes advancing/declining, new high/low, SMA50, SMA200 breadth data
from finviz.com homepage. Much faster than screener-based breadth
(which requires 4+ separate API calls).

Commands:
    breadth: Get current market breadth snapshot

Args:
    No required args.

Returns:
    dict with advancing_declining (advancing/declining pct+count),
    new_high_low (new_high/new_low pct+count),
    sma50 (above/below pct+count),
    sma200 (above/below pct+count)

Example:
    >>> python screening/market_breadth.py breadth
    {"advancing_declining": {"advancing": {"pct": 45.4, "count": 2528}, ...}, ...}
"""

import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import requests
from lxml import html

from utils import output_json, safe_run

_URL = "https://finviz.com/"
_USER_AGENT = (
	"Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
	"AppleWebKit/537.36 (KHTML, like Gecko) "
	"Chrome/120.0.0.0 Safari/537.36"
)

_FIELDS = [
	("advancing_declining", "advancing", "declining"),
	("new_high_low",        "new_high",  "new_low"),
	("sma50",               "above",     "below"),
	("sma200",              "above",     "below"),
]
_PCT_COUNT_RE = re.compile(r"([\d.]+)%\s*\((\d+)\)")  # "45.4% (2528)"
_COUNT_PCT_RE = re.compile(r"\((\d+)\)\s*([\d.]+)%")   # "(2746) 49.3%"


def _parse_side(text, pattern):
	m = pattern.search(text)
	if m and pattern is _PCT_COUNT_RE:
		return {"pct": float(m.group(1)), "count": int(m.group(2))}
	if m and pattern is _COUNT_PCT_RE:
		return {"pct": float(m.group(2)), "count": int(m.group(1))}
	return {"pct": 0.0, "count": 0}


def get_market_breadth():
	"""Scrape market breadth from Finviz homepage."""
	resp = requests.get(_URL, headers={"User-Agent": _USER_AGENT})
	resp.raise_for_status()
	tree = html.fromstring(resp.text)
	stats = tree.cssselect("div.market-stats")

	result = {}
	for (key, pos_name, neg_name), el in zip(_FIELDS, stats):
		pos_texts = [p.text_content().strip() for p in el.cssselect(".market-stats_labels_left p")]
		neg_texts = [p.text_content().strip() for p in el.cssselect(".market-stats_labels_right p")]

		pos = _parse_side(pos_texts[1], _PCT_COUNT_RE) if len(pos_texts) >= 2 else {"pct": 0.0, "count": 0}
		neg = _parse_side(neg_texts[1], _COUNT_PCT_RE) if len(neg_texts) >= 2 else {"pct": 0.0, "count": 0}

		result[key] = {
			pos_name: pos,
			neg_name: neg,
		}

	return result


@safe_run
def cmd_breadth(args):
	"""Get current market breadth snapshot."""
	output_json(get_market_breadth())


def main():
	parser = argparse.ArgumentParser(description="Market Breadth (Finviz Homepage)")
	sub = parser.add_subparsers(dest="command", required=True)

	sub.add_parser("breadth", help="Market breadth snapshot")

	args = parser.parse_args()

	if args.command == "breadth":
		cmd_breadth(args)


if __name__ == "__main__":
	main()
