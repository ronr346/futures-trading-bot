# 🏗️ Futures Trading Bot — Project Plan
## Autonomous AI Trader Using Elder Santis's Methodology

**Last Updated:** February 23, 2026

---

## 🎯 Vision

An autonomous AI agent that trades ES/NQ futures using Elder Santis's Supply & Demand + Order Flow methodology. The bot:
- Analyzes markets pre-session (4H→30M zones, volume profile, news)
- Identifies A+ setups in real-time during NY session
- Executes ONE trade per day with precise entries and exits
- Manages risk automatically (1-2% per trade, daily loss limit)
- Runs on a **TopStep funded account** via ProjectX API
- Reports every trade to Ron via Telegram with chart + reasoning

**End State:** A self-sustaining funded trading account generating consistent profits with zero human intervention during market hours.

---

## 📚 Knowledge Base (Completed)

| Document | Status | Content |
|----------|--------|---------|
| `FUTURES_TRADING_RESEARCH.md` | ✅ Done | Elder's methodology overview, prop firm comparison |
| `ELDER_COMPLETE_STUDY.md` | ✅ Done | 33KB — full channel analysis, 24 sections, 7 video transcripts |
| `ELDER_PINESCRIPT_RESEARCH.md` | ✅ Done | PineScript indicator architecture, open-source alternatives |
| `PROP_FIRM_API_RESEARCH.md` | ✅ Done | TopStep = #1 pick, ProjectX API details |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────┐
│                 FUTURES TRADING BOT              │
├─────────────────────────────────────────────────┤
│                                                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────────┐  │
│  │ Pre-Mkt  │→ │ Zone     │→ │ Real-Time    │  │
│  │ Analysis │  │ Engine   │  │ Monitor      │  │
│  └──────────┘  └──────────┘  └──────┬───────┘  │
│                                      │          │
│                              ┌───────▼───────┐  │
│                              │ Entry Engine  │  │
│                              │ (S&D + Volume │  │
│                              │  + Structure) │  │
│                              └───────┬───────┘  │
│                                      │          │
│                    ┌─────────────────▼────────┐ │
│                    │  Order Execution         │ │
│                    │  (ProjectX API)          │ │
│                    └─────────────────┬────────┘ │
│                                      │          │
│                    ┌─────────────────▼────────┐ │
│                    │  Trade Manager           │ │
│                    │  (Stop/Target/Exit)      │ │
│                    └─────────────────┬────────┘ │
│                                      │          │
│                    ┌─────────────────▼────────┐ │
│                    │  Telegram Reporter       │ │
│                    │  (Charts + P&L + Logic)  │ │
│                    └─────────────────────────┘  │
└─────────────────────────────────────────────────┘
```

---

## 📅 Phases

### Phase 1: Foundation (Week 1)
**Goal:** Get the infrastructure working end-to-end with paper trading.

| Task | Details | Est. Time |
|------|---------|-----------|
| 1.1 TopStep account | Sign up for $50K eval ($49/mo) | 10 min |
| 1.2 ProjectX API access | Subscribe ($25/mo), get API token | 10 min |
| 1.3 API client (Python) | Connect to ProjectX REST + WebSocket, fetch market data, place test orders | 4-6 hours |
| 1.4 Market data pipeline | Stream real-time ES/NQ price data via WebSocket (SignalR) | 2-3 hours |
| 1.5 Historical data loader | Fetch 4H, 30M, 5M candles for zone calculation | 2 hours |

**Deliverable:** Python script that connects to TopStep, streams live ES/NQ data, and can place/cancel orders.

---

### Phase 2: Zone Engine (Week 1-2)
**Goal:** Automatically identify Supply & Demand zones like Elder draws them.

| Task | Details | Est. Time |
|------|---------|-----------|
| 2.1 S&D Zone Detection | Find consolidation candles before explosive moves (Elder's rules: wick-to-body for demand, body-to-wick for supply) | 6-8 hours |
| 2.2 Multi-timeframe zones | Stack zones from 4H → 2H → 1H → 30M, refine at each level | 3-4 hours |
| 2.3 Zone strength scoring | Rank zones by: timeframe (4H strongest), Volume Profile POC inside zone, number of times tested | 3 hours |
| 2.4 Zone invalidation | 30M candle close through zone = invalidated (Elder's rule) | 1 hour |
| 2.5 Volume Profile | Calculate daily session POC, track POC direction (rising = bullish, falling = bearish) | 3-4 hours |

**Deliverable:** Engine that outputs a ranked list of active S&D zones with strength scores for ES/NQ.

---

### Phase 3: Signal Engine (Week 2-3)
**Goal:** Detect A+ setups and generate entry signals.

| Task | Details | Est. Time |
|------|---------|-----------|
| 3.1 Trend detector (4H) | Classify market as Bullish (HH/HL), Bearish (LL/LH), or Range | 2-3 hours |
| 3.2 Structure shift (5M) | Detect HH→HL for longs, LL→LH for shorts on 5M when price enters zone | 4-5 hours |
| 3.3 Volume analysis | Declining volume into zone = bounce expected, increasing = break expected | 3 hours |
| 3.4 Delta/absorption proxy | CVD divergence, delta spikes, volume exhaustion — replaces Bookmap | 6-8 hours |
| 3.5 A+ setup scorer | Combine: trend alignment + zone quality + structure shift + volume confirm = setup score | 3-4 hours |
| 3.6 News filter | Check Forex Factory for red folder events, reduce risk or skip during news | 2 hours |

**Deliverable:** Signal engine that fires A+ setup alerts with confidence scores.

---

### Phase 4: Execution Engine (Week 3)
**Goal:** Place orders, manage stops and targets automatically.

| Task | Details | Est. Time |
|------|---------|-----------|
| 4.1 Order placement | Market/limit orders via ProjectX API | 3 hours |
| 4.2 Stop loss logic | Place stop below HL (longs) or above LH (shorts) per Elder's rules | 2 hours |
| 4.3 Take profit targets | Target 1: VWAP, Target 2: next S&D zone or resting liquidity | 2 hours |
| 4.4 Position sizing | Calculate contracts based on stop distance + 1-2% account risk | 2 hours |
| 4.5 One & Done enforcement | Max 1 trade per day. After first trade (win or loss) → done | 1 hour |
| 4.6 Daily loss limit | Hard stop if daily P&L hits -$500 (prop firm compliant) | 1 hour |

**Deliverable:** Fully automated order execution with risk management.

---

### Phase 5: Reporting & Monitoring (Week 3-4)
**Goal:** Full visibility into what the bot is doing.

| Task | Details | Est. Time |
|------|---------|-----------|
| 5.1 Telegram notifications | Send pre-market analysis, trade alerts, daily P&L summary | 3 hours |
| 5.2 Chart generation | Generate annotated charts showing zones, entry, stop, target | 4-5 hours |
| 5.3 Trade journal | Auto-log every trade with: setup type, entry/exit, R multiple, reasoning | 2 hours |
| 5.4 Performance dashboard | Win rate, avg R, profit factor, equity curve | 3-4 hours |

**Deliverable:** Daily Telegram reports with annotated charts + running performance stats.

---

### Phase 6: TopStep Evaluation (Week 4+)
**Goal:** Pass the $50K TopStep Combine.

| Parameter | Target | TopStep Requirement |
|-----------|--------|-------------------|
| Profit target | $3,000 | $3,000 |
| Max drawdown | Stay above -$2,000 | -$2,000 trailing |
| Daily trades | 1 (One & Done) | No limit |
| Risk per trade | 1-2% ($500-1000) | N/A |
| Expected timeline | 10-20 trading days | No time limit |
| Win rate needed | 50%+ with 2:1 R:R | N/A |

**Strategy for passing:**
- Start with 1 MES contract (micro, $5/point) for first 3 days
- Scale to 1 ES contract ($50/point) once 3+ green days
- One & Done = natural consistency (no overtrading)
- Target $300-500/day → 10 green days = passed

---

## 💰 Costs

| Item | Cost | Frequency |
|------|------|-----------|
| TopStep 50K eval | $49 | Monthly |
| ProjectX API access | $25 | Monthly |
| Market data (included) | $0 | — |
| **Total startup** | **$74/month** | Until funded |

After funding: 90% profit split to us, 10% to TopStep.

---

## 🧠 Elder's Rules Embedded in Bot Logic

### Entry Rules (ALL must pass):
- [ ] 4H trend direction confirmed
- [ ] Price approaching valid S&D zone (30M or higher)
- [ ] Zone has Volume Profile POC confluence
- [ ] 5M structure shift confirms direction (HH/HL or LL/LH)
- [ ] Volume declining into zone (bounce) OR increasing through (break-retest)
- [ ] Delta/absorption confirmation (CVD divergence or exhaustion)
- [ ] No red folder news in next 30 min
- [ ] "Will I be mad if I lose?" → position size check passes

### Exit Rules:
- Stop: Below HL (long) or above LH (short)
- Target 1: VWAP
- Target 2: Next S&D zone / resting liquidity
- Hard exit: 30M candle closes through zone = invalidated

### Risk Rules:
- Max 1-2% account risk per trade
- Max 1 trade per day (One & Done)
- Daily loss limit: $500 (half of TopStep's $1000 daily)
- No trading during red folder news
- No revenge trading (enforced by One & Done)

---

## 🔧 Tech Stack

| Component | Technology |
|-----------|-----------|
| Language | Python 3.12 |
| API Client | ProjectX REST + WebSocket (SignalR) |
| Data Processing | pandas, numpy |
| Zone Detection | Custom S&D algorithm |
| Volume Analysis | Volume Profile + CVD calculation |
| Charts | mplfinance (reuse from Qullamaggie chart_generator) |
| Scheduling | APScheduler or cron (pre-market routine) |
| Notifications | Telegram Bot API (via OpenClaw) |
| Logging | Python logging + trade journal JSON |
| Hosting | Ron's PC initially → Railway later |

---

## 📊 Success Metrics

| Metric | Target | Timeframe |
|--------|--------|-----------|
| Pass TopStep eval | $3,000 profit | 1-2 months |
| Win rate | 55%+ | First 50 trades |
| Average R:R | 2:1+ | Ongoing |
| Profit factor | 1.5+ | Ongoing |
| Max daily loss | Never exceed $500 | Always |
| Monthly target (funded) | $2,000-5,000 | After funding |

---

## 🚀 What Success Looks Like

**Month 1:** Bot is live on TopStep eval, taking 1 trade/day, learning and adapting.

**Month 2:** Bot passes TopStep Combine. Funded account activated. First real profits.

**Month 3:** Bot trading funded account consistently. Scale to 100K account. $2,000-5,000/month profit.

**Month 6:** Multiple funded accounts (TopStep + Tradeify). Bot refined from 100+ trades. $5,000-10,000/month.

**Year 1:** Fully autonomous futures trading operation. Bot handles ES + NQ across multiple prop firm accounts. Combined monthly income: $10,000+.

**The dream:** Ron focuses on university and life while the bot quietly generates income from futures trading every single market day.

---

*"One & Done. One good trade. Every day. That's all it takes."* — Elder Santis
