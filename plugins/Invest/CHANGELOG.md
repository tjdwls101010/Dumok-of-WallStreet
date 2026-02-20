# Changelog

## 2026-02-20

### Added
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
