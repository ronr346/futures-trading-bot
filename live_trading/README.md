# Elder S&D Live Trading Bot — TopStep / ProjectX Gateway

Live trading bot for the Elder Santis Supply & Demand strategy on TopStep funded accounts via the ProjectX Gateway API.

## Strategy

**Elder Supply & Demand** — zones detected from price structure:

- **Demand zone**: Drop (explosive down) → Base (consolidation) → Rally (explosive up)
- **Supply zone**: Rally (explosive up) → Base (consolidation) → Drop (explosive down)

Entry requires **3 of 4 conditions** (A+ setup):

1. **Trend** — price above/below EMA-50
2. **Zone** — price touching a valid S/D zone
3. **Structure shift** — bullish/bearish candle confirmation
4. **Dead volume** — low volume on pullback into zone

Risk management:
- 2% equity risk per trade
- 1–10 contracts (position sized to risk)
- 2:1 reward-to-risk ratio
- Stop-loss below/above zone + ATR buffer
- Max 1 trade per day (One & Done)
- EOD exit at 15:45 ET

## Setup

### 1. Install dependencies

```bash
pip install httpx signalrcore pytz
```

### 2. Configure credentials

Create `live_trading/config_local.py`:

```python
def apply_overrides(cfg):
    # ProjectX Gateway credentials
    cfg.projectx.username = "your_topstep_email"
    cfg.projectx.api_key = "your_api_key"

    # Account settings
    cfg.risk.account_equity = 50000  # your funded account size
    cfg.risk.symbol = "ES"           # ES or MES

    # Telegram (optional)
    cfg.telegram.enabled = True
    cfg.telegram.bot_token = "123456:ABC-DEF..."
    cfg.telegram.chat_id = "your_chat_id"
```

### 3. Get your ProjectX API key

1. Log in to your TopStep dashboard
2. Go to API settings / ProjectX Gateway
3. Generate an API key
4. Copy your username and API key into `config_local.py`

### 4. Telegram bot (optional)

1. Message [@BotFather](https://t.me/BotFather) on Telegram
2. Create a new bot, copy the token
3. Start a chat with your bot, get your chat ID from `https://api.telegram.org/bot<TOKEN>/getUpdates`

## Running

```bash
python -m live_trading.bot
```

Run from the project root directory (`futures-trading-bot/`).

## Architecture

```
live_trading/
├── config.py              # Configuration dataclasses
├── config_local.py         # Your credentials (git-ignored)
├── projectx_client.py      # ProjectX REST + SignalR client
├── strategy.py             # Elder S&D zone detection + scoring
├── telegram_notifier.py    # Trade alert notifications
└── bot.py                  # Main orchestrator + bar aggregation
```

**Data flow:**

```
ProjectX SignalR (ticks) → BarAggregator (5min OHLCV) → Strategy (signal) → REST orders
                                                                           → Telegram alert
```

## Files

| File | Purpose |
|------|---------|
| `config.py` | All configuration with defaults — risk, strategy params, session times |
| `projectx_client.py` | `ProjectXRest` (httpx) for auth/orders + `ProjectXWebSocket` (signalrcore) for live quotes |
| `strategy.py` | Pure strategy logic — zone detection state machine, entry scoring, position sizing |
| `bot.py` | Orchestrator — connects data feed to strategy to execution, manages position lifecycle |
| `telegram_notifier.py` | Sends HTML-formatted trade entry/exit/status messages to Telegram |

## Safety

- The bot places **bracket orders** (entry + stop + target) for every trade
- EOD exit at 15:45 ET ensures no overnight positions
- Max 1 trade per day prevents overtrading
- Position sizing capped at 10 contracts
- All errors are logged and sent to Telegram

## Monitoring

Logs print to stdout with timestamps. Set `cfg.log_level = "DEBUG"` for verbose bar-by-bar output.

Telegram notifications cover:
- Bot start/stop
- Trade entries with full details (price, stop, target, R:R, score)
- Trade exits with P&L
- Errors and crashes
