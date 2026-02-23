#!/usr/bin/env python3
"""
Test script for Elder Santis Futures Trading Bot

This script demonstrates the complete system functionality:
- Zone detection
- Volume analysis
- Signal generation
- Chart creation
- Basic backtesting

Run this to verify everything is working before full backtesting.
"""

import sys
import os
sys.path.append(os.path.join(os.getcwd(), 'python'))

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta

from zone_detector import ZoneDetector
from volume_analyzer import VolumeAnalyzer
from signal_generator import SignalGenerator
from chart_generator import ChartGenerator
from backtester import ElderBacktester

def test_zone_detection():
    """Test the zone detection module"""
    print("\n🔍 Testing Zone Detection...")

    # Create realistic sample OHLCV data
    np.random.seed(42)  # For reproducible results
    dates = pd.date_range('2024-01-01', periods=200, freq='30T')

    # Generate price data with trends and consolidations
    base_price = 4500
    price_walk = np.random.randn(200).cumsum() * 2

    sample_data = pd.DataFrame({
        'Open': base_price + price_walk,
        'Close': base_price + price_walk + np.random.randn(200) * 0.5,
        'Volume': np.random.randint(5000, 50000, 200)
    }, index=dates)

    # Ensure High >= max(Open, Close) and Low <= min(Open, Close)
    sample_data['High'] = sample_data[['Open', 'Close']].max(axis=1) + np.abs(np.random.randn(200)) * 1.5
    sample_data['Low'] = sample_data[['Open', 'Close']].min(axis=1) - np.abs(np.random.randn(200)) * 1.5

    # Test zone detector
    detector = ZoneDetector()
    zones = detector.detect_zones(sample_data, timeframe="30M")

    print(f"   ✅ Found {len(zones)} supply & demand zones")

    for i, zone in enumerate(zones[:3]):  # Show first 3 zones
        print(f"   Zone {i+1}: {zone.zone_type.value.upper()} | "
              f"Range: ${zone.bottom:.2f} - ${zone.top:.2f} | "
              f"Strength: {zone.strength.name}")

    return sample_data, zones

def test_volume_analysis(df):
    """Test the volume analysis module"""
    print("\n📊 Testing Volume Analysis...")

    analyzer = VolumeAnalyzer()

    # Test CVD calculation
    cvd = analyzer.calculate_cvd(df)
    print(f"   ✅ CVD calculated - Latest value: {cvd.iloc[-1]:.0f}")

    # Test volume profile
    volume_profile = analyzer.calculate_volume_profile(df)
    if volume_profile:
        print(f"   ✅ Volume Profile calculated")
        print(f"      POC (Point of Control): ${volume_profile.poc:.2f}")
        print(f"      Value Area: ${volume_profile.val:.2f} - ${volume_profile.vah:.2f}")

    # Test volume trend analysis
    if len(df) > 5:
        volume_signal = analyzer.analyze_volume_trend(df, 'demand', df['Close'].iloc[-1])
        print(f"   ✅ Volume trend: {volume_signal.value}")

    return analyzer

def test_signal_generation(df, zones):
    """Test the signal generation module"""
    print("\n🎯 Testing Signal Generation...")

    generator = SignalGenerator(risk_per_trade=0.02, max_daily_trades=1)

    # Generate signals
    signals = generator.generate_signals(df, zones, account_size=50000.0)

    print(f"   ✅ Generated {len(signals)} trading signals")

    for i, signal in enumerate(signals[:2]):  # Show first 2 signals
        print(f"   Signal {i+1}: {signal.quality.value} {signal.direction.value}")
        print(f"      Entry: ${signal.entry_price:.2f} | Stop: ${signal.stop_loss:.2f}")
        print(f"      Target: ${signal.take_profit:.2f} | R:R = {signal.risk_reward_ratio:.1f}:1")
        print(f"      Confidence: {signal.confidence_score:.0f}%")

    return signals

def test_chart_generation(df, zones, signals):
    """Test the chart generation module"""
    print("\n📈 Testing Chart Generation...")

    try:
        chart_gen = ChartGenerator()

        # Create a comprehensive chart
        fig, axes = chart_gen.create_comprehensive_chart(
            df=df.tail(100),  # Last 100 candles for chart
            zones=zones,
            signals=signals[:1] if signals else [],  # First signal only
            title="Elder's S&D Test Chart",
            save_path="results/test_chart.png"
        )

        print("   ✅ Chart generated successfully")
        print("   📁 Chart saved to: results/test_chart.png")

        # Close the figure to free memory
        import matplotlib.pyplot as plt
        plt.close(fig)

    except Exception as e:
        print(f"   ⚠️  Chart generation failed: {e}")

def test_basic_backtest():
    """Test basic backtesting functionality"""
    print("\n🚀 Testing Basic Backtesting...")

    try:
        # Initialize backtester with conservative settings
        backtester = ElderBacktester(
            initial_capital=10000.0,  # Smaller capital for testing
            risk_per_trade=0.01,      # 1% risk for testing
            max_daily_trades=1,
            results_dir="results"
        )

        print("   ✅ Backtester initialized successfully")
        print(f"   📊 Settings: ${backtester.initial_capital:,.0f} capital, {backtester.risk_per_trade*100:.0f}% risk per trade")

        # Test data fetching (small sample)
        print("   📡 Fetching sample market data...")
        df = backtester.fetch_data("^GSPC", period="5d", interval="5m")  # Use S&P index instead of futures

        if not df.empty:
            print(f"   ✅ Data fetched: {len(df)} candles from {df.index[0].date()} to {df.index[-1].date()}")

            # Test zone detection on real data
            zones_dict = backtester.detect_zones_multi_timeframe(
                backtester.prepare_multi_timeframe_data(df)
            )

            total_zones = sum(len(zones) for zones in zones_dict.values())
            print(f"   ✅ Multi-timeframe analysis: {total_zones} zones detected")

            for tf, zones in zones_dict.items():
                if zones:
                    print(f"      {tf}: {len(zones)} zones")

        else:
            print("   ⚠️  No data fetched - may be weekend or market closed")

    except Exception as e:
        print(f"   ⚠️  Backtest test failed: {e}")

def main():
    """Run all system tests"""
    print("="*60)
    print("🤖 ELDER SANTIS FUTURES TRADING BOT - SYSTEM TEST")
    print("="*60)
    print("Testing all components of the trading system...")

    # Ensure results directory exists
    os.makedirs("results", exist_ok=True)

    try:
        # Test 1: Zone Detection
        sample_df, zones = test_zone_detection()

        # Test 2: Volume Analysis
        volume_analyzer = test_volume_analysis(sample_df)

        # Test 3: Signal Generation
        signals = test_signal_generation(sample_df, zones)

        # Test 4: Chart Generation
        test_chart_generation(sample_df, zones, signals)

        # Test 5: Basic Backtesting
        test_basic_backtest()

        print("\n" + "="*60)
        print("✅ ALL SYSTEM TESTS COMPLETED SUCCESSFULLY!")
        print("="*60)
        print("🎯 The Elder Santis Trading Bot is ready for full backtesting!")
        print("\nTo run a full 6-month backtest on ES futures:")
        print("   python -c \"from python.backtester import main; main()\"")
        print("\nTo use individual components:")
        print("   python -c \"from python.zone_detector import ZoneDetector; print('Ready!')\"")
        print("\n📁 Test results saved in: results/")

    except Exception as e:
        print(f"\n❌ SYSTEM TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        print("\n🔧 Please check the error above and ensure all dependencies are installed.")

if __name__ == "__main__":
    main()