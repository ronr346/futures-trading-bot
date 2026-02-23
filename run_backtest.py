"""Quick backtest runner"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
sys.stdout.reconfigure(line_buffering=True)

print("Importing...", flush=True)
from python.backtester import ElderBacktester

print("Starting backtest...", flush=True)
bt = ElderBacktester(initial_capital=50000.0, risk_per_trade=0.02, max_daily_trades=1)

try:
    results = bt.run_backtest(symbol='ES=F', period='60d')
    print("\n" + "="*60)
    print("FINAL RESULTS")
    print("="*60)
    print(f"Total Trades: {results.total_trades}")
    print(f"Winning: {results.winning_trades}")
    print(f"Losing: {results.losing_trades}")
    print(f"Win Rate: {results.win_rate:.1f}%")
    print(f"Profit Factor: {results.profit_factor:.2f}")
    print(f"Total PnL: ${results.total_pnl:.2f}")
    print(f"Max Drawdown: ${results.max_drawdown:.2f}")
    print(f"Avg R-Multiple: {results.avg_r_multiple:.2f}")
except Exception as e:
    import traceback
    print(f"ERROR: {e}", flush=True)
    traceback.print_exc()
