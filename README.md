# 📈 股市推播機器人

透過 Yahoo Finance 自動分析台股與美股市場，並將分析報告推播到 Discord。

## ✨ 功能特色

### 1. 大盤趨勢分析
- 台灣加權指數 (TWII)
- 美股四大指數 (S&P 500、道瓊、那斯達克、費城半導體)
- 技術指標分析 (均線、RSI、MACD)
- 趨勢判定與分數評估

### 2. 強勢類股篩選
- 台股七大類股分析
- 美股七大類股分析
- 類股強度排行
- 類股內強勢個股推薦

### 3. 未來走勢預測
- 基於技術分析的趨勢預測
- 樞紐點與斐波那契支撐壓力
- 目標價位預估
- 風險提示

### 4. Discord 推播
- 精美的 Embed 訊息格式
- 每日自動報告
- 手動觸發分析

---

## 🚀 快速開始

### 步驟 1：安裝依賴

```bash
pip install -r requirements.txt
```

### 步驟 2：設定 Discord Webhook

1. 在 Discord 頻道設定中，選擇「整合」→「Webhook」
2. 建立新的 Webhook，複製 URL
3. 編輯 `config/settings.py`，將 `DISCORD_WEBHOOK_URL` 替換成你的 URL

```python
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/YOUR_WEBHOOK_URL"
```

### 步驟 3：執行

```bash
# 執行一次完整分析並推播
python main.py

# 僅分析台股
python main.py --market tw

# 僅分析美股
python main.py --market us

# 快速模式（僅大盤）
python main.py --quick

# 不發送 Discord，僅在終端機顯示
python main.py --mode print

# 啟動排程模式（持續運行）
python main.py --mode schedule
```

---

## 📁 專案結構

```
stock_bot/
├── main.py                 # 主程式進入點
├── requirements.txt        # Python 依賴套件
├── README.md              # 說明文件
├── config/
│   ├── __init__.py
│   └── settings.py        # 配置設定
└── modules/
    ├── __init__.py
    ├── data_fetcher.py    # 數據抓取模組
    ├── market_analyzer.py # 大盤分析模組
    ├── sector_scanner.py  # 類股掃描模組
    ├── predictor.py       # 趨勢預測模組
    └── discord_bot.py     # Discord 推播模組
```

---

## ⚙️ 配置說明

### 市場設定 (`config/settings.py`)

可以自訂要追蹤的類股與個股：

```python
MARKETS = {
    "TW": {
        "sectors": {
            "半導體": ["2330.TW", "2454.TW", ...],
            "金融": ["2881.TW", "2882.TW", ...],
            # 新增自訂類股
            "我的自選": ["代碼1.TW", "代碼2.TW", ...],
        }
    },
    "US": {
        "sectors": {
            "科技巨頭": ["AAPL", "MSFT", ...],
            # 新增自訂類股
        }
    }
}
```

### 技術指標參數

```python
TECHNICAL_PARAMS = {
    "sma_short": 5,      # 短期均線
    "sma_medium": 20,    # 中期均線
    "sma_long": 60,      # 長期均線
    "rsi_period": 14,    # RSI 週期
    # ...
}
```

### 排程時間

```python
SCHEDULE = {
    "tw_market_close": "14:30",  # 台股收盤後
    "us_market_close": "05:30",  # 美股收盤後（台灣時間）
}
```

---

## 📊 Discord 訊息範例

機器人會發送以下類型的訊息：

### 大盤分析
```
📊 台股大盤分析報告
━━━━━━━━━━━━━━━
🚀 台灣加權指數
收盤價: 22,456.78
漲跌: +156.32 (+0.70%)
趨勢判定: 強勢多頭 (分數: 65)
━━━━━━━━━━━━━━━
技術指標:
RSI: 58.5 | MACD柱: +45.2 | 量能: 1.3x
```

### 類股排行
```
🏭 類股強弱分析
1. 🚀 半導體 | 強度: 75 | +2.3%
2. 📈 AI概念 | 強度: 68 | +1.8%
3. 📈 電子零組件 | 強度: 62 | +1.2%
```

### 強勢個股
```
💎 今日強勢個股
━━━━━━━━━━━━━━━
🔥 2330.TW - 台積電
現價: 985.00 | 漲跌: +2.5%
強度: 82/100 | RSI: 62
✅ 買入訊號 | 🔥 強勢上漲
```

---

## 🔧 進階使用

### 程式化使用

```python
from modules import DataFetcher, MarketAnalyzer, SectorScanner

# 初始化
fetcher = DataFetcher()
analyzer = MarketAnalyzer(fetcher)

# 分析單一股票
data = fetcher.get_stock_data("2330.TW")
print(data.tail())

# 分析大盤
tw_market = analyzer.analyze_taiwan_market()
print(f"趨勢: {tw_market.trend.value}")
```

### Docker 部署

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY . .
RUN pip install -r requirements.txt

CMD ["python", "main.py", "--mode", "schedule"]
```

### 系統服務 (Linux)

建立 `/etc/systemd/system/stock-bot.service`:

```ini
[Unit]
Description=Stock Bot
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/stock_bot
ExecStart=/usr/bin/python3 main.py --mode schedule
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable stock-bot
sudo systemctl start stock-bot
```

---

## ⚠️ 免責聲明

- 本工具僅供學習與參考用途
- 所有分析結果不構成投資建議
- 投資有風險，請依個人風險承受度審慎評估
- 過去績效不代表未來表現

---

## 📝 更新日誌

### v1.0.0 (2025-02)
- 初始版本
- 支援台股與美股分析
- Discord Webhook 推播
- 自動排程功能

---

## 🤝 貢獻

歡迎提交 Issue 或 Pull Request！

## 📄 授權

MIT License
