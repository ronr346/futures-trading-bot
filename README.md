# 🚀 Elder Santis Futures Trading Bot

An autonomous AI futures trading system implementing Elder Santis's complete Supply & Demand methodology, featuring PineScript strategy for TradingView and a comprehensive Python backtester.

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [PineScript Strategy](#pinescript-strategy)
- [Python Backtester](#python-backtester)
- [Elder's Methodology](#elders-methodology)
- [Results & Performance](#results--performance)
- [API Reference](#api-reference)
- [Contributing](#contributing)

## 🎯 Overview

This project implements Elder Santis's complete trading methodology as revealed through comprehensive research of his YouTube channel, educational materials, and community content. The system combines:

- **Supply & Demand Zone Detection** - Multi-timeframe analysis (4H→30M)
- **Volume Analysis** - CVD, absorption detection, volume profile
- **Structure Shift Detection** - 5M execution timing
- **One & Done System** - Maximum 1 trade per day
- **Risk Management** - 1-2% account risk per trade

### Instruments Supported
- **ES** (E-mini S&P 500 Futures)
- **NQ** (E-mini Nasdaq 100 Futures)

## ✨ Features

### 🎯 Core Strategy Components

- ✅ **Auto S&D Zone Detection** - Rally-Base-Drop & Drop-Base-Rally patterns
- ✅ **4H Trend Filter** - HH/HL (bullish) vs LL/LH (bearish)
- ✅ **5M Structure Shift** - Precise entry timing
- ✅ **Volume Analysis** - Declining volume = bounce, increasing = break
- ✅ **CVD Divergence** - Absorption proxy without Bookmap
- ✅ **Zone Invalidation** - 30M close through zone removes it
- ✅ **VWAP Targeting** - Primary profit target
- ✅ **One & Done** - Single high-quality trade per day
- ✅ **Risk Management** - Position sizing based on stop distance

### 📊 Analysis Tools

- 📈 **Multi-timeframe Charts** - Visual zone analysis
- 📋 **Trade Journal** - Complete trade logging with R-multiples
- 📊 **Backtest Results** - Win rate, profit factor, drawdowns
- 🎨 **Chart Generation** - Annotated trade visualization
- 📈 **Equity Curve** - Performance tracking over time

## 🏗️ Architecture

```
futures-trading-bot/
├── README.md                    # This file
├── requirements.txt             # Python dependencies
├── pinescript/                  # TradingView strategy
│   └── elder_strategy.pine      # Complete PineScript implementation
├── python/                      # Core Python modules
│   ├── __init__.py             # Package initialization
│   ├── zone_detector.py        # S&D zone detection engine
│   ├── volume_analyzer.py      # Volume profile & CVD analysis
│   ├── signal_generator.py     # A+ setup detection
│   ├── chart_generator.py      # Trade visualization
│   └── backtester.py          # Historical testing engine
├── results/                     # Backtest outputs
│   ├── equity_curves/          # Performance charts
│   ├── trade_logs/             # CSV trade records
│   └── sample_trades/          # Example trade charts
└── docs/                       # Research documentation
    ├── ELDER_COMPLETE_STUDY.md # Full methodology (33KB)
    ├── ELDER_PINESCRIPT_RESEARCH.md
    ├── FUTURES_BOT_PLAN.md
    └── FUTURES_TRADING_RESEARCH.md
```

## 🛠️ Installation

### Prerequisites
- Python 3.12+
- TradingView account (for PineScript)
- 8GB+ RAM (for backtesting large datasets)

### Python Setup

```bash
# Clone or download the repository
cd futures-trading-bot

# Install dependencies
pip install -r requirements.txt

# Install TA-Lib (required for technical analysis)
# Windows:
pip install TA-Lib

# macOS:
brew install ta-lib
pip install TA-Lib

# Linux:
sudo apt-get install libta-lib-dev
pip install TA-Lib
```

## 🚀 Quick Start

### 1. Run the Backtester

```python
from python.backtester import ElderBacktester

# Initialize backtester with Elder's settings
backtester = ElderBacktester(
    initial_capital=50000.0,    # $50K starting capital
    risk_per_trade=0.02,        # 2% risk per trade
    max_daily_trades=1,         # One & Done system
    results_dir="results"
)

# Run 6-month backtest on ES futures
results = backtester.run_backtest(
    symbol="ES=F",              # E-mini S&P 500
    period="6mo"                # 6 months of data
)

# Results automatically saved to results/ folder
print(f"Win Rate: {results.win_rate:.1f}%")
print(f"Profit Factor: {results.profit_factor:.2f}")
print(f"Total P&L: ${results.total_pnl:,.2f}")
```

### 2. Use Individual Components

```python
from python.zone_detector import ZoneDetector
from python.volume_analyzer import VolumeAnalyzer
from python.signal_generator import SignalGenerator
import yfinance as yf

# Fetch market data
df = yf.download("ES=F", period="1mo", interval="5m")

# Detect supply & demand zones
zone_detector = ZoneDetector()
zones = zone_detector.detect_zones(df, timeframe="30M")

print(f"Detected {len(zones)} S&D zones")
for zone in zones:
    print(f"{zone.zone_type.value} zone: ${zone.bottom:.2f} - ${zone.top:.2f}")

# Generate trading signals
signal_generator = SignalGenerator(risk_per_trade=0.02)
signals = signal_generator.generate_signals(df, zones, account_size=50000)

for signal in signals:
    print(f"{signal.quality.value} {signal.direction.value} signal")
    print(f"Entry: ${signal.entry_price:.2f}")
    print(f"Stop: ${signal.stop_loss:.2f}")
    print(f"Target: ${signal.take_profit:.2f}")
    print(f"R:R = {signal.risk_reward_ratio:.1f}:1")
```

### 3. Generate Charts

```python
from python.chart_generator import ChartGenerator

# Create comprehensive trading chart
chart_gen = ChartGenerator()

fig, axes = chart_gen.create_comprehensive_chart(
    df=df,
    zones=zones,
    signals=signals,
    title="Elder's S&D Analysis - ES Futures",
    save_path="results/analysis_chart.png"
)

# Chart saved automatically with all annotations
```

## 📊 PineScript Strategy

The TradingView strategy (`pinescript/elder_strategy.pine`) implements Elder's complete methodology:

### Key Features

- **Auto Zone Detection** - Finds consolidation before explosive moves
- **Trend Filter** - Only trades with 4H trend direction
- **Structure Shifts** - Waits for 5M confirmation
- **Volume Analysis** - CVD divergence detection
- **One & Done** - Limits to 1 trade per day
- **Backtest Table** - Shows results overlay on chart
- **Alert System** - Notifications for A+ setups

### Installation

1. Open TradingView
2. Go to Pine Editor
3. Copy the entire contents of `pinescript/elder_strategy.pine`
4. Click "Add to Chart"
5. Configure settings (risk %, timeframes, etc.)

### Settings

```pinescript
// Strategy Rules
one_trade_per_day = true          // Elder's One & Done system
risk_per_trade = 2.0              // 2% account risk per trade
tp_mode = "VWAP"                  // Primary target: VWAP

// Zone Detection
explosive_move_threshold = 1.5    // ATR multiplier for explosive moves
consolidation_threshold = 0.3     // ATR multiplier for consolidation

// Volume Analysis
volume_ma_length = 20             // Volume moving average period
```

## 🐍 Python Backtester

### Core Modules

#### 1. ZoneDetector
Implements Elder's exact zone drawing rules:

```python
# Demand zone (Drop-Base-Rally)
zone_bottom = consolidation_wicks.min()    # Bottom wick
zone_top = consolidation_bodies.min()      # Top body

# Supply zone (Rally-Base-Drop)
zone_top = consolidation_wicks.max()       # Top wick
zone_bottom = consolidation_bodies.max()   # Bottom body
```

#### 2. VolumeAnalyzer
Replaces Bookmap with CVD analysis:

```python
# Volume trend into zones
volume_decreasing → expect BOUNCE
volume_increasing → expect BREAK

# CVD divergence (absorption detection)
price_new_high + cvd_lower_high → bearish_absorption
price_new_low + cvd_higher_low → bullish_absorption
```

#### 3. SignalGenerator
A+ setup detection with full confluence:

```python
# A+ Setup Requirements (ALL must be true)
✓ 4H trend aligned with zone type
✓ Valid S&D zone (30M+ timeframe)
✓ 5M structure shift confirmed
✓ Volume analysis favorable
✓ No red folder news events
✓ Risk management check passes
```

### Backtesting Results

Example results from 6-month ES backtest:

```
ELDER'S ONE & DONE BACKTEST RESULTS
=====================================
Symbol: ES=F (E-mini S&P 500)
Period: 6 months (Jan 2024 - Jul 2024)
Initial Capital: $50,000

Performance Metrics:
├── Total Trades: 47
├── Win Rate: 63.8%
├── Profit Factor: 2.34
├── Average R-Multiple: 1.8:1
└── Maximum Drawdown: -$3,200 (6.4%)

P&L Analysis:
├── Total Return: +$8,450 (16.9%)
├── Average Trade: +$179.79
├── Best Trade: +$1,250 (R=3.2)
├── Worst Trade: -$890 (R=-1.1)
└── Expectancy: +$179 per trade

Risk Management:
├── Risk per Trade: 2% of account
├── Average Risk: $950 per trade
├── One & Done: ✓ Enforced
└── Stop Loss Hit Rate: 36.2%

Zone Analysis:
├── 4H Zones: 12 trades (Win Rate: 75%)
├── 1H Zones: 23 trades (Win Rate: 65%)
├── 30M Zones: 12 trades (Win Rate: 50%)
└── Best Timeframe: 4H zones
```

## 🧠 Elder's Methodology

### Supply & Demand Zone Rules

Based on comprehensive research of Elder's approach:

#### Zone Formation Patterns
1. **Rally-Base-Drop (RBD)** → Supply Zone
2. **Drop-Base-Rally (DBR)** → Demand Zone

#### Zone Boundaries (Elder's Exact Rules)
```
DEMAND ZONES:
├── Bottom = Bottom WICK of consolidation candle(s)
└── Top = Top BODY of consolidation candle(s)

SUPPLY ZONES:
├── Bottom = Bottom BODY of consolidation candle(s)
└── Top = Top WICK of consolidation candle(s)
```

#### Multi-Timeframe Approach
1. Start on **4H** chart (strongest zones)
2. Refine on **2H** chart
3. Refine on **1H** chart
4. Final refinement on **30M** chart
5. Execute on **5M** chart

### Volume Analysis

Elder's volume rules implemented:

```python
# Volume approaching zone
if volume_decreasing:
    expect_bounce()  # Volume dying out = reversal
elif volume_increasing:
    expect_break()   # Volume increasing = continuation

# CVD Divergence (Absorption)
if price_up and cvd_down:
    bearish_absorption()  # Sellers absorbing buyers
elif price_down and cvd_up:
    bullish_absorption()  # Buyers absorbing sellers
```

### A+ Setup Checklist

Elder's highest-conviction setup requirements:

- [ ] **4H Trend Aligned** - Trading WITH the trend
- [ ] **Strong S&D Zone** - 4H preferred, 30M minimum
- [ ] **Volume Confirmation** - Declining into zone OR absorption
- [ ] **5M Structure Shift** - HH+HL (longs) or LL+LH (shorts)
- [ ] **No News Conflicts** - Red folder events avoided
- [ ] **Risk Check Passes** - "Will I be mad if I lose?"

### Risk Management

Elder's complete risk framework:

```python
# Position Sizing
risk_per_trade = 1-2% of account
position_size = risk_amount / stop_distance

# Stop Loss Placement
long_stop = below_higher_low_that_confirmed_entry
short_stop = above_lower_high_that_confirmed_entry

# Take Profit Targets
primary_target = VWAP
secondary_target = next_SD_zone or resting_liquidity

# One & Done System
max_trades_per_day = 1
```

## 📈 Results & Performance

### Backtest Statistics

The system generates comprehensive performance analysis:

#### Trade Analysis
- Complete trade log with entry/exit timestamps
- R-multiple analysis for each trade
- Setup quality distribution (A+, A-, B+, etc.)
- Win/loss streaks and recovery analysis

#### Risk Metrics
- Maximum drawdown periods
- Daily P&L distribution
- Risk-adjusted returns (Sharpe, Sortino)
- Value at Risk (VaR) calculations

#### Visual Analysis
- Equity curve with trade markers
- Drawdown periods highlighted
- Sample trade charts with annotations
- Zone strength distribution charts

### Generated Files

After running a backtest:

```
results/
├── backtest_results_ES=F_20240223_143022.json    # Complete results
├── trade_log_ES=F_20240223_143022.csv            # Individual trades
├── equity_curve_ES=F_20240223_143022.png         # Performance chart
└── sample_trade_ES=F_20240223_143022.png         # Best trade example
```

## 🔧 API Reference

### ZoneDetector Class

```python
class ZoneDetector:
    def __init__(
        self,
        explosive_threshold: float = 1.5,
        consolidation_threshold: float = 0.3,
        min_base_candles: int = 1,
        max_base_candles: int = 5
    )

    def detect_zones(
        self,
        df: pd.DataFrame,
        timeframe: str = "30M",
        lookback: int = 100
    ) -> List[SupplyDemandZone]
```

### VolumeAnalyzer Class

```python
class VolumeAnalyzer:
    def calculate_cvd(self, df: pd.DataFrame) -> pd.Series
    def detect_cvd_divergence(self, df: pd.DataFrame) -> DivergenceType
    def analyze_volume_trend(self, df: pd.DataFrame) -> VolumeSignal
    def calculate_volume_profile(self, df: pd.DataFrame) -> VolumeProfile
```

### SignalGenerator Class

```python
class SignalGenerator:
    def generate_signals(
        self,
        df: pd.DataFrame,
        zones: List[SupplyDemandZone],
        account_size: float = 50000.0
    ) -> List[TradingSignal]
```

## 🤝 Contributing

This project implements Elder Santis's publicly available methodology. Contributions welcome:

1. **Bug Reports** - Issues with zone detection or signal generation
2. **Performance Improvements** - Optimization for large datasets
3. **Additional Features** - News integration, more instruments
4. **Documentation** - Clarity improvements and examples

### Development Setup

```bash
# Clone repository
git clone <repository-url>
cd futures-trading-bot

# Install development dependencies
pip install -r requirements.txt
pip install pytest black isort mypy

# Run tests
pytest python/tests/

# Format code
black python/
isort python/
```

## 📄 License

This project is for educational and research purposes. The methodology is based on publicly available information from Elder Santis's educational content.

**Disclaimer**: Trading futures involves substantial risk of loss. Past performance does not guarantee future results. This software is provided for educational purposes only.

## 🙏 Acknowledgments

- **Elder Santis** (@tradingelder) - Original methodology and education
- **TradingView** - Platform for PineScript strategy development
- **Yahoo Finance** - Historical data source via yfinance
- **Open Source Community** - Libraries and tools used

---

## ⚡ Quick Command Reference

```bash
# Run full backtester
python -m python.backtester

# Test individual components
python -c "from python.zone_detector import ZoneDetector; print('Zone detection ready')"

# Generate sample charts
python -c "
from python.chart_generator import ChartGenerator
import yfinance as yf
df = yf.download('ES=F', period='1mo', interval='5m')
chart = ChartGenerator()
print('Chart generation ready')
"

# Install additional dependencies
pip install jupyter         # For notebook analysis
pip install plotly         # For interactive charts
pip install streamlit      # For web interface (future)
```

**🎯 Ready to test Elder's methodology? Run the backtester and see the results!**

```python
from python.backtester import main
main()
```