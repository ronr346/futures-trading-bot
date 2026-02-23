# Elder Santis Complete Trading Methodology
## Comprehensive Study from @tradingelder YouTube Channel

> **Purpose:** Complete extraction of Elder Santis's trading methodology for building an autonomous futures trading bot.
> **Sources:** Full transcripts from key strategy videos + channel analysis + product descriptions + community content.
> **Instruments:** ES (E-mini S&P 500) and NQ (E-mini Nasdaq 100) futures.

---

## Table of Contents
1. [Core Philosophy & System Overview](#1-core-philosophy--system-overview)
2. [Supply & Demand Zone Rules](#2-supply--demand-zone-rules)
3. [Volume Analysis (Volume by Price)](#3-volume-analysis-volume-by-price)
4. [Order Flow & Tape Reading](#4-order-flow--tape-reading)
5. [Market Structure & Trend](#5-market-structure--trend)
6. [The A+ Setup (Full Checklist)](#6-the-a-setup-full-checklist)
7. [Entry Triggers](#7-entry-triggers)
8. [Stop Loss Placement](#8-stop-loss-placement)
9. [Take Profit / Targets](#9-take-profit--targets)
10. [Zone Invalidation Rules](#10-zone-invalidation-rules)
11. [VWAP Usage](#11-vwap-usage)
12. [Liquidity Concepts](#12-liquidity-concepts)
13. [Footprint Chart Analysis](#13-footprint-chart-analysis)
14. [Bookmap / Heatmap Analysis](#14-bookmap--heatmap-analysis)
15. [Imbalances (Continuation & Reversal)](#15-imbalances-continuation--reversal)
16. [Absorption & Exhaustion Detection](#16-absorption--exhaustion-detection)
17. [Risk Management Rules](#17-risk-management-rules)
18. [One & Done System](#18-one--done-system)
19. [Pre-Market Routine](#19-pre-market-routine)
20. [Trade Tracking & Journaling](#20-trade-tracking--journaling)
21. [Psychology & Discipline Rules](#21-psychology--discipline-rules)
22. [When NOT to Trade](#22-when-not-to-trade)
23. [Chart Configuration & Tools](#23-chart-configuration--tools)
24. [Bot Implementation Notes](#24-bot-implementation-notes)

---

## 1. Core Philosophy & System Overview

Elder's strategy is built on three pillars:
1. **Supply & Demand** — Where to look for trades (key levels)
2. **Volume by Price (Order Flow)** — Confirmation/confluence for direction
3. **Order Flow (Tape Reading)** — Entry trigger execution

**Why it works (Elder's reasoning):**
- "For supply and demand, for order flow, for volume to stop having an effect in the market, the market would basically have to disappear."
- The market is an **auction** — its main job is to **advertise price and facilitate trading**.
- Price moves because it needs **liquidity** — it needs to find orders to fill.
- "We don't predict the market. We react to what it does. We follow the trails."
- Understanding that **large capital moves the market** — the relationship between volume and price shows where institutional interest lies.

**The Three Fundamentals (in order):**
1. Strategy (mechanical, well-defined playbook)
2. Risk Management
3. Psychology/Mindset

> "Most people think their issue is psychology, but they don't even know if their mechanical strategy works."

---

## 2. Supply & Demand Zone Rules

### How to Draw Supply & Demand Zones

**Multi-Timeframe Process (Top-Down):**
1. Start on **4-hour chart** (best for intraday/scalp trades)
2. Work down to **2-hour**
3. Then **1-hour**
4. Finally refine on **30-minute** (the most important timeframe for zone validity)

**What to Look For:**
- **Massive moves up** or **massive moves down** from the market
- The **consolidation or neutral candle BEFORE the explosive move**
- Focus on levels **in or around current price** — don't draw levels far away

### Zone Drawing Rules — DEMAND Zones:
- **Bottom of zone** = Bottom WICK of the neutral/consolidation candle
- **Top of zone** = Top BODY of the neutral/consolidation candle

### Zone Drawing Rules — SUPPLY Zones:
- **Bottom of zone** = Bottom BODY of the neutral/consolidation candle
- **Top of zone** = Top WICK of the neutral/consolidation candle

### Candle Requirements:
- Look for **big body candles with small wicks** (massive body = strong institutional activity)
- OR **multiple medium/big body candles** in combination
- Must see **consolidation/neutral candle(s) BEFORE an explosive move**
- "If you see a level and you're uncertain if it's a level, it's probably not a level. Leave it alone."
- "If there's no neutral candle or consolidation before the move, don't draw the level."

### Refining Zones:
- As you go to smaller timeframes, zones will **shift, change, and move** — adjust them
- At each timeframe, try to get the **whole consolidation** and **whole wick** of the key candles
- On smaller timeframes, you'll discover **additional levels** that weren't visible on larger timeframes
- "These are levels where I've seen big money take action. Next time we get to that level, I want to pay heavy attention to the tape."

### What Makes a STRONG Zone:
- 4-hour levels are the strongest (don't get hit often, but very reliable)
- Zone has a **Volume Profile Point of Control (POC)** inside it
- Zone shows **imbalances** on the footprint chart (one-sided orders)
- Volume was present when the zone was created

---

## 3. Volume Analysis (Volume by Price)

### Volume Profile
- Each box on the chart = **one day session** (futures market open to close)
- **Yellow line = Point of Control (POC)** = price with the most volume transacted that day
- A new box forms when each new day opens

### How to Use Volume Profile:
1. **Confirm bias:** Volume POC and value area should be **moving in direction of your bias**
   - Bullish = POC moving higher day over day
   - First day where POC and value area are lower = potential reversal signal
2. **Strengthen S&D levels:** If a supply/demand level has a POC inside it = **much stronger level**
   - "Not only that, we see a volume point of control... this little level has had an insane amount of volume"
   - Trade these levels more aggressively (more size, expect bigger moves)
3. **Check daily interest:** More volume at the high of day vs low = bullish bias confirmed (and vice versa)

### Volume Bar Analysis:
- **Decreasing volume approaching a key level** = expect REVERSAL (bounce)
- **Increasing volume approaching a key level** = expect BREAK
- This is the primary method for determining break vs. bounce at S&D levels
- "Volume is showing me that we're going to break the level or not"

### Auction Theory:
- If price moves up and volume dries off at the top = nobody interested in higher prices → market must reverse down
- If price moves down and volume dries off at bottom = nobody interested in lower prices → market must reverse up
- Like an iPhone store analogy: if nobody buys at $1,500, seller must lower price to attract buyers

---

## 4. Order Flow & Tape Reading

### What Order Flow Shows You:
- **Aggressive buying pressure** vs **aggressive selling pressure** in real time
- **Resting liquidity** (where passive orders sit)
- **Exhaustion** (buyers/sellers dying out)
- **Absorption** (passive orders absorbing aggressive orders)
- Where to **take profit** (resting orders at a level)
- Where to **place stop loss** (resting stop losses — put yours beneath them)

### Bid vs. Ask:
- **Bid** = buyer's limit orders (highest price buyers willing to pay)
  - Seller hitting the bid = aggressive sell
- **Ask** = seller's limit orders (lowest price sellers willing to accept)
  - Buyer hitting the ask = aggressive buy

### Order Types:
- **Limit orders** = passive, waiting at a set price, PROVIDE liquidity
- **Market orders** = aggressive, execute instantly, REMOVE liquidity
- **Price moves when aggressive traders consume available liquidity**

### Key Principle:
- "Focus only around key levels. Don't drive yourself crazy by watching order flow at random locations."
- Watch order flow at: **VWAP, highs/lows, liquidity, prior day levels, supply and demand zones**

---

## 5. Market Structure & Trend

### Trend Determination:
- **4-hour chart** for overall trend/sentiment/bias
- Bullish = series of Higher Highs (HH) and Higher Lows (HL)
- Bearish = series of Lower Lows (LL) and Lower Highs (LH)
- **Always trade WITH the trend** — "The average time following a trend is much greater than breaking it"

### Structure Shift on 5-Minute (Entry Timeframe):
- At a **demand zone** (looking long): Wait for price to stop making LL/LH and form a **HH and HL**
  - Need BOTH: a higher high AND a higher low
  - "If we made a lower low but didn't have the lower high, we keep waiting"
- At a **supply zone** (looking short): Wait for price to stop making HH/HL and form a **LL and LH**
  - Need BOTH: a lower low AND a lower high

### 30-Minute Structure:
- If 4H is bullish and 30M shows a downtrend into demand = great long opportunity
- If 4H is bullish and 30M is also bullish breaking supply = also great

---

## 6. The A+ Setup (Full Checklist)

This is Elder's highest-conviction setup where he uses **maximum position size**. ALL checkboxes must align:

### Checklist:
- [ ] **1. Overall Trend/Sentiment (4H):** Must be trading WITH the 4H trend
- [ ] **2. Volume Analysis:** Volume picking up at higher prices (bullish) or lower prices (bearish) — not dying out
- [ ] **3. Volume Profile POC:** Moving in direction of bias (higher POC = bullish, lower POC = bearish)
- [ ] **4. Supply & Demand Level:** 4H level is strongest; 30M is minimum. Playing bounces off S/D OR breaks of S/D
- [ ] **5. No Red Folder News:** Check Forex Factory. No Trump speaking, no war, no crazy volatile events
- [ ] **6. 5-Minute Structure Shift:** Wait for structure to shift in your direction (HH/HL for longs, LL/LH for shorts)
  - Exception: If playing a break-retest, structure is already on your side after the break
- [ ] **7. Order Flow Entry Trigger:** Tape reading confirms (absorption, exhaustion, delta shift, passive order holding)

### Break-Retest Variant:
- Supply/demand level breaks → price retests the broken level
- On retest: look for **dead volume** (volume dying out on the pullback)
- Footprint shows: most volume was on the breakout side, weak volume on the retest
- Entry on the retest candle with stop loss beyond the broken level

### Sizing Rules:
- All stars align = **full size** (not full port — full normal size)
- Fewer confluences = reduced size
- "If what I just told you, everything looks perfect, you drop full size on that bitch"

---

## 7. Entry Triggers

Elder uses order flow / tape reading as his PRIMARY entry trigger. Entries always on the **5-minute timeframe**.

### Entry Trigger 1: Structure Shift at S&D Level
1. Price reaches supply/demand zone
2. Wait for 5M structure to shift (HH/HL for longs at demand; LL/LH for shorts at supply)
3. Enter on the shift confirmation
4. Stop loss below the new HL (for longs) or above the new LH (for shorts)

### Entry Trigger 2: Absorption + Exhaustion at Key Level
1. At supply: See aggressive buyers hitting passive sellers → market doesn't move up → **absorption confirmed**
2. See buyers getting smaller and smaller (exhaustion)
3. On the retest of the same level, see the same pattern repeat
4. Enter short after second confirmation of absorption

### Entry Trigger 3: Passive Order Confirmation
1. See passive sellers above price on Bookmap
2. See aggressive buying fail to break through → absorbed
3. Aggressive seller steps up → new low is made
4. On retest: see buyer exhaustion into the same passive sellers
5. Enter on the retest

### Entry Trigger 4: Footprint Imbalance Retest
1. Price creates a continuation imbalance (diagonal divergence in volume)
2. Wait for price to retrace back to the imbalance level
3. Enter at the imbalance with stop loss below/above it
4. If you get a reversal imbalance AT a continuation imbalance = premium trigger

### Entry Trigger 5: Three Consolidation Candles (Footprint)
1. Three 5M candles with approximately equal highs (at supply) or lows (at demand)
2. Footprint shows massive positive delta on all three = aggressive buying
3. But price doesn't make a new high = passive sellers in control (absorption)
4. Next candle shows negative delta and holds a new low
5. Enter immediately — "I'm in right away, bro"

### Entry Trigger 6: Volume Death at Key Level
1. Price approaches demand zone
2. Footprint shows the wick into demand has **no volume** (nobody selling down there)
3. Price retraces up, comes back to the same level — again no volume on the wick
4. Enter long with stop loss below the level

### Entry Trigger 7: Break-Retest with Tape Confirmation
1. Price breaks above supply (or below demand)
2. Volume was increasing on the break (confirmation)
3. Price retests the broken level with **decreasing volume**
4. On the footprint: most volume (POC) is on the breakout side, weak volume on the retest
5. Enter on the retest

---

## 8. Stop Loss Placement

- "I look for levels where my thesis for the trade is invalid"
- Place stop loss where **structure would shift against you**
- For longs: Stop below the new **Higher Low** that confirmed your entry
- For shorts: Stop above the new **Lower High** that confirmed your entry
- For break-retest: Stop beyond the broken level (above broken supply for longs)
- When using Bookmap: Place stop **behind passive orders** that are working in your favor
  - "I'm putting my stop-loss right above those sellers. I'm fucking with them. They're strong as fuck."
- When using imbalances: Stop beyond the imbalance level
- For resting stop losses visible on the tape: **put your stop BENEATH theirs** to avoid stop hunts

---

## 9. Take Profit / Targets

- **Primary target: VWAP** — frequently used as the first take-profit level
- **Secondary targets:** Any resting liquidity visible on Bookmap
- **Third target:** Prior day levels, session highs/lows
- Anywhere price could potentially reverse — look for **passive orders** on the other side
- Long-time-frame liquidity on Bookmap acts as a **magnet** — great take-profit level
- "I target any resting liquidity in the market, anywhere I can see price potentially reverse on me"

---

## 10. Zone Invalidation Rules

**Critical rule — 30-minute timeframe ONLY:**
- If a candle **CLOSES above a supply zone** on the 30M timeframe → zone is **INVALIDATED**
- If a candle **CLOSES below a demand zone** on the 30M timeframe → zone is **INVALIDATED**
- Once invalidated, **never trade that level again**
- "It has to be the 30-minute. If you close above or below a key level, above or below a zone, it's then invalid for me."

---

## 11. VWAP Usage

- VWAP is a **take-profit target** (primary target for most trades)
- VWAP is also a **key level** for order flow analysis (watch volume at VWAP)
- Used in confluence with other levels — not as a standalone entry signal
- Part of the "key levels" where you should focus order flow analysis:
  - VWAP, highs/lows, liquidity zones, prior day levels, supply/demand

---

## 12. Liquidity Concepts

### What is Liquidity:
- **Two sides to every transaction** — for a whale to buy $1B, someone must sell $1B
- Market moves to **find liquidity** (orders to fill positions)
- Stop losses are liquidity — price often runs stops before reversing

### How to See Real Liquidity:
- **Bookmap** shows actual resting orders (not guessing with lines)
- Dark red/orange lines = resting limit orders
- Below price = resting buy orders; Above price = resting sell orders
- "So many people get liquidity wrong — they think if they draw a line at session low/high, it's liquidity. You can see liquidity on the tape."

### Liquidity Sweeps/Grabs:
- Price sweeps a liquidity level (e.g., overnight lows, Asian session lows)
- Then reverses — classic "sweep and reverse" pattern
- Example: "Swept overnight liquidity into the London open, then reversed"
- Elder uses swept liquidity as a confirmation for entry direction

### Liquidity Pulls:
- Resting orders get pulled from the book suddenly
- If liquidity disappears below → market may drop (nothing stopping sellers)
- If liquidity disappears above → market may rip up (nothing stopping buyers)
- "You will see liquidity being pulled all the time — we actually took an entry today on liquidity being pulled"
- Algos front-run liquidity pulls frequently

### Long-Timeframe Liquidity:
- Orders that have been sitting on Bookmap for **days/hours** are more likely to get filled (not spoofed)
- Acts as a **magnet** — price tends to gravitate toward these levels
- Great take-profit target
- Often aligns with psychology levels (50s, 55s, 100s, round numbers)

---

## 13. Footprint Chart Analysis

### What the Footprint Chart Shows:
- **Every candle broken down by volume** at each price level
- Each cell: **Bid volume x Ask volume** (sellers on one side, buyers on the other)
- Green = buying pressure, Red = selling pressure
- **Blue histogram** = total volume of that candle
- **D = Delta** = difference between aggressive buyers and aggressive sellers
  - Positive delta = more aggressive buyers
  - Negative delta = more aggressive sellers
- **Yellow bar = Point of Control** = price level with most volume within that candle

### How to Read Footprint Charts:
1. **Volume dying out** at top of candle = no interest in higher prices → reversal signal
2. **Volume dying out** at bottom of candle = no interest in lower prices → reversal signal
3. **Absorption visible** = aggressive sellers with big volume but price doesn't drop → passive buyers absorbing
4. **Delta divergence** = price making new highs with decreasing delta → exhaustion
5. **Imbalances** = diagonal divergences showing abnormal one-sided activity

### Footprint vs. Bookmap:
- Footprint: Cannot see level 2 (resting liquidity)
- Footprint: Better for analysis (cleaner, prettier)
- Bookmap: Shows resting liquidity but cluttered
- Bookmap: Better for execution in real-time
- **Use both together** — Bookmap for liquidity, footprint for aggression analysis

---

## 14. Bookmap / Heatmap Analysis

### Reading the Heatmap:
- Orange/dark red lines = **resting limit orders** (liquidity)
- Above price = **passive sell orders**
- Below price = **passive buy orders**
- Darker/more red = more orders at that level
- These represent **institutional/bank/hedge fund/government** money — retail can't make a visible line

### Green/Red Bubbles:
- **Green bubbles** = aggressive buy orders (hitting the ask) — completed trades
- **Red bubbles** = aggressive sell orders (hitting the bid) — completed trades
- Bigger bubble = more volume

### Key Patterns to Watch:
1. **Absorption:** Aggressive orders hit passive wall but can't break through → wall holds
2. **Liquidity Pull:** Passive orders suddenly disappear → breakout potential
3. **Iceberg Orders:** Large institutional orders broken into small pieces to hide intent
4. **Front-Running:** Algos detect large orders and trade ahead of them

### For a level to break:
- The aggressive orders must be **equal to or greater than** the passive resting orders
- Example: "For this wave of 585 to get cleared out, it must be met by aggressive market orders of 585 hitting the ask"

---

## 15. Imbalances (Continuation & Reversal)

### Continuation Imbalances:
- **Red candle + Red imbalance** = sellers dominating → price likely continues DOWN
- **Green candle + Green imbalance** = buyers dominating → price likely continues UP
- Accompanied by strong delta and volume confirmation
- **How to trade:** Wait for price to retrace back to the imbalance level → enter in direction of the original move
- Stop loss below/above the imbalance
- "If you wait for the imbalance retest, your win rate is gonna be significantly higher"

### Reversal Imbalances:
- Appear at the **extreme ends** of a candle, signaling exhaustion
- **Top of green candle + Green imbalance at the very top + no ticks above** = bearish reversal signal
- **Bottom of red candle + Red imbalance at the very bottom + no ticks below** = bullish reversal signal
- Usually accompanied by dead/declining volume and lack of follow-through
- **Used as an entry trigger for reversals**

### Combining Both:
- Continuation imbalance forms → price retests it → reversal imbalance appears at the retest
- This is a **premium entry trigger** — both imbalance types confirming the same direction

### What Creates an Imbalance:
- A **diagonal divergence in price** showing abnormal activity
- Not horizontal, not vertical — diagonal
- One side massively outweighs the other (e.g., 400 vs 28, 1.5K vs 200)

---

## 16. Absorption & Exhaustion Detection

### Absorption:
- **Definition:** Passive orders absorbing all aggressive orders without price moving
- **How to detect without Bookmap:**
  - On footprint: See massive selling volume on the left side, but price doesn't drop
  - Delta may be negative, but candle body doesn't move down
  - "There's a lot of aggressive sellers hitting these passive buy offers, yet price doesn't move down"
  - Buy imbalance appears → market shoots up
- **On Bookmap:** See green bubbles (aggressive buys) hitting a level but not breaking through the passive sell wall

### Exhaustion:
- **Definition:** Volume dying out at extreme prices — nobody interested in transacting there
- **How to detect:**
  - Footprint: Top of candle has almost no volume
  - Bar chart: Volume getting smaller and smaller on consecutive candles
  - Delta getting weaker
  - Buyers/sellers getting smaller approaching a key level
- **Signal:** If volume exhausted at highs → reversal down; if exhausted at lows → reversal up

### For Bot Implementation (Without Bookmap):
1. **Volume declining** as price approaches a key S&D level → expect bounce
2. **Volume increasing** as price approaches a key S&D level → expect break
3. **Delta divergence** — price making new highs but delta decreasing → sell signal
4. **Delta divergence** — price making new lows but delta increasing → buy signal
5. **Absorption pattern** — large negative delta candle that doesn't move price down at demand = strong buy signal

---

## 17. Risk Management Rules

### Position Sizing:
- **Risk 1-3% of account per trade** (maximum)
- Elder personally risks **less than 1%** (has a large account)
- 2% is "even a lot" — depends on account size
- Keep risk **consistent** — don't size up based on confidence or P&L growth
- Only size up after **months or years** of consistent data proving your edge

### Sizing by Setup Quality:
- A+ setup with all confluences → full normal size
- Setup at S&D level with volume POC → more aggressive, more size, expect bigger move
- Setup without volume confirmation → reduced size
- 70% win rate setup → more size; 50% win rate setup → less size, tighter R:R required

### Key Risk Rules:
- Never risk money you need for bills/food/rent
- Never full-port (risk entire account on one trade)
- "Good risk management means you can lose a day, a week, a month, and still survive"
- Goal is **capital preservation** — "making money is a byproduct of following your system"

### Cautionary Tale:
- Elder flipped $4K → $132K in less than a week by full-porting
- Lost ALL of it the next day by trying to do it again
- "I reinforced bad habits. I sized up based on P&L, not based on consistency."

---

## 18. One & Done System

### Core Concept:
- **One trade per day** — take one high-quality setup and be done
- Typically done trading by 9:35-10:00 AM ET
- "Why sit in front of your screen for 10 hours? That defeats the purpose of trading."

### Philosophy:
- Trade less, win more
- Quality over quantity
- Fewer trades = easier tracking, easier psychology
- "If you take one and done, you're not tracking much — tracking one trade a day"

### When to NOT Trade:
- If the A+ setup doesn't appear by lunchtime → no trade
- "If I don't see my setup, I don't trade"
- Some weeks Elder barely takes any trades because the market doesn't give opportunity

---

## 19. Pre-Market Routine

Elder's daily pre-market process (wake up ~1 hour before market open):

1. **Check Forex Factory** for red folder news events
   - If red folder news: avoid holding positions into it
2. **Determine the macro trend** (4H chart)
   - Overall sentiment: bullish, bearish, consolidating
3. **Mark key levels** — Supply & Demand zones
   - Top-down: 4H → 2H → 1H → 30M
4. **Add Volume Profile** to confirm bias
   - POC direction, value area direction
5. **Draw pre-market scenarios** — EVERY possible scenario
   - "If price gets to X supply zone, bearish trend, I'm looking for structure shift with this entry trigger, stop loss here, take profit here"
   - "If this doesn't happen by lunchtime, I won't take a trade"
6. **Check for overnight events** (wars, Trump, major news)
   - If major overnight moves → may skip the day entirely

> "Every single day before the market opens, I draft out every single scenario. So I know: when this happens, I do this. When this happens, I do that."

---

## 20. Trade Tracking & Journaling

### What to Track (Elder's Complete Journal Template):

**Pre-Trade Analysis:**
- Sentiment: Bias, Trend Direction, Strength
- Volume Profile analysis
- Macro factors
- 5-minute sentiment, bias, micro trend
- Order flow observations
- Market internals
- Liquidity pockets identified

**Key Levels:**
- Supply/Demand zones marked
- VWAP
- High/Low of day
- Liquidity zones

**Trade Plan:**
- Intended entry level
- Entry trigger to use
- Stop placement
- Intended exit / target
- Plan for multiple scenarios

**Execution:**
- Actual entry
- Actual exit
- Final R-multiple
- Slippage
- Execution notes

**Psychology:**
- Before entry: Confidence level, hesitation, excitement, fear
- During trade: Patience, doubt, over-confidence, second-guessing
- After exit: Relief, frustration, satisfaction, lesson learned

**Review:**
- Did I follow my plan?
- Mistakes made
- Lessons for tomorrow
- Overall performance score (graded)

### Tracking Tips:
- Track **immediately after the session** while it's fresh
- If can't track immediately: **record your screen + face** → review later
- Track EVERY trade including bad days and tilt trades
- Tag every data point for filtering (e.g., market condition, setup type)
- Use TradeZilla or similar tools for filtering
- Track **intended exit** not just actual exit — a "win" with less profit than risked = negative R = not a real win

### Critical Metric: Intended vs. Actual R:R
- If you risked $500 to make $1000 but took partials and only made $400 → **negative R-multiple trade**
- "That's not a win. You made money, but that's not a win."

---

## 21. Psychology & Discipline Rules

### Core Mindset Rules:
1. **Remove money from the equation** — focus on the process, not P&L
2. **Base success on consistency**, not on dollar amount
3. **Don't compare yourself** to other traders on social media
4. **Meditate before market open** — "helped me more than I can put into words"
   - Be comfortable with silence, with doing nothing, with not trading
5. **Expect to fail** — pain is part of the learning process
6. **Have accountability** — trade with a friend or community, someone who knows when you mess up

### Discipline Rules:
- If you're nervous or hyped in a trade → you're risking too much money → downsize
- If setup doesn't appear → DO NOT TRADE
- Never revenge trade
- After a major overnight move → Elder skips the day entirely
- Keep risk consistent — don't size up after a win streak

### Character Traits of Elder's Most Successful Students:
1. Financially stable (not depending on trading income)
2. Extremely disciplined in all areas of life
3. Practice meditation
4. Consistent in gym/health routines
5. Show up and put in the work daily

---

## 22. When NOT to Trade

Elder explicitly avoids trading when:
- **Red folder news** on Forex Factory (during the event)
- **Trump speaking** or making announcements
- **War/geopolitical events** (e.g., Iran-Israel tensions)
- **Major overnight moves** → "I knew I wasn't gonna trade Friday because of what happened overnight"
- **Market structure is unclear** or shifting
- **Setup doesn't meet A+ criteria** by lunchtime
- **After going on tilt** — track it, don't continue trading
- **Choppy, consolidating markets** without clear S&D levels
- Volume is dead/abnormally low across the board

---

## 23. Chart Configuration & Tools

### Platforms/Tools:
- **Charting Platform:** Not explicitly named (uses footprint charts + volume profile)
- **Bookmap** (bookmap.com) for Level 2 / heatmap / resting liquidity
- **Footprint Charts** for volume analysis per candle
- **Volume Profile** (daily session boxes with POC)
- **Forex Factory** for economic calendar (red folder news)
- **TradeZilla** (or similar) for trade journaling with tags
- **Elder's Indicator Bundle** ($75/mo on Whop) — auto-plots S&D levels, delta spikes, daily POC, absorption alerts

### Timeframes Used:
| Timeframe | Purpose |
|-----------|---------|
| 4-Hour | Overall trend/sentiment, highest-quality S&D levels |
| 2-Hour | Secondary S&D refinement |
| 1-Hour | Additional S&D refinement |
| 30-Minute | Final S&D refinement, zone invalidation timeframe, volume profile |
| 5-Minute | Entry trigger timeframe, structure shift, order flow analysis |

### Chart Elements:
- Supply & Demand zones (drawn manually, top-down)
- Volume Profile (daily session, with POC and value area)
- Footprint chart (5M timeframe for execution)
- Bookmap heatmap (for live execution)
- VWAP (as target/key level)

### Indicators (from his product listing):
- **Key Level Indicator** — auto-plots supply, demand, and volume zones
- **Absorption Alerts** — real-time alerts when absorption detected
- **Delta Spikes** — shows abnormal buying/selling activity
- **Daily Volume POC** — highest volume price per day

---

## 24. Bot Implementation Notes

### Strategy Logic for Autonomous Bot:

**Phase 1: Pre-Market Setup (Before 9:30 AM ET)**
1. Determine 4H trend direction (HH/HL = bull, LL/LH = bear)
2. Draw S&D zones using the multi-timeframe approach (4H → 30M)
3. Calculate Volume Profile POC direction (rising = bullish, falling = bearish)
4. Check economic calendar for red folder news → if present, reduce risk or skip
5. Draft scenarios: which zones are closest to current price, expected direction

**Phase 2: Trade Identification (9:30 AM ET onwards)**
1. Wait for price to approach a key S&D zone
2. Check volume:
   - Declining into zone → expect bounce (trade with the zone)
   - Increasing into zone → expect break (trade the break-retest)
3. Check 5M structure:
   - For bounce longs at demand: wait for HH + HL
   - For bounce shorts at supply: wait for LL + LH
   - For break-retest: structure already in direction after break

**Phase 3: Entry Trigger**
1. Volume confirmation on footprint/candles:
   - Absorption: large selling volume but price doesn't drop (at demand)
   - Exhaustion: volume dying off at extreme of candle
   - Delta divergence: delta weakening while price pushes further
2. Enter on confirmation of structure + volume confluence

**Phase 4: Trade Management**
1. Stop loss: Below HL (longs) or above LH (shorts) that confirmed entry
2. Target 1: VWAP
3. Target 2: Next S&D zone or resting liquidity level
4. Risk: 1-3% of account per trade

**Phase 5: Exit**
1. Take profit at targets
2. If 30M candle closes through your S&D zone → exit (zone invalidated)
3. One trade per day → done after first trade (One & Done)

### Key Metrics to Monitor Without Bookmap:
Since a bot won't have Bookmap, replicate the concepts using:
1. **Volume analysis:** Compare volume bars approaching S&D levels (increasing vs. decreasing)
2. **Delta analysis:** Track cumulative delta and per-candle delta for absorption/exhaustion
3. **Footprint data (if available):** Bid/ask volume per price level per candle
4. **Volume Profile:** Daily session POC and value area direction
5. **Price-volume divergence:** Price making new highs/lows with declining volume = exhaustion

### Win Rate Expectations:
- Elder's strategies range from **50% to 70% win rate**
- 70% WR setups → more size, aggressive
- 50% WR setups → less size, need better R:R (at least 2:1)
- Long-term edge comes from consistent application + proper risk management

---

## Appendix: Video Sources

| Video ID | Title | Content Type |
|----------|-------|-------------|
| wNS45QL4hc0 | HOW TO DRAW SUPPLY AND DEMAND (CHEAT CODE) | S&D drawing rules, volume profile, zone invalidation, entry examples |
| 9QVzwLFm_Sc | ORDER FLOW EXPLAINED (GOD TOOL) | Order flow complete guide, bid/ask, bookmap, footprint, imbalances |
| Q5OYe0VS_t0 | 10 Years of Trading Knowledge in 20 Minutes | Strategy overview, S&D + volume + order flow philosophy, tracking |
| bu3-QG5nnSE | MOST OVERPOWERED DAY TRADING SETUP (2025) | A+ setup complete checklist, entry triggers with order flow |
| FFFUNV5NowI | 8 TRADING RULES I WISH I KNEW EARLIER | Playbook, backtesting, journaling, risk management, pre-market |
| ExcTGhcaotg | DECADE OF TRADING KNOWLEDGE IN 10 MINUTES | Mindset, risk management, strategy fundamentals |
| p7emxRPdLng | ONE and DONE (Episode One) | Podcast: prop firms, psychology, scaling, lifestyle |

*Additional sources: Elder's Whop products (free course, One & Done, Indicator Bundle), press releases, Reddit posts, community reviews.*

---

**Document compiled from comprehensive analysis of Elder Santis's @tradingelder YouTube channel.**
**Last updated: February 2026**
