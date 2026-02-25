Build a QuantConnect Python backtest for the ORB (Opening Range Breakout) strategy on NQ E-mini futures.

Save the file as: quantconnect/orb_nq_strategy.py

STRATEGY RULES (implement exactly):
1. Instrument: NQ E-mini futures continuous contract
2. Timeframe: 5-minute bars
3. Opening Range window: 9:30-9:45 AM ET (first 15 minutes of RTH) - track High and Low
4. Entry: 5-minute candle CLOSES ABOVE the Opening Range High -> Long entry at next bar open
5. Direction: LONG ONLY - if ORB breaks to downside first, skip the day entirely
6. ORB Size Filter: Skip day if (ORB_High - ORB_Low) / open_price > 0.008 (0.8%)
7. Stop Loss: ORB Low, but capped at max 50 NQ points below entry ($1,000 max loss)
8. Profit Target: entry + 50% of ORB range
9. One trade per day only - after any entry or downside break, done for the day
10. Trend Filter: Only trade when NQ daily close > 200-period daily EMA
11. Position Size: Always 1 NQ contract (fixed)
12. Starting Capital: 50000
13. EOD Exit: Force close at 15:45 ET if still open
14. Backtest Period: 2023-01-01 to 2025-11-30

QUANTCONNECT IMPLEMENTATION:
- class ORBNQStrategy(QCAlgorithm)
- self.AddFuture(Futures.Indices.NASDAQ100EMini, Resolution.Minute)
- Set DataNormalizationMode.BackwardsRatio for continuous contract
- Consolidate minute bars to 5-minute using TradeBarConsolidator
- self.Schedule.On for EOD exit at 15:45
- Track ORB High/Low during 9:30-9:45 window using OnData or consolidator callback
- Use self.Portfolio.Invested to check open position
- For 200 EMA trend filter: use daily bars, check daily close > EMA(200)

END-OF-BACKTEST (OnEndOfAlgorithm):
Log these stats using self.Log():
- Total trades, wins, losses
- Win Rate %
- Average win ($) and average loss ($)
- Profit Factor
- Max consecutive losses
- Total Net P&L
- Max Drawdown
- Monthly P&L table

When completely finished writing the file, run exactly:
openclaw system event --text "Done: ORB NQ strategy built at orb_nq_strategy.py" --mode now
