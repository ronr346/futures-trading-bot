# Prop Firm API & Algorithmic Trading Research

> Last updated: 2026-02-23

## 🏆 Executive Summary

**Best options for autonomous AI-driven trading via API:**

| Rank | Firm | API? | Algo Allowed? | Best Path |
|------|------|------|---------------|-----------|
| 🥇 | **TopStep (TopstepX)** | ✅ REST + WebSocket (ProjectX) | ✅ Yes, explicitly | ProjectX Gateway API — best documented, community active |
| 🥈 | **Tradeify** | ✅ ProjectX API + Tradovate API (live only) | ✅ Yes (no HFT) | ProjectX API for eval, Tradovate API for live funded |
| 🥉 | **Bulenox** | ⚠️ Via Rithmic API | ⚠️ Likely allowed, confirm first | Rithmic Protocol Buffer API via Python |
| 4 | **Elite Trader Funding** | ⚠️ Via Rithmic/NinjaTrader | ⚠️ Not explicitly prohibited | NinjaTrader + Rithmic |
| 5 | **My Funded Futures** | ⚠️ Via platform APIs | ❌ AI bots explicitly banned | Allows "automation tools" but NOT fully autonomous AI |

**Firms that explicitly BAN automated/algo trading:**
- ❌ **Apex Trader Funding** — "strictly prohibited" on all account types
- ❌ **Take Profit Trader** — "no automated or bot trading of any kind"
- ❌ **Leeloo Trading** — full automation not allowed on Practice/Performance accounts
- ❌ **Earn2Trade** — discouraged during evaluation, unclear for funded

---

## 📊 Detailed Firm Analysis

### 1. TopStep (topstep.com) ⭐ TOP PICK

**Platform:** TopstepX (powered by ProjectX)
**API:** ✅ REST + WebSocket via ProjectX Gateway API
- REST API for account management, order placement
- WebSocket (SignalR) for real-time market data streaming
- Historical data available
- API subscription: ~$25/month (includes token, market data, docs)

**Algo Trading:** ✅ **Explicitly allowed.** Traders can build and run trading bots, connect scripts, automate order execution.

**Account Sizes & Pricing:**
| Account | Monthly | Activation Fee | Profit Target |
|---------|---------|----------------|---------------|
| 50K | $49/mo | $149 | $3,000 |
| 100K | $99/mo | $149 | $6,000 |
| 150K | $149/mo | $149 | $9,000 |

**Profit Split:** 90% trader / 10% Topstep

**API Documentation:**
- ProjectX Gateway API: https://gateway.docs.projectx.com/
- TopstepX API Help: https://help.topstep.com/en/articles/11187768-topstepx-api-access
- GitHub community libs: https://github.com/topics/topstepx (TypeScript client available)
- Reddit community: r/TopStepX (active bot builders)

**Key Notes:**
- Single API subscription covers all accounts under your profile
- Active community building bots in Python, TypeScript, C++
- People have built fully functional trading bots already
- Best documented and most bot-friendly prop firm

---

### 2. Tradeify (tradeify.co) ⭐ STRONG OPTION

**Platform:** ProjectX (eval) + Tradovate (live funded)
**API:** ✅ ProjectX API for evaluation; Tradovate API for live funded accounts only

**Algo Trading:** ✅ **Personal bots allowed** — HFT bots are NOT permitted. Must hold >50% of trades longer than 10 seconds.

**Account Sizes & Pricing:**
| Account | Pricing | Profit Target |
|---------|---------|---------------|
| 50K Select | ~$49/mo | TBD |
| 100K Select | ~$99/mo | TBD |
| 150K Select | ~$149/mo | TBD |

**Profit Split:** 90% trader / 10% Tradeify

**Key Notes:**
- Also built on ProjectX, so same API infrastructure as TopStep
- Tradovate API only available for LIVE funded accounts (not eval)
- For eval phase, use ProjectX Gateway API
- No HFT, but regular algo strategies fine

---

### 3. Bulenox (bulenox.com)

**Platform:** Rithmic + NinjaTrader 8
**API:** Via Rithmic Protocol Buffer API (indirect)

**Algo Trading:** ⚠️ **Not explicitly prohibited, but confirm with support.** They use Rithmic, which supports programmatic trading. PickMyTrade and other automation services advertise Bulenox compatibility.

**Account Sizes:** $10K to $250K accounts available
**Profit Split:** Up to 90% trader

**Key Notes:**
- Uses Rithmic infrastructure → can use Python Rithmic libraries
- One Rithmic User ID per trader
- Unlimited evaluation accounts, up to 11 master accounts

---

### 4. Elite Trader Funding (elitetraderfunding.com)

**Platform:** Rithmic + NinjaTrader 8
**API:** Via Rithmic/NinjaTrader APIs

**Algo Trading:** ⚠️ **Not explicitly addressed** in publicly available rules. Uses Rithmic which technically supports algo trading.

**Account Sizes:** 25K, 50K, 100K, 150K+
**Key Notes:** Confirm automation rules with support before committing.

---

### 5. My Funded Futures (myfundedfutures.com)

**Platform:** Multiple (Rithmic-based)
**Algo Trading:** ⚠️ **Partially allowed.** As of Nov 2025, they permit automation tools, BUT:
- ❌ **AI-driven bots that operate entirely without human involvement are STRICTLY FORBIDDEN**
- ❌ High-frequency trading (>200 trades/day) prohibited
- ❌ Exploiting simulation quirks prohibited

This rules us out for fully autonomous AI trading.

---

### 6. Apex Trader Funding (apextraderfunding.com)

**Platform:** Rithmic + NinjaTrader/Tradovate
**Algo Trading:** ❌ **STRICTLY PROHIBITED** — "the use of automation is strictly prohibited on all account types. This includes any form of AI, Autobots, algorithms, fully automated trading systems, and HFTs."

**DO NOT USE for AI bot trading.**

---

### 7. Take Profit Trader (takeprofittrader.com)

**Platform:** Rithmic + NinjaTrader
**Algo Trading:** ❌ **STRICTLY PROHIBITED** — "We do not allow any automated or bot trading of any kind. All trades must be manually executed."

**DO NOT USE for AI bot trading.**

---

### 8. Earn2Trade (earn2trade.com)

**Platform:** NinjaTrader + Finamark (CQG-based for funded)
**Algo Trading:** ❌ **Discouraged/prohibited during evaluation.** Automated strategies "usually not encouraged during the evaluation stage."

**Not recommended for our use case.**

---

### 9. Leeloo Trading (leelootrading.com)

**Platform:** Rithmic + NinjaTrader
**Algo Trading:** ❌ **Full automation NOT allowed** — "Any system that places or manages trades without your manual input is not allowed on Practice or Performance Accounts."

**DO NOT USE for AI bot trading.**

---

### 10. BluSky Trading (blusky.pro)

**Platform:** NinjaTrader-based
**Algo Trading:** ⚠️ Unclear. TradersPost advertises connectivity, suggesting some automation is possible. Need to confirm with support.

**Not enough information to recommend.**

---

## 🔧 Platform APIs (The Infrastructure Layer)

### Tradovate API
- **Type:** REST + WebSocket
- **Docs:** https://api.tradovate.com/
- **Support:** https://support.tradovate.com/s/article/Tradovate-API-Access
- **Cost:** $25/month add-on (requires live account with $1,000+ balance)
- **CME data:** Additional ~$407/month for non-display CME data license
- **Capabilities:** Account info, order management, position management, market data (WebSocket only for real-time)
- **Note:** REST for orders, WebSocket for market data streaming
- **Endpoints:** `wss://md.tradovateapi.com/v1/websocket` (market data), `wss://live.tradovateapi.com/v1/websocket` (trading)
- **⚠️ Important:** Tradovate API requires LIVE account — won't work for sim/eval accounts at most prop firms. Use ProjectX API for evaluation phase.

### Rithmic API
- **Type:** Protocol Buffer over TCP (proprietary binary protocol)
- **Official:** https://www.rithmic.com/apis
- **Tiers:** R|Protocol API, R|API+, R|Diamond API (increasing capabilities/cost)
- **Python Libraries:**
  - `pyrithmic` — https://github.com/jacksonwoody/pyrithmic
  - `async-rithmic` — https://pypi.org/project/async-rithmic/ / https://github.com/rundef/async_rithmic
- **Capabilities:** Market data, order execution, account management, historical data
- **Key advantage:** Works with eval/sim accounts at prop firms using Rithmic
- **Gateway:** Test environment available at `RithmicEnvironment.RITHMIC_PAPER_TRADING`

### NinjaTrader API
- **Type:** C# NinjaScript (native) + ATI (Automated Trading Interface)
- **NinjaScript:** Full C# framework for strategies, indicators, order management
- **ATI:** External interface for sending commands to NinjaTrader
- **Third-party:** CrossTrade REST API (https://crosstrade.io/) — provides REST/WebSocket API for NinjaTrader 8, supports prop firms
- **Limitation:** NinjaTrader is Windows-only desktop application — requires running instance

### ProjectX Gateway API ⭐ KEY FOR PROP FIRMS
- **Type:** REST + WebSocket (SignalR)
- **Docs:** https://gateway.docs.projectx.com/
- **Used by:** TopstepX, Tradeify, FundingFutures, TickTickTrader, E8X, and 10+ other prop firms
- **Capabilities:** Full trading API — accounts, orders, positions, market data
- **Cost:** ~$25/month subscription through prop firm
- **Key advantage:** Works for BOTH evaluation and funded accounts
- **Auth:** Token-based authentication via dashboard

---

## 🐍 Connecting a Python Bot

### Recommended Architecture: TopstepX + ProjectX API

```
Python Bot → ProjectX REST API (orders) + WebSocket/SignalR (market data)
```

**Step 1:** Get TopstepX evaluation account ($49-149/mo)
**Step 2:** Subscribe to API access (~$25/mo)
**Step 3:** Get API token from ProjectX Dashboard
**Step 4:** Use REST for auth + order management
**Step 5:** Use WebSocket/SignalR for real-time market data

**Existing Python Libraries:**
- TopstepX community: Check https://github.com/topics/topstepx
- For SignalR in Python: `signalrcore` package
- For REST: `httpx` or `aiohttp`

### Alternative: Rithmic (for Bulenox, Elite Trader Funding)

```python
# Using async-rithmic library
pip install async-rithmic

from async_rithmic import RithmicClient, Gateway
client = RithmicClient(
    user="your_username", 
    password="your_password",
    system_name="Rithmic Test",
    app_name="my_bot",
    app_version="1.0",
    gateway=Gateway.TEST
)
await client.connect()
security_code = await client.get_front_month_contract("ES", "CME")
# Place orders, stream data, etc.
```

### Alternative: Tradovate API (for live funded accounts)

```python
# REST for orders
import httpx
base_url = "https://live.tradovateapi.com/v1"
# Auth → get token → place orders

# WebSocket for market data
import websockets
async with websockets.connect("wss://md.tradovateapi.com/v1/websocket") as ws:
    # Subscribe to market data
    pass
```

---

## 🎯 Recommended Strategy

### Phase 1: Evaluation (Pass the combine)
1. **Sign up for TopStep 50K** ($49/mo) — cheapest entry
2. **Subscribe to ProjectX API** ($25/mo)
3. **Build Python bot** using ProjectX Gateway API
4. **Pass evaluation** — profit target $3,000 with trailing drawdown
5. Total cost: ~$74/month during eval

### Phase 2: Funded Account
1. **Pay activation fee** ($149 one-time)
2. **Continue using same ProjectX API** — works for funded accounts too
3. **Trade autonomously** with AI bot
4. **Profit split:** 90% to you

### Phase 3: Scale
1. Once profitable, add more TopStep accounts (or try Tradeify)
2. Same bot, multiple accounts via single API subscription
3. Scale to 150K accounts for larger position sizes

### Why TopStep is #1 Pick:
- ✅ Explicitly allows trading bots
- ✅ Well-documented REST + WebSocket API
- ✅ Active community building bots
- ✅ Cheapest eval ($49/mo for 50K)
- ✅ 90/10 profit split
- ✅ Single API subscription for all accounts
- ✅ ProjectX API works for both eval AND funded phases
- ✅ No need for NinjaTrader desktop app — pure API access

---

## ⚠️ Important Considerations

1. **Consistency rules** — Most firms require you to not make >30-50% of total profit in a single day. Your bot needs to respect this.
2. **Drawdown limits** — Trailing drawdowns are the #1 reason traders fail. Bot must have strict risk management.
3. **Trading hours** — Most firms only allow trading during CME regular hours. Bot must respect market hours.
4. **No HFT** — Even firms that allow bots prohibit high-frequency trading. Keep trade frequency reasonable.
5. **Holding trades >10 seconds** — Tradeify requires >50% of profit from trades held >10s. TopStep may have similar rules.
6. **Simulation vs. Live fills** — Sim fills are optimistic. Strategy that works in eval may struggle in live. Plan for slippage.
7. **Rules can change** — Always check current rules before committing. Prop firms update policies frequently.
