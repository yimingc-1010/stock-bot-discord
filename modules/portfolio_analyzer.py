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
