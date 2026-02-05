"""
大盤趨勢分析模組
分析市場整體走勢、技術指標與市場情緒
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

from .data_fetcher import DataFetcher

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TrendDirection(Enum):
    """趨勢方向"""
    STRONG_BULLISH = "強勢多頭"
    BULLISH = "多頭"
    NEUTRAL = "盤整"
    BEARISH = "空頭"
    STRONG_BEARISH = "強勢空頭"


@dataclass
class MarketAnalysis:
    """市場分析結果"""
    symbol: str
    name: str
    current_price: float
    price_change: float
    price_change_pct: float
    trend: TrendDirection
    trend_score: int  # -100 到 100
    support_level: float
    resistance_level: float
    sma_5: float
    sma_20: float
    sma_60: float
    rsi: float
    macd: float
    macd_signal: float
    macd_histogram: float
    volume_ratio: float
    analysis_summary: str


class MarketAnalyzer:
    """大盤趨勢分析器"""

    def __init__(self, fetcher: Optional[DataFetcher] = None):
        self.fetcher = fetcher or DataFetcher()

    def calculate_sma(self, data: pd.Series, period: int) -> pd.Series:
        """計算簡單移動平均線"""
        return data.rolling(window=period).mean()

    def calculate_ema(self, data: pd.Series, period: int) -> pd.Series:
        """計算指數移動平均線"""
        return data.ewm(span=period, adjust=False).mean()

    def calculate_rsi(self, data: pd.Series, period: int = 14) -> pd.Series:
        """計算 RSI 相對強弱指標"""
        delta = data.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def calculate_macd(
        self,
        data: pd.Series,
        fast: int = 12,
        slow: int = 26,
        signal: int = 9
    ) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """計算 MACD 指標"""
        ema_fast = self.calculate_ema(data, fast)
        ema_slow = self.calculate_ema(data, slow)

        macd_line = ema_fast - ema_slow
        signal_line = self.calculate_ema(macd_line, signal)
        histogram = macd_line - signal_line

        return macd_line, signal_line, histogram

    def calculate_support_resistance(
        self,
        data: pd.DataFrame,
        lookback: int = 20
    ) -> Tuple[float, float]:
        """計算支撐與壓力位"""
        recent_data = data.tail(lookback)

        # 簡單方法：使用近期最低點和最高點
        support = recent_data['Low'].min()
        resistance = recent_data['High'].max()

        return support, resistance

    def calculate_volume_ratio(self, data: pd.DataFrame, period: int = 20) -> float:
        """計算成交量相對比率"""
        if len(data) < period:
            return 1.0

        avg_volume = data['Volume'].tail(period).mean()
        current_volume = data['Volume'].iloc[-1]

        if avg_volume > 0:
            return current_volume / avg_volume
        return 1.0

    def determine_trend(
        self,
        current_price: float,
        sma_5: float,
        sma_20: float,
        sma_60: float,
        rsi: float,
        macd_histogram: float,
        price_change_pct: float
    ) -> Tuple[TrendDirection, int]:
        """
        綜合判斷趨勢方向

        Returns:
            趨勢方向與分數 (-100 到 100)
        """
        score = 0

        # 均線排列 (最大 ±30)
        if current_price > sma_5 > sma_20 > sma_60:
            score += 30  # 多頭排列
        elif current_price < sma_5 < sma_20 < sma_60:
            score -= 30  # 空頭排列
        elif current_price > sma_20:
            score += 15
        elif current_price < sma_20:
            score -= 15

        # RSI (最大 ±25)
        if rsi > 70:
            score += 15  # 超買但代表強勢
        elif rsi > 50:
            score += 10
        elif rsi < 30:
            score -= 15  # 超賣
        elif rsi < 50:
            score -= 10

        # MACD (最大 ±25)
        if macd_histogram > 0:
            score += min(25, int(macd_histogram * 100))
        else:
            score += max(-25, int(macd_histogram * 100))

        # 價格變化 (最大 ±20)
        score += min(20, max(-20, int(price_change_pct * 5)))

        # 限制分數範圍
        score = max(-100, min(100, score))

        # 判斷趨勢
        if score >= 50:
            trend = TrendDirection.STRONG_BULLISH
        elif score >= 20:
            trend = TrendDirection.BULLISH
        elif score <= -50:
            trend = TrendDirection.STRONG_BEARISH
        elif score <= -20:
            trend = TrendDirection.BEARISH
        else:
            trend = TrendDirection.NEUTRAL

        return trend, score

    def generate_summary(
        self,
        trend: TrendDirection,
        score: int,
        rsi: float,
        macd_histogram: float,
        volume_ratio: float,
        price_change_pct: float
    ) -> str:
        """生成分析摘要"""
        parts = []

        # 趨勢描述
        parts.append(f"趨勢判定: {trend.value} (分數: {score})")

        # RSI 狀態
        if rsi > 70:
            parts.append("RSI 處於超買區，短期可能回調")
        elif rsi < 30:
            parts.append("RSI 處於超賣區，可能出現反彈")
        elif rsi > 50:
            parts.append("RSI 偏多方")
        else:
            parts.append("RSI 偏空方")

        # MACD 狀態
        if macd_histogram > 0:
            parts.append("MACD 柱狀圖為正，動能向上")
        else:
            parts.append("MACD 柱狀圖為負，動能向下")

        # 成交量
        if volume_ratio > 1.5:
            parts.append(f"成交量放大 {volume_ratio:.1f} 倍")
        elif volume_ratio < 0.7:
            parts.append("成交量萎縮")

        return " | ".join(parts)

    def analyze_index(
        self,
        symbol: str,
        name: str,
        period: str = "3mo"
    ) -> Optional[MarketAnalysis]:
        """
        分析單一指數

        Args:
            symbol: 指數代碼
            name: 指數名稱
            period: 分析時間範圍

        Returns:
            MarketAnalysis 分析結果
        """
        data = self.fetcher.get_stock_data(symbol, period=period)

        if data is None or len(data) < 60:
            logger.warning(f"數據不足，無法分析: {symbol}")
            return None

        try:
            close = data['Close']
            current_price = close.iloc[-1]
            prev_price = close.iloc[-2]

            price_change = current_price - prev_price
            price_change_pct = (price_change / prev_price) * 100

            # 計算技術指標
            sma_5 = self.calculate_sma(close, 5).iloc[-1]
            sma_20 = self.calculate_sma(close, 20).iloc[-1]
            sma_60 = self.calculate_sma(close, 60).iloc[-1]
            rsi = self.calculate_rsi(close).iloc[-1]

            macd_line, signal_line, histogram = self.calculate_macd(close)
            macd = macd_line.iloc[-1]
            macd_signal = signal_line.iloc[-1]
            macd_histogram = histogram.iloc[-1]

            support, resistance = self.calculate_support_resistance(data)
            volume_ratio = self.calculate_volume_ratio(data)

            # 判斷趨勢
            trend, score = self.determine_trend(
                current_price, sma_5, sma_20, sma_60,
                rsi, macd_histogram, price_change_pct
            )

            # 生成摘要
            summary = self.generate_summary(
                trend, score, rsi, macd_histogram,
                volume_ratio, price_change_pct
            )

            return MarketAnalysis(
                symbol=symbol,
                name=name,
                current_price=current_price,
                price_change=price_change,
                price_change_pct=price_change_pct,
                trend=trend,
                trend_score=score,
                support_level=support,
                resistance_level=resistance,
                sma_5=sma_5,
                sma_20=sma_20,
                sma_60=sma_60,
                rsi=rsi,
                macd=macd,
                macd_signal=macd_signal,
                macd_histogram=macd_histogram,
                volume_ratio=volume_ratio,
                analysis_summary=summary
            )

        except Exception as e:
            logger.error(f"分析 {symbol} 時發生錯誤: {e}")
            return None

    def analyze_taiwan_market(self) -> Optional[MarketAnalysis]:
        """分析台股大盤"""
        return self.analyze_index("^TWII", "台灣加權指數")

    def analyze_us_markets(self) -> Dict[str, MarketAnalysis]:
        """分析美股主要指數"""
        indices = {
            "^GSPC": "S&P 500",
            "^DJI": "道瓊工業指數",
            "^IXIC": "那斯達克指數",
            "^SOX": "費城半導體指數"
        }

        results = {}
        for symbol, name in indices.items():
            analysis = self.analyze_index(symbol, name)
            if analysis:
                results[symbol] = analysis

        return results


if __name__ == "__main__":
    analyzer = MarketAnalyzer()

    # 測試台股分析
    tw_analysis = analyzer.analyze_taiwan_market()
    if tw_analysis:
        print(f"\n=== {tw_analysis.name} ===")
        print(f"收盤價: {tw_analysis.current_price:.2f}")
        print(f"漲跌: {tw_analysis.price_change:+.2f} ({tw_analysis.price_change_pct:+.2f}%)")
        print(f"趨勢: {tw_analysis.trend.value}")
        print(f"分析: {tw_analysis.analysis_summary}")

    # 測試美股分析
    us_analyses = analyzer.analyze_us_markets()
    for symbol, analysis in us_analyses.items():
        print(f"\n=== {analysis.name} ===")
        print(f"收盤價: {analysis.current_price:.2f}")
        print(f"趨勢: {analysis.trend.value}")
