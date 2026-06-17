"""Minervini SEPA pipeline command implementations.

Two composable subcommands — NOT a closed pipeline, and deliberately WITHOUT an
"analyze everything at once" command. That monolith was the Serenity-style
total-collect crutch: it reasoned FOR the analyst by grouping every module into
one verdict-shaped blob, which invites deference to the shape instead of reading
the evidence. Deepening past the gate is done by calling the individual module
CLIs directly (vcp, earnings_acceleration, rs_ranking, volume_analysis, …), in
the order the funnel earns.

- qualify: cheap Tier-0 gate (Stage 2 + Trend Template + RS) — run this FIRST
- discover: market environment + RS leader discovery

Each module result is checked for errors and missing modules are tracked
(graceful degradation).
"""

import concurrent.futures
import time

from utils import output_json, safe_run

from ._runner import _run_script
from ._gates import compute_hard_gates


# ---------------------------------------------------------------------------
# cmd_qualify — Tier-0 cheap gate
# ---------------------------------------------------------------------------

@safe_run
def cmd_qualify(args):
	"""Tier-0 gate: the cheapest read that can disqualify a ticker.

	Runs only the three modules that decide whether deeper work is worth it —
	Trend Template, Stage analysis, RS — and returns the deterministic hard-gate
	verdict. AVOID means structurally disqualified: stop, don't spend a full
	analyze pass. PROCEED means the name earned a closer look, NOT that it's a buy.
	"""
	ticker = args.ticker.upper()
	start = time.time()

	scripts = {
		"trend_template": ("modules/trend_template.py", ["check", ticker]),
		"stage_analysis": ("modules/stage_analysis.py", ["classify", ticker]),
		"rs_ranking": ("modules/rs_ranking.py", ["score", ticker]),
	}

	with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
		futures = {
			name: executor.submit(_run_script, path, a)
			for name, (path, a) in scripts.items()
		}
		results = {name: future.result() for name, future in futures.items()}

	hard_gate_fail, hard_gates, overall_pass = compute_hard_gates(results)

	stage = results.get("stage_analysis", {})
	rs = results.get("rs_ranking", {})
	tt_gate = next((g for g in hard_gates if g["gate"] == "trend_template"), {})

	verdict = "PROCEED" if overall_pass else "AVOID"
	failed = [g["gate"] for g in hard_gates if not g["passed"]]

	elapsed = round(time.time() - start, 1)

	output_json({
		"ticker": ticker,
		"verdict": verdict,
		"overall_pass": overall_pass,
		"failed_gates": failed,
		"hard_gates": hard_gates,
		"stage": stage.get("stage") if not stage.get("error") else None,
		"trend_template_score": tt_gate.get("score"),
		"rs_rating": rs.get("rs_rating") if not rs.get("error") else None,
		"interpretation": {
			"PROCEED": "both hard gates pass (Stage 2 + Trend Template 8/8) — worth a full read, NOT yet a buy",
			"AVOID": "a hard gate failed — structurally disqualified; stop here, do not deepen",
		},
		"metadata": {"execution_time_seconds": elapsed},
	})



# ---------------------------------------------------------------------------
# cmd_market_leaders
# ---------------------------------------------------------------------------

@safe_run
def cmd_discover(args):
	"""Market environment + RS leader discovery.

	Assesses market health (breadth, distribution days) and identifies
	RS leaders (sector/industry rankings, top stocks, movers) for
	candidate discovery using the ibd-rs-rating library.
	"""
	start = time.time()

	from rs_rating import RS
	_rs = RS()

	# Single executor: RS calls complete in ~1s, finviz market-breadth ~20-30s.
	# Submit industry_top as soon as industry_ranking completes (overlaps with
	# market-breadth wait, so adds zero wall-clock time).
	with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
		f_breadth = executor.submit(_run_script, "modules/market_breadth.py", ["breadth"])
		f_spy = executor.submit(_run_script, "modules/volume_analysis.py", ["analyze", "SPY"])
		f_rs_ref = executor.submit(lambda: _rs.reference())
		f_rs_top = executor.submit(lambda: _rs.top(20))
		f_sector_rank = executor.submit(lambda: _rs.sector_ranking())
		f_industry_rank = executor.submit(lambda: _rs.industry_ranking())
		f_movers = executor.submit(lambda: _rs.movers(days=5, n=20, direction="up"))

		# Wait for industry_ranking first (~0.8s) then submit industry_top
		# while market-breadth is still running (~20-30s remaining)
		try:
			industry_rank = f_industry_rank.result() or []
		except Exception:
			industry_rank = []

		industry_futures = {}
		for ind in industry_rank[:15]:
			ind_name = ind.get("industry", "")
			if ind_name:
				f = executor.submit(lambda name=ind_name: _rs.industry_top(name, n=5))
				industry_futures[f] = ind

		# Collect remaining Phase 1 results (market-breadth is the bottleneck)
		breadth_result = f_breadth.result()
		spy_vol = f_spy.result()

		# RS data (graceful on failure)
		try:
			rs_ref = f_rs_ref.result()
		except Exception:
			rs_ref = []
		try:
			rs_top = f_rs_top.result()
		except Exception:
			rs_top = []
		try:
			sector_rank = f_sector_rank.result() or []
		except Exception:
			sector_rank = []
		try:
			movers_result = f_movers.result() or []
		except Exception:
			movers_result = []

		# Collect industry_top results (already completed during breadth wait)
		for f in concurrent.futures.as_completed(industry_futures):
			ind = industry_futures[f]
			try:
				tickers = f.result() or []
				ind["leader_tickers"] = [t["ticker"] for t in tickers]
				ind["leader_count"] = len(ind["leader_tickers"])
			except Exception:
				ind["leader_tickers"] = []
				ind["leader_count"] = 0

	# Assign leadership ranks
	for i, ind in enumerate(industry_rank):
		ind["leadership_rank"] = i + 1

	# Distribution day count from SPY volume analysis
	dist_days = 0
	if not spy_vol.get("error"):
		clusters = spy_vol.get("distribution_clusters", {})
		dist_days = clusters.get("dist_days_25d", 0)
		if dist_days == 0:
			dist_days = spy_vol.get("distribution_clusters", {}).get("clusters_found", 0)

	# Market breadth
	new_highs = 0
	new_lows = 0
	if not breadth_result.get("error"):
		hl = breadth_result.get("new_high_low", {})
		new_highs = hl.get("new_high", {}).get("count", 0)
		new_lows = hl.get("new_low", {}).get("count", 0)

	# Verdict — breadth-primary. Minervini times the market off LEADERSHIP and the
	# new-high/new-low spread (and its expansion), not an O'Neil distribution-day
	# tally. So breadth (highs vs lows) is the primary axis here; distribution days
	# are a SECONDARY tape read that only nuances how late a bull tape is, never the
	# gate. The leadership read itself (rs_leaders, leadership_dashboard, movers)
	# is for the analyst to weigh — it is richer than any single label.
	highs_lows_ratio = round(new_highs / max(new_lows, 1), 2)
	heavy_distribution = dist_days >= 5  # secondary caution only

	if new_highs > new_lows * 2:
		verdict = "bull_late" if heavy_distribution else "bull_early"
	elif new_highs > new_lows:
		verdict = "bull_late"
	elif new_lows > new_highs * 2:
		verdict = "bear"
	else:
		verdict = "correction"

	verdict_evidence = {
		"new_highs_vs_lows": highs_lows_ratio,
		"distribution_days_25d": dist_days,
		"distribution_days_role": "secondary tape read, not the regime gate; leaders + new-high/new-low expansion lead the index",
	}

	# Build RS leaders section
	spy_rs = None
	qqq_rs = None
	for ref in (rs_ref or []):
		if ref.get("ticker") == "SPY":
			spy_rs = ref.get("rs_rating")
		elif ref.get("ticker") == "QQQ":
			qqq_rs = ref.get("rs_rating")

	rs_leaders = {
		"spy_rs": spy_rs,
		"qqq_rs": qqq_rs,
		"top_20": rs_top[:20] if rs_top else [],
		"movers_5d": movers_result[:20],
	}

	# Add rank to sector_ranking
	for i, s in enumerate(sector_rank):
		s["rank"] = i + 1

	elapsed = round(time.time() - start, 1)

	output_json({
		"market_verdict": verdict,
		"verdict_evidence": verdict_evidence,
		"breadth": {
			"new_highs": new_highs,
			"new_lows": new_lows,
			"detail": breadth_result if not breadth_result.get("error") else None,
		},
		"rs_leaders": rs_leaders,
		"sector_ranking": sector_rank,
		"leadership_dashboard": industry_rank,
		"thresholds": {
			"verdict_rules": {
				"bull_early": "highs > lows*2 (and distribution not heavy)",
				"bull_late": "highs > lows, OR highs > lows*2 with heavy distribution (dist_days >= 5)",
				"correction": "lows >= highs but not > highs*2",
				"bear": "lows > highs*2",
				"note": "breadth-primary; distribution days only nuance bull_early vs bull_late. Read leadership (rs_leaders/leadership_dashboard) for the real regime signal.",
			},
		},
		"metadata": {
			"execution_time_seconds": elapsed,
		},
	})

