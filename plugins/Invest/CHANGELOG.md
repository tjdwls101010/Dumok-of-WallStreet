# Changelog

## 2026-02-25 (v1.9.0) — Pipeline Facade Refactoring

### Added
- **`minervini.py`** — 4 new pipeline subcommands (Facade pattern):
  - `market-leaders`: Market environment assessment via sector leadership dashboard, market breadth, and batch TT checks on top leaders (classifies healthy vs broken leaders)
  - `screen`: Sector-based SEPA candidate screening using Finviz sector-screen + watchlist-level analysis (TT, Stage, RS, Earnings, Volume) with composite scoring
  - `compare`: Multi-ticker full SEPA comparison with head-to-head ranking, side-by-side comparison table, and top candidate recommendation
  - `recheck`: Position management recheck for held positions (TT status, Stage, post-breakout behavior, volume condition, earnings proximity, consolidated risk update)
- **`traderlion.py`** — 4 new pipeline subcommands (Facade pattern):
  - `market-cycle`: Market cycle assessment via QQQ 21 EMA status, gauge stock MA alignment, and market breadth. Produces composite cycle score (0-8) with cycle stage classification and exposure guidance
  - `screen`: Sector-based S.N.I.P.E. candidate screening using Finviz + watchlist-level SNIPE analysis with edge detection
  - `compare`: Multi-ticker full S.N.I.P.E. comparison with 7-axis ranking (edge count, RS, winning characteristics, setup maturity, base count, volume grade, constructive ratio)
  - `recheck`: Position management recheck (TT, Stage, post-breakout, closing range, volume edge freshness, earnings proximity, position grade data)
- **`serenity.py`** — 1 new pipeline subcommand:
  - `capex-cascade`: Supply chain CapEx cascade tracking across multiple tickers with 8Q trend per ticker, cascade health summary (upstream→downstream consistency), and hyperscaler signal detection

### Changed
- **`serenity.py`** — `compare` expanded from 11 to 12 metrics: added `asymmetry_score` via `bottleneck_scorer.py validate` per ticker. New relative_strength: `best_asymmetry`. Bottleneck health gate flags integrated into per-ticker health gates.
- **`Minervini.md`** — Abstracted pipeline references: replaced specific script invocations with pipeline-first guidance. Added `extract_docstring.py` discovery instruction for subcommand lookup.
- **`TraderLion.md`** — Abstracted pipeline references: replaced SNIPE pipeline naming with TraderLion pipeline. Pipeline-first soft guide added.
- **`Serenity.md`** — Abstracted pipeline references: pipeline-first soft guide with `extract_docstring.py` discovery. Script-automated section consolidated to pipeline entry point.
- **`SKILL.md`** — Pipeline section updated: descriptions reflect expanded Facade scope (market environment, screening, comparison, position management) without listing specific subcommands. Added pipeline-first guidance with `extract_docstring.py` discovery note.

## 2026-02-24 (v1.8.3)

### Fixed
- **`info.py`** — `get-info-fields` now uses 3-tier fallback for key fields: (1) `ticker.get_info()`, (2) `ticker.fast_info` for marketCap/currentPrice/52w range, (3) `ticker.history(period="5d")` last Close for currentPrice. Eliminates null values for ADRs and some large-caps (e.g., AVGO, TSM) that yfinance `get_info()` sometimes fails to populate.

### Changed
- **`serenity.py`** — `compare` expanded from 9 to 11 metrics: added `sbc_flag` (from sbc_analyzer) and `consecutive_beats` (from earnings_surprise). Two new relative_strengths: `best_sbc_health` and `best_earnings_momentum`. Updated docstring to reflect 11 metrics.
- **`Serenity.md`** — Progressive Disclosure cleanup: removed inline VENV/SCRIPTS paths and extract_docstring.py call syntax from Script Execution section; replaced with `SKILL.md` reference. Replaced Script Failure Fallback Protocol with one-line reference to `SKILL.md` "Error Handling & Fallback Guide". Retained two `[HARD]` behavioral rules.
- **`SKILL.md`** — Added VENV/SCRIPTS environment variable definitions to "How to Use" section. Expanded `serenity` pipeline description: added L1/L2/L3/L6 level annotations and "11 metrics" for compare.

## 2026-02-23 (v1.8.2)

### Changed
- **Pipeline scripts** — Moved from `screening/` to new `pipelines/` directory for semantic clarity
  - `screening/sepa_pipeline.py` → `pipelines/minervini.py`
  - `screening/snipe_pipeline.py` → `pipelines/traderlion.py`
  - `screening/serenity_pipeline.py` → `pipelines/serenity.py`
- **`SKILL.md`** — New "Pipelines" category added above Screening; function names updated
- **`Minervini.md`** — Pipeline path added to Analysis Protocol Step 2
- **`TraderLion.md`** — Pipeline references updated to new path
- **`Serenity.md`** — Pipeline references updated to new path

## 2026-02-22 (v1.8.1)

### Fixed
- **`serenity_pipeline.py`** — Fixed `revenue_growth_yoy` = null bug in `cmd_compare()`: was extracting from `earnings_acceleration` code33 output (which has no `quarters` key or `revenue_growth_yoy` field), now correctly sources from `forward_pe` (analyst consensus revenue growth estimate). No additional API calls needed — `forward_pe` was already executed per-ticker.

### Changed
- **`serenity_pipeline.py`** — Removed `earnings_acceleration` from `cmd_compare()` script list. After the `revenue_growth_yoy` fix, no compare metric or health gate uses it. Saves 1 subprocess + API call per ticker.
- **`serenity_pipeline.py`** — Output size optimization in `cmd_analyze()` (~5-9KB/ticker reduction):
  - `earnings_dates`: capped at 8 most recent via `_cap_earnings_dates()` post-processing (yfinance ignores `--limit`, was 20+ entries)
  - `earnings_acceleration`: compressed via `_compress_earnings_acceleration()` to 8 essential fields (status flags + 3 most recent growth rates)
  - `holders`: summarized via `_summarize_holders()` to top 5 holders (name, pctHeld, shares) + total count
- **`serenity_pipeline.py`** — Updated module docstring: `revenue_growth_yoy` source, compressed L4 field descriptions, new Notes entries for all output optimizations.
- **`Serenity.md`** — Added Cross-Subcommand Optimization guidance (use `--skip-macro`, expected L4 re-execution, compare-first workflow).
- **`Serenity.md`** — Consolidated Data Source Routing section: replaced verbose paragraphs with `methodology.md` reference + bulleted query-type directives.
- **`supply_chain_bottleneck.md`** — Consolidated Scenario-Driven Discovery Protocol Steps 3-5: replaced re-explanations of 5-Layer Template and 6-Criteria Scoring with references to definitions earlier in the same file (~22 lines saved).
- **`supply_chain_bottleneck.md`** — Moved Historical Case Studies to end-of-file Appendix with HARD GUARDRAIL against defaulting to historical tickers on new queries.

### Added
- **`serenity_pipeline.py`** — New helper functions: `_cap_earnings_dates()` (trims dict-of-dicts to 8 most recent, workaround for yfinance ignoring limit), `_compress_earnings_acceleration()` (retains status flags + 3 recent growth rates), `_summarize_holders()` (top 5 holders with key fields + total count).

## 2026-02-22 (v1.8.0)

### Fixed
- **`serenity_pipeline.py`** — Fixed ERP and Fear&Greed signal extraction paths in `_classify_macro_regime()`, `cmd_macro()`, and `cmd_analyze()`. ERP was using top-level `erp.get("erp_pct")` but `erp.py` returns `{"current": {"erp": float}}` → now uses `erp.get("current", {}).get("erp")`. Fear&Greed was using `fear_greed.get("value")` but `fear_greed.py` returns `{"current": {"score": float}}` → now uses `fear_greed.get("current", {}).get("score")`. Both signals were always `null` in prior versions.
- **`serenity_pipeline.py`** — Improved macro decision_rules: now distinguishes between "data unavailable" (null) vs "below threshold" (actual value shown). ERP and Fear&Greed rules display actual values (e.g., "ERP at 2.15% — below healthy threshold (>3%)" instead of generic "ERP below healthy threshold").

### Changed
- **`serenity_pipeline.py`** — Token optimization (~17-22KB/ticker, ~35-45% reduction):
  - Removed `shares_history` from L4 (~5-10KB/ticker) — `sbc_analyzer` already provides `shares_change_qoq_pct` and `dilution_flag`
  - Removed `earnings_calendar` from L5 (~4KB/ticker) — was fetching market-wide calendar (no ticker arg), identical across all tickers; `earnings_dates` already provides ticker-specific dates
  - Added `--start` (12-month lookback) to `insider_transactions` and post-processing via `_summarize_insider_transactions()`: buy/sell count+amount aggregation, `net_direction` classification, capped at 20 most recent transactions (~9KB/ticker savings)
  - Compare: replaced `get-info` (100+ fields) with `get-info-fields` (5 fields: marketCap, currentPrice, fiftyTwoWeekLow, fiftyTwoWeekHigh, shortPercentOfFloat) (~4.8KB/ticker savings)
  - Removed `earnings_calendar` from `cmd_evidence_chain` L6 scripts

### Added
- **`serenity_pipeline.py`** — L2 company CapEx auto-inclusion: `capex_tracker.py track --quarters 8` runs in L4 parallel batch, result moved to `L2_capex_flow.company_capex`. Supply chain cascade still requires agent context (`cascade_requires_context: true`).
- **`serenity_pipeline.py`** — Revenue trajectory: quarterly income statement fetched via `financials.py get-income-stmt --freq quarterly`, post-processed by `_extract_revenue_trajectory()` to extract TotalRevenue for 8 quarters. Placed in L4 as `revenue_trajectory`.
- **`serenity_pipeline.py`** — Compare metrics expanded from 5 to 9: added `market_cap`, `revenue_growth_yoy` (from earnings_acceleration), `short_interest_pct`, `52w_range_position`. Added `best_revenue_growth` and `best_52w_position` to relative_strengths.
- **`serenity_pipeline.py`** — New helper functions: `_summarize_insider_transactions()` (buy/sell aggregation + net_direction + cap at 20), `_extract_revenue_trajectory()` (TotalRevenue extraction from income statement, 8 quarters).

## 2026-02-22 (v1.7.1)

### Fixed
- **`serenity_pipeline.py`** — Fixed net liquidity signal bug in `_classify_macro_regime()`: field path was `net_liq.get("trend")` but actual output structure is `net_liq.get("net_liquidity", {}).get("direction")`. Result: `net_liq_positive` was always False, net liquidity signal never reflected in macro regime classification.

### Changed
- **`serenity_pipeline.py`** — Output size optimization (~5.1MB → ~50-100KB, ~98% reduction):
  - Yield curve: added `--limit 5` to `rates.py yield-curve` call (was fetching 25 years of daily data, ~3-4MB)
  - Net liquidity: added `--limit 10` to `net_liquidity.py` call (was fetching 52 days of history, only trend needed)
  - Macro raw data: replaced `"data": macro_results` with `"signals"` dict extracting 9 scalar values (erp_pct, vix_spot, vix_regime, vix_structure, net_liq_direction, net_liq_current, fear_greed, fedwatch_next_meeting, fedwatch_probabilities)
  - Removed raw financial statements (income_stmt, cash_flow, balance_sheet) from L4 — individual analysis scripts already extract needed metrics independently
  - Replaced `info.py get-info` (100+ fields) with `get-info-fields` (24 essential fields for analysis)
- **`serenity_pipeline.py`** — Added missing methodology data to pipeline:
  - L4: `insider_transactions` (holders.py get-insider-transactions --exclude-grants) for insider activity tracking
  - L4: `shares_history` (info.py get-shares-full, 2-year window) for dilution tracking
  - L5: `earnings_surprise` (earnings_acceleration.py surprise) for post-ER reaction data
  - L5: `analyst_recommendations` (analysis.py get-recommendations-summary) for consensus direction
  - L5: `analyst_price_targets` (analysis.py get-analyst-price-targets) for valuation context
  - L5: `analyst_revisions` (earnings_acceleration.py revisions) for estimate revision tracking

## 2026-02-22 (v1.7.0)

### Added
- **`serenity_pipeline.py`** (`skills/MarketData/scripts/screening/serenity_pipeline.py`) — Full Serenity 6-Level analytical hierarchy pipeline. 5 subcommands: `macro` (Level 1 macro regime assessment with 6 parallel scripts, regime classification as risk_on/risk_off/transitional, --extended for DXY+BDI), `analyze` (full 6-Level analysis with L1/L4/L5 auto-execution and L2/L3 requires_context for agent-driven supply chain analysis, 4 health gates: Bear-Bull Paradox/Active Dilution/No-Growth Fail/Margin Collapse), `evidence_chain` (6-link data availability check with chain_completeness scoring), `compare` (multi-ticker side-by-side comparison table with relative_strengths), `screen` (sector-based bottleneck candidate screening via finviz + bottleneck_scorer). Sector-agnostic: works for any industry.
- **`bottleneck_scorer.py`** (`skills/MarketData/scripts/analysis/bottleneck_scorer.py`) — Sector-agnostic financial validation of supply chain bottleneck candidates. 3 subcommands: `validate` (4 health gates — Bear-Bull Paradox, Active Dilution, No-Growth Floor, Margin Collapse — plus asymmetry score 0-100), `batch` (multi-ticker validation sorted by asymmetry score), `rank` (priority ranking using Supply Dominance formula).
- **`capex_tracker.py`** (`skills/MarketData/scripts/analysis/capex_tracker.py`) — Sector-agnostic CapEx tracker across supply chain layers. 3 subcommands: `track` (QoQ/YoY CapEx tracking with direction classification), `cascade` (supply chain layer-wise CapEx health with user-defined layers), `compare` (side-by-side CapEx comparison).

### Changed
- **`Serenity.md` command** — Progressive disclosure refactor: removed 11 direct `.py` script references (serenity_pipeline x8, bottleneck_scorer x2, capex_tracker x1, info.py x1) from pipeline routing, Step 2b, and Type D Phase 4. Replaced with functional descriptions that match SKILL.md catalog vocabulary for agent discovery. Added Health-Gate Interpretation section (output interpretation context — the one place the pipeline is named, matching Minervini pattern). Added Script-Automated vs Agent-Level Inference section listing 6-Level concepts. Net `.py` references: 14 → 3 (extract_docstring.py only). No behavioral change — same pipeline subcommands discovered via SKILL.md instead of hardcoded references.
- **`methodology.md`** — Removed Conviction and Rating System (moved to Command for cross-cutting access on all query types). Cleaned MarketData-First section: added prefix clarifying Command enforcement, added WebSearch Autonomous Usage Principle, added Industry-specific data row to source guide. Replaced duplicate 2-Phase Workflow with Domain-Specific Data Source Guide.
- **`valuation_fundamentals.md`** — Converted 4 script references to purpose/data/interpretation format: No-Growth Stress Test automation, Margin Trajectory analysis, SBC/Real FCF test, SBC Filter. Removed all `.py` filename references from persona file.

## 2026-02-21 (v1.6.0)

### Added
- **`snipe_pipeline.py`** (`skills/MarketData/scripts/screening/snipe_pipeline.py`) — Full TraderLion S.N.I.P.E. pipeline script (~640 lines). SNIPE Composite Score (0-100) with 6 weighted components: Edge Detection (30), Stage/Trend (20), Growth (15), Setup Quality (15), Volume Confirmation (10), Winning Characteristics (10). 4 hard gates (Stage 3/4, TT<5/8, no institutional footprint, distribution+weak construction). 5 signal levels (AGGRESSIVE/STANDARD/REDUCED/MONITOR/AVOID). Edge-based position sizing (10%+2.5% per edge). TIGERS summary, earnings proximity detection, winning characteristics detail. Commands: `analyze` (single), `watchlist` (batch with provisional mode).

### Fixed
- **Progressive disclosure compliance** — Removed 16 direct script references from persona files (`trade_management.md`, `stock_identification.md`, `market_environment.md`). Reduced script coupling in `TraderLion.md` command (individual script names → concept names). Collapsed Quick Reference from ~55 lines to ~15 lines, delegating methodology tables to persona files. All per `Command → SKILL.md → Persona → Scripts` layering principle.
- **Methodology purity** — Removed time-dependent data from persona files: ZM benchmark example from `stock_identification.md`, hardcoded ticker symbols (TSLA/GOOGL/NVDA) from `market_environment.md` gauge section. Replaced with abstract selection criteria preserving the methodology without stale references.

### Changed
- **`TraderLion.md` command** — 6 structural enhancements:
  - Added **Type G (Stock Comparison)** query classification with 7-axis head-to-head comparison protocol
  - Restructured **Analysis Protocol** from 8-step to 10-step with snipe_pipeline as primary entry point (step 3), hard-gate check (step 4), and mandatory volume confirmation (step 6: "no edge verdict without volume confirmation")
  - Replaced **Short-Circuit Rules** with 3-tier system: Full Path / Reduced Path (with re-qualification conditions) / AVOID Path
  - Added **Hard-Gate Interpretation** section mapping each blocker code to TraderLion methodology principles
  - Added **Agent Orchestration Guide** defining main-agent vs sub-agent responsibilities with explicit "never delegate" list
  - Added **Provisional Signal Handling** rules for watchlist batch results
- **`trade_management.md`** — 4 new operational enforcement sections:
  - **Post-Entry Behavior Classification**: Tennis Ball / Egg / Squat behavior classification with constructive bar ratio monitoring and 20MA sell rule integration
  - **Disposition Effect Check Protocol**: Mandatory 6-signal audit on every Type E query, trigger counting (3+ = alert), adding-to-a-loser refusal rule
  - **Earnings Event Protocol**: 5-day proximity activation, edge freshness check, position health assessment, 3-option framework (full exit / half position / hold with absolute stop)
  - **Four Contingency Plans**: Initial stop, re-entry, profit-taking, disaster scenario — all mandatory before trade entry confirmation
- **`stock_identification.md`** — Added **Head-to-Head Comparison Framework** (Type G support): 7-axis comparison table (edge count, RS, winning characteristics, setup maturity, base count, volume grade, constructive ratio) with tiebreaker rules and comparison protocol
- **`market_environment.md`** — Added **Market Breadth Quantification**: NH/NL ratio formula with 5-tier interpretation, leadership breadth assessment, breadth divergence detection rule, integration with cycle score
- **`SKILL.md`** — Added `snipe_pipeline` catalog entry in Screening section + fallback chain entry
- **`plugin.json`** — Version bump 1.5.1 → 1.6.0
- **`marketplace.json`** — Plugin version sync + metadata version bump to 1.6.0

## 2026-02-21

### Changed
- **`williams.py`** — Extracted 4 pattern detection functions from monolithic `_detect_patterns()`: `_detect_outside_day()`, `_detect_smash_day_naked()`, `_detect_smash_day_hidden()`, `_detect_oops_gap()`. The orchestrator `_detect_patterns()` reduced from ~158 lines to ~50 lines of loop + dispatch logic. No external interface or output format changes.
- **`methodology.md`** — Added "Script Output Interpretation Guide" section with `williams_r`, `volatility_breakout`, `swing_points`, and `range_analysis` interpretation subsections. All content extracted from Williams.db original text (Ch.1, Ch.3, Ch.4, Ch.5, Ch.8).
- **`short_term_trading.md`** — Added "Script Output Interpretation Guide" section with `pattern_scan` interpretation subsection covering all 5 pattern types, signal status meanings, multi-pattern priority ranking, and TDW interaction rules. All content extracted from Williams.db original text (Ch.6, Ch.7).

### Changed (earlier same day)
- **`williams.py`** — Refactored inline calculation logic into reusable private helpers (`_fetch_data`, `_calculate_wr`, `_calculate_breakout_levels`, `_calculate_range_phase`). Added TDW/TDM lookup tables, `_detect_patterns` helper (5 Williams chart patterns), `cmd_pattern_scan` subcommand, and `cmd_trade_setup` composite subcommand (runs all 5 filters — TDW, TDM, bond trend, 20-day MA, patterns — with conviction scoring and position sizing). Updated module docstring with new commands/args/returns.
- **`money_management.md`** — Removed non-methodology content (~95 lines): compressed Business of Speculation to 3-line list, replaced position sizing formula with trade_setup reference, collapsed Historical Money Management to 1 line, removed Blowup narrative (kept 5 rules), removed emotional counseling sections. Added trade_setup result interpretation guide (conviction-based risk selection, 4-loser simulation, position sizing verification).
- **`market_analysis.md`** — Removed non-methodology content (~110 lines): removed 50-Year Wisdom, Losers vs Winners, Forecasting Is Futile, Hard Truths, compressed Market Cycle Awareness. Merged "Public vs Professionals" into Price Behavior Truth 3. Removed backtest numbers from bond section. Added trade_setup filter interpretation guide (bond scenarios, filter conflict resolution, conviction scenarios).
- **`Williams.md` command** — Restructured Analysis Protocol around trade_setup as primary entry point (8-step → 5-step). Reclassified TDW/TDM/bond/MA/pattern/conviction/sizing from agent-level to script-automated. Updated Short-Circuit Rules to reference trade_setup output fields. Added error handling for trade_setup and pattern_scan failures.

### Added
- **Williams command** (`commands/Williams.md`) — Short-term volatility breakout trading specialist replicating Larry Williams' price/time framework and money management methodology. Applied to US stocks with ATR-based breakout entries, Trading Day of Week/Month filters, bond intermarket confirmation, and fixed-percentage position sizing (2-4% risk per trade).
- **Williams persona files** (4 files in `skills/MarketData/Personas/Williams/`):
  - `methodology.md` — Volatility breakout system (core entry formulas), market structure (swing points), TDW filter, trend filters (20-day MA + bond), large-range day capture, five trading tools
  - `short_term_trading.md` — Chart patterns (outside day, smash day, specialists' trap, Oops!), Greatest Swing Value (GSV), Willspread inter-market indicator, TDM patterns, 3-bar channel, seasonal strategies, exit rules
  - `money_management.md` — Position sizing formula, 2-4% risk framework, 4-consecutive-loser survival test, Kelly Formula critique, blowup phenomenon, emotional discipline, speculation mindset
  - `market_analysis.md` — Bond-stock leading indicator relationship, COT analysis, price behavior truths, freight train theory, 50-year market wisdom, winner/loser traits, hard truths
- **`williams.py`** (`skills/MarketData/scripts/technical/williams.py`) — Larry Williams short-term trading tools: Williams %R oscillator, volatility breakout signal generation, range expansion/contraction analysis, and mechanical swing point identification; williams_r, volatility_breakout, range_analysis, and swing_points subcommands

## 2026-02-20

### Added
- **TraderLion command** (`commands/TraderLion.md`) — Momentum trading process architect replicating TraderLion's S.N.I.P.E. workflow and volume-edge methodology. Applied to US growth stocks with market cycle assessment, edge-based position sizing, 11 entry tactics, and staged sell rules.
- **TraderLion persona files** (4 files in `skills/MarketData/Personas/TraderLion/`):
  - `methodology.md` — S.N.I.P.E. workflow, TIGERS stock selection, 4-stage trader development, edge discovery meta-methodology, screening framework
  - `stock_identification.md` — Volume edges (HVE/HVIPO/HV1/Increasing Avg Vol), RS edge, N-Factor, setups (Launch Pad/Gapper/Base Breakout), Closing Range, Winning Characteristics checklist
  - `trade_management.md` — 11 entry tactics, edge-based position sizing, stop system, sell rules (Stage 1-2/Progressive/Performance), post analysis
  - `market_environment.md` — Market cycle 4 stages, gauge system, breadth analysis, cycle score, volatility contraction, multi-timeframe alignment, failed vs successful breakouts
- **`closing_range.py`** (`skills/MarketData/scripts/technical/closing_range.py`) — Closing Range calculation with Constructive/Non-constructive bar classification; analyze and screen subcommands
- **`volume_edge.py`** (`skills/MarketData/scripts/technical/volume_edge.py`) — Volume edge detection (HVE/HVIPO/HV1/Increasing Average Volume/Volume Run Rate); detect and screen subcommands

- **SidneyKim0 command** (`commands/SidneyKim0.md`) — Macro-statistical analysis specialist replicating SidneyKim0's methodology. Applied to US markets with regime classification, cross-asset divergence detection, historical analog mapping, and probabilistic scenario construction.
- **SidneyKim0 persona files** (4 files in `skills/MarketData/Personas/SidneyKim0/`):
  - `methodology.md` — Market regime classification, data cascade hierarchy, analysis workflow
  - `quantitative_models.md` — Residual Z-score, pattern similarity, RSI percentile, correlation analysis, ERP model, event study framework
  - `cross_asset_analysis.md` — Yield curve, DXY-equity, gold, liquidity (TGA/RRP), credit spreads, commodity-macro connections
  - `historical_analogies.md` — Analog selection methodology, 1993/1997/1998/2007/2011 reference points, validation/invalidation framework
- **`macro_inference.py`** (`skills/MarketData/scripts/macro/macro_inference.py`) — Multi-parameter macro inference model with rolling OLS/ridge regression, residual Z-score analysis, backtest, and sensitivity subcommands

## 2026-02-16

### Added
- **[HARD] Truncation Recovery Rule** in `SKILL.md` — Prevents cascading failures when `extract_docstring.py` output exceeds 30KB and gets truncated by the system. Forces Claude to read the saved full-output file before executing any script, eliminating subcommand guessing from partial previews.

### Changed
- **Batch Discovery Rule** — `extract_docstring.py` 호출 시 최대 5개 스크립트 배치 제한 추가. 카테고리 내 스크립트가 10개 이상인 경우에도 토큰 소비를 적절히 관리.
