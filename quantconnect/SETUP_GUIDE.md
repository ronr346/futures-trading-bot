# QuantConnect Setup Guide — Elder S&D Strategy
*גרסה סופית — מוכן להרצה מיידית*

## שלב 1: פתח חשבון (2 דקות)
1. לך ל-[quantconnect.com](https://quantconnect.com)
2. "Get Started Free" → הרשם
3. לא צריך כרטיס אשראי — חינם לחלוטין לbacktest

## שלב 2: צור פרויקט חדש
1. לחץ **"+ New Project"**
2. שם: `Elder-SD-Strategy`
3. שפה: **Python**
4. לחץ **Create**

## שלב 3: הדבק את הקוד
1. מחק את כל הקוד הקיים בעורך
2. פתח את הקובץ: `quantconnect/elder_sd_strategy.py`
3. העתק הכל (Ctrl+A → Ctrl+C) → הדבק בעורך QuantConnect (Ctrl+V)
4. **Ctrl+S** לשמור

## שלב 4: הרץ Backtest
1. לחץ **"Build & Backtest"** (▶️)
2. המתן ~2-5 דקות
3. תקבל:
   - Equity Curve (גרף רווחיות)
   - Win Rate
   - Profit Factor
   - Max Drawdown
   - רשימת כל הטריידים עם פרטים

---

## פרמטרים

| פרמטר | ערך |
|-------|------|
| נכס | ES (E-mini S&P 500 Futures) |
| טיים פריים | **5 דקות** |
| תקופת Backtest | ינואר 2024 – דצמבר 2025 |
| הון התחלתי | $50,000 |
| Risk per trade | 2% ($1,000 max) |
| מקסימום עסקאות | 1 ביום (One & Done) |
| חוזים | 1–10 לפי חישוב סיכון |
| R:R | 2:1 |

## לוגיקת כניסה (Elder's A+ Setup)
ניקוד 3 מתוך 4 נדרש:
1. **מגמה** — מחיר מעל/מתחת EMA50
2. **Zone** — מחיר נוגע באזור Supply/Demand
3. **Structure Shift** — Higher Low (לונג) / Lower High (שורט)
4. **Dead Volume** — ווליום מתחת ל-85% מהממוצע

## Stop & Target
- **Stop Loss**: מתחת/מעל ה-Zone + buffer (ATR × 0.25)
- **Take Profit**: 2:1 Risk:Reward
- **EOD Exit**: 15:45 ET (סגירת יום מסחר)

---

*Updated: 25/2/2026 — Final Version*
