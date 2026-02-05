#!/bin/bash
# GitHub 設定腳本
# 請在終端機執行此腳本來推送程式碼到 GitHub

cd "$(dirname "$0")"

echo "🚀 設定 GitHub Repository..."

# 移除可能的 lock 檔案
rm -f .git/index.lock 2>/dev/null

# 初始化 Git（如果尚未初始化）
if [ ! -d ".git" ]; then
    git init
    git branch -M main
fi

# 添加檔案
git add .gitignore README.md requirements.txt run.sh main.py
git add config/__init__.py config/settings.example.py
git add modules/*.py
git add .github/workflows/stock-analysis.yml

# 提交
git commit -m "Initial commit: 股市推播機器人

功能：
- 透過 Yahoo Finance 抓取台股與美股數據
- 大盤趨勢分析（均線、RSI、MACD）
- 強勢類股與個股篩選
- 未來走勢預測
- Discord Webhook 推播
- 每日自動排程

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"

# 設定遠端並推送
git remote add origin git@github.com:yimingc-1010/stock-bot-discord.git 2>/dev/null || true
git branch -M main
git push -u origin main

echo ""
echo "✅ 程式碼已推送！"
echo ""
echo "📌 接下來請設定 GitHub Secrets："
echo "   1. 前往 https://github.com/yimingc-1010/stock-bot-discord/settings/secrets/actions"
echo "   2. 點擊 'New repository secret'"
echo "   3. Name: DISCORD_WEBHOOK_URL"
echo "   4. Secret: 你的 Discord Webhook URL"
echo ""
echo "🚀 設定完成後，GitHub Actions 會自動排程執行！"
