"""
總體經濟數據擷取模組
從 FRED (Federal Reserve Economic Data) 取得美國總體經濟指標
需要免費 FRED API Key：https://fred.stlouisfed.org/docs/api/api_key.html
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional

import pandas as pd

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FRED 指標代碼對照表
FRED_SERIES = {
    "manufacturing_production": {"code": "IPMAN", "name": "製造業生產指數", "category": "投資"},
    "jobless_claims": {"code": "ICSA", "name": "初領失業救濟金", "category": "勞動"},
    "nonfarm_payrolls": {"code": "PAYEMS", "name": "非農就業人數", "category": "勞動"},
    "retail_sales": {"code": "RSXFS", "name": "實質零售銷售", "category": "消費"},
    "pce": {"code": "PCE", "name": "個人消費支出", "category": "消費"},
    "savings_rate": {"code": "PSAVERT", "name": "個人儲蓄率", "category": "消費"},
    "consumer_sentiment": {"code": "UMCSENT", "name": "密大消費者信心", "category": "信心"},
    "yield_spread": {"code": "T10Y2Y", "name": "10Y-2Y 利差", "category": "政策"},
    "cpi": {"code": "CPIAUCSL", "name": "CPI 消費者物價", "category": "通膨"},
    "private_investment": {"code": "GPDIC1", "name": "實質民間投資", "category": "投資"},
}


def _get_fred_api_key() -> Optional[str]:
    """取得 FRED API Key（優先環境變數，其次設定檔）"""
    key = os.environ.get("FRED_API_KEY")
    if key:
        return key
    try:
        from config.settings import FRED_API_KEY
        return FRED_API_KEY
    except (ImportError, AttributeError):
        return None


class MacroFetcher:
    """總體經濟數據擷取器"""

    def __init__(self, api_key: Optional[str] = None, cache_hours: int = 24):
        self._api_key = api_key or _get_fred_api_key()
        self._cache: Dict[str, pd.Series] = {}
        self._cache_time: Optional[datetime] = None
        self._cache_duration = timedelta(hours=cache_hours)

    def _is_cache_valid(self) -> bool:
        if self._cache_time is None:
            return False
        return (datetime.now() - self._cache_time) < self._cache_duration

    def _get_fred(self):
        """建立 Fred 客戶端"""
        if not self._api_key:
            raise ValueError(
                "FRED API Key 未設定。請至 https://fred.stlouisfed.org/docs/api/api_key.html "
                "申請免費 key，然後設定環境變數 FRED_API_KEY 或在 config/settings.py 中加入 FRED_API_KEY"
            )
        from fredapi import Fred
        return Fred(api_key=self._api_key)

    def fetch_series(self, fred_code: str, months: int = 36) -> Optional[pd.Series]:
        """
        從 FRED 取得單一時間序列

        Args:
            fred_code: FRED 系列代碼
            months: 回溯月數

        Returns:
            pandas Series 或 None
        """
        try:
            fred = self._get_fred()
            start = datetime.now() - timedelta(days=months * 30)
            series = fred.get_series(fred_code, observation_start=start)
            series = series.dropna()
            if series.empty:
                logger.warning(f"FRED 系列 {fred_code} 無資料")
                return None
            return series
        except Exception as e:
            logger.warning(f"取得 FRED 資料失敗 ({fred_code}): {e}")
            return None

    def fetch_all(self) -> Optional[Dict[str, pd.Series]]:
        """
        取得所有總體經濟指標

        Returns:
            dict 映射指標 key → pandas Series，失敗時回傳 None
        """
        if self._is_cache_valid() and self._cache:
            logger.info("使用快取的總經資料")
            return self._cache

        logger.info("從 FRED 取得總體經濟數據...")

        try:
            fred = self._get_fred()
            start = datetime.now() - timedelta(days=36 * 30)

            result: Dict[str, pd.Series] = {}
            for key, info in FRED_SERIES.items():
                try:
                    series = fred.get_series(info["code"], observation_start=start)
                    series = series.dropna()
                    if not series.empty:
                        result[key] = series
                except Exception as e:
                    logger.warning(f"取得 {info['code']} 失敗: {e}")

            if not result:
                logger.warning("未取得任何 FRED 資料")
                return None

            logger.info(f"成功取得 {len(result)}/{len(FRED_SERIES)} 項總經指標")
            self._cache = result
            self._cache_time = datetime.now()
            return result

        except Exception as e:
            logger.warning(f"FRED 資料取得失敗: {e}")
            return None

    def clear_cache(self):
        """清除快取"""
        self._cache.clear()
        self._cache_time = None


if __name__ == "__main__":
    fetcher = MacroFetcher()
    data = fetcher.fetch_all()

    if data:
        print(f"\n=== 總體經濟指標 ({len(data)} 項) ===\n")
        for key, series in data.items():
            info = FRED_SERIES[key]
            latest = series.iloc[-1]
            date = series.index[-1].strftime("%Y-%m-%d")
            print(f"  {info['name']} ({info['code']}): {latest:.2f}  [{date}]")
    else:
        print("無法取得 FRED 資料（請確認 FRED_API_KEY 已設定）")
