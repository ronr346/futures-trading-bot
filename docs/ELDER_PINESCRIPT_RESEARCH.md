# Elder Santis (Trading Elder) — Full Strategy Research for PineScript Implementation

**Research Date:** 2026-02-23  
**Channel:** https://www.youtube.com/@tradingelder (also https://www.youtube.com/channel/UCcQoXUcwMQF-Pv9uq6etT9Q)  
**Website:** https://eldersantis.com (redirects to WordPress blog)  
**Whop Store:** https://whop.com/master-trader/  
**Instagram:** @tradingelder (183K followers)  
**Reddit:** u/Eldersantis, r/ElderSantis  
**Background:** ~9 years trading experience, former football player at Lassiter High School (Marietta, GA)

---

## ⚠️ IMPORTANT CAVEAT

Elder Santis keeps his **detailed methodology behind a paywall** (Master Trader mentorship ~$2K+, Indicator Bundle $75/mo, individual indicators $49.99/mo each). His free YouTube content and free Whop courses ("Stop Wasting Money on Trading Courses" + "One & Done" system) are **lead magnets** that give high-level concepts but deliberately withhold specific rules. The information below is reconstructed from:
- His Reddit posts (u/Eldersantis) 
- Whop product descriptions and reviews
- Community discussions about his strategy
- General S&D + order flow methodology that aligns with his described approach
- Reviews from his mentorship students

---

## 1. CORE STRATEGY OVERVIEW

From his own Reddit post (u/Eldersantis):
> "Here's how I approach the market:
> - **Key levels:** I use supply and demand zones to identify areas of interest.
> - **Bias:** I rely on volume by price and sentiment to gauge overall direction.
> - **Confirmation:** Order flow helps me confirm my thesis before entering."

From eldersantis.com:
> His strategy combines:
> - **Supply and demand zones** to identify where large buyers and sellers are active
> - **Order-flow analysis** to confirm real-time buying and selling pressure
> - **Volume-by-price tools** to spot liquidity imbalances

**Instruments:** Primarily NQ (Nasdaq) and ES (S&P 500) futures  
**Style:** Intraday scalping / day trading  
**Platform:** Uses Bookmap for order flow + TradingView for charting  

---

## 2. SUPPLY & DEMAND ZONE METHODOLOGY

### How He Likely Draws S&D Zones (Reconstructed)

Elder uses a **classic institutional S&D approach** combined with volume confirmation. Based on community feedback and his product descriptions:

#### Zone Formation Patterns:
1. **Rally-Base-Drop (RBD)** → Supply Zone (the base is the zone)
2. **Drop-Base-Rally (DBR)** → Demand Zone (the base is the zone)
3. **Rally-Base-Rally (RBR)** → Continuation Demand Zone
4. **Drop-Base-Drop (DBD)** → Continuation Supply Zone

#### Zone Construction Rules (Best Approximation):
- **Base identification:** 1-5 candles of consolidation (small-bodied candles, dojis, or inside bars) between an impulsive move away and an impulsive move toward
- **Zone boundaries:** 
  - Top of zone = highest wick in the base area
  - Bottom of zone = lowest body (or wick) in the base area
  - Some traders use the open of the last candle before the explosive move
- **Valid zone requirements:**
  - Strong departure move (explosive candle leaving the base)
  - Fresh/untested (price hasn't returned to the zone yet)
  - Created significant displacement (large candle bodies)

#### Zone Invalidation:
- Zone is **invalidated when price closes through it** (not just wicks into it)
- A wick into the zone that reverses = zone is being respected (still valid)
- Multiple tests weaken the zone (first touch is highest probability)

#### Key Level Indicator (What It Likely Does):
From Whop: **"Key Supply, Demand & Volume Zones"** — $49.99/month
- Automatically draws S&D zones on the chart
- Incorporates **volume-by-price** (volume profile) to validate zones
- Likely highlights zones where high volume nodes (HVN) or low volume nodes (LVN) align with S&D structure
- A student review mentions: "Elders Daily Levels are precise" — suggests he provides **daily pre-market levels** (prior day high/low, key S&D zones from higher timeframes)

### PineScript Implementation Approach:
```
// Key concepts to code:
// 1. Detect consolidation (base) candles: small range relative to ATR
// 2. Detect explosive moves away from base: candle body > 1.5x ATR
// 3. Draw zone from base high to base low
// 4. Track if zone has been tested (price returned to it)
// 5. Invalidate zone on close through it
// 6. Overlay volume profile POC/VAH/VAL for confluence
```

---

## 3. STRUCTURE SHIFT RULES

Elder doesn't publish exact structure shift rules publicly. Based on his style (5-min chart futures scalping with S&D):

### Likely Approach:
- **Higher timeframe bias:** Uses 15m/30m/1H for overall direction (trend)
- **5-minute execution:** Looks for structure shifts on 5-min to time entries
- **Higher High / Higher Low (bullish):** 
  - Swing low holds above previous swing low
  - Price breaks above previous swing high
  - Minimum 2-3 candles to confirm a swing point
- **Lower High / Lower Low (bearish):** Mirror of above
- **Break of Structure (BOS):** When price breaks the most recent swing high (bullish) or swing low (bearish) — this confirms the shift
- **Change of Character (ChoCH):** First break against the prevailing trend direction

### For Entry:
1. Mark higher timeframe S&D zone
2. Wait for price to reach zone on 5-min
3. Look for structure shift (ChoCH) on 5-min within the zone
4. Enter on the first pullback after structure shift
5. Stop loss below the zone (demand) or above the zone (supply)

### PineScript Implementation:
```
// Use pivot highs/lows on 5-min
// Track swing sequence: HH, HL (bullish) or LH, LL (bearish)
// Detect BOS when price closes beyond last pivot
// Signal ChoCH when first counter-trend break occurs
// Combine with S&D zone proximity for high-probability signals
```

---

## 4. ABSORPTION DETECTION

### What Elder Uses:
Elder uses **Bookmap** for live order flow and absorption detection. His paid **"Absorption Alerts"** product ($49.99/mo) provides "Real-Time Absorption Alerts."

### What Absorption Means:
Absorption occurs when **aggressive market orders are being absorbed by passive limit orders** at a price level. This indicates:
- Large institutional players defending a level
- Price is likely to reverse or hold at that level
- Visible on Bookmap as: large resting orders that don't get depleted despite heavy hitting

### TradingView Approximation (Without Bookmap):

**YES, it can be approximated!** Several approaches:

#### A. CVD (Cumulative Volume Delta) Divergence
The best TradingView proxy. An open-source indicator already exists:
**"CVD Absorption + Confirmation [Orderflow & Volume]"** by ratipetya
(https://www.tradingview.com/script/LzJGJVHc/)

How it works:
- **Bearish absorption:** CVD makes a higher high, but price does NOT → sellers absorbing buyers
- **Bullish absorption:** CVD makes a lower low, but price does NOT → buyers absorbing sellers
- Confirmed by: engulfing candles, pin bars with high volume, CVD slope reversal

#### B. Volume Delta Analysis
- TradingView now has built-in **CVD Candles** indicator
- Compare per-bar delta (buy vol - sell vol) with price direction
- Divergence = absorption signal

#### C. Volume Spike at Support/Resistance
- Unusually high volume at a key level without significant price movement
- This implies absorption (orders being absorbed, not pushing through)

#### D. Footprint Chart Approximation
- TradingView doesn't have true footprint charts
- Use **volume delta per bar** + **volume profile** as proxy
- Look for bars with high volume but small range (absorption bars)

### Recommended TradingView Indicators for Absorption:
1. **CVD Absorption + Confirmation [Orderflow & Volume]** — ratipetya (open source)
2. **CVD - Cumulative Volume Delta (Chart)** — TradingView built-in
3. **CVD Zones & Divergence [Pro]** — kb1ath
4. **Adaptive Volume Delta Map** — dboichenko

### PineScript Absorption Logic:
```
// Core absorption detection:
// 1. Calculate per-bar volume delta (approximate via intrabar analysis)
// 2. Build cumulative delta
// 3. Compare CVD direction vs price direction
// 4. Divergence at S&D zone = absorption signal
// 
// Confirmation patterns:
// - Engulfing candle + low volume (easy reversal after absorption)
// - Pin bar + high volume (wick shows absorption)
// - CVD flattening / slope change
```

---

## 5. INDICATOR BUNDLE BREAKDOWN

### Products on Whop (Master Trader):

| Product | Price | Description |
|---------|-------|-------------|
| **FREE COURSE** | Free | "Stop Wasting Money on Trading Courses" — 54.7K members, basic concepts |
| **One & Done** | Free | "The One & Done Trading System" — one setup per day approach |
| **Key Level Indicator** | $49.99/mo (waitlist) | "Key Supply, Demand & Volume Zones" — auto-draws zones |
| **Absorption Alerts** | $49.99/mo (waitlist) | "Real-Time Absorption Alerts" — live absorption signals |
| **Elder's Indicator Bundle** | $75/mo | Both indicators combined: "Supply, Demand & Absorption Alerts" |
| **Mentorship** | ~$2,000+ | Group + 1-on-1 sessions |

### What the Key Level Indicator Likely Does:
1. **Auto-draws S&D zones** from higher timeframes
2. **Volume profile integration** — highlights zones where volume clusters align with S&D
3. **Daily levels** — prior day high/low, session open, key pivots
4. **VWAP levels** — session VWAP as dynamic support/resistance
5. **Zone freshness tracking** — marks tested vs untested zones

### What Absorption Alerts Likely Does:
1. **Real-time CVD divergence detection** at key levels
2. **Volume anomaly alerts** — unusual volume at S&D zones
3. **Possibly uses Bookmap API data** or approximates with exchange data
4. **Alert system** — push notifications when absorption detected at mapped zones

---

## 6. VWAP USAGE

Elder's approach to VWAP (based on his strategy description and community context):

### Session VWAP:
- **Primary tool** — uses daily session VWAP as dynamic mean
- Price above VWAP = bullish bias (look for demand zones)
- Price below VWAP = bearish bias (look for supply zones)

### VWAP as Confluence:
- S&D zone + VWAP alignment = highest probability trade
- Example: Demand zone sits right at VWAP → strong long setup
- VWAP acts as "value area" — institutions revert to VWAP

### Likely VWAP Configuration:
- **Session VWAP** (standard, resets daily) — PRIMARY
- **VWAP bands** (1σ, 2σ) — for extreme deviation plays
- **Anchored VWAP** — possibly from session open, prior day close, or significant swing points
- **Previous day VWAP close** — as a reference level

### PineScript:
```
// VWAP is built into TradingView (ta.vwap)
// For bands: calculate standard deviation of (price - vwap)
// Key levels: VWAP, VWAP+1σ, VWAP-1σ, VWAP+2σ, VWAP-2σ
// Anchored VWAP from user-defined points
```

---

## 7. LIQUIDITY SWEEP PATTERNS

### How Elder Likely Identifies Sweeps:

A liquidity sweep occurs when price **briefly breaks a key level** (taking out stop losses) then **immediately reverses** back inside the range.

#### Pattern Recognition:
1. **Equal highs/lows** form (liquidity pools) — many stops sitting above/below
2. Price **spikes through** the equal level
3. **Quick reversal** — often a pin bar or engulfing candle
4. This occurs AT or NEAR a higher-timeframe S&D zone
5. **Volume spike** on the sweep candle confirms the grab

#### Sweep + S&D Zone Confluence:
- Prior day high with supply zone above → sweep of PDH into supply = short
- Prior day low with demand zone below → sweep of PDL into demand = long
- Session high/low sweeps same logic

#### Sweep Characteristics:
- Wick extends beyond the level, body closes back inside
- Often accompanied by absorption (CVD divergence)
- Happens fast — usually 1-3 candles

### PineScript Implementation:
```
// 1. Detect equal highs/lows (price within small tolerance)
// 2. Track when price breaks beyond them
// 3. Check if price closes back inside within 1-3 bars
// 4. Confirm with volume spike (volume > 2x average)
// 5. Check proximity to S&D zone
// 6. Signal: "Liquidity Sweep at [Supply/Demand] Zone"
```

---

## 8. THE "ONE & DONE" SYSTEM

From the Whop description:
> "Discover the exact strategy that helped hundreds of traders quit overcomplicating their setups, trade with confidence, and scale their results. This free course breaks down my step-by-step approach to mastering day trading using **one proven setup a day** so you can trade less, win more, and live life on your terms."

### Likely Structure:
1. **Pre-market analysis:** Mark key S&D zones from daily/4H charts
2. **Identify the ONE best setup:** Highest confluence zone (S&D + VWAP + volume + prior day level)
3. **Wait for confirmation:** Structure shift on 5-min + absorption signal at the zone
4. **Execute ONE trade:** Enter with tight stop below/above zone
5. **Scale out:** Partial at 1:1 RR, remainder at 2:1 or 3:1
6. **Done for the day:** No revenge trading, no overtrading

---

## 9. COMMUNITY SCRIPTS & OPEN-SOURCE RESOURCES

### TradingView Scripts That Replicate His Approach:

1. **Supply & Demand Zones:**
   - LuxAlgo "Rally Base Drop SND Pivots" — https://www.tradingview.com/script/PVsY637u/
   - Uses RBD/DBR/RBR/DBD pattern detection
   - Open-source PineScript

2. **CVD Absorption:**
   - ratipetya "CVD Absorption + Confirmation" — https://www.tradingview.com/script/LzJGJVHc/
   - Detects CVD divergence + candle confirmation
   - Open-source

3. **Volume Supply & Demand:**
   - Heavy91 GitHub — https://github.com/Heavy91/TradingView_Indicators
   - Combines volume profile with S&D zones

4. **CVD Tools:**
   - TradingView built-in "CVD - Cumulative Volume Delta" candles and chart
   - fluxchart "CVD Oscillator Toolkit"
   - kb1ath "CVD Zones & Divergence [Pro]"

---

## 10. FULL PINESCRIPT ARCHITECTURE RECOMMENDATION

Based on everything gathered, here's the architecture for replicating Elder's approach:

### Indicator 1: Key Level Indicator (S&D Zones + Volume)
```
Components:
├── Supply/Demand Zone Detection
│   ├── Detect consolidation bases (ATR-relative small candles)
│   ├── Detect explosive departures (large body candles)
│   ├── Draw zone boxes from base high to base low
│   ├── Track zone freshness (tested/untested)
│   └── Invalidate on close through zone
├── Volume Profile Overlay
│   ├── Session volume profile (POC, VAH, VAL)
│   ├── Highlight HVN/LVN zones
│   └── Flag S&D zones that align with volume nodes
├── Key Daily Levels
│   ├── Prior day high/low/close
│   ├── Session open
│   ├── VWAP + bands (1σ, 2σ)
│   └── Pre-market high/low (if applicable)
└── Zone Scoring
    ├── Freshness (first touch > second touch)
    ├── Volume confluence (zone at HVN = stronger)
    ├── VWAP proximity
    └── Higher timeframe alignment
```

### Indicator 2: Absorption Alerts
```
Components:
├── CVD Calculation
│   ├── Per-bar volume delta (intrabar analysis)
│   ├── Cumulative delta line
│   └── CVD slope detection
├── Absorption Detection
│   ├── CVD vs Price divergence (core signal)
│   ├── High volume + small range bars
│   └── CVD flattening at key levels
├── Confirmation Patterns
│   ├── Engulfing candle detection
│   ├── Pin bar detection
│   ├── Volume anomaly (> 2x average)
│   └── CVD slope reversal
├── Context Filter
│   ├── Only signal at/near S&D zones
│   ├── Only signal at/near VWAP
│   └── Require structure shift alignment
└── Alerts
    ├── "Bullish Absorption at Demand Zone"
    ├── "Bearish Absorption at Supply Zone"
    └── "Liquidity Sweep + Absorption"
```

### Indicator 3: Structure + Liquidity
```
Components:
├── Market Structure
│   ├── Swing high/low detection (pivot-based)
│   ├── HH/HL/LH/LL tracking
│   ├── Break of Structure (BOS) signals
│   └── Change of Character (ChoCH) signals
├── Liquidity Sweeps
│   ├── Equal high/low detection
│   ├── Sweep detection (break + close back inside)
│   ├── Volume confirmation on sweep bar
│   └── S&D zone proximity check
└── Multi-Timeframe
    ├── HTF trend direction (15m/1H)
    ├── HTF S&D zones projected on 5-min
    └── Bias alignment scoring
```

---

## 11. REDDIT COMMUNITY SENTIMENT

### Positive:
- Students mention "Elders Daily Levels are precise"
- Free course has 54.7K members, 746 reviews at 5.0 rating
- Uses Bookmap which is considered professional-grade
- Focuses on ONE strategy (S&D + order flow) consistently

### Negative:
- r/ElderSantis has scam complaints about mentorship refund policy
- u/scammedbyeldersantis account exists with detailed complaints
- Some view him as primarily a content/course seller
- One Reddit post describes YouTube traders (including those like him) as "targeting beginners" with rotating topics
- Mentorship pricing (~$2K+) is high for what's delivered

### Neutral Assessment:
His **core methodology is sound** (S&D zones + order flow + VWAP is a legitimate institutional approach). The question is whether his paid indicators provide meaningful edge beyond what you can build yourself with open-source tools. Based on this research — **you can replicate ~90% of his approach** using open-source PineScript indicators and the architecture above.

---

## 12. KEY UNKNOWNS (Behind Paywall)

These specific details are only available through his paid mentorship/courses:

1. **Exact candle count** for base validation (his specific rule)
2. **ATR multiplier** thresholds for "explosive" departure candles
3. **Specific volume profile settings** he uses (resolution, lookback)
4. **Bookmap-specific absorption thresholds** (order size, speed)
5. **Exact risk management rules** (position sizing, max daily loss)
6. **Specific times he trades** (likely 9:30-11:30 AM ET based on futures scalping norms)
7. **Whether his indicators use proprietary exchange data** or just standard OHLCV
8. **His exact VWAP configuration** (anchoring points, band settings)

---

## 13. RECOMMENDED NEXT STEPS

1. **Watch his free YouTube content** for visual examples of his zone drawing style
2. **Join the free Whop course** (54.7K members) — may have more specific rules in the course materials
3. **Start building** with the LuxAlgo RBD SND Pivots + CVD Absorption indicator as base
4. **Backtest** the S&D + absorption + VWAP confluence on NQ/ES 5-min charts
5. **Consider** the $75/mo indicator bundle for 1 month to reverse-engineer the exact logic
6. **Build custom PineScript** using the architecture in Section 10

---

*This research was compiled from publicly available sources. No paid content was accessed or reproduced.*
