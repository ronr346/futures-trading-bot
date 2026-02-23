"""
Chart Generator for Elder Santis Supply & Demand Strategy

This module generates annotated charts showing:
- Supply & Demand zones (colored rectangles)
- Entry/exit arrows and levels
- Stop loss and target levels
- VWAP line
- Volume analysis
- Trade result annotations
- Zone strength indicators

Uses mplfinance with dark theme for professional appearance.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import Rectangle, FancyBboxPatch
import mplfinance as mpf
from typing import List, Dict, Optional, Tuple
import warnings
from datetime import datetime
import os

try:
    from .zone_detector import SupplyDemandZone, ZoneType, ZoneStrength
    from .signal_generator import TradingSignal, SignalDirection, SetupQuality
    from .volume_analyzer import VolumeProfile
except ImportError:
    from zone_detector import SupplyDemandZone, ZoneType, ZoneStrength
    from signal_generator import TradingSignal, SignalDirection, SetupQuality
    from volume_analyzer import VolumeProfile

warnings.filterwarnings('ignore')

class ChartGenerator:
    """
    Generates professional trading charts with Elder's methodology annotations

    Features:
    - Dark theme for reduced eye strain
    - Supply/Demand zones with strength color coding
    - Entry/exit points with arrows
    - VWAP and key levels
    - Volume analysis overlay
    - Trade performance annotations
    """

    def __init__(
        self,
        style: str = "charles",  # Dark theme for mplfinance
        chart_width: int = 16,
        chart_height: int = 10,
        dpi: int = 100
    ):
        self.style = style
        self.chart_width = chart_width
        self.chart_height = chart_height
        self.dpi = dpi

        # Color scheme for zones based on strength
        self.zone_colors = {
            ZoneStrength.VERY_STRONG: '#FF4444',  # Bright red/green for 4H zones
            ZoneStrength.STRONG: '#FF6666',       # Medium red/green for 2H zones
            ZoneStrength.MEDIUM: '#FF8888',       # Light red/green for 1H zones
            ZoneStrength.WEAK: '#FFAAAA'          # Very light red/green for 30M zones
        }

        # Setup matplotlib for dark theme
        plt.style.use('dark_background')

    def calculate_vwap(self, df: pd.DataFrame) -> pd.Series:
        """Calculate VWAP (Volume Weighted Average Price)"""
        typical_price = (df['High'] + df['Low'] + df['Close']) / 3
        vwap = (typical_price * df['Volume']).cumsum() / df['Volume'].cumsum()
        return vwap

    def prepare_chart_data(
        self,
        df: pd.DataFrame,
        zones: List[SupplyDemandZone],
        signals: List[TradingSignal] = None,
        show_last_n_candles: int = 100
    ) -> Tuple[pd.DataFrame, Dict]:
        """
        Prepare data for chart plotting

        Args:
            df: OHLCV DataFrame
            zones: List of S&D zones to plot
            signals: Trading signals to annotate
            show_last_n_candles: Number of recent candles to display

        Returns:
            Tuple of (chart_df, plot_elements)
        """
        # Get recent data for chart
        chart_df = df.tail(show_last_n_candles).copy()

        # Calculate indicators
        chart_df['VWAP'] = self.calculate_vwap(chart_df)

        # Calculate volume moving average for reference
        chart_df['Volume_MA'] = chart_df['Volume'].rolling(20).mean()

        # Prepare plot elements
        plot_elements = {
            'addplot': [],
            'zones': [],
            'signals': [],
            'annotations': []
        }

        # Add VWAP line
        vwap_plot = mpf.make_addplot(
            chart_df['VWAP'],
            color='yellow',
            width=2,
            linestyle='-',
            alpha=0.8,
            secondary_y=False
        )
        plot_elements['addplot'].append(vwap_plot)

        # Add volume MA reference line
        vol_ma_plot = mpf.make_addplot(
            chart_df['Volume_MA'],
            panel=1,
            color='orange',
            width=1,
            linestyle='--',
            alpha=0.6,
            secondary_y=False
        )
        plot_elements['addplot'].append(vol_ma_plot)

        # Process zones that are relevant to the chart timeframe
        chart_start = chart_df.index[0]
        chart_end = chart_df.index[-1]

        for zone in zones:
            if zone.valid:
                # Add zone to plot elements for custom drawing
                plot_elements['zones'].append({
                    'zone': zone,
                    'start_time': chart_start,
                    'end_time': chart_end
                })

        # Process signals
        if signals:
            for signal in signals:
                if chart_start <= signal.timestamp <= chart_end:
                    plot_elements['signals'].append(signal)

        return chart_df, plot_elements

    def create_base_chart(
        self,
        df: pd.DataFrame,
        plot_elements: Dict,
        title: str = "Elder's S&D Strategy"
    ) -> Tuple[plt.Figure, plt.Axes]:
        """
        Create the base candlestick chart with volume

        Returns:
            Tuple of (figure, axes)
        """
        # Create the plot
        fig, axes = mpf.plot(
            df,
            type='candle',
            addplot=plot_elements['addplot'],
            volume=True,
            style=self.style,
            figsize=(self.chart_width, self.chart_height),
            title=title,
            ylabel='Price',
            ylabel_lower='Volume',
            returnfig=True,
            tight_layout=True
        )

        return fig, axes

    def draw_zones(
        self,
        ax: plt.Axes,
        df: pd.DataFrame,
        zones_data: List[Dict]
    ):
        """
        Draw Supply & Demand zones on the chart

        Args:
            ax: Price axis
            df: Chart DataFrame
            zones_data: List of zone dictionaries
        """
        for zone_data in zones_data:
            zone = zone_data['zone']

            # Determine zone color based on type and strength
            base_color = self.zone_colors[zone.strength]

            if zone.zone_type == ZoneType.SUPPLY:
                zone_color = base_color.replace('FF', 'FF')  # Red for supply
                alpha = 0.3
            else:  # DEMAND
                zone_color = base_color.replace('FF', '44FF44')  # Green for demand
                alpha = 0.3

            # Convert time range to plot coordinates
            x_start = 0  # Start of visible chart
            x_end = len(df) - 1  # End of visible chart

            # Draw zone rectangle
            zone_rect = Rectangle(
                (x_start, zone.bottom),
                x_end - x_start,
                zone.height,
                linewidth=1,
                edgecolor=zone_color,
                facecolor=zone_color,
                alpha=alpha,
                zorder=1
            )
            ax.add_patch(zone_rect)

            # Add zone label
            label_text = f"{zone.zone_type.value.upper()}\n{zone.timeframe}\n{zone.strength.name}"

            # Position label at the right edge of the zone
            label_x = x_end - 5
            label_y = zone.mid_point

            ax.text(
                label_x, label_y,
                label_text,
                fontsize=8,
                color='white',
                fontweight='bold',
                ha='right',
                va='center',
                bbox=dict(
                    boxstyle="round,pad=0.3",
                    facecolor=zone_color,
                    alpha=0.8,
                    edgecolor='white'
                ),
                zorder=5
            )

            # Draw zone boundary lines
            ax.axhline(y=zone.top, color=zone_color, linestyle='--', alpha=0.8, zorder=2)
            ax.axhline(y=zone.bottom, color=zone_color, linestyle='--', alpha=0.8, zorder=2)

            # Add test count indicator if zone has been tested
            if zone.test_count > 0:
                test_text = f"Tests: {zone.test_count}"
                ax.text(
                    x_start + 2, zone.top - zone.height * 0.1,
                    test_text,
                    fontsize=7,
                    color='white',
                    alpha=0.9
                )

    def draw_signals(
        self,
        ax: plt.Axes,
        df: pd.DataFrame,
        signals: List[TradingSignal]
    ):
        """
        Draw trading signals (entry/exit points) on the chart

        Args:
            ax: Price axis
            df: Chart DataFrame
            signals: List of trading signals
        """
        for signal in signals:
            try:
                # Find the closest timestamp in the chart data
                signal_time = signal.timestamp
                closest_idx = df.index.get_indexer([signal_time], method='nearest')[0]

                if closest_idx < 0 or closest_idx >= len(df):
                    continue

                # Entry arrow
                entry_y = signal.entry_price
                arrow_color = 'lime' if signal.direction == SignalDirection.LONG else 'red'
                arrow_style = '↑' if signal.direction == SignalDirection.LONG else '↓'

                ax.annotate(
                    arrow_style,
                    xy=(closest_idx, entry_y),
                    xytext=(closest_idx, entry_y + (entry_y * 0.01 * (1 if signal.direction == SignalDirection.LONG else -1))),
                    fontsize=20,
                    color=arrow_color,
                    ha='center',
                    va='bottom' if signal.direction == SignalDirection.LONG else 'top',
                    fontweight='bold',
                    zorder=10
                )

                # Entry level line
                ax.axhline(
                    y=signal.entry_price,
                    color=arrow_color,
                    linestyle='-',
                    alpha=0.8,
                    linewidth=2,
                    zorder=3
                )

                # Stop loss level
                sl_color = 'orangered'
                ax.axhline(
                    y=signal.stop_loss,
                    color=sl_color,
                    linestyle=':',
                    alpha=0.8,
                    linewidth=1,
                    zorder=3
                )

                # Take profit level
                tp_color = 'lightgreen'
                ax.axhline(
                    y=signal.take_profit,
                    color=tp_color,
                    linestyle=':',
                    alpha=0.8,
                    linewidth=1,
                    zorder=3
                )

                # Signal quality badge
                quality_colors = {
                    SetupQuality.A_PLUS: '#00FF00',
                    SetupQuality.A_MINUS: '#90EE90',
                    SetupQuality.B_PLUS: '#FFD700',
                    SetupQuality.B_MINUS: '#FFA500',
                    SetupQuality.C: '#FF6B6B'
                }

                quality_color = quality_colors.get(signal.quality, '#FFFFFF')

                # Position signal info box
                info_x = closest_idx + 2
                info_y = signal.entry_price

                signal_info = (
                    f"{signal.quality.value}\n"
                    f"{signal.confidence_score:.0f}%\n"
                    f"R:R {signal.risk_reward_ratio:.1f}:1"
                )

                ax.text(
                    info_x, info_y,
                    signal_info,
                    fontsize=9,
                    color='white',
                    fontweight='bold',
                    ha='left',
                    va='center',
                    bbox=dict(
                        boxstyle="round,pad=0.5",
                        facecolor=quality_color,
                        alpha=0.8,
                        edgecolor='white'
                    ),
                    zorder=6
                )

                # Level labels
                level_offset = len(df) * 0.02

                ax.text(
                    len(df) - level_offset, signal.entry_price,
                    f"Entry: {signal.entry_price:.2f}",
                    fontsize=8, color=arrow_color, fontweight='bold',
                    ha='right', va='center'
                )

                ax.text(
                    len(df) - level_offset, signal.stop_loss,
                    f"Stop: {signal.stop_loss:.2f}",
                    fontsize=8, color=sl_color, fontweight='bold',
                    ha='right', va='center'
                )

                ax.text(
                    len(df) - level_offset, signal.take_profit,
                    f"Target: {signal.take_profit:.2f}",
                    fontsize=8, color=tp_color, fontweight='bold',
                    ha='right', va='center'
                )

            except Exception as e:
                print(f"Error drawing signal: {e}")
                continue

    def add_volume_analysis(
        self,
        ax_volume: plt.Axes,
        df: pd.DataFrame,
        volume_profile: Optional[VolumeProfile] = None
    ):
        """
        Add volume analysis annotations to the volume panel

        Args:
            ax_volume: Volume axis
            df: Chart DataFrame
            volume_profile: Volume profile data if available
        """
        # Color volume bars based on price action
        volume_colors = []
        for i in range(len(df)):
            if df['Close'].iloc[i] > df['Open'].iloc[i]:
                volume_colors.append('green')
            elif df['Close'].iloc[i] < df['Open'].iloc[i]:
                volume_colors.append('red')
            else:
                volume_colors.append('gray')

        # Volume moving average (already added in prepare_chart_data)
        vol_ma = df['Volume'].rolling(20).mean()

        # Highlight volume spikes
        vol_spike_threshold = vol_ma * 1.5
        spike_indices = df[df['Volume'] > vol_spike_threshold].index

        for idx in spike_indices:
            idx_pos = df.index.get_loc(idx)
            ax_volume.annotate(
                '!',
                xy=(idx_pos, df.loc[idx, 'Volume']),
                xytext=(idx_pos, df.loc[idx, 'Volume'] * 1.2),
                fontsize=12,
                color='yellow',
                ha='center',
                fontweight='bold'
            )

    def add_chart_legend(self, ax: plt.Axes):
        """Add comprehensive legend to the chart"""
        legend_elements = [
            plt.Line2D([0], [0], color='yellow', lw=2, label='VWAP'),
            plt.Line2D([0], [0], color='lime', lw=2, label='Long Entry'),
            plt.Line2D([0], [0], color='red', lw=2, label='Short Entry'),
            plt.Line2D([0], [0], color='orangered', lw=1, linestyle=':', label='Stop Loss'),
            plt.Line2D([0], [0], color='lightgreen', lw=1, linestyle=':', label='Take Profit'),
            patches.Patch(color='#44FF44', alpha=0.3, label='Demand Zone'),
            patches.Patch(color='#FF4444', alpha=0.3, label='Supply Zone')
        ]

        ax.legend(
            handles=legend_elements,
            loc='upper left',
            frameon=True,
            fancybox=True,
            shadow=True,
            fontsize=9
        )

    def create_comprehensive_chart(
        self,
        df: pd.DataFrame,
        zones: List[SupplyDemandZone],
        signals: List[TradingSignal] = None,
        volume_profile: Optional[VolumeProfile] = None,
        title: str = "Elder's Supply & Demand Analysis",
        save_path: Optional[str] = None
    ) -> Tuple[plt.Figure, List[plt.Axes]]:
        """
        Create a comprehensive chart with all elements

        Args:
            df: OHLCV DataFrame
            zones: Supply & Demand zones
            signals: Trading signals
            volume_profile: Volume profile data
            title: Chart title
            save_path: Path to save the chart

        Returns:
            Tuple of (figure, axes_list)
        """
        # Prepare chart data
        chart_df, plot_elements = self.prepare_chart_data(df, zones, signals)

        # Create base chart
        fig, axes = self.create_base_chart(chart_df, plot_elements, title)

        # Get the price and volume axes
        ax_price = axes[0]  # Main price chart
        ax_volume = axes[1] if len(axes) > 1 else None  # Volume panel

        # Draw zones
        if plot_elements['zones']:
            self.draw_zones(ax_price, chart_df, plot_elements['zones'])

        # Draw signals
        if plot_elements['signals']:
            self.draw_signals(ax_price, chart_df, plot_elements['signals'])

        # Add volume analysis
        if ax_volume:
            self.add_volume_analysis(ax_volume, chart_df, volume_profile)

        # Add legend
        self.add_chart_legend(ax_price)

        # Add timestamp and metadata
        timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        fig.text(
            0.99, 0.01,
            f"Generated: {timestamp_str} | Elder's S&D Methodology",
            ha='right', va='bottom',
            fontsize=8, color='gray'
        )

        # Add performance summary if signals exist
        if signals:
            self.add_performance_summary(fig, signals)

        # Save chart if path provided
        if save_path:
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            fig.savefig(
                save_path,
                dpi=self.dpi,
                bbox_inches='tight',
                facecolor='black',
                edgecolor='none'
            )
            print(f"Chart saved to: {save_path}")

        return fig, axes

    def add_performance_summary(self, fig: plt.Figure, signals: List[TradingSignal]):
        """Add performance summary box to the chart"""
        if not signals:
            return

        # Calculate summary statistics
        total_signals = len(signals)
        a_plus_signals = len([s for s in signals if s.quality == SetupQuality.A_PLUS])
        avg_confidence = np.mean([s.confidence_score for s in signals])
        avg_rr = np.mean([s.risk_reward_ratio for s in signals])

        summary_text = (
            f"Signal Summary:\n"
            f"Total Signals: {total_signals}\n"
            f"A+ Setups: {a_plus_signals}\n"
            f"Avg Confidence: {avg_confidence:.1f}%\n"
            f"Avg R:R: {avg_rr:.1f}:1"
        )

        # Position summary box
        fig.text(
            0.02, 0.98,
            summary_text,
            ha='left', va='top',
            fontsize=10,
            color='white',
            bbox=dict(
                boxstyle="round,pad=0.5",
                facecolor='#333333',
                alpha=0.8,
                edgecolor='white'
            ),
            transform=fig.transFigure
        )

    def create_trade_review_chart(
        self,
        df: pd.DataFrame,
        executed_signal: TradingSignal,
        exit_price: float,
        exit_timestamp: pd.Timestamp,
        pnl: float,
        title: str = "Trade Review"
    ) -> plt.Figure:
        """
        Create a chart for reviewing an executed trade

        Shows the complete trade lifecycle from entry to exit
        """
        # Extend the chart to show more context around the trade
        trade_idx = df.index.get_indexer([executed_signal.timestamp], method='nearest')[0]
        exit_idx = df.index.get_indexer([exit_timestamp], method='nearest')[0]

        # Show data from 50 candles before entry to 20 candles after exit
        start_idx = max(0, trade_idx - 50)
        end_idx = min(len(df), exit_idx + 20)

        review_df = df.iloc[start_idx:end_idx].copy()

        # Create chart with the executed signal
        fig, axes = self.create_comprehensive_chart(
            review_df,
            [executed_signal.zone],
            [executed_signal],
            title=f"{title} - P&L: ${pnl:.2f}"
        )

        ax_price = axes[0]

        # Add exit point
        exit_color = 'lime' if pnl > 0 else 'red'
        exit_idx_chart = review_df.index.get_loc(exit_timestamp)

        ax_price.scatter(
            exit_idx_chart, exit_price,
            color=exit_color, s=100, marker='X',
            zorder=10, label=f'Exit: ${exit_price:.2f}'
        )

        # Add P&L annotation
        pnl_color = 'lime' if pnl > 0 else 'red'
        pnl_text = f"P&L: ${pnl:.2f}\n{'✓' if pnl > 0 else '✗'}"

        ax_price.text(
            exit_idx_chart + 2, exit_price,
            pnl_text,
            fontsize=12,
            color=pnl_color,
            fontweight='bold',
            ha='left', va='center',
            bbox=dict(
                boxstyle="round,pad=0.5",
                facecolor=pnl_color,
                alpha=0.2,
                edgecolor=pnl_color
            )
        )

        return fig

    def create_multi_timeframe_chart(
        self,
        data_dict: Dict[str, pd.DataFrame],
        zones_dict: Dict[str, List[SupplyDemandZone]],
        title: str = "Multi-Timeframe Analysis"
    ) -> plt.Figure:
        """
        Create a multi-panel chart showing different timeframes

        Args:
            data_dict: Dictionary of {timeframe: DataFrame}
            zones_dict: Dictionary of {timeframe: [zones]}
            title: Chart title

        Returns:
            Multi-panel figure
        """
        timeframes = list(data_dict.keys())
        n_panels = len(timeframes)

        fig, axes = plt.subplots(
            n_panels, 1,
            figsize=(self.chart_width, self.chart_height * n_panels),
            facecolor='black'
        )

        if n_panels == 1:
            axes = [axes]

        for i, tf in enumerate(timeframes):
            df = data_dict[tf]
            zones = zones_dict.get(tf, [])

            # Create individual chart for this timeframe
            chart_df, plot_elements = self.prepare_chart_data(
                df, zones, show_last_n_candles=100
            )

            # Plot candlesticks on this axis
            mpf.plot(
                chart_df,
                type='candle',
                ax=axes[i],
                volume=False,
                addplot=plot_elements['addplot'],
                style=self.style,
                ylabel=f'{tf} Price'
            )

            # Draw zones for this timeframe
            if plot_elements['zones']:
                self.draw_zones(axes[i], chart_df, plot_elements['zones'])

            axes[i].set_title(f"{tf} - Elder's S&D Analysis", color='white')

        plt.tight_layout()
        return fig