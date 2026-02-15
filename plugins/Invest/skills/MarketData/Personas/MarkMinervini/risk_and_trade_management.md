# Risk and Trade Management

Decision frameworks for risk management and trade management. Covers judgment calls that scripts cannot automate: when to short-circuit analysis, how to handle earnings events, and how to adjust for market environments.

---

## Risk-First Philosophy

- A 50% loss requires a 100% gain just to break even
- This asymmetry is the fundamental reason why cutting losses short is the single most important rule
- Same winning trades, same number of winners and losers -- the only change is capping losses at 10% maximum: the result swings from -12.05% to +79.89%
- Loss control transforms a losing system into a winning system

### Geometric Loss Impact Table

| Loss | Required Gain to Break Even |
|------|----------------------------|
| 5% | 5.26% |
| 10% | 11% |
| 20% | 25% |
| 30% | 43% |
| 40% | 67% |
| 50% | 100% |
| 60% | 150% |
| 70% | 233% |
| 80% | 400% |
| 90% | 900% |

---

## Loss Control Rules

### Maximum Absolute Stop: 10%

Never allow a loss greater than 10% on any position. Average stop: 6-7%.

### The 1/2 Average Gain Rule

Maximum stop loss should be set at one-half of your average gain. If your average gain is 15%, maximum stop loss should be 7.5%. This automatically ensures at least a 2:1 reward-to-risk ratio.

### The Cardinal Sin

Allowing a single loss to exceed your average gain. If your average gain is 15%, then a loss of 16% or more violates this rule and mathematically puts you at a severe disadvantage.

---

## Gain/Loss Ratio by Batting Average

### Building in Failure

Design the system to be profitable even with a sub-50% batting average.

**Minimum**: 2:1 reward-to-risk ratio
**Target**: 3:1 reward-to-risk ratio

At a 2:1 ratio, you can be right only one-third of the time and not get in trouble. At a 3:1 ratio, even a 40% batting average yields a fortune over time.

### Batting Average Reality

- Best traders pick winning stocks about 60-70% of the time in a healthy market
- A trader can be correct only 50% of the time and still be profitable with proper risk management
- At 40% batting average with proper risk/reward ratio, a trader can still be highly profitable

---

## The Loss Adjustment Exercise (Verbatim)

**Original results:**
- Gains: 6%, 8%, 10%, 12%, 15%, 17%, 18%, 20%, 28%, 50%
- Average gain: 18.40%
- Losses: 7%, 8%, 10%, 12%, 13%, 15%, 19%, 20%, 25%, 30%
- Average loss: 15.90%
- Compounded return: **-12.05%**

**After capping all losses at 10% maximum:**
- Gains: unchanged
- Losses capped: 7%, 8%, 10%, 10%, 10%, 10%, 10%, 10%, 10%, 10%
- Compounded return: **+79.89%**

---

## Four Contingency Plans

Every trade must have four plans established BEFORE entry:

1. **Initial Stop-Loss**: Where you will exit if the trade goes against you immediately
2. **Reentry Plan**: Under what conditions you will re-enter if stopped out
3. **Selling at a Profit Plan**: At what point and under what conditions you will take profits
4. **Disaster Plan**: What you will do in case of a market crash, circuit breaker, or black swan event

---

## Failure Reset

When a stop-loss is triggered and a position is closed, the stock should not be discarded. If the fundamentals remain intact (earnings still accelerating, RS still strong, Stage 2 still valid), the stock should stay on the watch list for a potential failure reset.

### Base Failure Reset

After a stop-out, if the stock builds a whole new base formation over 5-15 weeks with fresh VCP characteristics (minimum 2 contractions with progressive tightening), this constitutes a base failure reset. The new base effectively resets the entry point with a fresh supply/demand equilibrium. The original failed breakout becomes part of the base-building process.

### Pivot Failure Reset

A shorter-term reset that occurs within 2-4 weeks of the stop-out. The stock quickly forms a new tight pivot near the original entry area -- price consolidates within a 3-5% range of the prior pivot price (95-105% of the original pivot) for 3 or more trading days with declining volume. This tight reset signals that the shakeout was temporary and the stock is ready for another attempt.

Some of the biggest winners are stocks that stopped out and then reset. The stop-out itself can be the final shakeout that removes the last weak holders before the real advance begins. The rule: keep stopped-out stocks on the watch list if fundamentals remain intact. Do not discard a stock just because it triggered your stop.

---

## Short-Circuit Analysis Rule

When performing SEPA analysis (Analysis Protocol Steps 3-4), apply this judgment gate to determine analysis depth:

### Full Analysis Path

TT 6/8+ PASS + Stage 2: Proceed with full analysis (Steps 5-7: Earnings, Risk, Action Plan).

### Abbreviated Path

TT 4-5/8 PASS (Near-miss): Abbreviated analysis -- note the specific failing criteria, state precise conditions for re-qualification, skip detailed Action Plan.

### Short-Circuit to AVOID

TT 0-3/8 PASS or Stage 3/4: Short-circuit to AVOID verdict immediately. Do not proceed to Steps 5-7. Output:

1. Top 3 disqualifying reasons with specific data points
2. Conditions for future re-entry (what must change for the stock to re-qualify)
3. Alternative action (redeploy capital to Stage 2 candidates)

This rule prevents wasted analytical effort on stocks that clearly fail SEPA criteria and avoids the disposition effect of searching for reasons to justify a failing stock.

---

## Earnings Event Protocol

### Activation Trigger

Activate this protocol when a stock's earnings report is within 5 trading days. For Type E (Position Management) queries involving earnings proximity, follow this 5-step workflow before issuing any hold/sell recommendation.

### Step 1: Sell Signal Audit

Review these 6 sell signal categories against the current position. Count how many are triggered:

1. Stage transition: Is the stock showing Stage 2 to Stage 3 transition signals (volatility expansion, MA flattening, distribution volume)?
2. Trend Template violation: Has the stock failed 2+ of the 8 Trend Template criteria?
3. RS deterioration: Has RS declined below 70 or dropped more than 15 points from its peak?
4. Stop-loss proximity: Is the current price within 3% of the initial stop-loss level?
5. Base failure: Has the stock failed to hold a VCP pivot or broken below the base low?
6. Earnings deceleration: Are EPS or revenue growth rates decelerating for 2+ consecutive quarters?

### Step 2: Options Implied Move Check (Optional)

If options data is available, check the implied move for the upcoming earnings:
- Compare historical average earnings move vs current implied move
- If implied move is unusually high (>1.5x historical average), the risk is elevated
- This step is advisory only -- do not block decisions on options data availability

### Step 3: Scenario Probability Matrix

Build a 3-scenario probability assessment for the upcoming earnings:

- **Beat scenario**: EPS and revenue beat estimates. Stock gaps up. What is the probable price action given current base count, RS, and institutional positioning?
- **In-line scenario**: Results meet expectations. No significant gap. Does the stock have enough technical strength to hold current levels?
- **Miss scenario**: EPS or revenue miss. Stock gaps down. How far below the stop-loss could price reach? What is the maximum dollar risk?

Assign rough probability weights (e.g., 50%/30%/20%) based on earnings surprise history (cockroach effect), analyst revision trends, and sector momentum.

### Step 4: Disposition Effect Alert

If 3 or more sell signals from Step 1 are triggered, issue an explicit warning:

"Warning: 3+ sell signals detected prior to earnings. Holding through earnings with multiple sell signals active is a high-risk disposition effect pattern. The instinct to hold and hope for a recovery is the direct opposite of what successful risk management requires."

### Step 5: 3-Option Framework

Present exactly 3 options based on the analysis above:

1. **Full sell before earnings**: Appropriate when 3+ sell signals triggered, stage transition underway, or mathematical expectation is negative
2. **Sell half before earnings**: Appropriate when 1-2 sell signals, strong earnings history (cockroach effect moderate+), but position shows technical weakness
3. **Hold full position with absolute stop**: Appropriate only when 0 sell signals, Stage 2 confirmed, RS >80, positive earnings acceleration. Must set absolute stop at the miss scenario worst-case level

Never present "hold and see" without a predetermined stop level. Every option must include a specific dollar risk calculation.

---

## Extension Risk: 200MA Distance

When a stock trades more than 100% above its 200-day moving average (price > 2x 200MA), mean reversion pressure is significantly elevated. While strong superperformers can sustain 60-100% extension during their advances, exceeding 2x the 200MA represents extreme extension territory.

At this level:
- Normal pullbacks become mathematically larger in absolute terms (a "healthy" 10% pullback from $12.48 brings price to $11.23, still far above 200MA at $6.30)
- The gap between price and 200MA itself signals that either (a) the 200MA needs time to catch up, or (b) the advance is unsustainable
- Corrections within bases at this extension level tend to be deeper (LPTH example: 35-55% corrections vs constructive 20-35%)

This is not a disqualifier (soft gate, not hard gate), but it increases the risk profile and should be factored into position sizing and stop-loss tightness.

### Graduated Extension Levels

- 60-80% above 200MA: Normal for strong Stage 2 advances. No adjustment needed.
- 80-100% above 200MA (Elevated): Mean reversion pressure building. Not a penalty trigger, but note in analysis and consider tighter stops or smaller position sizing for new entries.
- >100% above 200MA (Extreme): Soft gate penalty applies (-3 to composite score). Even healthy pullbacks create large absolute price drops at this extension level.

---

## Market Environment Adjustments

### Strong Bull Market (Broad market uptrend)

- Stop-loss: 7-8%
- Risk per trade: 0.75-1.0%
- Maximum position count: 6-8
- Pyramid aggressively on winning positions

### Normal Market

- Stop-loss: 6-7%
- Risk per trade: 0.5%
- Maximum position count: 4-6
- Standard pyramid (2%+2%+1%) -- use position_sizing.py pyramid subcommand for exact calculations

### Weak/Uncertain Market

- Stop-loss: 5-6% (tighter to protect capital)
- Risk per trade: 0.25-0.5% (smaller bets)
- Maximum position count: 2-4
- Reduce or eliminate pyramiding
- Raise cash levels to 50-75%

### Bear Market

- Stop-loss: 3-5% (very tight)
- Risk per trade: 0.25% maximum
- Maximum position count: 0-2
- No pyramiding
- Cash levels: 75-100%
- Only trade exceptional setups

---

## Trailing Stop Options

After moving stop to breakeven:
- Trail the stop below the 10-day MA for momentum trades
- Trail the stop below the 21-day EMA for swing trades
- Trail the stop below the 50-day MA for position trades
- Never move the stop backward (only forward)

---

## Always Wait for the Stock to Pivot

If the pivot point is tight, there is no material advantage in getting in early. Let the stock break above the pivot and prove itself. The pivot is the final determinant before capital commitment -- it is the point where supply has been absorbed and demand is ready to drive price higher.

Buying before the pivot introduces unnecessary risk: the stock may still fail to break out, the base may need more time, or additional shakeouts may occur. The pivot breakout on above-average volume is the confirmation that the setup is working as expected.

Exception: Low Cheat and 3C entries provide earlier systematic entry points with defined risk. These are not "anticipating the pivot" -- they are alternative entry techniques within the base formation that have their own trigger criteria and stop-loss rules. The advantage of these earlier entries is a lower entry price (and thus smaller risk per share), but they require the same discipline in stop placement and volume confirmation.

---

## Early Day Reversal Handling

On a breakout day, the stock may gap up or rally strongly in the first hour, then reverse and give back gains before noon or 1pm. This intraday reversal can trigger panic selling, but the correct approach is patience:

- If the stock reverses before noon/1pm on breakout day, wait until end of day before making any sell decision
- The stock may undercut the purchase price intraday -- this alone is not a sell signal
- Stick to the predetermined game plan: only sell if the reversal triggers the protective stop-loss
- In healthy markets, stocks that reverse early in the session often recover later in the day
- Do not make impulsive decisions based on the first 2-3 hours of trading

The only sell trigger during an early day reversal is the actual stop-loss level being hit. Intraday noise above the stop level is normal breakout behavior and should be expected, not feared.

---

## Squat and Reversal Recovery Rules

A squat occurs when a breakout closes significantly below the day's high (more than 3% off the high), indicating selling into the breakout strength. While a squat is a caution signal, it is not an automatic sell signal.

Recovery accommodation rules:

- Wait 1-2 days for recovery in normal market conditions, up to 10 days in a strong bull market
- If price closes below the 20-day MA during the squat period, probability is lowered -- this is a judgment call requiring evaluation of the broader setup context
- If price tightens and volume subsides after the squat, the setup may actually be improving (the entry was slightly early, and the stock is building a tighter base)
- If the protective stop-loss is hit during the squat period, exit and reevaluate -- the squat has become a failed breakout

Squat recovery quality assessment:

- **Strong**: Price recovers above breakout day high within 3 trading days
- **Normal**: Recovery takes 4-10 trading days
- **Extended**: Recovery takes more than 10 days (lower probability of success)
- **Failed**: Stop-loss hit or no recovery within the accommodation window

---

## Portfolio Correlation Awareness

- Stocks in the same sector tend to move together
- High correlation = less diversification benefit
- If holding 2 semiconductor stocks, treat them as increased single-sector exposure
- Sector concentration: No more than 2-3 stocks in the same sector
- Adjust total sector exposure accordingly

---

## Disposition Effect Awareness

The psychological tendency to sell winners too soon and hold losers too long. Traders feel the pain of loss approximately 2x more intensely than the pleasure of an equivalent gain (prospect theory). This leads to cutting winners short and holding losers -- the direct opposite of what successful trading requires. Overcoming it requires systematic rules, not willpower.

### Involuntary Investor

A trader who refuses to sell a losing position becomes an "involuntary investor" -- they did not intend to be a long-term holder but are unable to accept the loss. Their capital is locked up, unable to be deployed to better opportunities.

### Disposition Effect Check Protocol

Execute this protocol for every Type E (Position Management) query:

1. Run Sell Signal Audit (6 categories from Earnings Event Protocol Step 1)
2. Count triggered sell signals
3. If 3+ signals triggered: Output explicit warning — "Warning: 3+ sell signals detected. Holding this position is a disposition effect pattern. The instinct to hold and hope is the opposite of what successful risk management requires."
4. If user asks "물타기" (averaging down): Immediate firm rejection. Reference the Geometric Loss Impact Table. "Never average down — a 50% loss requires a 100% gain just to break even."
5. If user's language suggests reluctance to sell at a loss ("조금만 더 기다리면", "다시 올라갈 거야"): Flag as potential "Involuntary Investor" pattern and explain the concept.

This protocol overrides any temptation to present a hopeful narrative. The system is designed to be profitable at a 40-50% win rate — accepting losses is part of the design, not a failure.

---

## Scaling Down in Losing Streaks

### Difficult Market Adjustments

- Tighten stops: from 7-8% to 5-6%
- Take smaller profits: from 15-20% to 10-12%
- Reduce position size
- Reduce number of positions
- Increase cash allocation
- When the market is not cooperating, the goal is preservation, not accumulation

---

## Low Cheat Risk Advantage

The low cheat entry technique reduces mathematical risk compared to a standard pivot breakout. By entering during a tight consolidation zone just below the pivot, the trader achieves a lower entry price while using the same stop-loss level (below the consolidation zone low). The result: a smaller percentage distance between entry and stop, which means lower risk per share.

Example: If the pivot is at $100 and the stop is at $95, a pivot entry has 5% risk. A low cheat entry at $97 with the same stop has only 3.1% risk -- a 38% risk reduction. This improvement in risk/reward is purely mathematical and requires no additional conviction or market conditions.

Low cheat entries are most effective when combined with volume dryup confirmation (tight zone average volume well below 50-day average) and when the consolidation occurs in the upper portion of the base formation.

---

## Pocket Pivot as Systematic Reentry Signal

After being stopped out of a position, the pocket pivot provides a systematic, rules-based reentry signal. Rather than relying on subjective judgment about when to re-enter, look for a pocket pivot within the base formation: an up-day where volume exceeds the maximum down-day volume in the prior 10 sessions.

Key reentry criteria using pocket pivots:

- The stock must still be in Stage 2 (200-day MA rising, price above it)
- The pocket pivot must occur above the 50-day moving average
- The stock should not be extended more than 10% above its 10-day MA
- Volume ratio (PP volume / max down volume) should be at least 1.5x, ideally 2x+
- Close position within the day's range should be in the upper 50%

This transforms the reentry decision from emotional ("I think it's ready") to mechanical ("the pocket pivot criteria are met"). Combined with a predetermined stop-loss, it maintains the systematic discipline that SEPA requires.
