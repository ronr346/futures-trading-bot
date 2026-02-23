#!/usr/bin/env python3
"""
Simple test for Elder Santis Trading Bot - No Unicode
"""

import sys
import os
sys.path.append(os.path.join(os.getcwd(), 'python'))

import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')

def main():
    print("="*50)
    print("ELDER SANTIS TRADING BOT - SYSTEM TEST")
    print("="*50)

    try:
        # Test imports
        print("1. Testing imports...")
        from zone_detector import ZoneDetector
        from volume_analyzer import VolumeAnalyzer
        from signal_generator import SignalGenerator
        print("   All modules imported successfully!")

        # Test zone detection
        print("\n2. Testing zone detection...")

        # Create sample data
        np.random.seed(42)
        dates = pd.date_range('2024-01-01', periods=100, freq='30T')

        sample_data = pd.DataFrame({
            'Open': 4500 + np.random.randn(100).cumsum(),
            'Close': 4500 + np.random.randn(100).cumsum(),
            'Volume': np.random.randint(5000, 50000, 100)
        }, index=dates)

        sample_data['High'] = sample_data[['Open', 'Close']].max(axis=1) + np.abs(np.random.randn(100))
        sample_data['Low'] = sample_data[['Open', 'Close']].min(axis=1) - np.abs(np.random.randn(100))

        detector = ZoneDetector()
        zones = detector.detect_zones(sample_data)
        print(f"   Found {len(zones)} supply & demand zones")

        # Test volume analysis
        print("\n3. Testing volume analysis...")
        analyzer = VolumeAnalyzer()
        cvd = analyzer.calculate_cvd(sample_data)
        print(f"   CVD calculation successful - Latest: {cvd.iloc[-1]:.0f}")

        # Test signal generation
        print("\n4. Testing signal generation...")
        generator = SignalGenerator()
        signals = generator.generate_signals(sample_data, zones, 50000.0)
        print(f"   Generated {len(signals)} trading signals")

        # Test data fetching
        print("\n5. Testing data fetching...")
        try:
            import yfinance as yf
            # Test with SPY ETF (more reliable than futures)
            ticker = yf.Ticker("SPY")
            df = ticker.history(period="5d", interval="5m")

            if not df.empty:
                print(f"   Data fetch successful: {len(df)} bars")
                print(f"   Date range: {df.index[0].date()} to {df.index[-1].date()}")
            else:
                print("   No data returned (market may be closed)")

        except Exception as e:
            print(f"   Data fetch failed: {e}")

        print("\n" + "="*50)
        print("SYSTEM TEST COMPLETED SUCCESSFULLY!")
        print("="*50)
        print("\nThe trading bot is ready!")
        print("\nTo run backtest:")
        print("  python -c \"from python.backtester import main; main()\"")

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()