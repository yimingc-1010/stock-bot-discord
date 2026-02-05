#!/bin/bash
# 股市推播機器人啟動腳本

cd "$(dirname "$0")"

echo "📈 股市推播機器人"
echo "=================="
echo ""

# 檢查 Python
if ! command -v python3 &> /dev/null; then
    echo "❌ 請先安裝 Python 3"
    exit 1
fi

# 檢查並安裝依賴
echo "📦 檢查依賴套件..."
pip3 install -r requirements.txt -q 2>/dev/null

echo ""
echo "請選擇執行模式:"
echo "  1) 分析並顯示結果 (不發送 Discord)"
echo "  2) 分析並發送到 Discord"
echo "  3) 啟動每日自動排程"
echo "  4) 僅分析台股"
echo "  5) 僅分析美股"
echo ""
read -p "請輸入選項 (1-5): " choice

case $choice in
    1)
        python3 main.py --mode print
        ;;
    2)
        python3 main.py
        ;;
    3)
        python3 main.py --mode schedule
        ;;
    4)
        python3 main.py --mode print --market tw
        ;;
    5)
        python3 main.py --mode print --market us
        ;;
    *)
        echo "無效選項"
        exit 1
        ;;
esac
