"""
Configuration for Elder S&D Live Trading Bot — TopStep / ProjectX Gateway.

Copy this file to config_local.py and fill in your credentials.
The bot loads config_local.py first, falling back to this file.
"""
from dataclasses import dataclass, field
from datetime import time


# ── ProjectX Gateway API ────────────────────────────────────────────
@dataclass
class ProjectXConfig:
    base_url: str = "https://gateway-api.s.projectx.com"
    username: str = "YOUR_TOPSTEP_USERNAME"
    api_key: str = "YOUR_API_KEY"
    # Populated after login
    token: str = ""
    account_id: int = 0
    # ES futures contract ID on ProjectX (lookup at runtime)
    contract_id: int = 0


# ── Risk Management ─────────────────────────────────────────────────
@dataclass
class RiskConfig:
    risk_pct: float = 0.02          # 2% of equity per trade
    max_contracts: int = 10
    min_contracts: int = 1
    account_equity: float = 50_000  # TopStep funded account size
    es_point_value: float = 50.0    # ES = $50/point (MES = $5)
    symbol: str = "ES"              # ES or MES


# ── Strategy Parameters ─────────────────────────────────────────────
@dataclass
class StrategyConfig:
    atr_period: int = 14
    ema_period: int = 50
    explosive_mult: float = 1.5     # body > ATR * this = explosive candle
    consol_mult: float = 0.5        # body < ATR * this = consolidation
    zone_max: int = 20              # max active zones to track
    rr_ratio: float = 2.0           # reward:risk ratio for TP
    stop_buffer_mult: float = 0.25  # ATR multiplier for stop buffer
    zone_invalidation_mult: float = 0.1  # ATR mult for zone invalidation
    min_score: int = 3              # minimum score out of 4 for entry
    volume_dead_mult: float = 0.85  # volume < MA * this = dead volume


# ── Session Times (Eastern Time) ────────────────────────────────────
@dataclass
class SessionConfig:
    no_entry_before: time = field(default_factory=lambda: time(10, 0))
    no_entry_after: time = field(default_factory=lambda: time(15, 0))
    eod_exit_time: time = field(default_factory=lambda: time(15, 45))
    bar_interval_minutes: int = 5
    timezone: str = "US/Eastern"


# ── Telegram Notifications ──────────────────────────────────────────
@dataclass
class TelegramConfig:
    enabled: bool = False
    bot_token: str = "YOUR_TELEGRAM_BOT_TOKEN"
    chat_id: str = "YOUR_CHAT_ID"


# ── Master Config ───────────────────────────────────────────────────
@dataclass
class Config:
    projectx: ProjectXConfig = field(default_factory=ProjectXConfig)
    risk: RiskConfig = field(default_factory=RiskConfig)
    strategy: StrategyConfig = field(default_factory=StrategyConfig)
    session: SessionConfig = field(default_factory=SessionConfig)
    telegram: TelegramConfig = field(default_factory=TelegramConfig)
    log_level: str = "INFO"


def load_config() -> Config:
    """Load config, preferring config_local.py overrides if present."""
    cfg = Config()
    try:
        from live_trading.config_local import apply_overrides
        apply_overrides(cfg)
    except ImportError:
        pass
    return cfg
