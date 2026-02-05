"""
趨勢預測模組
基於技術分析與統計方法預測未來走勢
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timedelta
import logging

from .data_fetcher import DataFetcher
from .market_analyzer import MarketAnalyzer, TrendDirection

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PredictionConfidence(Enum):
    """預測信心度"""
    HIGH = "高"
    MEDIUM = "中"
    LOW = "低"


class PredictionDirection(Enum):
    """預測方向"""
    STRONG_UP = "強勢上漲"
    UP = "偏多上漲"
    NEUTRAL = "盤整震盪"
    DOWN = "偏空下跌"
    STRONG_DOWN = "強勢下跌"


@dataclass
class PricePrediction:
    """價格預測結果"""
    symbol: str
    name: str
    current_price: float
    predicted_direction: PredictionDirection
    confidence: PredictionConfidence
    target_price_high: float
    target_price_low: float
    support_levels: List[float]
    resistance_levels: List[float]
    key_factors: List[str]
    risk_warning: str
    time_horizon: str  # 預測時間範圍


@dataclass
class MarketOutlook:
    """市場展望"""
    market_name: str
    overall_direction: PredictionDirection
    confidence: PredictionConfidence
    key_observations: List[str]
    bullish_factors: List[str]
    bearish_factors: List[str]
    recommended_strategy: str
    risk_level: str


class TrendPredictor:
    """趨勢預測器"""

    def __init__(self, fetcher: Optional[DataFetcher] = None):
        self.fetcher = fetcher or DataFetcher()
        self.analyzer = MarketAnalyzer(self.fetcher)

    def calculate_pivot_points(self, data: pd.DataFrame) -> Dict[str, float]:
        """
        計算樞紐點 (Pivot Points)

        Args:
            data: OHLCV 數據

        Returns:
            樞紐點字典
        """
        last_day = data.iloc[-1]
        high = last_day['High']
        low = last_day['Low']
        close = last_day['Close']

        pivot = (high + low + close) / 3

        return {
            'pivot': pivot,
            'r1': 2 * pivot - low,
            'r2': pivot + (high - low),
            'r3': high + 2 * (pivot - low),
            's1': 2 * pivot - high,
            's2': pivot - (high - low),
            's3': low - 2 * (high - pivot)
        }

    def calculate_fibonacci_levels(
        self,
        data: pd.DataFrame,
        lookback: int = 60
    ) -> Dict[str, float]:
        """
        計算斐波那契回撤/延伸位

        Args:
            data: OHLCV 數據
            lookback: 回看週期

        Returns:
            斐波那契水平字典
        """
        recent_data = data.tail(lookback)
        high = recent_data['High'].max()
        low = recent_data['Low'].min()
        diff = high - low

        current_trend_up = data['Close'].iloc[-1] > data['Close'].iloc[-lookback]

        if current_trend_up:
            # 上升趨勢，計算回撤位
            return {
                '0%': high,
                '23.6%': high - diff * 0.236,
                '38.2%': high - diff * 0.382,
                '50%': high - diff * 0.5,
                '61.8%': high - diff * 0.618,
                '78.6%': high - diff * 0.786,
                '100%': low,
                'ext_127.2%': high + diff * 0.272,
                'ext_161.8%': high + diff * 0.618
            }
        else:
            # 下降趨勢，計算反彈位
            return {
                '0%': low,
                '23.6%': low + diff * 0.236,
                '38.2%': low + diff * 0.382,
                '50%': low + diff * 0.5,
                '61.8%': low + diff * 0.618,
                '78.6%': low + diff * 0.786,
                '100%': high
            }

    def analyze_price_pattern(self, data: pd.DataFrame) -> Dict[str, any]:
        """
        分析價格形態

        Args:
            data: OHLCV 數據

        Returns:
            形態分析結果
        """
        close = data['Close']
        high = data['High']
        low = data['Low']

        # 計算近期趨勢
        sma_5 = close.rolling(5).mean()
        sma_20 = close.rolling(20).mean()

        patterns = []
        signals = []

        # 檢查均線交叉
        if len(close) >= 2:
            prev_diff = sma_5.iloc[-2] - sma_20.iloc[-2]
            curr_diff = sma_5.iloc[-1] - sma_20.iloc[-1]

            if prev_diff < 0 and curr_diff > 0:
                patterns.append("黃金交叉")
                signals.append(("bullish", "均線黃金交叉，短期看漲"))
            elif prev_diff > 0 and curr_diff < 0:
                patterns.append("死亡交叉")
                signals.append(("bearish", "均線死亡交叉，短期看跌"))

        # 檢查突破
        recent_high = high.tail(20).max()
        recent_low = low.tail(20).min()
        current_price = close.iloc[-1]

        if current_price >= recent_high * 0.98:
            patterns.append("突破近期高點")
            signals.append(("bullish", "價格突破近期高點"))
        elif current_price <= recent_low * 1.02:
            patterns.append("跌破近期低點")
            signals.append(("bearish", "價格跌破近期低點"))

        # 檢查連續漲跌
        recent_changes = close.pct_change().tail(5)
        up_days = (recent_changes > 0).sum()
        down_days = (recent_changes < 0).sum()

        if up_days >= 4:
            patterns.append("連續上漲")
            signals.append(("bullish", f"近5日有{up_days}日上漲"))
        elif down_days >= 4:
            patterns.append("連續下跌")
            signals.append(("bearish", f"近5日有{down_days}日下跌"))

        return {
            'patterns': patterns,
            'signals': signals
        }

    def calculate_volatility(self, data: pd.DataFrame, period: int = 20) -> float:
        """計算波動率"""
        returns = data['Close'].pct_change().tail(period)
        return returns.std() * np.sqrt(252) * 100  # 年化波動率 %

    def predict_stock(
        self,
        symbol: str,
        name: str,
        period: str = "6mo",
        horizon: str = "1週"
    ) -> Optional[PricePrediction]:
        """
        預測單一股票走勢

        Args:
            symbol: 股票代碼
            name: 股票名稱
            period: 分析期間
            horizon: 預測時間範圍

        Returns:
            PricePrediction 預測結果
        """
        data = self.fetcher.get_stock_data(symbol, period=period)

        if data is None or len(data) < 60:
            return None

        try:
            close = data['Close']
            current_price = close.iloc[-1]

            # 計算技術指標
            sma_20 = self.analyzer.calculate_sma(close, 20).iloc[-1]
            sma_60 = self.analyzer.calculate_sma(close, 60).iloc[-1]
            rsi = self.analyzer.calculate_rsi(close).iloc[-1]

            macd_line, signal_line, histogram = self.analyzer.calculate_macd(close)
            macd_hist = histogram.iloc[-1]

            # 計算支撐壓力
            pivots = self.calculate_pivot_points(data)
            fib_levels = self.calculate_fibonacci_levels(data)

            # 分析形態
            pattern_analysis = self.analyze_price_pattern(data)

            # 計算波動率
            volatility = self.calculate_volatility(data)

            # 綜合評估預測方向
            direction, confidence, factors = self._evaluate_prediction(
                current_price, sma_20, sma_60, rsi, macd_hist,
                pattern_analysis, volatility
            )

            # 計算目標價
            price_range = self._calculate_target_prices(
                current_price, direction, volatility,
                pivots, fib_levels
            )

            # 整理支撐壓力位
            support_levels = sorted([
                pivots['s1'], pivots['s2'],
                fib_levels.get('38.2%', current_price * 0.95),
                fib_levels.get('50%', current_price * 0.93)
            ])[:3]

            resistance_levels = sorted([
                pivots['r1'], pivots['r2'],
                fib_levels.get('38.2%', current_price * 1.05),
                fib_levels.get('50%', current_price * 1.07)
            ], reverse=True)[:3]

            # 風險警告
            risk_warning = self._generate_risk_warning(
                rsi, volatility, direction
            )

            return PricePrediction(
                symbol=symbol,
                name=name,
                current_price=current_price,
                predicted_direction=direction,
                confidence=confidence,
                target_price_high=price_range['high'],
                target_price_low=price_range['low'],
                support_levels=support_levels,
                resistance_levels=resistance_levels,
                key_factors=factors,
                risk_warning=risk_warning,
                time_horizon=horizon
            )

        except Exception as e:
            logger.error(f"預測 {symbol} 時發生錯誤: {e}")
            return None

    def _evaluate_prediction(
        self,
        current_price: float,
        sma_20: float,
        sma_60: float,
        rsi: float,
        macd_hist: float,
        pattern_analysis: Dict,
        volatility: float
    ) -> Tuple[PredictionDirection, PredictionConfidence, List[str]]:
        """評估預測方向與信心度"""
        score = 0
        factors = []

        # 均線位置
        if current_price > sma_20 > sma_60:
            score += 2
            factors.append("價格站穩均線之上，多頭排列")
        elif current_price < sma_20 < sma_60:
            score -= 2
            factors.append("價格跌破均線，空頭排列")
        elif current_price > sma_20:
            score += 1
            factors.append("價格高於20日均線")
        else:
            score -= 1
            factors.append("價格低於20日均線")

        # RSI
        if rsi > 70:
            score -= 1
            factors.append(f"RSI({rsi:.0f}) 處於超買區，可能回調")
        elif rsi < 30:
            score += 1
            factors.append(f"RSI({rsi:.0f}) 處於超賣區，可能反彈")
        elif rsi > 50:
            score += 0.5
            factors.append(f"RSI({rsi:.0f}) 偏多")

        # MACD
        if macd_hist > 0:
            score += 1
            factors.append("MACD 動能向上")
        else:
            score -= 1
            factors.append("MACD 動能向下")

        # 形態訊號
        for signal_type, description in pattern_analysis.get('signals', []):
            if signal_type == 'bullish':
                score += 1
                factors.append(description)
            else:
                score -= 1
                factors.append(description)

        # 判斷方向
        if score >= 3:
            direction = PredictionDirection.STRONG_UP
        elif score >= 1:
            direction = PredictionDirection.UP
        elif score <= -3:
            direction = PredictionDirection.STRONG_DOWN
        elif score <= -1:
            direction = PredictionDirection.DOWN
        else:
            direction = PredictionDirection.NEUTRAL

        # 判斷信心度
        if abs(score) >= 3 and volatility < 30:
            confidence = PredictionConfidence.HIGH
        elif abs(score) >= 2:
            confidence = PredictionConfidence.MEDIUM
        else:
            confidence = PredictionConfidence.LOW

        return direction, confidence, factors[:5]

    def _calculate_target_prices(
        self,
        current_price: float,
        direction: PredictionDirection,
        volatility: float,
        pivots: Dict,
        fib_levels: Dict
    ) -> Dict[str, float]:
        """計算目標價位"""
        # 基於波動率估算價格範圍
        weekly_volatility = volatility / np.sqrt(52)
        expected_move = current_price * (weekly_volatility / 100)

        if direction in [PredictionDirection.STRONG_UP, PredictionDirection.UP]:
            target_high = min(
                current_price + expected_move * 1.5,
                pivots.get('r2', current_price * 1.05)
            )
            target_low = max(
                current_price - expected_move * 0.5,
                pivots.get('s1', current_price * 0.98)
            )
        elif direction in [PredictionDirection.STRONG_DOWN, PredictionDirection.DOWN]:
            target_high = min(
                current_price + expected_move * 0.5,
                pivots.get('r1', current_price * 1.02)
            )
            target_low = max(
                current_price - expected_move * 1.5,
                pivots.get('s2', current_price * 0.95)
            )
        else:
            target_high = current_price + expected_move
            target_low = current_price - expected_move

        return {
            'high': round(target_high, 2),
            'low': round(target_low, 2)
        }

    def _generate_risk_warning(
        self,
        rsi: float,
        volatility: float,
        direction: PredictionDirection
    ) -> str:
        """生成風險警告"""
        warnings = []

        if volatility > 40:
            warnings.append("高波動風險")
        elif volatility > 25:
            warnings.append("波動較大")

        if rsi > 75:
            warnings.append("嚴重超買，追高風險大")
        elif rsi < 25:
            warnings.append("嚴重超賣，可能持續下跌")

        if direction == PredictionDirection.NEUTRAL:
            warnings.append("方向不明，建議觀望")

        if not warnings:
            return "風險適中"

        return "⚠️ " + "，".join(warnings)

    def generate_market_outlook(
        self,
        market_name: str,
        index_analysis,
        sector_analyses: List
    ) -> MarketOutlook:
        """
        生成市場展望

        Args:
            market_name: 市場名稱
            index_analysis: 指數分析結果
            sector_analyses: 類股分析結果列表

        Returns:
            MarketOutlook 市場展望
        """
        bullish_factors = []
        bearish_factors = []
        observations = []

        # 從指數分析提取
        if index_analysis:
            if index_analysis.trend in [TrendDirection.STRONG_BULLISH, TrendDirection.BULLISH]:
                bullish_factors.append(f"{index_analysis.name}呈現{index_analysis.trend.value}")
            elif index_analysis.trend in [TrendDirection.STRONG_BEARISH, TrendDirection.BEARISH]:
                bearish_factors.append(f"{index_analysis.name}呈現{index_analysis.trend.value}")

            if index_analysis.rsi > 70:
                bearish_factors.append("大盤RSI過熱")
            elif index_analysis.rsi < 30:
                bullish_factors.append("大盤RSI超賣")

            observations.append(
                f"大盤收盤 {index_analysis.current_price:.2f}，"
                f"漲跌 {index_analysis.price_change_pct:+.2f}%"
            )

        # 從類股分析提取
        if sector_analyses:
            strong_sectors = [s for s in sector_analyses if s.strength_score >= 60]
            weak_sectors = [s for s in sector_analyses if s.strength_score <= 40]

            if len(strong_sectors) > len(sector_analyses) / 2:
                bullish_factors.append(f"{len(strong_sectors)}個類股表現強勢")
            if len(weak_sectors) > len(sector_analyses) / 2:
                bearish_factors.append(f"{len(weak_sectors)}個類股表現疲弱")

            if strong_sectors:
                top_sectors = ", ".join([s.name for s in strong_sectors[:3]])
                observations.append(f"強勢類股: {top_sectors}")

        # 綜合判斷
        bullish_score = len(bullish_factors)
        bearish_score = len(bearish_factors)

        if bullish_score >= bearish_score + 2:
            direction = PredictionDirection.STRONG_UP
            confidence = PredictionConfidence.HIGH
            strategy = "積極布局，可加碼強勢類股"
            risk = "低"
        elif bullish_score > bearish_score:
            direction = PredictionDirection.UP
            confidence = PredictionConfidence.MEDIUM
            strategy = "維持多方思維，逢低布局"
            risk = "中低"
        elif bearish_score >= bullish_score + 2:
            direction = PredictionDirection.STRONG_DOWN
            confidence = PredictionConfidence.HIGH
            strategy = "保守操作，減碼或空手觀望"
            risk = "高"
        elif bearish_score > bullish_score:
            direction = PredictionDirection.DOWN
            confidence = PredictionConfidence.MEDIUM
            strategy = "謹慎操作，控制持股水位"
            risk = "中高"
        else:
            direction = PredictionDirection.NEUTRAL
            confidence = PredictionConfidence.LOW
            strategy = "區間操作，高出低進"
            risk = "中"

        return MarketOutlook(
            market_name=market_name,
            overall_direction=direction,
            confidence=confidence,
            key_observations=observations,
            bullish_factors=bullish_factors,
            bearish_factors=bearish_factors,
            recommended_strategy=strategy,
            risk_level=risk
        )


if __name__ == "__main__":
    predictor = TrendPredictor()

    # 測試台積電預測
    prediction = predictor.predict_stock("2330.TW", "台積電")
    if prediction:
        print(f"\n=== {prediction.name} 預測 ===")
        print(f"現價: {prediction.current_price:.2f}")
        print(f"預測方向: {prediction.predicted_direction.value}")
        print(f"信心度: {prediction.confidence.value}")
        print(f"目標區間: {prediction.target_price_low:.2f} - {prediction.target_price_high:.2f}")
        print(f"關鍵因素:")
        for factor in prediction.key_factors:
            print(f"  - {factor}")
        print(f"風險提示: {prediction.risk_warning}")
