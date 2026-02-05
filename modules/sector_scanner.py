"""
強勢區塊與個股篩選模組
識別市場中表現最強的類股與個股
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging

from .data_fetcher import DataFetcher
from .market_analyzer import MarketAnalyzer, TrendDirection

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class StockAnalysis:
    """個股分析結果"""
    symbol: str
    name: str
    sector: str
    current_price: float
    price_change_pct: float
    volume_ratio: float
    rsi: float
    trend_score: int
    strength_score: float  # 綜合強度分數
    buy_signal: bool
    analysis_note: str


@dataclass
class SectorAnalysis:
    """類股分析結果"""
    name: str
    avg_change_pct: float
    strength_score: float
    trend: TrendDirection
    top_stocks: List[StockAnalysis] = field(default_factory=list)
    stock_count: int = 0
    bullish_count: int = 0


class SectorScanner:
    """強勢類股與個股掃描器"""

    def __init__(self, fetcher: Optional[DataFetcher] = None):
        self.fetcher = fetcher or DataFetcher()
        self.analyzer = MarketAnalyzer(self.fetcher)

    def analyze_stock(
        self,
        symbol: str,
        sector: str,
        period: str = "3mo"
    ) -> Optional[StockAnalysis]:
        """
        分析單一個股

        Args:
            symbol: 股票代碼
            sector: 所屬類股
            period: 分析期間

        Returns:
            StockAnalysis 分析結果
        """
        data = self.fetcher.get_stock_data(symbol, period=period)

        if data is None or len(data) < 20:
            return None

        try:
            close = data['Close']
            current_price = close.iloc[-1]

            # 計算漲跌幅
            if len(close) >= 2:
                prev_price = close.iloc[-2]
                price_change_pct = ((current_price - prev_price) / prev_price) * 100
            else:
                price_change_pct = 0

            # 計算技術指標
            sma_5 = self.analyzer.calculate_sma(close, 5).iloc[-1]
            sma_20 = self.analyzer.calculate_sma(close, 20).iloc[-1]
            sma_60 = self.analyzer.calculate_sma(close, min(60, len(close) - 1)).iloc[-1]
            rsi = self.analyzer.calculate_rsi(close).iloc[-1]

            macd_line, signal_line, histogram = self.analyzer.calculate_macd(close)
            macd_histogram = histogram.iloc[-1]

            # 計算成交量比率
            volume_ratio = self.analyzer.calculate_volume_ratio(data)

            # 計算趨勢分數
            trend, trend_score = self.analyzer.determine_trend(
                current_price, sma_5, sma_20, sma_60,
                rsi, macd_histogram, price_change_pct
            )

            # 計算綜合強度分數 (0-100)
            strength_score = self._calculate_strength_score(
                price_change_pct, volume_ratio, rsi,
                trend_score, current_price, sma_20
            )

            # 判斷買入訊號
            buy_signal = self._check_buy_signal(
                current_price, sma_5, sma_20, rsi,
                macd_histogram, volume_ratio, price_change_pct
            )

            # 生成分析註記
            analysis_note = self._generate_stock_note(
                price_change_pct, volume_ratio, rsi,
                trend, buy_signal
            )

            # 獲取股票名稱
            info = self.fetcher.get_stock_info(symbol)
            name = info.get("name", symbol) if info else symbol

            return StockAnalysis(
                symbol=symbol,
                name=name,
                sector=sector,
                current_price=current_price,
                price_change_pct=price_change_pct,
                volume_ratio=volume_ratio,
                rsi=rsi,
                trend_score=trend_score,
                strength_score=strength_score,
                buy_signal=buy_signal,
                analysis_note=analysis_note
            )

        except Exception as e:
            logger.error(f"分析 {symbol} 時發生錯誤: {e}")
            return None

    def _calculate_strength_score(
        self,
        price_change_pct: float,
        volume_ratio: float,
        rsi: float,
        trend_score: int,
        current_price: float,
        sma_20: float
    ) -> float:
        """計算綜合強度分數"""
        score = 50  # 基礎分數

        # 價格變化貢獻 (最大 ±20)
        score += min(20, max(-20, price_change_pct * 4))

        # 成交量放大貢獻 (最大 +15)
        if volume_ratio > 1:
            score += min(15, (volume_ratio - 1) * 10)

        # RSI 貢獻 (最大 ±10)
        if 40 <= rsi <= 70:
            score += 10  # 健康區間
        elif rsi > 70:
            score += 5   # 強勢但可能過熱
        else:
            score -= 5   # 弱勢

        # 趨勢分數貢獻 (最大 ±15)
        score += trend_score * 0.15

        # 價格位置貢獻 (最大 ±10)
        if current_price > sma_20:
            score += 10
        else:
            score -= 5

        return max(0, min(100, score))

    def _check_buy_signal(
        self,
        current_price: float,
        sma_5: float,
        sma_20: float,
        rsi: float,
        macd_histogram: float,
        volume_ratio: float,
        price_change_pct: float
    ) -> bool:
        """檢查是否有買入訊號"""
        signals = 0

        # 價格站上均線
        if current_price > sma_5 > sma_20:
            signals += 1

        # RSI 在健康區間且向上
        if 40 <= rsi <= 70:
            signals += 1

        # MACD 柱狀圖為正
        if macd_histogram > 0:
            signals += 1

        # 成交量放大
        if volume_ratio > 1.2:
            signals += 1

        # 漲幅適中（不追高）
        if 1 <= price_change_pct <= 7:
            signals += 1

        return signals >= 3

    def _generate_stock_note(
        self,
        price_change_pct: float,
        volume_ratio: float,
        rsi: float,
        trend: TrendDirection,
        buy_signal: bool
    ) -> str:
        """生成個股分析註記"""
        notes = []

        if buy_signal:
            notes.append("✅ 符合買入條件")

        if price_change_pct > 3:
            notes.append(f"🔥 強勢上漲 {price_change_pct:.1f}%")
        elif price_change_pct > 0:
            notes.append(f"📈 溫和上漲")

        if volume_ratio > 2:
            notes.append(f"📊 爆量 {volume_ratio:.1f}x")
        elif volume_ratio > 1.5:
            notes.append(f"📊 量增")

        if rsi > 70:
            notes.append("⚠️ RSI 過熱")
        elif rsi < 30:
            notes.append("💡 RSI 超賣")

        return " | ".join(notes) if notes else trend.value

    def scan_sector(
        self,
        sector_name: str,
        symbols: List[str],
        period: str = "3mo"
    ) -> SectorAnalysis:
        """
        掃描單一類股

        Args:
            sector_name: 類股名稱
            symbols: 該類股的股票代碼列表
            period: 分析期間

        Returns:
            SectorAnalysis 類股分析結果
        """
        stock_analyses = []

        # 並行分析個股
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {
                executor.submit(self.analyze_stock, symbol, sector_name, period): symbol
                for symbol in symbols
            }

            for future in as_completed(futures):
                result = future.result()
                if result:
                    stock_analyses.append(result)

        if not stock_analyses:
            return SectorAnalysis(
                name=sector_name,
                avg_change_pct=0,
                strength_score=0,
                trend=TrendDirection.NEUTRAL,
                stock_count=0
            )

        # 計算類股統計
        avg_change = np.mean([s.price_change_pct for s in stock_analyses])
        avg_strength = np.mean([s.strength_score for s in stock_analyses])
        bullish_count = sum(1 for s in stock_analyses if s.trend_score > 0)

        # 判斷類股趨勢
        if avg_strength >= 70:
            sector_trend = TrendDirection.STRONG_BULLISH
        elif avg_strength >= 55:
            sector_trend = TrendDirection.BULLISH
        elif avg_strength <= 30:
            sector_trend = TrendDirection.STRONG_BEARISH
        elif avg_strength <= 45:
            sector_trend = TrendDirection.BEARISH
        else:
            sector_trend = TrendDirection.NEUTRAL

        # 排序並取得強勢股
        top_stocks = sorted(
            stock_analyses,
            key=lambda x: x.strength_score,
            reverse=True
        )[:5]

        return SectorAnalysis(
            name=sector_name,
            avg_change_pct=avg_change,
            strength_score=avg_strength,
            trend=sector_trend,
            top_stocks=top_stocks,
            stock_count=len(stock_analyses),
            bullish_count=bullish_count
        )

    def scan_all_sectors(
        self,
        sectors_config: Dict[str, List[str]],
        period: str = "3mo"
    ) -> List[SectorAnalysis]:
        """
        掃描所有類股

        Args:
            sectors_config: 類股配置 {類股名稱: [股票代碼列表]}
            period: 分析期間

        Returns:
            按強度排序的類股分析結果列表
        """
        results = []

        for sector_name, symbols in sectors_config.items():
            logger.info(f"掃描類股: {sector_name}")
            analysis = self.scan_sector(sector_name, symbols, period)
            results.append(analysis)

        # 按強度分數排序
        results.sort(key=lambda x: x.strength_score, reverse=True)

        return results

    def get_top_stocks(
        self,
        sector_analyses: List[SectorAnalysis],
        top_n: int = 10
    ) -> List[StockAnalysis]:
        """
        從所有類股中獲取最強勢的個股

        Args:
            sector_analyses: 類股分析結果列表
            top_n: 返回數量

        Returns:
            最強勢個股列表
        """
        all_stocks = []
        for sector in sector_analyses:
            all_stocks.extend(sector.top_stocks)

        # 按強度分數排序並去重
        seen = set()
        unique_stocks = []
        for stock in sorted(all_stocks, key=lambda x: x.strength_score, reverse=True):
            if stock.symbol not in seen:
                seen.add(stock.symbol)
                unique_stocks.append(stock)
                if len(unique_stocks) >= top_n:
                    break

        return unique_stocks

    def get_buy_signals(
        self,
        sector_analyses: List[SectorAnalysis]
    ) -> List[StockAnalysis]:
        """
        獲取所有發出買入訊號的個股

        Args:
            sector_analyses: 類股分析結果列表

        Returns:
            有買入訊號的個股列表
        """
        buy_stocks = []
        for sector in sector_analyses:
            for stock in sector.top_stocks:
                if stock.buy_signal:
                    buy_stocks.append(stock)

        return sorted(buy_stocks, key=lambda x: x.strength_score, reverse=True)


if __name__ == "__main__":
    from config.settings import MARKETS

    scanner = SectorScanner()

    # 測試台股類股掃描
    print("\n=== 台股類股掃描 ===")
    tw_sectors = scanner.scan_all_sectors(MARKETS["TW"]["sectors"])

    for sector in tw_sectors[:3]:
        print(f"\n{sector.name}: {sector.trend.value}")
        print(f"  平均漲跌: {sector.avg_change_pct:+.2f}%")
        print(f"  強度分數: {sector.strength_score:.1f}")
        print(f"  前三強勢股:")
        for stock in sector.top_stocks[:3]:
            print(f"    - {stock.symbol}: {stock.price_change_pct:+.2f}% | {stock.analysis_note}")
