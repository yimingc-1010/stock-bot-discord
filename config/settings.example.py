"""
股票推播機器人配置檔案
請複製此檔案並重命名為 settings.py，然後設定你的 Discord Webhook URL
"""

import json
import os

# 取得配置檔案路徑
CONFIG_DIR = os.path.dirname(os.path.abspath(__file__))
STOCKS_FILE = os.path.join(CONFIG_DIR, "stocks.json")

# Discord Webhook URL (請替換成你的 Webhook URL)
DISCORD_WEBHOOK_URL = "YOUR_DISCORD_WEBHOOK_URL_HERE"


def load_markets():
    """從 JSON 檔案載入市場與股票設定"""
    if os.path.exists(STOCKS_FILE):
        with open(STOCKS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        # 預設配置（當 JSON 檔案不存在時）
        return {
            "TW": {
                "name": "台股",
                "index_symbol": "^TWII",
                "sectors": {}
            },
            "US": {
                "name": "美股",
                "indices": {},
                "sectors": {}
            }
        }


def save_markets(markets):
    """儲存市場與股票設定到 JSON 檔案"""
    with open(STOCKS_FILE, 'w', encoding='utf-8') as f:
        json.dump(markets, f, ensure_ascii=False, indent=2)


def add_stock(market: str, sector: str, symbol: str):
    """
    新增股票到指定類股

    Args:
        market: "TW" 或 "US"
        sector: 類股名稱
        symbol: 股票代碼
    """
    markets = load_markets()
    if market in markets:
        if sector not in markets[market]["sectors"]:
            markets[market]["sectors"][sector] = []
        if symbol not in markets[market]["sectors"][sector]:
            markets[market]["sectors"][sector].append(symbol)
            save_markets(markets)
            return True
    return False


def remove_stock(market: str, sector: str, symbol: str):
    """
    從指定類股移除股票

    Args:
        market: "TW" 或 "US"
        sector: 類股名稱
        symbol: 股票代碼
    """
    markets = load_markets()
    if market in markets and sector in markets[market]["sectors"]:
        if symbol in markets[market]["sectors"][sector]:
            markets[market]["sectors"][sector].remove(symbol)
            save_markets(markets)
            return True
    return False


def add_sector(market: str, sector: str, stocks: list = None):
    """
    新增類股

    Args:
        market: "TW" 或 "US"
        sector: 類股名稱
        stocks: 股票代碼列表
    """
    markets = load_markets()
    if market in markets:
        markets[market]["sectors"][sector] = stocks or []
        save_markets(markets)
        return True
    return False


def remove_sector(market: str, sector: str):
    """
    移除類股

    Args:
        market: "TW" 或 "US"
        sector: 類股名稱
    """
    markets = load_markets()
    if market in markets and sector in markets[market]["sectors"]:
        del markets[market]["sectors"][sector]
        save_markets(markets)
        return True
    return False


# 載入市場設定
MARKETS = load_markets()

# 技術指標參數
TECHNICAL_PARAMS = {
    "sma_short": 5,      # 短期均線
    "sma_medium": 20,    # 中期均線
    "sma_long": 60,      # 長期均線
    "rsi_period": 14,    # RSI 週期
    "rsi_overbought": 70,
    "rsi_oversold": 30,
    "macd_fast": 12,
    "macd_slow": 26,
    "macd_signal": 9,
    "volume_ma": 20,     # 成交量均線
}

# 篩選條件
FILTER_PARAMS = {
    "min_volume_ratio": 1.5,      # 最小成交量放大倍數
    "min_price_change": 2.0,      # 最小漲幅 (%)
    "max_price_change": 10.0,     # 最大漲幅 (%) - 避免過度追高
    "rsi_min": 40,                # RSI 最小值
    "rsi_max": 75,                # RSI 最大值
}

# 排程設定
SCHEDULE = {
    "tw_market_close": "14:30",  # 台股收盤後分析時間
    "us_market_close": "05:30",  # 美股收盤後分析時間 (台灣時間)
    "timezone": "Asia/Taipei"
}
