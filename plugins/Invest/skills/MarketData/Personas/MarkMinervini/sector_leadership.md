# Sector Leadership Identification Guide

## Bottom-Up Sector Identification Workflow

Minervini's approach: "Let stocks point you to the sector." Do not start with macro narratives or sector rotation theories. Start with leader stocks, then see where they cluster.

### Step 1: Scan for Leaders

Screen for stocks matching the Minervini leader profile (yearly +20%, quarterly +10%, near 52W high, EPS growth >25%, above 200MA) and group them by industry. Rank industry groups by leader concentration.

### Step 2: Identify Top Groups

Focus on the top 3-5 industry groups by leader count. A group with 5+ leaders is a strong signal of institutional rotation into that sector.

### Step 3: Cross-Reference Group Performance

Validate leader concentration with group-level price performance. The ideal setup: high leader count AND strong group performance. A group with many leaders but weak aggregate performance may indicate selective (not broad) leadership -- still valid but narrower.

### Step 4: Drill Into Leaders

For each top group, examine the individual leaders through the full SEPA pipeline. Assess each leader for: Trend Template pass/fail, base count (earlier = better), VCP formation, earnings acceleration.

### Step 5: Assess Sector Maturity

Determine whether the sector's advance is early, mid, or late stage:

- **Early stage**: Most leaders on base 1-2, RS recently crossed 80, group just starting to outperform. Highest reward potential.
- **Mid stage**: Leaders on base 2-3, some with extended gains (+100%+), strong but decelerating group momentum. Still buyable with selectivity.
- **Late stage**: Leaders on base 3-4+, widespread media attention on the sector, parabolic moves, RS divergences appearing. Reduce new entries, tighten stops on existing.

Use base count as the primary maturity signal.

---

## Sector Leadership Rotation Signals

### Detecting Rotation in Real-Time

Rotation happens when capital flows from old leading groups to new ones. Detect this by:

1. **Dashboard comparison over time**: If Group A's leader count drops from 8 to 3 while Group B rises from 2 to 7, rotation is underway.

2. **RS deterioration in old leaders**: Former top-group leaders showing RS declining below 80, Stage 3 transitions, 50MA violations.

3. **New group breakouts**: Groups that had zero leaders 4-8 weeks ago now showing 3+ leaders = emerging leadership.

### Dashboard Interpretation

**Healthy leadership**: 8+ industry groups with 3+ leaders each. Broad participation = strong market.

**Narrowing leadership**: Only 2-3 groups with leaders, total leader count declining. This is a risk signal -- the market advance is becoming dependent on fewer stocks.

**Rotation in progress**: Total leader count stable, but the composition shifts. Old groups losing leaders, new groups gaining. This is neutral-to-positive if the new groups are fundamentally strong.

**Leadership collapse**: Total leader count drops sharply (e.g., 50+ to under 20 in 4 weeks). Major risk signal -- reduce exposure.

---

## Broken Leader Detection

Former cycle leaders rarely lead the next advance. Fewer than 25% of leaders repeat.

1. Identify previous cycle's top leaders (stocks that were RS 90+ and in top industry groups)
2. Check their current stage: Stage 3 or 4 = confirmed broken leader. Do not buy.
3. Stage 1 with improving RS = possible re-emergence (rare, <25% probability)

Broken leaders often show: declining earnings deceleration, RS below 50, base count reset after Stage 4, loss of institutional sponsorship.

---

## Integration with Query Types

### Type A (Market Environment)

Start with the sector dashboard to assess market health:

1. Assess leader count and distribution across industry groups
2. Interpret: total leaders = market health proxy, group distribution = breadth proxy
3. Check for narrowing leadership as an early warning
4. Cross-reference with sector-level performance distribution
5. Check new highs/new lows by exchange with NYSE/NASDAQ divergence detection

Market health verdict derives from LEADER BEHAVIOR, not aggregate statistics.

### Type C (Stock Discovery)

Start with sector-first discovery, then drill into individual leaders:

1. Identify leading groups (top 5 by leader concentration)
2. Screen within those sectors for candidates meeting Minervini criteria
3. Apply SEPA filters to the sector results
4. Rank candidates by: base count (lower = better), RS score (higher = better), earnings acceleration (Code 33 = bonus)

This aligns with Minervini's approach: find the sector first, then the leader within it.

### Type F (Risk Check)

Check for narrowing leadership as a risk indicator:

1. Assess total leader count across all groups
2. Compare against previous assessment (if available) for trend
3. Fewer leaders + fewer groups = increasing risk
4. Check broken leader count in previously top groups
5. Combine with Stage 3/4 transition counts for comprehensive risk view

---

## ETF-Based Sector Analysis (Fallback)

When detailed industry screening is unavailable, use ETF-based sector analysis as an alternative path. Compare 11 sector ETFs (XLK, XLV, XLF, XLC, XLI, XLP, XLY, XLE, XLRE, XLB, XLU) against SPY using RS scoring.

### Limitations

- **Sector-level only**: Cannot identify individual stock leaders within sectors
- **No industry group granularity**: ETFs represent broad sectors, not the ~150 industry groups. "Technology leading" is less actionable than "Semiconductors leading."
- **No filter criteria**: Cannot apply Minervini filters (EPS growth, near 52W high, etc.) via ETF data

### Fallback Chain

1. **Retry with backoff**: Automatic retry with exponential backoff (up to 3 attempts)
2. **ETF-based sector scan**: Sector-level RS ranking via ETF comparison
3. **Manual screening**: Use available tools on known watchlist stocks

---

## Sector Context Check Protocol

When analyzing an individual stock (Type B/D/E), consider checking the health of its sector peers. This is recommended but not required.

### When to Activate

- The target stock shows mixed signals (e.g., Stage 2 but RS declining)
- Earnings are approaching and sector context matters
- The stock's industry group has been flagged as losing leaders in recent scans
- Type F (Risk Check) analysis where sector-wide health matters

### Workflow

1. Identify 3-5 peers in the same industry group
2. Classify the stage for each peer
3. Assess: If 3+ peers are in Stage 3/4, the sector may be rolling over regardless of the target stock's individual technicals
4. Factor this into the risk assessment -- sector headwinds reduce the probability of successful breakouts even for individually strong stocks

### Interpretation

- **All peers Stage 2**: Healthy sector, individual stock analysis stands on its own merit
- **Mixed stages (some Stage 2, some Stage 3)**: Rotation within sector, favor the peers still in Stage 2
- **Most peers Stage 3/4**: Sector is topping, increase caution even for the target stock. Consider tighter stops or reduced position size.
