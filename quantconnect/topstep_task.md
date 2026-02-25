# TASK: Modify ORB Strategy for TopStep Compliance

## File to modify
`orb_nq_strategy.py` → create NEW file `orb_mnq_topstep.py` in the same folder

## Goal
Adapt the ORB strategy to pass TopStep's $50K Combine rules by implementing:
1. Switch NQ → MNQ (Micro NASDAQ100 E-mini)
2. Dynamic Position Sizing based on equity cushion from trailing drawdown
3. Monthly Profit Lock at $3,000

DO NOT change:
- ORB logic (9:30-9:45 window, 5-min breakout bar, downside break rule)
- 200-day EMA trend filter
- EOD exit at 15:45
- Stop = ORB Low (capped at 50pts below entry)
- Target = entry + 50% ORB range
- One trade per day

---

## Change 1: NQ → MNQ

Replace:
```python
self.nq = self.AddFuture(
    Futures.Indices.NASDAQ100EMini,
    Resolution.Minute,
    ...
)
```

With:
```python
self.mnq = self.AddFuture(
    Futures.Indices.MicroNASDAQ100EMini,
    Resolution.Minute,
    dataNormalizationMode=DataNormalizationMode.BackwardsRatio,
    dataMappingMode=DataMappingMode.LastTradingDay,
    contractDepthOffset=0
)
self.mnq.SetFilter(0, 90)
```

Update ALL references: `self.nq` → `self.mnq`, `self.nq.Symbol` → `self.mnq.Symbol`

---

## Change 2: Add TopStepRiskManager class BEFORE the main class

```python
class TopStepRiskManager:
    """
    Manages position sizing and monthly profit lock for TopStep Combine.

    TopStep $50K rules:
    - Trailing Drawdown: $2,000 from highest equity point
    - Daily Loss Limit: $1,000
    - Profit Target: $3,000

    Our rules (conservative buffer):
    - Stop trading if within $200 of trailing drawdown level
    - Monthly profit lock: stop trading once $3,000 gained in a month
    - Dynamic contracts: press gas when safe, reduce when close to DD
    """

    TRAILING_DD = 2000       # TopStep trailing drawdown limit
    DD_BUFFER   = 200        # Our extra buffer before the DD level
    MONTHLY_LOCK = 3000      # Stop trading month after this profit

    def __init__(self, starting_equity: float = 50000.0):
        self.peak_equity     = starting_equity
        self.monthly_pnl     = {}    # "YYYY-MM" -> float
        self.current_month   = None

    def update_peak(self, equity: float) -> None:
        """Call every bar to track the all-time high equity."""
        if equity > self.peak_equity:
            self.peak_equity = equity

    def dd_level(self) -> float:
        """The trailing drawdown liquidation level."""
        return self.peak_equity - self.TRAILING_DD

    def cushion(self, equity: float) -> float:
        """Distance between current equity and the DD level."""
        return equity - self.dd_level()

    def get_contracts(self, equity: float) -> int:
        """
        Dynamic position sizing based on cushion from DD level.

        Logic:
        - Far from danger (cushion > $1,500) → press the gas → 10 MNQ
        - Safe zone (cushion $1,000-$1,500)  → 7 MNQ
        - Moderate (cushion $600-$1,000)     → 5 MNQ
        - Caution (cushion $300-$600)        → 3 MNQ
        - Danger (cushion $200-$300)         → 1 MNQ (minimal)
        - Too close (cushion < $200)         → 0 (do not trade)

        Note: 10 MNQ ≈ 1 full NQ contract in dollar exposure.
        """
        c = self.cushion(equity)
        if   c > 1500: return 10
        elif c > 1000: return 7
        elif c >  600: return 5
        elif c >  300: return 3
        elif c >  200: return 1
        else:          return 0

    def can_trade(self, equity: float) -> bool:
        """Return False if we should not open new positions."""
        # Too close to drawdown level
        if self.cushion(equity) <= self.DD_BUFFER:
            return False
        return True

    def update_monthly_pnl(self, month_key: str, pnl: float) -> None:
        """Add trade P&L to monthly tracker."""
        if month_key not in self.monthly_pnl:
            self.monthly_pnl[month_key] = 0.0
        self.monthly_pnl[month_key] += pnl

    def is_month_locked(self, month_key: str) -> bool:
        """Return True if we've hit $3,000 profit this month → stop trading."""
        return self.monthly_pnl.get(month_key, 0.0) >= self.MONTHLY_LOCK

    def get_monthly_summary(self) -> dict:
        """Return the monthly P&L dict for reporting."""
        return dict(self.monthly_pnl)
```

---

## Change 3: Initialize TopStepRiskManager in Initialize()

Add after `self.max_drawdown = 0.0`:
```python
# TopStep Risk Manager
self.risk_mgr = TopStepRiskManager(starting_equity=50000.0)
```

---

## Change 4: Update _execute_entry() to use dynamic sizing

Replace:
```python
def _execute_entry(self):
    if self.orb_high is None or self.orb_low is None:
        return
    self.MarketOrder(self.symbol, 1)
    self.traded_today  = True
    self.total_trades += 1
```

With:
```python
def _execute_entry(self):
    if self.orb_high is None or self.orb_low is None:
        return

    equity = float(self.Portfolio.TotalPortfolioValue)

    # Check monthly lock
    month_key = self.Time.strftime("%Y-%m")
    if self.risk_mgr.is_month_locked(month_key):
        self.Debug(f"{self.Time.date()} MONTH LOCKED — ${self.risk_mgr.monthly_pnl.get(month_key,0):,.0f} profit this month, no more trades")
        self.traded_today = True
        return

    # Check cushion (too close to trailing DD)
    if not self.risk_mgr.can_trade(equity):
        self.Debug(f"{self.Time.date()} DD PROTECTION — cushion ${self.risk_mgr.cushion(equity):,.0f} too small, skipping")
        self.traded_today = True
        return

    # Dynamic contracts
    contracts = self.risk_mgr.get_contracts(equity)
    if contracts == 0:
        self.traded_today = True
        return

    self.MarketOrder(self.symbol, contracts)
    self.traded_today  = True
    self.total_trades += 1
    self.Debug(f"{self.Time.date()} ENTRY {contracts} MNQ | cushion=${self.risk_mgr.cushion(equity):,.0f}")
```

---

## Change 5: Update _close_position() to feed the risk manager

At the end of `_close_position()`, after recording monthly_pnl, add:
```python
# Update TopStep risk manager
self.risk_mgr.update_monthly_pnl(month_key, pnl)
```

And in OnData / _update_drawdown(), call:
```python
self.risk_mgr.update_peak(float(self.Portfolio.TotalPortfolioValue))
```

---

## Change 6: Update OnEndOfAlgorithm to show TopStep stats

Add to the stats output (after existing stats):
```python
self.Log("=" * 60)
self.Log("TOPSTEP COMPLIANCE REPORT")
self.Log("-" * 40)
self.Log(f"Peak Equity:             ${self.risk_mgr.peak_equity:,.0f}")
self.Log(f"Final DD Level:          ${self.risk_mgr.dd_level():,.0f}")
self.Log(f"Final Cushion:           ${self.risk_mgr.cushion(equity):,.0f}")
locked_months = [m for m, p in self.risk_mgr.monthly_pnl.items() if p >= 3000]
self.Log(f"Months hit $3K lock:     {len(locked_months)} → {locked_months}")
self.Log("=" * 60)
self.Log("MONTHLY P&L (TopStep Risk Manager)")
self.Log("-" * 40)
for month in sorted(self.risk_mgr.monthly_pnl.keys()):
    pnl = self.risk_mgr.monthly_pnl[month]
    locked = " 🔒 LOCKED" if pnl >= 3000 else ""
    marker = "+" if pnl >= 0 else "-"
    self.Log(f"  {month}:  {marker}${abs(pnl):>8,.0f}{locked}")
self.Log("=" * 60)
```

---

## Change 7: Class name and docstring

Rename class to `ORBMNQTopStep` and update the docstring to describe the changes.

---

## Verification after writing

After writing the file, confirm:
1. `grep -n "MicroNASDAQ100EMini" orb_mnq_topstep.py` → should find it
2. `grep -n "TopStepRiskManager" orb_mnq_topstep.py` → should find the class + usage
3. `grep -n "is_month_locked" orb_mnq_topstep.py` → should find usage
4. `grep -n "get_contracts" orb_mnq_topstep.py` → should find usage
5. `python -m py_compile orb_mnq_topstep.py` → must succeed with no errors

---

## Final output
A clean, working `orb_mnq_topstep.py` file ready to paste into QuantConnect.
