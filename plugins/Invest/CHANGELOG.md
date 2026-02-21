# Changelog

## 2026-02-21

### Changed
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
