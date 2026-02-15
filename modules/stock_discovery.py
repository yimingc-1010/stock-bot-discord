"""
動態股票發現模組
從 Yahoo Finance 篩選量能動能領先股，發現觀察名單以外的機會
"""

import time
import logging
from typing import Dict, List, Optional, Set

import yfinance as yf

from .data_fetcher import DataFetcher
from .sector_scanner import SectorScanner, StockAnalysis

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 台股掃描宇宙：觀察名單外的主要個股，供動態篩選使用
TW_DISCOVERY_UNIVERSE = [
    # 半導體 & IC 設計
    "2344.TW", "3034.TW", "3443.TW", "6669.TW",
    "2449.TW", "3661.TW", "2458.TW",
    # 電子代工 & 零組件
    "2354.TW", "2356.TW", "2395.TW", "3231.TW", "6239.TW",
    # 金融
    "2886.TW", "2887.TW", "2885.TW", "2892.TW", "5876.TW",
    # 傳產 & 食品
    "1101.TW", "1102.TW", "1216.TW", "2912.TW", "1227.TW",
    # 電信 & 媒體
    "2412.TW", "3045.TW", "4904.TW",
    # 鋼鐵 & 水泥
    "2006.TW", "2014.TW", "1110.TW",
    # 紡織 & 塑膠
    "1402.TW", "1434.TW",
    # 其他熱門
    "2207.TW", "9910.TW", "2633.TW", "5871.TW", "2801.TW",
    "3037.TW", "2049.TW", "6581.TW",
]


class StockDiscovery:
    """動態股票發現器"""

    def __init__(
        self,
        fetcher: Optional[DataFetcher] = None,
        scanner: Optional[SectorScanner] = None,
        fetch_delay: float = 0.3,
    ):
        self.fetcher = fetcher or DataFetcher()
        self.scanner = scanner or SectorScanner(self.fetcher)
        self.fetch_delay = fetch_delay

    def _get_watchlist_symbols(self, market: str) -> Set[str]:
        """取得觀察名單中的所有股票代碼"""
        from config.settings import MARKETS

        symbols: Set[str] = set()
        market_data = MARKETS.get(market, {})
        for sector_stocks in market_data.get("sectors", {}).values():
            symbols.update(sector_stocks)
        return symbols

    def _analyze_candidates(
        self,
        symbols: List[str],
        sector_label: str,
        top_n: int,
    ) -> List[StockAnalysis]:
        """逐一分析候選股票，帶速率限制"""
        results: List[StockAnalysis] = []

        for i, symbol in enumerate(symbols):
            analysis = self.scanner.analyze_stock(symbol, sector_label)
            if analysis and analysis.strength_score > 0:
                results.append(analysis)

            # 速率限制（最後一筆不需要等待）
            if i < len(symbols) - 1:
                time.sleep(self.fetch_delay)

        results.sort(key=lambda x: x.strength_score, reverse=True)
        return results[:top_n]

    def discover_us_movers(self, top_n: int = 10) -> List[StockAnalysis]:
        """
        發現美股量能動能領先股

        使用 yfinance screener API 取得當日最活躍和漲幅最大的股票，
        排除觀察名單中已有的股票，再進行技術分析排名。

        Args:
            top_n: 回傳數量上限

        Returns:
            依強度分數排序的 StockAnalysis 列表
        """
        logger.info("開始發現美股量能動能領先股...")
        watchlist = self._get_watchlist_symbols("US")
        candidates: List[str] = []

        for screener_key in ("most_actives", "day_gainers"):
            try:
                result = yf.screen(screener_key)
                if result and "quotes" in result:
                    for quote in result["quotes"]:
                        symbol = quote.get("symbol", "")
                        if symbol and symbol not in watchlist and symbol not in candidates:
                            candidates.append(symbol)
            except Exception as e:
                logger.warning(f"yfinance screener '{screener_key}' 失敗: {e}")

        if not candidates:
            logger.warning("未取得任何美股候選股票")
            return []

        # 限制候選數量以控制 API 用量
        candidates = candidates[:top_n * 2]
        logger.info(f"美股候選股數: {len(candidates)}")

        return self._analyze_candidates(candidates, "發現", top_n)

    def discover_tw_movers(self, top_n: int = 10) -> List[StockAnalysis]:
        """
        發現台股量能動能領先股

        掃描預定義的台股擴展宇宙，排除觀察名單中已有的股票，
        篩選量能放大且具正向動能的個股。

        Args:
            top_n: 回傳數量上限

        Returns:
            依強度分數排序的 StockAnalysis 列表
        """
        logger.info("開始發現台股量能動能領先股...")
        watchlist = self._get_watchlist_symbols("TW")
        candidates = [s for s in TW_DISCOVERY_UNIVERSE if s not in watchlist]

        if not candidates:
            logger.warning("台股掃描宇宙中無新候選股票")
            return []

        logger.info(f"台股候選股數: {len(candidates)}")
        results = self._analyze_candidates(candidates, "發現", top_n * 2)

        # 額外篩選：量能放大 > 1.5 且漲幅為正
        filtered = [
            s for s in results
            if s.volume_ratio > 1.5 and s.price_change_pct > 0
        ]

        # 如果嚴格篩選後不足，放寬為 volume_ratio > 1.0
        if len(filtered) < 3:
            filtered = [
                s for s in results
                if s.volume_ratio > 1.0 and s.price_change_pct > 0
            ]

        return filtered[:top_n]

    def discover(
        self,
        market: str = "all",
        top_n: int = 10,
    ) -> Dict[str, List[StockAnalysis]]:
        """
        執行市場發現

        Args:
            market: "tw", "us", 或 "all"
            top_n: 每個市場回傳數量上限

        Returns:
            {"tw": [...], "us": [...]}
        """
        discoveries: Dict[str, List[StockAnalysis]] = {}

        if market in ("tw", "all"):
            discoveries["tw"] = self.discover_tw_movers(top_n)

        if market in ("us", "all"):
            discoveries["us"] = self.discover_us_movers(top_n)

        return discoveries


if __name__ == "__main__":
    import sys
    sys.path.insert(0, ".")

    from config.settings import MARKETS

    discovery = StockDiscovery()

    print("\n=== 美股動態發現 ===")
    us_movers = discovery.discover_us_movers(top_n=5)
    for stock in us_movers:
        print(
            f"  {stock.symbol} ({stock.name}): "
            f"強度 {stock.strength_score:.0f} | "
            f"漲跌 {stock.price_change_pct:+.2f}% | "
            f"量能 {stock.volume_ratio:.1f}x | "
            f"{stock.analysis_note}"
        )

    print("\n=== 台股動態發現 ===")
    tw_movers = discovery.discover_tw_movers(top_n=5)
    for stock in tw_movers:
        print(
            f"  {stock.symbol} ({stock.name}): "
            f"強度 {stock.strength_score:.0f} | "
            f"漲跌 {stock.price_change_pct:+.2f}% | "
            f"量能 {stock.volume_ratio:.1f}x | "
            f"{stock.analysis_note}"
        )
