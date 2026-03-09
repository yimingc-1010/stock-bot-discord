# Portfolio Evaluator — Design Document

**Date:** 2026-03-10
**Status:** Approved

## Overview

Add a portfolio evaluation feature to the stock bot that:
1. Tracks user holdings via a config file
2. Calculates risk-adjusted target weights (Sharpe Ratio)
3. Recommends add / reduce / remove actions when actual weights deviate from targets
4. Suggests entry price ranges for add recommendations (using existing Predictor module)
5. Sends a portfolio evaluation block as part of the daily Discord report

---

## Data Config

**File:** `config/holdings.json`

```json
{
  "portfolio_target_return": 0.15,
  "rebalance_threshold": 0.05,
  "holdings": [
    { "symbol": "NVDA", "shares": 10, "avg_cost": 450.00 },
    { "symbol": "AAPL", "shares": 20, "avg_cost": 175.00 },
    { "symbol": "2330", "shares": 100, "avg_cost": 850.00 }
  ]
}
```

| Field | Description |
|-------|-------------|
| `portfolio_target_return` | Annual target return, e.g. 0.15 = 15% |
| `rebalance_threshold` | Weight deviation threshold to trigger recommendation, e.g. 0.05 = ±5% |
| `symbol` | Ticker (TW or US, mixed supported) |
| `shares` | Number of shares held |
| `avg_cost` | Average cost per share (TWD or USD per symbol) |

---

## Module Architecture

**New file:** `modules/portfolio_analyzer.py` (standalone, independently testable)

### Computation Pipeline

```
holdings.json
     ↓
Load holdings + fetch current prices (DataFetcher)
     ↓
Per-stock calculations:
  - Current market value & actual portfolio weight
  - P&L (unrealized): (current_price - avg_cost) * shares
  - 1-year annualized return (from historical close prices)
  - 1-year return volatility → Sharpe Ratio (annualized return / volatility)
     ↓
Calculate target weights proportional to Sharpe Ratio
(negative Sharpe stocks get weight = 0, flagged for removal)
     ↓
Compare actual vs target weights; flag if deviation > rebalance_threshold
     ↓
Generate recommendation list
     ↓
For "add" recommendations: call Predictor for support/Fibonacci levels
     ↓
Calculate portfolio summary: total value, overall P&L, gap to target return
```

### Recommendation Rules

| Condition | Action |
|-----------|--------|
| actual_weight < target_weight - threshold | 📈 Add |
| actual_weight > target_weight + threshold | 📉 Reduce |
| Sharpe Ratio < 0 (1-year loss + high volatility) | 🗑️ Consider removing |
| Otherwise | ✅ Hold |

### Entry Price for "Add" Recommendations

Reuses `modules/predictor.py` existing logic:
- Fibonacci retracement levels (38.2%, 50%)
- 20-day SMA as secondary support
- Presented as a price range: `$845–$860 (Fib 38.2%)`

---

## Discord Message Format

Appended as a new embed section in the daily report:

```
📊 持倉評估報告

💼 整體組合
  總市值：$45,230
  整體損益：+$3,420 (+8.2%)
  距年目標(15%)：還差 6.8%

─────────────────────────
📈 建議加碼
  NVDA  實際 18% → 目標 25%
  損益：+12.3%｜Sharpe：1.42
  加碼區間：$845–$860（Fib 38.2%）
  次要支撐：$820（SMA20）

📉 建議減碼
  TSLA  實際 22% → 目標 12%
  損益：+5.1%｜Sharpe：0.61

🗑️ 建議移除
  LCID  Sharpe：-0.83（1年 -45%，高波動）
  損益：-$1,200 (-38%)

✅ 維持
  AAPL、MSFT、2330
─────────────────────────
```

---

## Integration

- `modules/portfolio_analyzer.py` — standalone module with `if __name__ == "__main__":` test block
- `main.py` — `send_daily_report()` calls `PortfolioAnalyzer` and appends embed to Discord report
- CLI: `--no-portfolio` flag to disable portfolio evaluation (default: enabled if `holdings.json` exists)

---

## Key Data Classes

```python
@dataclass
class HoldingAnalysis:
    symbol: str
    shares: float
    avg_cost: float
    current_price: float
    market_value: float
    actual_weight: float       # current % of portfolio
    target_weight: float       # Sharpe-based target %
    weight_deviation: float    # actual - target
    pnl: float                 # unrealized P&L in currency
    pnl_pct: float             # unrealized P&L %
    sharpe_ratio: float        # 1-year annualized return / volatility
    annual_return_1y: float    # 1-year annualized return
    recommendation: str        # "add" | "reduce" | "remove" | "hold"
    add_price_range: tuple | None  # (lower, upper) support range if recommendation == "add"
    add_price_note: str | None     # e.g. "Fib 38.2% support"

@dataclass
class PortfolioSummary:
    total_value: float
    total_pnl: float
    total_pnl_pct: float
    target_return: float
    gap_to_target: float       # target_return - annualized portfolio return
    holdings: list[HoldingAnalysis]
```

---

## Out of Scope

- Broker API integration (no live account connection)
- Trade execution
- Tax lot tracking
- Multi-currency conversion (TWD/USD mixed portfolios show in native currency)
