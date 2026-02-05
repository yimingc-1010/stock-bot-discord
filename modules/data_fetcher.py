"""
數據抓取模組
使用 yfinance 從 Yahoo Finance 獲取股票數據
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataFetcher:
    """股票數據抓取器"""

    def __init__(self):
        self.cache = {}
        self.cache_expiry = {}
        self.cache_duration = timedelta(minutes=15)

    def get_stock_data(
        self,
        symbol: str,
        period: str = "3mo",
        interval: str = "1d"
    ) -> Optional[pd.DataFrame]:
        """
        獲取單一股票的歷史數據

        Args:
            symbol: 股票代碼 (如 2330.TW, AAPL)
            period: 時間範圍 (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
            interval: 時間間隔 (1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo)

        Returns:
            DataFrame with OHLCV data
        """
        cache_key = f"{symbol}_{period}_{interval}"

        # 檢查快取
        if cache_key in self.cache:
            if datetime.now() < self.cache_expiry.get(cache_key, datetime.min):
                logger.debug(f"使用快取數據: {symbol}")
                return self.cache[cache_key]

        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(period=period, interval=interval)

            if df.empty:
                logger.warning(f"無法獲取數據: {symbol}")
                return None

            # 更新快取
            self.cache[cache_key] = df
            self.cache_expiry[cache_key] = datetime.now() + self.cache_duration

            logger.info(f"成功獲取數據: {symbol}, 共 {len(df)} 筆")
            return df

        except Exception as e:
            logger.error(f"獲取 {symbol} 數據時發生錯誤: {e}")
            return None

    def get_multiple_stocks(
        self,
        symbols: List[str],
        period: str = "3mo",
        interval: str = "1d"
    ) -> Dict[str, pd.DataFrame]:
        """
        批量獲取多支股票數據

        Args:
            symbols: 股票代碼列表
            period: 時間範圍
            interval: 時間間隔

        Returns:
            字典，鍵為股票代碼，值為 DataFrame
        """
        results = {}

        for symbol in symbols:
            data = self.get_stock_data(symbol, period, interval)
            if data is not None:
                results[symbol] = data

        logger.info(f"批量獲取完成: {len(results)}/{len(symbols)} 支股票")
        return results

    def get_stock_info(self, symbol: str) -> Optional[Dict]:
        """
        獲取股票基本資訊

        Args:
            symbol: 股票代碼

        Returns:
            股票資訊字典
        """
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info

            return {
                "symbol": symbol,
                "name": info.get("shortName", info.get("longName", symbol)),
                "sector": info.get("sector", "N/A"),
                "industry": info.get("industry", "N/A"),
                "market_cap": info.get("marketCap", 0),
                "pe_ratio": info.get("trailingPE", None),
                "pb_ratio": info.get("priceToBook", None),
                "dividend_yield": info.get("dividendYield", None),
                "52_week_high": info.get("fiftyTwoWeekHigh", None),
                "52_week_low": info.get("fiftyTwoWeekLow", None),
            }
        except Exception as e:
            logger.error(f"獲取 {symbol} 資訊時發生錯誤: {e}")
            return None

    def get_realtime_quote(self, symbol: str) -> Optional[Dict]:
        """
        獲取即時報價

        Args:
            symbol: 股票代碼

        Returns:
            即時報價字典
        """
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info

            return {
                "symbol": symbol,
                "price": info.get("regularMarketPrice", info.get("currentPrice")),
                "change": info.get("regularMarketChange"),
                "change_percent": info.get("regularMarketChangePercent"),
                "volume": info.get("regularMarketVolume"),
                "avg_volume": info.get("averageVolume"),
                "day_high": info.get("regularMarketDayHigh"),
                "day_low": info.get("regularMarketDayLow"),
                "open": info.get("regularMarketOpen"),
                "previous_close": info.get("regularMarketPreviousClose"),
            }
        except Exception as e:
            logger.error(f"獲取 {symbol} 即時報價時發生錯誤: {e}")
            return None

    def clear_cache(self):
        """清除所有快取"""
        self.cache.clear()
        self.cache_expiry.clear()
        logger.info("快取已清除")


if __name__ == "__main__":
    # 測試
    fetcher = DataFetcher()

    # 測試台股
    tw_data = fetcher.get_stock_data("2330.TW")
    if tw_data is not None:
        print("台積電最近數據:")
        print(tw_data.tail())

    # 測試美股
    us_data = fetcher.get_stock_data("AAPL")
    if us_data is not None:
        print("\n蘋果最近數據:")
        print(us_data.tail())
