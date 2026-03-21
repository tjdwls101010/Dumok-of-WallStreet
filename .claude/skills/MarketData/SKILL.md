---
name: marketdata
description: Multi-source financial data collection skill for stock prices, macro data, SEC filings, and market analysis. Integrates YFinance, FRED, SEC EDGAR, Finviz, and CFTC data sources.
allowed-tools: Bash, Read
---

# MarketData Collection Skill

Multi-source financial data retrieval system providing comprehensive market analysis capabilities through autonomous data collection. All scripts output JSON to stdout with `{"error": "message"}` for errors.

**Data Sources**: YFinance (stocks), FRED (macro), SEC EDGAR (filings), Finviz (screening/breadth), YCharts (CAPE), CBOE (IV/VIX futures)

**Setup**:
```bash
cd $SKILL_ROOT/scripts
python -m venv .venv
.venv/bin/pip install -r requirements.txt
```
> In Cowork sessions, the scripts directory is read-only. Create the venv in the session working directory instead and point `$VENV` to it.

## Environment Bootstrap Protocol

### First-time Setup (automatic)
Before running any script, verify the following:
1. Check if `.venv` exists → if not:
   ```bash
   cd $SKILL_ROOT/scripts
   python3 -m venv .venv
   .venv/bin/pip install -r requirements.txt
   ```

### Cowork Environment
The plugin cache directory in Cowork is **read-only** — venv creation will fail in the scripts directory.
Create the venv in the session working directory instead (e.g., `/sessions/{session-id}/.venv`),
install requirements from the original scripts path, and set `$VENV` to the new venv's python path.
Scripts remain executable from their original read-only location — no copying needed.

## Progressive Disclosure Architecture

This skill uses **2-level Progressive Disclosure**:

- **Level 1: SKILL.md** (this file) - Complete function catalog with all categories
- **Level 2: Python Docstrings** - Detailed documentation extracted via `tools/extract_docstring.py`

See **Script Execution Safety Protocol** below for mandatory discovery and execution rules.

### Navigation Flow

```
Need VCP? → SKILL.md Technical section → find vcp.py → python tools/extract_docstring.py scripts/technical/vcp.py
```

## Function Catalog

### Pipelines

Persona-specific analysis orchestrators (Facade) — prefer these as the primary data interface. Discover available subcommands via `extract_docstring.py`.

| Function | Description | Script |
|----------|-------------|--------|
| `minervini` | Full SEPA pipeline (Pipeline-Complete, 2 subcommands: analyze, discover): SEPA composite scoring (0-100) with hard-gate safety (Stage 2 + Trend Template 8/8), VCP/entry pattern synthesis, Code 33 and earnings quality integration, risk assessment with R:R calculation, position sizing, market leadership dashboard with distribution day counting | `pipelines/minervini/` |
| `serenity` | Full Serenity 6-Level pipeline (Pipeline-Complete, 3 subcommands: macro, analyze, discover): macro regime assessment, fundamental validation (5 health gates), SEC supply chain extraction via edgartools + Gemini, 6-Criteria Bottleneck scoring, CapEx flow tracking, composite signal generation, control layer outputs. Sector-agnostic | `pipelines/serenity.py` |

### Pipeline-Used Modules

Modules actively called by Minervini and/or Serenity pipelines via subprocess.

#### Technical

Stage Analysis, RS Ranking, VCP, Base Counting, Volume Analysis, Pocket Pivot, Tight Closes, Sell Signals, Stock Character, Entry Patterns

| Function | Description | Script |
|----------|-------------|--------|
| `base_count` | Track base number within Stage 2 advance with pattern classification and risk assessment | `technical/base_count.py` |
| `entry_patterns` | Entry pattern detection: MA pullback, consolidation pivot, inside day, double inside day, tight day, gap reversal, support reclaim with trigger/stop prices | `technical/entry_patterns.py` |
| `indicators` | Technical indicator calculation functions (shared library used by multiple modules) | `technical/indicators.py` |
| `pocket_pivot` | Pocket pivot detection: institutional buying signals within base formations | `technical/pocket_pivot.py` |
| `rs_ranking` | Dual-approach RS ranking: YFinance score calculation (0-99) and Finviz high-RS screening | `technical/rs_ranking.py` |
| `sell_signals` | Sell signal detection: MA breach, high-volume reversal, vertical acceleration, key reversal, distribution cluster | `technical/sell_signals.py` |
| `stage_analysis` | Minervini Stage 1-4 classification with confidence scoring and transition signal detection | `technical/stage_analysis.py` |
| `stock_character` | Stock character assessment: ADR%, clean/choppy classification, personality grade (A-D), liquidity tier | `technical/stock_character.py` |
| `tight_closes` | Tight close cluster detection (daily/weekly): supply dryup confirmation near pivots | `technical/tight_closes.py` |
| `vcp` | VCP detection with Cup & Handle, Power Play, 3C entry point, shakeout grading, setup readiness scoring | `technical/vcp.py` |
| `volume_analysis` | Institutional accumulation/distribution analysis with A-E grading and breakout confirmation | `technical/volume_analysis.py` |

#### Data Sources

Financials, actions, holders, earnings, macro proxies

| Function | Description | Script |
|----------|-------------|--------|
| `actions` | Corporate actions, earnings dates, calendar, and news | `data_sources/actions.py` |
| `bdi` | Baltic Dry Index (BDI) tracking via BDRY ETF with z-score analysis | `data_sources/bdi.py` |
| `dxy` | Dollar Index (DXY) tracking with z-score analysis | `data_sources/dxy.py` |
| `earnings_acceleration` | Code 33 validation, earnings/sales acceleration patterns, surprise history, and analyst revisions | `data_sources/earnings_acceleration.py` |
| `financials` | Financial statements retrieval | `data_sources/financials.py` |
| `holders` | Holder and insider transaction data | `data_sources/holders.py` |
| `info` | Ticker information retrieval | `data_sources/info.py` |
| `superinvestor` | Superinvestor holdings from Dataroma: 81 top fund managers, recent activity per ticker | `data_sources/superinvestor.py` |

#### Analysis

Fundamental analysis and valuation tools

| Function | Description | Script |
|----------|-------------|--------|
| `analysis` | Analyst Estimates and Recommendations aggregating Wall Street consensus | `analysis/analysis.py` |
| `capex_tracker` | Sector-agnostic CapEx tracker: quarterly track, cascade, compare | `analysis/capex_tracker.py` |
| `debt_structure` | Balance sheet health analyzer: debt structure, interest coverage, stress testing | `analysis/debt_structure.py` |
| `fear_greed` | CNN Fear & Greed Index: 7-indicator composite scoring system | `analysis/sentiment/fear_greed.py` |
| `forward_pe` | Forward P/E calculator from analyst estimates | `analysis/forward_pe.py` |
| `institutional_quality` | Institutional ownership quality scorer (1-10) | `analysis/institutional_quality.py` |
| `iv_context` | IV Rank/Percentile via CBOE: IV30, HV30, classification | `analysis/iv_context.py` |
| `margin_tracker` | Margin expansion tracker: Q/Q and Y/Y changes with flags | `analysis/margin_tracker.py` |
| `no_growth_valuation` | Zero-growth stress test: intrinsic value at 0% growth with margin of safety | `analysis/no_growth_valuation.py` |
| `position_sizing` | Risk-based position sizing: calculate, pyramid, expectation | `analysis/position_sizing.py` |
| `sbc_analyzer` | Stock-Based Compensation analysis: SBC %, real FCF, health flag | `analysis/sbc_analyzer.py` |
| `bottleneck_scorer` | Bottleneck financial validation (part of serenity pipeline) | `pipelines/serenity/_scorer.py` |

#### Macro

ERP, net liquidity, VIX curve

| Function | Description | Script |
|----------|-------------|--------|
| `erp` | Equity Risk Premium (ERP) = Earnings Yield - US10Y for valuation danger detection | `macro/erp.py` |
| `net_liquidity` | Fed Net Liquidity composite (Balance Sheet - TGA - RRP) for systemic liquidity tracking | `macro/net_liquidity.py` |
| `vix_curve` | VIX Futures Curve analyzer via CBOE: VX1-VX9 term structure, contango/backwardation, regime classification | `macro/vix_curve.py` |

#### Screening

Market breadth, trend template

| Function | Description | Script |
|----------|-------------|--------|
| `market_breadth` | Fast Finviz homepage scraper: advancing/declining, new high/low, SMA breadth | `screening/market_breadth.py` |
| `trend_template` | Minervini Trend Template 8-criteria checklist for Stage 2 qualification screening | `screening/trend_template.py` |

#### Valuation

CAPE ratio (dependency of macro/erp.py)

| Function | Description | Script |
|----------|-------------|--------|
| `cape` | CAPE (Cyclically Adjusted Price-to-Earnings) Ratio data from YCharts | `valuation/cape.py` |

### Advanced Data Sources

#### FRED

Yield curve, inflation

| Function | Description | Script |
|----------|-------------|--------|
| `inflation` | FRED inflation indicators and expectations data | `data_advanced/fred/inflation.py` |
| `rates` | FRED interest rate and yield curve data access | `data_advanced/fred/rates.py` |

#### Fed

FedWatch Tool

| Function | Description | Script |
|----------|-------------|--------|
| `fedwatch` | CME FedWatch Tool - FOMC rate change probabilities from Fed Funds futures | `data_advanced/fed/fedwatch.py` |
| `fomc_calendar` | FOMC meeting calendar (dependency of fedwatch.py) | `data_advanced/fed/fomc_calendar.py` |

#### SEC

Filings, supply chain intelligence

| Function | Description | Script |
|----------|-------------|--------|
| `filings` | SEC company filings access and MD&A extraction | `data_advanced/sec/filings.py` |
| `supply_chain` | SEC 10-K/10-Q/20-F supply chain intelligence extraction via edgartools + XBRL + Gemini | `data_advanced/sec/supply_chain.py` |
| `events` | SEC 8-K supply chain event detection | `data_advanced/sec/supply_chain.py` |

## How to Use

**Environment variables** (for all script execution):
```bash
VENV=$SKILL_ROOT/scripts/.venv/bin/python
SCRIPTS=$SKILL_ROOT/scripts
```
> In Cowork (read-only filesystem), `$VENV` should point to the venv created in the writable session directory.

**Step 1**: Find the script you need in the catalog above.

**Step 2**: Discover exact subcommands via `extract_docstring.py` (see Safety Protocol below).

**Step 3**: Run the script: `$VENV $SCRIPTS/{path} {subcommand} {args}`

All scripts return JSON. Error format: `{"error": "message"}` with exit code 1.

## Script Execution Safety Protocol

### [HARD] Core Rule: Discover Before Execute

Never execute a script without first discovering its subcommands via `extract_docstring.py`. Subcommand names CANNOT be guessed from Level 1 (SKILL.md catalog) alone. For example, `info.py` has subcommands `get-fast-info` and `get-info`, NOT `get`.

**Execution flow**:
1. Identify which script(s) you need to call
2. Run `extract_docstring.py` on those specific scripts
3. Execute with the discovered subcommands

**Pipeline usage**: When using a pipeline (e.g., `minervini.py`), discover only the pipeline itself. The pipeline internally calls individual modules — you do not need to discover those modules unless you plan to call them individually as supplements AFTER the pipeline.

**Batch execution**: When calling multiple scripts in parallel, discover ALL of them beforehand in a single `extract_docstring.py` call (max 5 per call) to prevent cascading "Sibling tool call errored" failures from wrong subcommand names.

**Skip condition**: If you have already successfully discovered a script's subcommands in the current session, you may reuse them without re-discovery.

### [HARD] Never Read Code Files Directly

Always use `extract_docstring.py` for function details. Direct `.py` file Read is severe token waste.

### [HARD] Output Integrity Rule

Never pipe script output through `head`, `tail`, or any truncation command. Always capture and use full output.

### [HARD] Script Failure Mandatory Retry Rule

Every failed script execution MUST be retried. No exceptions.

**Retry Protocol:**
1. Script returns error or non-zero exit code → Retry with corrected arguments
2. "Sibling tool call errored" (parallel execution failure) → Re-execute in the NEXT turn
3. Second failure → Try alternative script from Fallback Chain (see below)
4. Fallback also fails → Explicitly declare: "⚠️ [script name] data unavailable. Analysis proceeds WITHOUT this data. Affected sections marked."

**Prohibited Behaviors:**
- NEVER skip a failed script and proceed as if data was collected
- NEVER infer or estimate values that a failed script would have returned
- NEVER substitute WebSearch results for failed MarketData scripts without explicitly stating the data source downgrade