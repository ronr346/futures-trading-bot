"""
Backtester for Elder Santis Supply & Demand Strategy

This standalone Python backtester implements and tests Elder's complete methodology:
- Fetches ES/NQ data from yfinance
- Detects S&D zones using Elder's rules
- Applies 4H trend filter and 5M structure shift logic
- Implements volume analysis and absorption detection
- One & Done: max 1 trade per day
- Risk management: 1-2% per trade, stops at swing levels
- Targets: VWAP or next S&D zone

Outputs comprehensive backtest results with statistics and charts.
"""

import pandas as pd
import numpy as np
import yfinance as yf
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import warnings
import json
import os

try:
    from .zone_detector import ZoneDetector, SupplyDemandZone, ZoneType, ZoneStrength
    from .volume_analyzer import VolumeAnalyzer, VolumeSignal
    from .signal_generator import SignalGenerator, TradingSignal, SignalDirection, SetupQuality
    from .chart_generator import ChartGenerator
except ImportError:
    from zone_detector import ZoneDetector, SupplyDemandZone, ZoneType, ZoneStrength
    from volume_analyzer import VolumeAnalyzer, VolumeSignal
    from signal_generator import SignalGenerator, TradingSignal, SignalDirection, SetupQuality
    from chart_generator import ChartGenerator

warnings.filterwarnings('ignore')

@dataclass
class Trade:
    """Individual trade record"""
    trade_id: str
    entry_timestamp: pd.Timestamp
    exit_timestamp: Optional[pd.Timestamp]
    signal: TradingSignal
    entry_price: float
    exit_price: Optional[float]
    exit_reason: str
    pnl: float
    pnl_percentage: float
    r_multiple: float
    position_size: float
    commission: float
    slippage: float
    duration_minutes: Optional[int]
    max_favorable_excursion: float
    max_adverse_excursion: float

@dataclass
class BacktestResults:
    """Complete backtest results and statistics"""
    # Basic metrics
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float

    # P&L metrics
    total_pnl: float
    total_pnl_percentage: float
    gross_profit: float
    gross_loss: float
    profit_factor: float

    # Risk metrics
    max_drawdown: float
    max_drawdown_percentage: float
    avg_trade_pnl: float
    avg_winning_trade: float
    avg_losing_trade: float

    # R-multiple analysis
    avg_r_multiple: float
    best_trade_r: float
    worst_trade_r: float

    # Additional metrics
    sharpe_ratio: float
    sortino_ratio: float
    calmar_ratio: float
    expectancy: float

    # Trade distribution
    trades_by_setup: Dict[str, int]
    trades_by_month: Dict[str, int]

    # Equity curve
    equity_curve: pd.Series
    drawdown_curve: pd.Series

class ElderBacktester:
    """
    Comprehensive backtester for Elder Santis's methodology

    Features:
    - Historical data fetching (ES/NQ futures via yfinance)
    - Multi-timeframe analysis
    - Complete signal generation with all confluence factors
    - Realistic execution (slippage, commissions)
    - One & Done enforcement
    - Detailed trade tracking and analysis
    - Performance visualization
    """

    def __init__(
        self,
        initial_capital: float = 50000.0,
        risk_per_trade: float = 0.02,
        commission_per_contract: float = 4.0,
        slippage_ticks: int = 2,
        tick_value: float = 12.50,  # ES futures: $12.50 per tick
        max_daily_trades: int = 1,  # One & Done
        results_dir: str = "results"
    ):
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.risk_per_trade = risk_per_trade
        self.commission_per_contract = commission_per_contract
        self.slippage_ticks = slippage_ticks
        self.tick_value = tick_value
        self.max_daily_trades = max_daily_trades
        self.results_dir = results_dir

        # Initialize components
        self.zone_detector = ZoneDetector()
        self.volume_analyzer = VolumeAnalyzer()
        self.signal_generator = SignalGenerator(
            risk_per_trade=risk_per_trade,
            max_daily_trades=max_daily_trades
        )
        self.chart_generator = ChartGenerator()

        # Trade tracking
        self.trades: List[Trade] = []
        self.open_position = None
        self.equity_curve = []
        self.daily_pnl = {}

        # Create results directory
        os.makedirs(results_dir, exist_ok=True)

    def fetch_data(
        self,
        symbol: str,
        period: str = "6mo",
        interval: str = "5m"
    ) -> pd.DataFrame:
        """
        Fetch historical data from Yahoo Finance

        Args:
            symbol: ES=F or NQ=F for futures, ^GSPC or ^IXIC for indices
            period: Data period (6mo, 1y, 2y, etc.)
            interval: Data interval (5m, 15m, 30m, 1h, 4h, 1d)

        Returns:
            OHLCV DataFrame with proper datetime index
        """
        print(f"Fetching {symbol} data - Period: {period}, Interval: {interval}")

        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(period=period, interval=interval)

            if df.empty:
                raise ValueError(f"No data retrieved for {symbol}")

            # Ensure we have the required columns
            required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
            missing_columns = [col for col in required_columns if col not in df.columns]

            if missing_columns:
                raise ValueError(f"Missing columns: {missing_columns}")

            # Clean data
            df = df.dropna()

            # Remove any rows with zero volume (market closed)
            df = df[df['Volume'] > 0]

            print(f"Data fetched successfully: {len(df)} rows from {df.index[0]} to {df.index[-1]}")
            return df

        except Exception as e:
            print(f"Error fetching data for {symbol}: {e}")
            return pd.DataFrame()

    def prepare_multi_timeframe_data(
        self,
        df_5m: pd.DataFrame
    ) -> Dict[str, pd.DataFrame]:
        """
        Convert 5-minute data to multiple timeframes for Elder's analysis

        Returns dictionary with 4H, 1H, 30M, 15M, 5M data
        """
        timeframe_data = {}

        # 5-minute (base data)
        timeframe_data['5M'] = df_5m.copy()

        # 15-minute
        df_15m = df_5m.resample('15T').agg({
            'Open': 'first',
            'High': 'max',
            'Low': 'min',
            'Close': 'last',
            'Volume': 'sum'
        }).dropna()
        timeframe_data['15M'] = df_15m

        # 30-minute (most important for Elder's zone detection)
        df_30m = df_5m.resample('30T').agg({
            'Open': 'first',
            'High': 'max',
            'Low': 'min',
            'Close': 'last',
            'Volume': 'sum'
        }).dropna()
        timeframe_data['30M'] = df_30m

        # 1-hour
        df_1h = df_5m.resample('1H').agg({
            'Open': 'first',
            'High': 'max',
            'Low': 'min',
            'Close': 'last',
            'Volume': 'sum'
        }).dropna()
        timeframe_data['1H'] = df_1h

        # 4-hour (for trend analysis)
        df_4h = df_5m.resample('4H').agg({
            'Open': 'first',
            'High': 'max',
            'Low': 'min',
            'Close': 'last',
            'Volume': 'sum'
        }).dropna()
        timeframe_data['4H'] = df_4h

        return timeframe_data

    def detect_zones_multi_timeframe(
        self,
        timeframe_data: Dict[str, pd.DataFrame]
    ) -> Dict[str, List[SupplyDemandZone]]:
        """
        Detect S&D zones across multiple timeframes using Elder's top-down approach
        """
        all_zones = {}

        # Process timeframes in order of importance (Elder's approach)
        for tf in ['4H', '1H', '30M', '15M']:
            if tf in timeframe_data:
                zones = self.zone_detector.detect_zones(
                    timeframe_data[tf],
                    timeframe=tf,
                    lookback=100
                )
                all_zones[tf] = zones
                print(f"Detected {len(zones)} zones on {tf} timeframe")

        return all_zones

    def simulate_trade_execution(
        self,
        signal: TradingSignal,
        df: pd.DataFrame,
        current_timestamp: pd.Timestamp
    ) -> Optional[Trade]:
        """
        Simulate realistic trade execution with slippage and commissions

        Returns None if trade cannot be executed
        """
        try:
            # Calculate actual entry price with slippage
            slippage_amount = self.slippage_ticks * self.tick_value / 100  # Convert to price

            if signal.direction == SignalDirection.LONG:
                actual_entry_price = signal.entry_price + slippage_amount
            else:
                actual_entry_price = signal.entry_price - slippage_amount

            # Calculate position size based on available capital
            risk_amount = self.current_capital * signal.risk_amount / self.initial_capital

            if signal.direction == SignalDirection.LONG:
                stop_distance = actual_entry_price - signal.stop_loss
            else:
                stop_distance = signal.stop_loss - actual_entry_price

            if stop_distance <= 0:
                return None  # Invalid trade setup

            # Calculate contracts (assuming ES futures)
            contract_value = actual_entry_price * 50  # ES multiplier
            position_size_contracts = risk_amount / stop_distance / 50

            # Minimum 1 contract
            position_size_contracts = max(1, int(position_size_contracts))

            # Calculate commission
            commission = position_size_contracts * self.commission_per_contract

            trade_id = f"{signal.signal_id}_{current_timestamp.strftime('%Y%m%d_%H%M%S')}"

            trade = Trade(
                trade_id=trade_id,
                entry_timestamp=current_timestamp,
                exit_timestamp=None,
                signal=signal,
                entry_price=actual_entry_price,
                exit_price=None,
                exit_reason="",
                pnl=0.0,
                pnl_percentage=0.0,
                r_multiple=0.0,
                position_size=position_size_contracts,
                commission=commission,
                slippage=abs(actual_entry_price - signal.entry_price),
                duration_minutes=None,
                max_favorable_excursion=0.0,
                max_adverse_excursion=0.0
            )

            return trade

        except Exception as e:
            print(f"Error simulating trade execution: {e}")
            return None

    def update_open_trade(self, trade: Trade, df: pd.DataFrame, current_idx: int):
        """
        Update open trade with current unrealized P&L and excursions
        """
        if current_idx >= len(df):
            return

        current_price = df['Close'].iloc[current_idx]

        if trade.signal.direction == SignalDirection.LONG:
            unrealized_pnl = (current_price - trade.entry_price) * trade.position_size * 50
            excursion = current_price - trade.entry_price
        else:
            unrealized_pnl = (trade.entry_price - current_price) * trade.position_size * 50
            excursion = trade.entry_price - current_price

        # Update excursions
        if excursion > trade.max_favorable_excursion:
            trade.max_favorable_excursion = excursion

        if excursion < 0 and abs(excursion) > trade.max_adverse_excursion:
            trade.max_adverse_excursion = abs(excursion)

        # Update current capital (mark-to-market)
        trade.pnl = unrealized_pnl - trade.commission

    def check_exit_conditions(
        self,
        trade: Trade,
        df: pd.DataFrame,
        current_idx: int,
        zones: List[SupplyDemandZone]
    ) -> Tuple[bool, Optional[float], str]:
        """
        Check if any exit conditions are met

        Returns: (should_exit, exit_price, exit_reason)
        """
        if current_idx >= len(df):
            return False, None, ""

        current_candle = df.iloc[current_idx]
        current_price = current_candle['Close']

        # Stop loss hit
        if trade.signal.direction == SignalDirection.LONG:
            if current_candle['Low'] <= trade.signal.stop_loss:
                return True, trade.signal.stop_loss, "Stop Loss"
        else:
            if current_candle['High'] >= trade.signal.stop_loss:
                return True, trade.signal.stop_loss, "Stop Loss"

        # Take profit hit
        if trade.signal.direction == SignalDirection.LONG:
            if current_candle['High'] >= trade.signal.take_profit:
                return True, trade.signal.take_profit, "Take Profit"
        else:
            if current_candle['Low'] <= trade.signal.take_profit:
                return True, trade.signal.take_profit, "Take Profit"

        # Zone invalidation (Elder's 30M close through zone rule)
        if current_candle.name.minute % 30 == 0:  # On 30-minute closes
            zone = trade.signal.zone

            if trade.signal.direction == SignalDirection.LONG:
                # Long from demand zone - exit if price closes below zone
                if current_price < zone.bottom:
                    return True, current_price, "Zone Invalidated"
            else:
                # Short from supply zone - exit if price closes above zone
                if current_price > zone.top:
                    return True, current_price, "Zone Invalidated"

        # Time-based exit (end of day)
        if hasattr(current_candle.name, 'time'):
            if current_candle.name.time() >= pd.Timestamp("16:00").time():
                return True, current_price, "End of Day"

        return False, None, ""

    def close_trade(
        self,
        trade: Trade,
        exit_price: float,
        exit_reason: str,
        exit_timestamp: pd.Timestamp
    ):
        """Close an open trade and calculate final P&L"""

        # Apply slippage to exit
        slippage_amount = self.slippage_ticks * self.tick_value / 100

        if trade.signal.direction == SignalDirection.LONG:
            actual_exit_price = exit_price - slippage_amount
        else:
            actual_exit_price = exit_price + slippage_amount

        trade.exit_price = actual_exit_price
        trade.exit_timestamp = exit_timestamp
        trade.exit_reason = exit_reason

        # Calculate final P&L
        if trade.signal.direction == SignalDirection.LONG:
            price_diff = actual_exit_price - trade.entry_price
        else:
            price_diff = trade.entry_price - actual_exit_price

        gross_pnl = price_diff * trade.position_size * 50  # ES multiplier
        net_pnl = gross_pnl - (trade.commission * 2)  # Entry + exit commission

        trade.pnl = net_pnl
        trade.pnl_percentage = (net_pnl / self.current_capital) * 100

        # Calculate R-multiple
        if trade.signal.direction == SignalDirection.LONG:
            risk_amount = (trade.entry_price - trade.signal.stop_loss) * trade.position_size * 50
        else:
            risk_amount = (trade.signal.stop_loss - trade.entry_price) * trade.position_size * 50

        if risk_amount > 0:
            trade.r_multiple = net_pnl / risk_amount
        else:
            trade.r_multiple = 0

        # Calculate duration
        if trade.entry_timestamp and exit_timestamp:
            duration = exit_timestamp - trade.entry_timestamp
            trade.duration_minutes = int(duration.total_seconds() / 60)

        # Update capital
        self.current_capital += net_pnl

        # Record daily P&L
        trade_date = exit_timestamp.date()
        if trade_date not in self.daily_pnl:
            self.daily_pnl[trade_date] = 0
        self.daily_pnl[trade_date] += net_pnl

        self.trades.append(trade)
        self.open_position = None

        print(f"Trade closed: {exit_reason} | P&L: ${net_pnl:.2f} | R: {trade.r_multiple:.2f}")

    def run_backtest(
        self,
        symbol: str = "ES=F",
        period: str = "6mo",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> BacktestResults:
        """
        Run complete backtest on historical data

        Args:
            symbol: ES=F (E-mini S&P 500) or NQ=F (E-mini Nasdaq)
            period: Data period or use start/end dates
            start_date: Start date (YYYY-MM-DD format)
            end_date: End date (YYYY-MM-DD format)

        Returns:
            Complete backtest results
        """
        print(f"Starting backtest for {symbol}")
        print(f"Initial Capital: ${self.initial_capital:,.2f}")
        print(f"Risk per trade: {self.risk_per_trade*100:.1f}%")
        print(f"Max daily trades: {self.max_daily_trades}")
        print("-" * 50)

        # Fetch 5-minute data
        df_5m = self.fetch_data(symbol, period, "5m")

        if df_5m.empty:
            raise ValueError("No data available for backtesting")

        # Filter by date range if specified
        if start_date and end_date:
            mask = (df_5m.index >= start_date) & (df_5m.index <= end_date)
            df_5m = df_5m.loc[mask]

        # Prepare multi-timeframe data
        timeframe_data = self.prepare_multi_timeframe_data(df_5m)

        # Detect zones across all timeframes
        zones_dict = self.detect_zones_multi_timeframe(timeframe_data)

        # Get all zones for signal generation (combine timeframes)
        all_zones = []
        for tf_zones in zones_dict.values():
            all_zones.extend(tf_zones)

        print(f"Total zones detected: {len(all_zones)}")

        # Main backtesting loop
        self.current_capital = self.initial_capital
        self.trades = []
        self.open_position = None
        self.equity_curve = []
        self.daily_pnl = {}

        # Track equity curve
        for i, (timestamp, candle) in enumerate(df_5m.iterrows()):

            # Update equity curve
            self.equity_curve.append({
                'timestamp': timestamp,
                'equity': self.current_capital,
                'price': candle['Close']
            })

            # Update open position if exists
            if self.open_position:
                self.update_open_trade(self.open_position, df_5m, i)

                # Check exit conditions
                should_exit, exit_price, exit_reason = self.check_exit_conditions(
                    self.open_position, df_5m, i, all_zones
                )

                if should_exit:
                    self.close_trade(
                        self.open_position,
                        exit_price,
                        exit_reason,
                        timestamp
                    )

            # Look for new signals (only if no open position)
            elif i > 100:  # Need some history for analysis

                # Get recent data for analysis
                lookback = min(200, i)
                recent_df = df_5m.iloc[max(0, i-lookback):i+1]

                # Generate signals
                signals = self.signal_generator.generate_signals(
                    recent_df,
                    all_zones,
                    self.current_capital,
                    timestamp
                )

                # Execute the best signal if available
                if signals:
                    best_signal = signals[0]  # Already sorted by confidence

                    # Simulate trade execution
                    trade = self.simulate_trade_execution(
                        best_signal, df_5m, timestamp
                    )

                    if trade:
                        self.open_position = trade
                        self.signal_generator.record_trade(timestamp)
                        print(f"Trade opened: {best_signal.direction.value} | "
                              f"Entry: ${trade.entry_price:.2f} | "
                              f"Quality: {best_signal.quality.value}")

            # Progress indicator
            if i % 1000 == 0:
                progress = (i / len(df_5m)) * 100
                print(f"Progress: {progress:.1f}% | "
                      f"Capital: ${self.current_capital:,.2f} | "
                      f"Trades: {len(self.trades)}")

        # Close any remaining open position
        if self.open_position:
            final_price = df_5m['Close'].iloc[-1]
            self.close_trade(
                self.open_position,
                final_price,
                "Backtest End",
                df_5m.index[-1]
            )

        # Calculate and return results
        results = self.calculate_results()

        # Save results
        self.save_results(results, symbol)

        # Generate charts
        self.generate_charts(df_5m, all_zones, symbol)

        print("\n" + "="*50)
        print("BACKTEST COMPLETED")
        print("="*50)
        print(f"Total Trades: {results.total_trades}")
        print(f"Win Rate: {results.win_rate:.1f}%")
        print(f"Profit Factor: {results.profit_factor:.2f}")
        print(f"Total P&L: ${results.total_pnl:,.2f}")
        print(f"Max Drawdown: ${results.max_drawdown:,.2f}")
        print(f"Average R-Multiple: {results.avg_r_multiple:.2f}")

        return results

    def calculate_results(self) -> BacktestResults:
        """Calculate comprehensive backtest statistics"""

        if not self.trades:
            # Return empty results if no trades
            return BacktestResults(
                total_trades=0,
                winning_trades=0,
                losing_trades=0,
                win_rate=0.0,
                total_pnl=0.0,
                total_pnl_percentage=0.0,
                gross_profit=0.0,
                gross_loss=0.0,
                profit_factor=0.0,
                max_drawdown=0.0,
                max_drawdown_percentage=0.0,
                avg_trade_pnl=0.0,
                avg_winning_trade=0.0,
                avg_losing_trade=0.0,
                avg_r_multiple=0.0,
                best_trade_r=0.0,
                worst_trade_r=0.0,
                sharpe_ratio=0.0,
                sortino_ratio=0.0,
                calmar_ratio=0.0,
                expectancy=0.0,
                trades_by_setup={},
                trades_by_month={},
                equity_curve=pd.Series(),
                drawdown_curve=pd.Series()
            )

        # Basic metrics
        total_trades = len(self.trades)
        winning_trades = len([t for t in self.trades if t.pnl > 0])
        losing_trades = len([t for t in self.trades if t.pnl < 0])
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0

        # P&L metrics
        pnls = [t.pnl for t in self.trades]
        total_pnl = sum(pnls)
        total_pnl_percentage = (total_pnl / self.initial_capital) * 100

        winning_pnls = [t.pnl for t in self.trades if t.pnl > 0]
        losing_pnls = [t.pnl for t in self.trades if t.pnl < 0]

        gross_profit = sum(winning_pnls) if winning_pnls else 0
        gross_loss = abs(sum(losing_pnls)) if losing_pnls else 0
        profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else float('inf')

        avg_trade_pnl = np.mean(pnls)
        avg_winning_trade = np.mean(winning_pnls) if winning_pnls else 0
        avg_losing_trade = np.mean(losing_pnls) if losing_pnls else 0

        # R-multiple analysis
        r_multiples = [t.r_multiple for t in self.trades if not pd.isna(t.r_multiple)]
        avg_r_multiple = np.mean(r_multiples) if r_multiples else 0
        best_trade_r = max(r_multiples) if r_multiples else 0
        worst_trade_r = min(r_multiples) if r_multiples else 0

        # Equity curve analysis
        equity_df = pd.DataFrame(self.equity_curve)
        if not equity_df.empty:
            equity_series = equity_df.set_index('timestamp')['equity']

            # Calculate drawdown
            peak = equity_series.expanding().max()
            drawdown = equity_series - peak
            max_drawdown = drawdown.min()
            max_drawdown_percentage = (max_drawdown / peak.max()) * 100 if peak.max() > 0 else 0
        else:
            equity_series = pd.Series()
            drawdown = pd.Series()
            max_drawdown = 0
            max_drawdown_percentage = 0

        # Risk-adjusted returns
        if not equity_df.empty and len(equity_df) > 1:
            returns = equity_df['equity'].pct_change().dropna()

            if len(returns) > 0:
                sharpe_ratio = np.mean(returns) / np.std(returns) * np.sqrt(252) if np.std(returns) > 0 else 0
                negative_returns = returns[returns < 0]
                sortino_ratio = np.mean(returns) / np.std(negative_returns) * np.sqrt(252) if len(negative_returns) > 0 and np.std(negative_returns) > 0 else 0
                calmar_ratio = total_pnl_percentage / abs(max_drawdown_percentage) if max_drawdown_percentage != 0 else 0
            else:
                sharpe_ratio = sortino_ratio = calmar_ratio = 0
        else:
            sharpe_ratio = sortino_ratio = calmar_ratio = 0

        # Expectancy
        expectancy = (win_rate/100 * avg_winning_trade) + ((100-win_rate)/100 * avg_losing_trade)

        # Trade distribution analysis
        trades_by_setup = {}
        trades_by_month = {}

        for trade in self.trades:
            # By setup quality
            setup = trade.signal.quality.value
            trades_by_setup[setup] = trades_by_setup.get(setup, 0) + 1

            # By month
            if trade.entry_timestamp:
                month = trade.entry_timestamp.strftime('%Y-%m')
                trades_by_month[month] = trades_by_month.get(month, 0) + 1

        return BacktestResults(
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            win_rate=win_rate,
            total_pnl=total_pnl,
            total_pnl_percentage=total_pnl_percentage,
            gross_profit=gross_profit,
            gross_loss=gross_loss,
            profit_factor=profit_factor,
            max_drawdown=max_drawdown,
            max_drawdown_percentage=max_drawdown_percentage,
            avg_trade_pnl=avg_trade_pnl,
            avg_winning_trade=avg_winning_trade,
            avg_losing_trade=avg_losing_trade,
            avg_r_multiple=avg_r_multiple,
            best_trade_r=best_trade_r,
            worst_trade_r=worst_trade_r,
            sharpe_ratio=sharpe_ratio,
            sortino_ratio=sortino_ratio,
            calmar_ratio=calmar_ratio,
            expectancy=expectancy,
            trades_by_setup=trades_by_setup,
            trades_by_month=trades_by_month,
            equity_curve=equity_series,
            drawdown_curve=drawdown
        )

    def save_results(self, results: BacktestResults, symbol: str):
        """Save backtest results to files"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Save results JSON
        results_dict = asdict(results)

        # Convert pandas Series to lists for JSON serialization
        if hasattr(results.equity_curve, 'to_list'):
            results_dict['equity_curve'] = results.equity_curve.to_list()
        if hasattr(results.drawdown_curve, 'to_list'):
            results_dict['drawdown_curve'] = results.drawdown_curve.to_list()

        results_file = os.path.join(self.results_dir, f"backtest_results_{symbol}_{timestamp}.json")
        with open(results_file, 'w') as f:
            json.dump(results_dict, f, indent=2, default=str)

        # Save trade log CSV
        if self.trades:
            trades_data = []
            for trade in self.trades:
                trade_dict = asdict(trade)
                # Remove the signal object for CSV export
                trade_dict.pop('signal', None)
                trades_data.append(trade_dict)

            trades_df = pd.DataFrame(trades_data)
            trades_file = os.path.join(self.results_dir, f"trade_log_{symbol}_{timestamp}.csv")
            trades_df.to_csv(trades_file, index=False)

        print(f"Results saved to {results_file}")

    def generate_charts(
        self,
        df: pd.DataFrame,
        zones: List[SupplyDemandZone],
        symbol: str
    ):
        """Generate backtest visualization charts"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # 1. Equity curve chart
        if self.equity_curve:
            equity_df = pd.DataFrame(self.equity_curve)

            plt.figure(figsize=(12, 8), facecolor='black')
            plt.plot(equity_df['timestamp'], equity_df['equity'], 'lime', linewidth=2)
            plt.title(f'Equity Curve - {symbol}', color='white', fontsize=16)
            plt.xlabel('Date', color='white')
            plt.ylabel('Account Value ($)', color='white')
            plt.grid(True, alpha=0.3)

            # Add trade markers
            for trade in self.trades:
                color = 'green' if trade.pnl > 0 else 'red'
                plt.scatter(trade.exit_timestamp,
                          self.initial_capital + sum(t.pnl for t in self.trades
                                                   if t.exit_timestamp <= trade.exit_timestamp),
                          color=color, s=30, alpha=0.7)

            plt.tight_layout()
            equity_file = os.path.join(self.results_dir, f"equity_curve_{symbol}_{timestamp}.png")
            plt.savefig(equity_file, facecolor='black', dpi=100)
            plt.close()

        # 2. Sample trade chart (if trades exist)
        if self.trades:
            # Find a good winning trade to showcase
            winning_trades = [t for t in self.trades if t.pnl > 0]
            if winning_trades:
                sample_trade = max(winning_trades, key=lambda t: t.r_multiple)

                # Get data around the trade
                trade_start = sample_trade.entry_timestamp - timedelta(hours=2)
                trade_end = sample_trade.exit_timestamp + timedelta(hours=1)

                trade_mask = (df.index >= trade_start) & (df.index <= trade_end)
                trade_df = df.loc[trade_mask]

                if not trade_df.empty:
                    fig = self.chart_generator.create_trade_review_chart(
                        trade_df,
                        sample_trade,
                        sample_trade.exit_price,
                        sample_trade.exit_timestamp,
                        sample_trade.pnl,
                        title=f"Best Trade Example - {symbol}"
                    )

                    trade_chart_file = os.path.join(
                        self.results_dir,
                        f"sample_trade_{symbol}_{timestamp}.png"
                    )
                    fig.savefig(trade_chart_file, facecolor='black', dpi=100)
                    plt.close()

        print(f"Charts saved to {self.results_dir}/")


def main():
    """
    Run the backtester with Elder Santis's complete methodology
    """
    # Initialize backtester
    backtester = ElderBacktester(
        initial_capital=50000.0,
        risk_per_trade=0.02,  # 2% risk per trade
        max_daily_trades=1,   # One & Done
        results_dir="results"
    )

    # Run backtest on ES (E-mini S&P 500)
    print("="*60)
    print("ELDER SANTIS SUPPLY & DEMAND BACKTESTER")
    print("="*60)

    try:
        results = backtester.run_backtest(
            symbol="ES=F",
            period="6mo"  # Test on 6 months of data
        )

        print("\n" + "="*60)
        print("BACKTEST SUMMARY")
        print("="*60)
        print(f"Strategy: Elder's One & Done S&D")
        print(f"Symbol: ES=F (E-mini S&P 500)")
        print(f"Period: 6 months")
        print(f"Initial Capital: ${backtester.initial_capital:,.2f}")
        print("-"*40)
        print(f"Total Trades: {results.total_trades}")
        print(f"Win Rate: {results.win_rate:.1f}%")
        print(f"Profit Factor: {results.profit_factor:.2f}")
        print(f"Average R-Multiple: {results.avg_r_multiple:.2f}")
        print("-"*40)
        print(f"Total P&L: ${results.total_pnl:,.2f}")
        print(f"Return: {results.total_pnl_percentage:.1f}%")
        print(f"Max Drawdown: ${results.max_drawdown:,.2f} ({results.max_drawdown_percentage:.1f}%)")
        print(f"Sharpe Ratio: {results.sharpe_ratio:.2f}")
        print("="*60)

    except Exception as e:
        print(f"Backtest failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()