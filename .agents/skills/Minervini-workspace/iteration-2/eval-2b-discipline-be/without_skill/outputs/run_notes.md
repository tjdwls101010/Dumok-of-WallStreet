# Run notes — BE discipline eval (without_skill)

Tool: raw yfinance only, via Minervini .venv python. No skills/scripts loaded.
Data pulled 2026-06-17 close (yfinance auto_adjust=True).

## Ticker: BE (Bloom Energy Corporation)

### Price / trend (history period=2y, auto_adjust)
- rows: 501; last date 2026-06-17
- last close: 287.53 (1y pull showed 287.15 — intraday/feed diff, used ~287.5)
- MA50: 254.83
- MA150: 171.55
- MA200: 151.56 ; MA200 1mo ago: 128.09 → MA200 rising = True
- Stage-2 alignment: price > MA50 > MA150 > MA200 (clean uptrend)
- 52wk high: 307.88 ; 52wk low: 21.34
- pct off 52wk high: -6.6%
- pct above 52wk low: +1247.4%
- avg vol 50d: 10,456,860 ; last vol: 2,712,581

### Performance / RS
- 3mo: +83.4% ; 6mo: +220.6% ; 1yr: +1245.6%
- SPY 6mo: +11.0% ; SPY 1yr: +26.8% → BE massively outperforming (strong RS)

### Volatility / recent swing (key disqualifier)
- avg daily range last 20d: 8.1%
- beta: 3.746
- last close vs 50dma: +12.7% (extended, chase zone)
- Recent 9-day path: 291→264→254→260→234→249→260→275→287
  (~-24% high-to-low then +23% bounce in ~9 sessions → "support reclaim" is just noise; can't set sane stop)

### Fundamentals / valuation (.info)
- sector: Industrials ; industry: Electrical Equipment & Parts
- marketCap: 81,763,418,112 (~$81.8B)
- totalRevenue: 2,449,027,072 → PSR ~33x
- forwardPE: 66.13 ; trailingPE: None
- profitMargins: 0.00246 (~0.25%) ; grossMargins: 0.3009
- revenueGrowth: 1.304 (+130%) ; earningsGrowth: None
- totalDebt: 2,952,817,920 ; totalCash: 2,491,432,960 (net debt)
- sharesShort: 28,556,389 ; shortRatio: 2.69 ; floatShares: 278,991,079 (~10% of float short)
- sharesOutstanding: 284,443,868
- 52WeekChange: 12.06 (yfinance field; note unit looks like ratio*12 oddity — relied on own 1245% calc instead)
- recommendationKey: buy ; targetMeanPrice: 263.648 (BELOW current price)
- currentPrice: 287.45

## Verdict logic
Strong Stage-2 trend + elite RS, BUT: price is -6.6% off 52wk high (chase, not bottom "support"),
8.1% daily range / beta 3.75 makes stops unworkable, PSR 33x / fwd PE 66x / ~0% margin,
mean target below price. → Do NOT chase at market now; if entering, demand: confirm signal basis,
wait for pullback toward 50dma, pre-set stop, small size. Disciplined "no/wait" answer.
