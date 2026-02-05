"""
股票推播機器人配置檔案
請複製此檔案並重命名為 settings.py，然後設定你的 Discord Webhook URL
"""

# Discord Webhook URL (請替換成你的 Webhook URL)
DISCORD_WEBHOOK_URL = "YOUR_DISCORD_WEBHOOK_URL_HERE"

# 市場設定
MARKETS = {
    "TW": {
        "name": "台股",
        "index_symbol": "^TWII",  # 台灣加權指數
        "sectors": {
            "半導體": ["2330.TW", "2454.TW", "2303.TW", "3711.TW", "2379.TW"],
            "電子零組件": ["2317.TW", "2382.TW", "3008.TW", "2408.TW", "2327.TW"],
            "金融": ["2881.TW", "2882.TW", "2883.TW", "2884.TW", "2891.TW"],
            "傳產": ["1301.TW", "1303.TW", "1326.TW", "2002.TW", "2105.TW"],
            "航運": ["2603.TW", "2609.TW", "2615.TW", "2618.TW", "5880.TW"],
            "生技醫療": ["4904.TW", "1476.TW", "6446.TW", "4743.TW", "1707.TW"],
            "綠能": ["3481.TW", "6803.TW", "3576.TW", "6443.TW", "6488.TW"],
        }
    },
    "US": {
        "name": "美股",
        "indices": {
            "S&P 500": "^GSPC",
            "道瓊工業": "^DJI",
            "那斯達克": "^IXIC",
            "費城半導體": "^SOX",
        },
        "sectors": {
            "科技巨頭": ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA"],
            "半導體": ["NVDA", "AMD", "INTC", "TSM", "AVGO", "QCOM"],
            "AI概念": ["NVDA", "MSFT", "GOOGL", "PLTR", "AI", "SNOW"],
            "電動車": ["TSLA", "RIVN", "LCID", "NIO", "LI", "XPEV"],
            "金融": ["JPM", "BAC", "WFC", "GS", "MS", "C"],
            "醫療保健": ["JNJ", "UNH", "PFE", "ABBV", "MRK", "LLY"],
            "能源": ["XOM", "CVX", "COP", "SLB", "EOG", "PXD"],
        }
    }
}

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
