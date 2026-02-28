---
name: marketdata
description: Multi-source financial data collection skill for stock prices, macro data, SEC filings, and market analysis. Integrates YFinance, FRED, SEC EDGAR, Finviz, and CFTC data sources.
allowed-tools: Bash, Read
---

# MarketData Collection Skill

Multi-source financial data retrieval system providing comprehensive market analysis capabilities through autonomous data collection. All scripts output JSON to stdout with `{"error": "message"}` for errors.

**Data Sources**: YFinance (stocks), FRED (macro), SEC EDGAR (filings), Finviz (screening), CFTC (futures), YCharts (CAPE), CBOE (IV/options chains/VIX futures)

**Setup**:
```bash
cd skills/MarketData/scripts
python -m venv .venv
.venv/bin/pip install -r requirements.txt
```
> In Cowork sessions, the scripts directory is read-only. Create the venv in the session working directory instead and point `$VENV` to it.

## Environment Bootstrap Protocol

### First-time Setup (automatic)
Before running any script, verify the following:
1. Check if `.venv` exists → if not:
   ```bash
   cd skills/MarketData/scripts
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
Need RSI? → SKILL.md Technical section → find oscillators.py → python tools/extract_docstring.py scripts/technical/oscillators.py
```

## Function Catalog

### Pipelines

Persona-specific analysis orchestrators (Facade) — prefer these as the primary data interface for each persona. Each pipeline covers single-ticker analysis, batch watchlist, market environment assessment, sector screening, multi-ticker comparison, and position management. Discover available subcommands via `extract_docstring.py`.

| Function | Description | Script |
|----------|-------------|--------|
| `minervini` | Full SEPA pipeline: composite scoring with hard-gate safety, signal reason codes, provisional watchlist mode, earnings proximity detection, company category hint, market environment assessment with industry group ranking, sector screening with valuation benchmarks, multi-ticker comparison, and position recheck | `pipelines/minervini.py` |
| `traderlion` | Full S.N.I.P.E. pipeline (Pipeline-Complete): SNIPE composite score (0-100) with 4 hard gates, edge-based position sizing, volume edge integration, constructive bar ratio, winning characteristics, TIGERS summary, provisional watchlist mode, market cycle assessment, sector screening, multi-ticker comparison, and position recheck | `pipelines/traderlion.py` |
| `serenity` | Full Serenity 6-Level pipeline (Pipeline-Complete): macro regime assessment, fundamental validation (4 health gates + fundamental readiness codes), conditional SEC dilution verification, evidence chain verification, multi-ticker comparison (12 metrics including asymmetry score), sector bottleneck screening, and CapEx cascade tracking. L2 CapEx Flow and L3 Bottleneck require agent-driven context. L6 Taxonomy requires LLM classification. Sector-agnostic | `pipelines/serenity.py` |
| `sidneykim0` | Macro-statistical pipeline: regime classification with confidence scoring, cross-asset divergence scan, historical analog matching with fan chart, deep-dive indicator analysis (rates/dollar/gold/liquidity/vix/erp/cape/credit), integrated scenario construction, and lightweight dashboard summary. No individual ticker required — analyzes the macro environment as a whole | `pipelines/sidneykim0.py` |
| `williams` | Full Williams short-term volatility breakout pipeline: trade-setup composite filter (TDW+TDM+bond+MA+pattern → conviction scoring with position sizing), single-ticker deep analysis, multi-ticker pattern scanning, market context (bond trend+COT+TDW/TDM calendar), batch watchlist evaluation, and quick dashboard | `pipelines/williams.py` |

### Core Analysis

#### Statistics

Z-score, percentile, correlation, extremes

| Function | Description | Script |
|----------|-------------|--------|
| `cointegration` | Test cointegration between two symbols using Engle-Granger method for pairs trading | `statistics/cointegration.py` |
| `correlation` | Calculate correlation between two symbols to identify relationship strength and regime changes | `statistics/correlation.py` |
| `distribution` | Calculate distribution statistics for returns to analyze risk, reward, and tail characteristics | `statistics/distribution.py` |
| `extremes` | Find extreme events beyond threshold sigma to identify historical tail risk events | `statistics/extremes.py` |
| `multi_correlation` | Calculate correlation matrix for multiple symbols to identify relationship patterns and pair rankings | `statistics/multi_correlation.py` |
| `multi_extremes` | Multi-Asset Extreme Detection - Identify simultaneous extreme z-scores across multiple assets | `statistics/multi_extremes.py` |
| `percentile` | Calculate percentile rank for stock price or returns to identify relative positioning | `statistics/percentile.py` |
| `zscore` | Calculate z-score for stock price or returns to identify statistical overbought/oversold levels | `statistics/zscore.py` |

#### Technical

RSI, MACD, SMA, EMA, Bollinger Bands, Stage Analysis, RS Ranking, VCP, Base Counting, Volume Analysis, Pocket Pivot, Low Cheat, Tight Closes, Closing Range, Volume Edge, Sell Signals, Special Patterns, Stock Character, Entry Patterns

| Function | Description | Script |
|----------|-------------|--------|
| `base_count` | Track base number within Stage 2 advance with pattern classification and risk assessment | `technical/base_count.py` |
| `indicators` | Technical indicator calculation functions for market data analysis | `technical/indicators.py` |
| `low_cheat` | Low cheat setup detection: tight consolidation below pivot for reduced-risk entry | `technical/low_cheat.py` |
| `oscillators` | Calculate momentum oscillators including RSI and MACD for overbought/oversold detection | `technical/oscillators.py` |
| `pocket_pivot` | Pocket pivot detection: institutional buying signals within base formations | `technical/pocket_pivot.py` |
| `rs_ranking` | Dual-approach RS ranking: YFinance score calculation (0-99) and Finviz high-RS screening | `technical/rs_ranking.py` |
| `slope` | 20-day rolling price slope normalization and RSI derivative momentum signals | `technical/slope.py` |
| `stage_analysis` | Minervini Stage 1-4 classification with confidence scoring and transition signal detection | `technical/stage_analysis.py` |
| `tight_closes` | Tight close cluster detection (daily/weekly): supply dryup confirmation near pivots | `technical/tight_closes.py` |
| `trend` | Calculate trend-following indicators including SMA, EMA, and Bollinger Bands | `technical/trend.py` |
| `vcp` | VCP detection with Cup & Handle, Power Play, 3C entry point, shakeout grading, relative correction, setup readiness scoring. Supports daily (default) and weekly intervals | `technical/vcp.py` |
| `post_breakout` | Post-breakout monitoring: tennis ball/egg behavior, squat recovery grading, failure reset detection, 20MA sell rule | `technical/post_breakout.py` |
| `volume_analysis` | Institutional accumulation/distribution analysis with A-E grading and breakout confirmation | `technical/volume_analysis.py` |
| `closing_range` | Closing Range (CR) calculation with Constructive/Non-constructive bar classification and screening | `technical/closing_range.py` |
| `volume_edge` | Volume edge detection: HVE, HVIPO, HV1, Increasing Average Volume, Volume Run Rate with conviction scoring | `technical/volume_edge.py` |
| `sell_signals` | Sell signal detection: MA breach (21 EMA / 50 SMA), high-volume reversal, vertical acceleration, key reversal, distribution cluster with severity grading and disposition effect audit | `technical/sell_signals.py` |
| `special_patterns` | Special bullish reversal/continuation pattern detection: Positive Expectation Breaker (bearish setup breakout), No Follow-Through Down (failed bearish event), Undercut & Rally (shakeout recovery) for hidden institutional demand | `technical/special_patterns.py` |
| `stock_character` | Stock character assessment: ADR%, clean/choppy classification, MA respect consistency, personality grade (A-D), liquidity tier | `technical/stock_character.py` |
| `entry_patterns` | Entry pattern detection: MA pullback, consolidation pivot, inside day, double inside day, tight day, gap reversal, support reclaim with trigger/stop prices | `technical/entry_patterns.py` |
| `williams` | Larry Williams short-term trading tools: Williams %R, volatility breakout levels, range analysis, swing point identification, pattern scanning (Outside Day/Smash Day/Hidden Smash Day/Specialists' Trap/Oops!), and composite trade setup filter with TDW/TDM/bond confirmation | `technical/williams.py` |

#### Data Sources

Price, financials, options, actions

| Function | Description | Script |
|----------|-------------|--------|
| `actions` | Corporate actions, earnings dates, calendar, and news | `data_sources/actions.py` |
| `earnings_acceleration` | Code 33 validation, earnings/sales acceleration patterns, surprise history, and analyst revisions | `data_sources/earnings_acceleration.py` |
| `bdi` | Baltic Dry Index (BDI) tracking via BDRY ETF with z-score analysis | `data_sources/bdi.py` |
| `calendars` | Financial calendars: earnings, IPO, economic events, and stock splits | `data_sources/calendars.py` |
| `dxy` | Dollar Index (DXY) tracking with z-score analysis | `data_sources/dxy.py` |
| `financials` | Financial statements retrieval | `data_sources/financials.py` |
| `funds` | YFinance funds data wrapper | `data_sources/funds.py` |
| `holders` | Holder and insider transaction data | `data_sources/holders.py` |
| `info` | Ticker information retrieval | `data_sources/info.py` |
| `market` | Market status and summary data via yfinance | `data_sources/market.py` |
| `multi` | Multi-ticker operations: compare, download, and news | `data_sources/multi.py` |
| `options` | Options data retrieval via yfinance | `data_sources/options.py` |
| `price` | Price data retrieval: history, download, and quote | `data_sources/price.py` |
| `search` | Search, screening, sector and industry data via yfinance | `data_sources/search.py` |

#### Analysis

Statistical analysis, fundamental analysis, and valuation tools

| Function | Description | Script |
|----------|-------------|--------|
| `analysis` | Analyst Estimates and Recommendations aggregating Wall Street consensus for earnings, revenue, and price targets | `analysis/analysis.py` |
| `analysis_utils` | Statistical Analysis Utilities providing reusable functions for multi-asset correlation, z-score, and percentile calculations | `analysis/analysis_utils.py` |
| `position_sizing` | Risk-based position sizing: calculate (entry sizing), pyramid (2%+2%+1% scaling plan), expectation (mathematical expectation with Kelly Criterion) | `analysis/position_sizing.py` |
| `convergence` | Multi-Model Convergence Analysis - SidneyKim0 methodology | `analysis/convergence.py` |
| `divergence` | Multi-Asset Divergence Detection analyzing correlation breakdown between traditionally linked assets | `analysis/divergence.py` |
| `putcall_ratio` | Put/Call Ratio analyzing options market sentiment through put vs call volume imbalance | `analysis/putcall_ratio.py` |
| `sbc_analyzer` | Stock-Based Compensation analysis: SBC amount, % of revenue, real FCF (FCF minus SBC), health flag | `analysis/sbc_analyzer.py` |
| `forward_pe` | Forward P/E calculator from analyst estimates with Walmart benchmark (45x) comparison | `analysis/forward_pe.py` |
| `margin_tracker` | Margin expansion tracker: gross/operating/net margin Q/Q and Y/Y changes with EXPANDING/STABLE/COMPRESSION/COLLAPSE flags | `analysis/margin_tracker.py` |
| `debt_structure` | Balance sheet health analyzer: debt structure, interest coverage, stress testing with rate hike scenarios | `analysis/debt_structure.py` |
| `institutional_quality` | Institutional ownership quality scorer (1-10) classifying holders as PASSIVE/LONG_ONLY/HEDGE/QUANT_MM | `analysis/institutional_quality.py` |
| `no_growth_valuation` | Zero-growth stress test: intrinsic value assuming 0% growth (revenue x margin x 15 P/E) with margin of safety | `analysis/no_growth_valuation.py` |
| `iv_context` | IV Rank/Percentile via CBOE: current IV30, annual high/low, IV Rank, HV30 comparison, cheap/fair/elevated/expensive classification | `analysis/iv_context.py` |
| `leaps_scanner` | LEAPS finder via CBOE options chain: optimal long-dated calls by target delta with breakeven and annualized cost | `analysis/leaps_scanner.py` |
| `csp_yield` | Cash-Secured Put yield calculator via CBOE: annualized yield, breakeven, downside cushion for put selling strategy | `analysis/csp_yield.py` |
| `capex_tracker` | Sector-agnostic CapEx tracker: quarterly track (QoQ/YoY direction), cascade (supply chain layer-wise health with user-defined layers), compare (side-by-side) | `analysis/capex_tracker.py` |
| `bottleneck_scorer` | Bottleneck financial validation: validate (4 health gates + asymmetry score), batch (multi-ticker sorted), rank (Supply Dominance formula priority ranking) | `analysis/bottleneck_scorer.py` |

#### Backtest

Conditional probability, event returns

| Function | Description | Script |
|----------|-------------|--------|
| `conditional` | Calculate conditional probability of reaching a target given a condition event | `backtest/conditional.py` |
| `event_returns` | Calculate forward return statistics after condition trigger events | `backtest/event_returns.py` |
| `extreme_reversals` | Detect extreme price events and measure mean reversion characteristics | `backtest/extreme_reversals.py` |
| `helpers` | Core helper functions for backtest analysis | `backtest/helpers.py` |
| `rate_cut_precedent` | Analyze historical Fed rate cut cycles and S&P 500 forward returns | `backtest/rate_cut_precedent.py` |
| `ratio` | Calculate and analyze asset price ratios for relative value assessment | `backtest/ratio.py` |

#### Macro

GBM fair value, multi-factor models

| Function | Description | Script |
|----------|-------------|--------|
| `erp` | Equity Risk Premium (ERP) = Earnings Yield - US10Y for valuation danger detection | `macro/erp.py` |
| `gbm` | Geometric Brownian Motion (GBM) Fair Value Model | `macro/gbm.py` |
| `macro` | Macro model and fair value analysis for SidneyKim0 methodology | `macro/macro.py` |
| `macro_inference` | Multi-parameter macro inference model: rolling OLS/ridge regression, residual Z-score, backtest, sensitivity analysis (SidneyKim0 signature tool) | `macro/macro_inference.py` |
| `macro_utils` | Macro analysis utility functions for MarketData skill | `macro/macro_utils.py` |
| `net_liquidity` | Fed Net Liquidity composite (Balance Sheet - TGA - RRP) for systemic liquidity tracking | `macro/net_liquidity.py` |
| `vix_curve` | VIX Futures Curve analyzer via CBOE: VX1-VX9 term structure, contango/backwardation, regime classification (complacent/normal/anxious/panic) | `macro/vix_curve.py` |

### Specialized Analysis

#### Convergence

Multi-model convergence (SidneyKim0)

| Function | Description | Script |
|----------|-------------|--------|
| `convergence` | Multi-Model Convergence Analysis - SidneyKim0 methodology | `analysis/convergence.py` |

#### Divergence

Model divergence detection

| Function | Description | Script |
|----------|-------------|--------|
| `divergence` | Multi-Asset Divergence Detection analyzing correlation breakdown between traditionally linked assets | `analysis/divergence.py` |

#### Sentiment

Fear & Greed Index

| Function | Description | Script |
|----------|-------------|--------|
| `fear_greed` | CNN Fear & Greed Index tracking market sentiment through 7-indicator composite scoring system | `analysis/sentiment/fear_greed.py` |

#### Pattern

Technical patterns, regime detection

| Function | Description | Script |
|----------|-------------|--------|
| `fanchart` | Fan chart visualization | `technical/pattern/fanchart.py` |
| `helpers` | Pattern analysis helper functions for DTW, correlation, and forward return calculations | `technical/pattern/helpers.py` |
| `multi_dtw` | Multi-feature DTW pattern matching using price+RSI+slope+volatility+D2H vectors | `technical/pattern/multi_dtw.py` |
| `regime` | Market regime detection | `technical/pattern/regime.py` |
| `similarity` | Pattern similarity analysis | `technical/pattern/similarity.py` |

#### Valuation

CAPE ratio, dividend yield

| Function | Description | Script |
|----------|-------------|--------|
| `cape` | CAPE (Cyclically Adjusted Price-to-Earnings) Ratio data from YCharts | `valuation/cape.py` |
| `cape_historical` | Historical CAPE data from Robert Shiller dataset | `valuation/cape_historical.py` |
| `dividend_yield` | S&P 500 dividend yield calculation | `valuation/dividend_yield.py` |

### Data & Screening

#### Info

Company information

| Function | Description | Script |
|----------|-------------|--------|
| `info` | Ticker information retrieval | `data_sources/info.py` |

#### Screening

Finviz stock screener and Minervini Trend Template

| Function | Description | Script |
|----------|-------------|--------|
| `finviz` | Finviz stock screening, sector/industry group analysis, industry-level screening (partial name match), and market breadth (new 52W highs/lows by exchange) | `screening/finviz.py` |
| `finviz_presets` | Finviz screening preset definitions (includes Minervini SEPA presets) | `screening/finviz_presets.py` |
| `sector_leaders` | Bottom-up sector leadership dashboard: leader count by industry group with performance enrichment | `screening/sector_leaders.py` |
| `trend_template` | Minervini Trend Template 8-criteria checklist for Stage 2 qualification screening | `screening/trend_template.py` |

#### CFTC

Futures commitment of traders

| Function | Description | Script |
|----------|-------------|--------|
| `cftc` | CFTC Commitment of Traders (COT) data retrieval | `data_advanced/cftc/cftc.py` |

### Advanced Data Sources

#### FRED

Fed Funds, yield curve, inflation, policy

| Function | Description | Script |
|----------|-------------|--------|
| `inflation` | Federal Reserve Economic Data (FRED) inflation indicators and expectations data | `data_advanced/fred/inflation.py` |
| `policy` | Federal Reserve Economic Data (FRED) monetary policy and liquidity indicators | `data_advanced/fred/policy.py` |
| `rates` | Federal Reserve Economic Data (FRED) interest rate and yield curve data access | `data_advanced/fred/rates.py` |
| `series` | Federal Reserve Economic Data (FRED) generic series access utility | `data_advanced/fred/series.py` |

#### Fed

FedWatch Tool, FOMC calendar

| Function | Description | Script |
|----------|-------------|--------|
| `fedwatch` | CME FedWatch Tool - FOMC rate change probabilities from Fed Funds futures | `data_advanced/fed/fedwatch.py` |
| `fomc_calendar` | FOMC meeting calendar with official Federal Reserve meeting schedule | `data_advanced/fed/fomc_calendar.py` |

#### SEC

Filings, insider trades, 13F, FTD

| Function | Description | Script |
|----------|-------------|--------|
| `filings` | SEC company filings access and Management Discussion & Analysis (MD&A) extraction | `data_advanced/sec/filings.py` |
| `ftd` | SEC Failures to Deliver (FTD) and litigation releases data | `data_advanced/sec/ftd.py` |
| `insider` | SEC Form 4 insider trading activity tracking | `data_advanced/sec/insider.py` |
| `institutions` | SEC 13F filing lookup by company CIK (investment managers only, not stock ownership) | `data_advanced/sec/institutions.py` |

## How to Use

**Environment variables** (for all script execution):
```bash
VENV=skills/MarketData/scripts/.venv/bin/python
SCRIPTS=skills/MarketData/scripts
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