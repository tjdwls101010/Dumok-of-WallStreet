# Changelog

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
