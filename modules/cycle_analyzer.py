"""
景氣循環分析模組（愛榭客 Izaax 方法）
根據美國總體經濟指標判斷景氣所處的四階段：復甦、成長、榮景、衰退
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional

import pandas as pd

from .macro_fetcher import MacroFetcher, FRED_SERIES

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CyclePhase(Enum):
    RECOVERY = "復甦期"
    GROWTH = "成長期"
    BOOM = "榮景期"
    RECESSION = "衰退期"


class Confidence(Enum):
    HIGH = "高"
    MEDIUM = "中"
    LOW = "低"


PHASE_COLORS = {
    CyclePhase.RECOVERY: 0x00FF00,   # green
    CyclePhase.GROWTH: 0x0099FF,     # blue
    CyclePhase.BOOM: 0xFF9900,       # orange
    CyclePhase.RECESSION: 0xFF0000,  # red
}

PHASE_ALLOCATION = {
    CyclePhase.RECOVERY: "全力做多（建議持股 100%）",
    CyclePhase.GROWTH: "穩定持股",
    CyclePhase.BOOM: "分批減碼（持股 70%→50%→30%）",
    CyclePhase.RECESSION: "避險，持有公債/現金",
}


@dataclass
class IndicatorSnapshot:
    """單一指標快照"""
    name: str
    category: str
    value: float
    trend: str       # "↑", "↓", "→"
    data_date: str   # YYYY-MM-DD


@dataclass
class CycleAnalysis:
    """景氣循環分析結果"""
    phase: CyclePhase
    confidence: Confidence
    allocation: str
    indicators: List[IndicatorSnapshot] = field(default_factory=list)
    phase_scores: Dict[str, float] = field(default_factory=dict)


class CycleAnalyzer:
    """景氣循環分析器"""

    def __init__(self, fetcher: Optional[MacroFetcher] = None):
        self.fetcher = fetcher or MacroFetcher()

    @staticmethod
    def _trend(series: pd.Series, lookback: int = 3) -> str:
        """
        判斷趨勢方向

        比較最新值與 lookback 期前的值，閾值為 ±1%。

        Args:
            series: 時間序列
            lookback: 回溯期數

        Returns:
            "↑", "↓", 或 "→"
        """
        if len(series) < lookback + 1:
            return "→"
        recent = series.iloc[-1]
        earlier = series.iloc[-(lookback + 1)]
        if earlier == 0:
            return "→"
        pct_change = (recent - earlier) / abs(earlier) * 100
        if pct_change > 1:
            return "↑"
        elif pct_change < -1:
            return "↓"
        return "→"

    @staticmethod
    def _yoy_change(series: pd.Series) -> Optional[float]:
        """計算年增率 (%)"""
        if len(series) < 13:
            return None
        recent = series.iloc[-1]
        year_ago = series.iloc[-13]
        if year_ago == 0:
            return None
        return (recent - year_ago) / abs(year_ago) * 100

    def _build_snapshots(
        self, data: Dict[str, pd.Series]
    ) -> List[IndicatorSnapshot]:
        """從原始資料建構指標快照列表"""
        snapshots = []
        for key, series in data.items():
            info = FRED_SERIES.get(key)
            if info is None:
                continue
            snapshots.append(IndicatorSnapshot(
                name=info["name"],
                category=info["category"],
                value=round(float(series.iloc[-1]), 2),
                trend=self._trend(series),
                data_date=series.index[-1].strftime("%Y-%m-%d"),
            ))
        return snapshots

    def _score_phases(
        self, data: Dict[str, pd.Series]
    ) -> Dict[str, float]:
        """
        對四階段分別評分

        每個符合的訊號加 1 分，總分最高者為判定結果。
        """
        scores = {
            CyclePhase.RECOVERY.name: 0.0,
            CyclePhase.GROWTH.name: 0.0,
            CyclePhase.BOOM.name: 0.0,
            CyclePhase.RECESSION.name: 0.0,
        }

        # --- 製造業生產指數 (IPMAN) ---
        mfg = data.get("manufacturing_production")
        if mfg is not None and len(mfg) > 6:
            trend = self._trend(mfg)
            yoy = self._yoy_change(mfg)
            # 從谷底回升 = 復甦
            if trend == "↑" and yoy is not None and yoy < 0:
                scores[CyclePhase.RECOVERY.name] += 2
            elif trend == "↑":
                scores[CyclePhase.GROWTH.name] += 1
            # 持續成長中
            if yoy is not None and yoy > 3:
                scores[CyclePhase.BOOM.name] += 0.5
            # 下滑 = 衰退警訊
            if trend == "↓" and yoy is not None and yoy < -2:
                scores[CyclePhase.RECESSION.name] += 1

        # --- 初領失業救濟金 ---
        claims = data.get("jobless_claims")
        if claims is not None and len(claims) > 12:
            trend = self._trend(claims, lookback=4)
            peak = claims.max()
            current = claims.iloc[-1]
            # 從高點回落 = 復甦
            if current < peak * 0.85 and trend == "↓":
                scores[CyclePhase.RECOVERY.name] += 1
            # 低檔穩定 = 成長
            elif trend == "→" or trend == "↓":
                scores[CyclePhase.GROWTH.name] += 0.5
            # 上升 = 衰退警訊
            if trend == "↑":
                scores[CyclePhase.RECESSION.name] += 1

        # --- 非農就業 ---
        payrolls = data.get("nonfarm_payrolls")
        if payrolls is not None and len(payrolls) > 6:
            trend = self._trend(payrolls, lookback=3)
            if trend == "↑":
                scores[CyclePhase.GROWTH.name] += 1
            elif trend == "↓":
                scores[CyclePhase.RECESSION.name] += 1

        # --- 儲蓄率 ---
        savings = data.get("savings_rate")
        if savings is not None and len(savings) > 6:
            val = savings.iloc[-1]
            trend = self._trend(savings)
            # 高儲蓄 + 下降 = 復甦轉成長（消費潛力釋放）
            if val > 8 and trend == "↓":
                scores[CyclePhase.RECOVERY.name] += 0.5
                scores[CyclePhase.GROWTH.name] += 0.5
            # 低儲蓄 = 榮景（透支消費）
            if val < 4:
                scores[CyclePhase.BOOM.name] += 1
            # 儲蓄率持續下滑 = 成長期特徵
            if trend == "↓":
                scores[CyclePhase.GROWTH.name] += 0.5

        # --- PCE vs 可支配所得（用 PCE YoY 代替） ---
        pce = data.get("pce")
        if pce is not None:
            pce_yoy = self._yoy_change(pce)
            if pce_yoy is not None:
                if pce_yoy > 6:
                    scores[CyclePhase.BOOM.name] += 1
                elif pce_yoy > 3:
                    scores[CyclePhase.GROWTH.name] += 0.5

        # --- 零售銷售年增率 ---
        retail = data.get("retail_sales")
        if retail is not None:
            retail_yoy = self._yoy_change(retail)
            if retail_yoy is not None:
                if retail_yoy < 0:
                    scores[CyclePhase.RECESSION.name] += 1.5
                elif retail_yoy > 5:
                    scores[CyclePhase.GROWTH.name] += 0.5

        # --- CPI 通膨 ---
        cpi = data.get("cpi")
        if cpi is not None:
            cpi_yoy = self._yoy_change(cpi)
            if cpi_yoy is not None:
                if cpi_yoy > 5:
                    scores[CyclePhase.BOOM.name] += 1
                elif cpi_yoy > 3:
                    scores[CyclePhase.BOOM.name] += 0.5

        # --- 10Y-2Y 利差 ---
        spread = data.get("yield_spread")
        if spread is not None and len(spread) > 20:
            val = spread.iloc[-1]
            trend = self._trend(spread, lookback=5)
            # 倒掛 = 衰退預警
            if val < 0:
                scores[CyclePhase.RECESSION.name] += 1
            # 由負轉正（脫離倒掛）= 可能正在衰退或復甦
            if val > 0 and spread.iloc[-10] < 0:
                scores[CyclePhase.RECESSION.name] += 0.5
                scores[CyclePhase.RECOVERY.name] += 0.5
            # 正常正利差 = 成長
            if val > 0.5:
                scores[CyclePhase.GROWTH.name] += 0.5

        # --- 消費者信心 ---
        sentiment = data.get("consumer_sentiment")
        if sentiment is not None and len(sentiment) > 3:
            trend = self._trend(sentiment)
            if trend == "↑":
                scores[CyclePhase.RECOVERY.name] += 0.5
                scores[CyclePhase.GROWTH.name] += 0.5
            elif trend == "↓":
                scores[CyclePhase.RECESSION.name] += 0.5

        # --- 實質民間投資 ---
        investment = data.get("private_investment")
        if investment is not None and len(investment) > 4:
            trend = self._trend(investment, lookback=2)
            if trend == "↑":
                scores[CyclePhase.RECOVERY.name] += 1
                scores[CyclePhase.GROWTH.name] += 0.5
            elif trend == "↓":
                scores[CyclePhase.RECESSION.name] += 0.5

        return scores

    def analyze(self) -> Optional[CycleAnalysis]:
        """
        執行景氣循環分析

        Returns:
            CycleAnalysis 或 None（資料不可用時）
        """
        data = self.fetcher.fetch_all()
        if not data:
            return None

        scores = self._score_phases(data)
        snapshots = self._build_snapshots(data)

        # 取最高分的階段
        best_phase_name = max(scores, key=scores.get)
        best_score = scores[best_phase_name]
        phase = CyclePhase[best_phase_name]

        # 計算信心度：最高分與第二高分的差距
        sorted_scores = sorted(scores.values(), reverse=True)
        gap = sorted_scores[0] - sorted_scores[1] if len(sorted_scores) > 1 else best_score

        if gap >= 2 and best_score >= 3:
            confidence = Confidence.HIGH
        elif gap >= 1:
            confidence = Confidence.MEDIUM
        else:
            confidence = Confidence.LOW

        return CycleAnalysis(
            phase=phase,
            confidence=confidence,
            allocation=PHASE_ALLOCATION[phase],
            indicators=snapshots,
            phase_scores=scores,
        )


if __name__ == "__main__":
    import sys
    sys.path.insert(0, ".")

    analyzer = CycleAnalyzer()
    result = analyzer.analyze()

    if result:
        print(f"\n=== 景氣循環分析 (Izaax Method) ===\n")
        print(f"  當前階段: {result.phase.value}")
        print(f"  信心度:   {result.confidence.value}")
        print(f"  配置建議: {result.allocation}")
        print(f"\n  階段分數:")
        for phase_name, score in sorted(result.phase_scores.items(), key=lambda x: x[1], reverse=True):
            marker = " ◀" if phase_name == result.phase.name else ""
            print(f"    {CyclePhase[phase_name].value}: {score:.1f}{marker}")
        print(f"\n  指標快照:")
        for ind in result.indicators:
            print(f"    {ind.trend} {ind.name}: {ind.value:.2f}  [{ind.data_date}]")
    else:
        print("無法取得總經資料進行分析")
