# Portfolio Evaluator Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a portfolio evaluation feature that scores holdings by Sharpe Ratio, recommends add/reduce/remove based on weight deviation, suggests entry price ranges, and sends results to Discord as part of the daily report.

**Architecture:** New standalone module `modules/portfolio_analyzer.py` owns all portfolio logic (data loading, Sharpe calculation, target weights, recommendations, entry prices). `DiscordNotifier` gets one new method `send_portfolio_report()`. `main.py` wires it in via `--no-portfolio` flag.

**Tech Stack:** Python dataclasses, pandas/numpy (already in requirements), Yahoo Finance via existing DataFetcher, TrendPredictor for entry price levels, Discord Webhook via existing DiscordNotifier.

---

### Task 1: Create holdings config file

**Files:**
- Create: `config/holdings.json`
- Create: `config/holdings.example.json`

**Step 1: Create the example config**

```json
{
  "portfolio_target_return": 0.15,
  "rebalance_threshold": 0.05,
  "holdings": [
    { "symbol": "NVDA", "shares": 10, "avg_cost": 450.00 },
    { "symbol": "AAPL", "shares": 20, "avg_cost": 175.00 },
    { "symbol": "2330.TW", "shares": 100, "avg_cost": 850.00 }
  ]
}
```

Save the above as both `config/holdings.example.json` (committed) and `config/holdings.json` (your actual holdings — add to `.gitignore`).

Note: Taiwan stocks must use Yahoo Finance format with `.TW` suffix (e.g. `2330.TW`).

**Step 2: Add holdings.json to .gitignore**

Open `.gitignore` and add:
```
config/holdings.json
```

**Step 3: Verify**

```bash
cat config/holdings.example.json
grep holdings .gitignore
```

Expected: file contents print, gitignore line present.

**Step 4: Commit**

```bash
git add config/holdings.example.json .gitignore
git commit -m "feat: add holdings config template for portfolio evaluator"
```

---

### Task 2: Create portfolio_analyzer.py — data classes and holdings loader

**Files:**
- Create: `modules/portfolio_analyzer.py`

**Step 1: Write the file with data classes and load function**

```python
"""
持倉分析模組
基於 Sharpe Ratio 評估持股並給出再平衡建議
"""

import json
import logging
import numpy as np
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

HOLDINGS_PATH = Path(__file__).parent.parent / "config" / "holdings.json"


@dataclass
class HoldingAnalysis:
    symbol: str
    shares: float
    avg_cost: float
    current_price: float
    market_value: float
    actual_weight: float        # fraction of total portfolio value
    target_weight: float        # Sharpe-based target fraction
    weight_deviation: float     # actual_weight - target_weight
    pnl: float                  # unrealized P&L in currency
    pnl_pct: float              # unrealized P&L as fraction
    sharpe_ratio: float         # 1-year annualized return / volatility
    annual_return_1y: float     # 1-year annualized return as fraction
    recommendation: str         # "add" | "reduce" | "remove" | "hold"
    add_price_low: Optional[float] = None
    add_price_high: Optional[float] = None
    add_price_note: Optional[str] = None


@dataclass
class PortfolioSummary:
    total_value: float
    total_pnl: float
    total_pnl_pct: float
    target_return: float        # from holdings.json
    portfolio_return_1y: float  # weighted 1-year return
    gap_to_target: float        # target_return - portfolio_return_1y
    holdings: list = field(default_factory=list)  # list[HoldingAnalysis]


def load_holdings_config() -> dict:
    """
    從 config/holdings.json 讀取持倉設定。

    Returns:
        dict with keys: portfolio_target_return, rebalance_threshold, holdings

    Raises:
        FileNotFoundError: if holdings.json doesn't exist
        ValueError: if required fields are missing
    """
    if not HOLDINGS_PATH.exists():
        raise FileNotFoundError(
            f"找不到 {HOLDINGS_PATH}。"
            "請複製 config/holdings.example.json 並填入您的持倉。"
        )

    with open(HOLDINGS_PATH, "r", encoding="utf-8") as f:
        config = json.load(f)

    required = ["portfolio_target_return", "rebalance_threshold", "holdings"]
    for key in required:
        if key not in config:
            raise ValueError(f"holdings.json 缺少必要欄位: {key}")

    if not config["holdings"]:
        raise ValueError("holdings.json 中的 holdings 清單不能為空")

    for h in config["holdings"]:
        for field_name in ["symbol", "shares", "avg_cost"]:
            if field_name not in h:
                raise ValueError(f"持倉項目缺少欄位 '{field_name}': {h}")

    return config
```

**Step 2: Verify file is importable**

```bash
python -c "from modules.portfolio_analyzer import load_holdings_config, HoldingAnalysis, PortfolioSummary; print('OK')"
```

Expected: `OK`

**Step 3: Commit**

```bash
git add modules/portfolio_analyzer.py
git commit -m "feat: add portfolio_analyzer data classes and holdings loader"
```

---

### Task 3: Add Sharpe ratio and target weight calculations

**Files:**
- Modify: `modules/portfolio_analyzer.py` — add PortfolioAnalyzer class with calculation methods

**Step 1: Add PortfolioAnalyzer class after the dataclasses**

```python
from modules.data_fetcher import DataFetcher


class PortfolioAnalyzer:
    """持倉分析器：計算 Sharpe Ratio、目標比例、再平衡建議"""

    TRADING_DAYS = 252

    def __init__(self, fetcher: DataFetcher = None):
        self.fetcher = fetcher or DataFetcher()

    def _fetch_price_and_history(self, symbol: str):
        """
        取得現價與 1 年歷史資料。

        Returns:
            (current_price, history_df) or (None, None) on failure
        """
        data = self.fetcher.get_stock_data(symbol, period="1y")
        if data is None or len(data) < 60:
            logger.warning(f"無法取得 {symbol} 的歷史資料")
            return None, None
        current_price = float(data["Close"].iloc[-1])
        return current_price, data

    def _calculate_sharpe(self, history) -> tuple[float, float]:
        """
        計算 1 年年化報酬率與 Sharpe Ratio（無風險利率假設 0）。

        Returns:
            (annual_return, sharpe_ratio)
        """
        close = history["Close"]
        daily_returns = close.pct_change().dropna()

        annual_return = float((1 + daily_returns).prod() ** (self.TRADING_DAYS / len(daily_returns)) - 1)
        volatility = float(daily_returns.std() * np.sqrt(self.TRADING_DAYS))

        if volatility == 0:
            return annual_return, 0.0

        sharpe = annual_return / volatility
        return annual_return, sharpe

    def _calculate_target_weights(self, sharpe_ratios: dict[str, float]) -> dict[str, float]:
        """
        依 Sharpe Ratio 計算目標比例。
        負 Sharpe 的股票目標比例為 0（建議移除）。

        Args:
            sharpe_ratios: {symbol: sharpe_ratio}

        Returns:
            {symbol: target_weight}  — values sum to 1.0
        """
        positive = {sym: max(sharpe, 0.0) for sym, sharpe in sharpe_ratios.items()}
        total = sum(positive.values())

        if total == 0:
            # 全部為負 Sharpe — 平均分配（讓使用者自行決定是否移除）
            n = len(positive)
            return {sym: 1.0 / n for sym in positive}

        return {sym: val / total for sym, val in positive.items()}
```

**Step 2: Verify class is importable**

```bash
python -c "from modules.portfolio_analyzer import PortfolioAnalyzer; pa = PortfolioAnalyzer(); print('OK')"
```

Expected: `OK`

**Step 3: Commit**

```bash
git add modules/portfolio_analyzer.py
git commit -m "feat: add Sharpe ratio and target weight calculations to PortfolioAnalyzer"
```

---

### Task 4: Add recommendation logic and full analyze() method

**Files:**
- Modify: `modules/portfolio_analyzer.py` — add `_make_recommendation()` and `analyze()` to PortfolioAnalyzer

**Step 1: Add methods inside PortfolioAnalyzer class**

```python
    def _make_recommendation(
        self,
        actual_weight: float,
        target_weight: float,
        sharpe: float,
        threshold: float,
    ) -> str:
        """
        決定再平衡建議。

        Rules (in priority order):
          1. Sharpe < 0  → "remove"
          2. actual > target + threshold → "reduce"
          3. actual < target - threshold → "add"
          4. otherwise → "hold"
        """
        if sharpe < 0:
            return "remove"
        deviation = actual_weight - target_weight
        if deviation > threshold:
            return "reduce"
        if deviation < -threshold:
            return "add"
        return "hold"

    def analyze(self) -> PortfolioSummary:
        """
        執行完整持倉分析。

        Returns:
            PortfolioSummary with all HoldingAnalysis populated
        """
        config = load_holdings_config()
        target_return = config["portfolio_target_return"]
        threshold = config["rebalance_threshold"]
        holdings_cfg = config["holdings"]

        # 1. Fetch prices and compute market values
        rows = []
        for h in holdings_cfg:
            symbol = h["symbol"]
            current_price, history = self._fetch_price_and_history(symbol)
            if current_price is None:
                logger.warning(f"跳過 {symbol}（無法取得資料）")
                continue

            market_value = current_price * h["shares"]
            pnl = (current_price - h["avg_cost"]) * h["shares"]
            pnl_pct = (current_price - h["avg_cost"]) / h["avg_cost"]
            annual_return, sharpe = self._calculate_sharpe(history)

            rows.append({
                "symbol": symbol,
                "shares": h["shares"],
                "avg_cost": h["avg_cost"],
                "current_price": current_price,
                "market_value": market_value,
                "pnl": pnl,
                "pnl_pct": pnl_pct,
                "annual_return_1y": annual_return,
                "sharpe_ratio": sharpe,
                "history": history,
            })

        if not rows:
            raise RuntimeError("所有持股資料取得失敗，無法進行分析")

        total_value = sum(r["market_value"] for r in rows)
        total_cost = sum(r["avg_cost"] * r["shares"] for r in rows)
        total_pnl = total_value - total_cost
        total_pnl_pct = total_pnl / total_cost if total_cost else 0.0

        # 2. Actual weights
        for r in rows:
            r["actual_weight"] = r["market_value"] / total_value

        # 3. Target weights from Sharpe
        sharpe_map = {r["symbol"]: r["sharpe_ratio"] for r in rows}
        target_weights = self._calculate_target_weights(sharpe_map)

        # 4. Recommendations
        holdings_out = []
        for r in rows:
            symbol = r["symbol"]
            actual_w = r["actual_weight"]
            target_w = target_weights[symbol]
            deviation = actual_w - target_w
            sharpe = r["sharpe_ratio"]
            rec = self._make_recommendation(actual_w, target_w, sharpe, threshold)

            holdings_out.append(HoldingAnalysis(
                symbol=symbol,
                shares=r["shares"],
                avg_cost=r["avg_cost"],
                current_price=r["current_price"],
                market_value=r["market_value"],
                actual_weight=actual_w,
                target_weight=target_w,
                weight_deviation=deviation,
                pnl=r["pnl"],
                pnl_pct=r["pnl_pct"],
                sharpe_ratio=sharpe,
                annual_return_1y=r["annual_return_1y"],
                recommendation=rec,
            ))

        # 5. Portfolio-level 1Y return (weighted)
        portfolio_return_1y = sum(
            r["annual_return_1y"] * r["actual_weight"] for r in rows
        )
        gap_to_target = target_return - portfolio_return_1y

        return PortfolioSummary(
            total_value=total_value,
            total_pnl=total_pnl,
            total_pnl_pct=total_pnl_pct,
            target_return=target_return,
            portfolio_return_1y=portfolio_return_1y,
            gap_to_target=gap_to_target,
            holdings=holdings_out,
        )
```

**Step 2: Quick smoke test (requires real holdings.json)**

```bash
python -c "
from modules.portfolio_analyzer import PortfolioAnalyzer
pa = PortfolioAnalyzer()
s = pa.analyze()
print(f'Total value: {s.total_value:.2f}')
print(f'Holdings: {[h.symbol for h in s.holdings]}')
print(f'Recommendations: {[h.recommendation for h in s.holdings]}')
"
```

Expected: prints total value and one recommendation per holding with no exceptions.

**Step 3: Commit**

```bash
git add modules/portfolio_analyzer.py
git commit -m "feat: add recommendation logic and analyze() to PortfolioAnalyzer"
```

---

### Task 5: Add entry price ranges for "add" recommendations

**Files:**
- Modify: `modules/portfolio_analyzer.py` — add `_enrich_add_prices()` method and call it in `analyze()`

**Step 1: Add import at top of file**

```python
from modules.predictor import TrendPredictor
```

**Step 2: Add method to PortfolioAnalyzer**

```python
    def _enrich_add_prices(self, holding: HoldingAnalysis, history) -> None:
        """
        用 TrendPredictor 的 Fibonacci 回調位填入加碼點位。
        直接修改 holding 的 add_price_* 欄位（in-place）。
        """
        try:
            predictor = TrendPredictor(self.fetcher)
            fib = predictor.calculate_fibonacci_levels(history, lookback=60)
            sma20 = float(history["Close"].rolling(20).mean().iloc[-1])
            current = holding.current_price

            fib_382 = fib.get("38.2%")
            fib_50 = fib.get("50%")

            # Only suggest levels below current price (support, not resistance)
            candidates = [
                v for v in [fib_382, fib_50] if v is not None and v < current
            ]

            if candidates:
                holding.add_price_low = round(min(candidates), 2)
                holding.add_price_high = round(max(candidates), 2)
                holding.add_price_note = "Fib 38.2%–50% 支撐"
            elif sma20 < current:
                holding.add_price_low = round(sma20 * 0.99, 2)
                holding.add_price_high = round(sma20, 2)
                holding.add_price_note = "SMA20 支撐"

        except Exception as e:
            logger.warning(f"無法計算 {holding.symbol} 加碼點位: {e}")
```

**Step 3: Call it inside `analyze()`, after holdings_out is built**

Find the line `return PortfolioSummary(` in `analyze()` and insert before it:

```python
        # 6. Enrich "add" recommendations with entry price ranges
        history_map = {r["symbol"]: r["history"] for r in rows}
        for h in holdings_out:
            if h.recommendation == "add":
                self._enrich_add_prices(h, history_map[h.symbol])
```

**Step 4: Verify smoke test still passes**

```bash
python -c "
from modules.portfolio_analyzer import PortfolioAnalyzer
pa = PortfolioAnalyzer()
s = pa.analyze()
for h in s.holdings:
    if h.recommendation == 'add':
        print(f'{h.symbol}: add range {h.add_price_low}–{h.add_price_high} ({h.add_price_note})')
"
```

Expected: "add" holdings print a price range (or nothing if all are "hold").

**Step 5: Commit**

```bash
git add modules/portfolio_analyzer.py
git commit -m "feat: add Fibonacci entry price ranges for add recommendations"
```

---

### Task 6: Add standalone test block to portfolio_analyzer.py

**Files:**
- Modify: `modules/portfolio_analyzer.py` — add `if __name__ == "__main__":` block at bottom

**Step 1: Append to end of file**

```python
if __name__ == "__main__":
    import sys

    print("=== 持倉分析測試 ===\n")
    pa = PortfolioAnalyzer()

    try:
        summary = pa.analyze()
    except FileNotFoundError as e:
        print(f"錯誤: {e}")
        sys.exit(1)

    print(f"💼 整體組合")
    print(f"  總市值：{summary.total_value:,.2f}")
    sign = "+" if summary.total_pnl >= 0 else ""
    print(f"  整體損益：{sign}{summary.total_pnl:,.2f} ({sign}{summary.total_pnl_pct:.1%})")
    print(f"  1年加權報酬：{summary.portfolio_return_1y:.1%}")
    gap_sign = "+" if summary.gap_to_target >= 0 else ""
    print(f"  距年目標({summary.target_return:.0%})：{gap_sign}{summary.gap_to_target:.1%}\n")

    for rec_label, rec_code in [
        ("📈 建議加碼", "add"),
        ("📉 建議減碼", "reduce"),
        ("🗑️  建議移除", "remove"),
        ("✅ 維持", "hold"),
    ]:
        group = [h for h in summary.holdings if h.recommendation == rec_code]
        if not group:
            continue
        print(rec_label)
        for h in group:
            pnl_sign = "+" if h.pnl >= 0 else ""
            print(f"  {h.symbol}  實際 {h.actual_weight:.0%} → 目標 {h.target_weight:.0%}")
            print(f"    損益：{pnl_sign}{h.pnl:,.2f} ({pnl_sign}{h.pnl_pct:.1%})｜Sharpe：{h.sharpe_ratio:.2f}")
            if h.recommendation == "add" and h.add_price_low:
                print(f"    加碼區間：{h.add_price_low}–{h.add_price_high}（{h.add_price_note}）")
        print()
```

**Step 2: Run standalone test**

```bash
python modules/portfolio_analyzer.py
```

Expected: clean formatted output matching the Discord message design, no exceptions.

**Step 3: Commit**

```bash
git add modules/portfolio_analyzer.py
git commit -m "feat: add standalone test block to portfolio_analyzer"
```

---

### Task 7: Add send_portfolio_report() to DiscordNotifier

**Files:**
- Modify: `modules/discord_bot.py` — add import and new method

**Step 1: Add import at top of discord_bot.py**

Find the existing imports and add after them:
```python
from .portfolio_analyzer import PortfolioSummary, HoldingAnalysis
```

**Step 2: Add method to DiscordNotifier class**

Add at the end of the class (before any standalone code):

```python
    def send_portfolio_report(self, summary: PortfolioSummary) -> bool:
        """
        發送持倉評估報告到 Discord。

        Args:
            summary: PortfolioSummary from PortfolioAnalyzer.analyze()

        Returns:
            True if sent successfully
        """
        pnl_sign = "+" if summary.total_pnl >= 0 else ""
        gap_sign = "還差 " if summary.gap_to_target > 0 else "已超越 "
        gap_abs = abs(summary.gap_to_target)

        lines = [
            f"💼 **整體組合**",
            f"　總市值：{summary.total_value:,.0f}",
            f"　整體損益：{pnl_sign}{summary.total_pnl:,.0f} ({pnl_sign}{summary.total_pnl_pct:.1%})",
            f"　1年加權報酬：{summary.portfolio_return_1y:.1%}",
            f"　距年目標({summary.target_return:.0%})：{gap_sign}{gap_abs:.1%}",
            "─" * 25,
        ]

        for rec_label, rec_code in [
            ("📈 建議加碼", "add"),
            ("📉 建議減碼", "reduce"),
            ("🗑️  建議移除", "remove"),
            ("✅ 維持", "hold"),
        ]:
            group = [h for h in summary.holdings if h.recommendation == rec_code]
            if not group:
                continue

            lines.append(f"**{rec_label}**")

            if rec_code == "hold":
                symbols = "、".join(h.symbol for h in group)
                lines.append(f"　{symbols}")
            else:
                for h in group:
                    pnl_sign = "+" if h.pnl >= 0 else ""
                    lines.append(
                        f"　**{h.symbol}**　實際 {h.actual_weight:.0%} → 目標 {h.target_weight:.0%}"
                    )
                    lines.append(
                        f"　損益：{pnl_sign}{h.pnl:,.0f} ({pnl_sign}{h.pnl_pct:.1%})｜Sharpe：{h.sharpe_ratio:.2f}"
                    )
                    if h.recommendation == "add" and h.add_price_low:
                        lines.append(
                            f"　加碼區間：{h.add_price_low}–{h.add_price_high}（{h.add_price_note}）"
                        )

            lines.append("")

        lines.append("─" * 25)
        description = "\n".join(lines)

        # Discord embed colour: green if portfolio beats target, orange if behind
        color = self.colors["bullish"] if summary.gap_to_target <= 0 else self.colors["warning"]

        embed = {
            "title": "📊 持倉評估報告",
            "description": description,
            "color": color,
        }

        return self.send_message(embeds=[embed])
```

**Step 3: Verify import works**

```bash
python -c "from modules.discord_bot import DiscordNotifier; print('OK')"
```

Expected: `OK`

**Step 4: Commit**

```bash
git add modules/discord_bot.py
git commit -m "feat: add send_portfolio_report() to DiscordNotifier"
```

---

### Task 8: Integrate into main.py

**Files:**
- Modify: `main.py` — add import, `enable_portfolio` flag, and call in `send_daily_report()`

**Step 1: Add import at top of main.py (after existing imports)**

```python
from modules.portfolio_analyzer import PortfolioAnalyzer
```

**Step 2: Add `enable_portfolio` parameter to `StockBot.__init__`**

Find:
```python
def __init__(self, webhook_url: str = None, enable_discovery: bool = True, enable_macro: bool = True):
```
Replace with:
```python
def __init__(self, webhook_url: str = None, enable_discovery: bool = True, enable_macro: bool = True, enable_portfolio: bool = True):
```

Find the body where `self.enable_macro` is set and add after it:
```python
        self.enable_portfolio = enable_portfolio
        self.portfolio_analyzer = PortfolioAnalyzer(self.fetcher) if enable_portfolio else None
```

**Step 3: Add portfolio section in `send_daily_report()`**

Find the block that sends the disclaimer (around line 233):
```python
            # 最後發送免責聲明
```

Insert before it:
```python
            # 發送持倉評估報告
            if self.enable_portfolio and self.portfolio_analyzer:
                try:
                    portfolio_summary = self.portfolio_analyzer.analyze()
                    self.notifier.send_portfolio_report(portfolio_summary)
                except FileNotFoundError:
                    logger.info("未找到 holdings.json，跳過持倉評估")
                except Exception as e:
                    logger.warning(f"持倉評估失敗: {e}")

```

**Step 4: Add `--no-portfolio` CLI flag**

Find where `--no-discovery` argument is added in the argparse section and add after it:
```python
    parser.add_argument(
        "--no-portfolio",
        action="store_true",
        help="停用持倉評估"
    )
```

Find where `StockBot` is instantiated (look for `bot = StockBot(`) and add `enable_portfolio`:
```python
    bot = StockBot(
        enable_discovery=not args.no_discovery,
        enable_macro=not args.no_macro,
        enable_portfolio=not args.no_portfolio,
    )
```

**Step 5: Verify CLI help shows new flag**

```bash
python main.py --help
```

Expected: `--no-portfolio` appears in output.

**Step 6: Test print mode (no Discord send)**

```bash
python main.py --mode print --no-portfolio
```

Expected: runs without error, no portfolio section.

**Step 7: Commit**

```bash
git add main.py
git commit -m "feat: integrate portfolio evaluator into StockBot daily report"
```

---

### Task 9: End-to-end manual verification

**Step 1: Run portfolio analyzer standalone**

```bash
python modules/portfolio_analyzer.py
```

Expected: full formatted report printed with at least one holding.

**Step 2: Run full bot in print mode with portfolio**

```bash
python main.py --mode print
```

Expected: portfolio section appears in terminal output near end of report.

**Step 3: (Optional) Send test report to Discord**

```bash
python main.py --mode once --market tw
```

Expected: Discord channel receives embed titled "📊 持倉評估報告".

**Step 4: Final commit if any cleanup needed**

```bash
git add -p
git commit -m "fix: portfolio evaluator cleanup after e2e test"
```
