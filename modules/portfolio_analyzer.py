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

from modules.data_fetcher import DataFetcher

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
