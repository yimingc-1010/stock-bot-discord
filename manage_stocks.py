#!/usr/bin/env python3
"""
股票清單管理工具
用於新增、移除、查看追蹤的股票與類股
"""

import sys
import json
sys.path.insert(0, '.')

from config.settings import (
    load_markets, save_markets,
    add_stock, remove_stock,
    add_sector, remove_sector,
    STOCKS_FILE
)


def show_menu():
    """顯示主選單"""
    print("\n" + "=" * 50)
    print("📈 股票清單管理工具")
    print("=" * 50)
    print("1. 查看所有股票")
    print("2. 新增股票")
    print("3. 移除股票")
    print("4. 新增類股")
    print("5. 移除類股")
    print("6. 匯出設定")
    print("7. 離開")
    print("=" * 50)


def show_all_stocks():
    """顯示所有股票"""
    markets = load_markets()

    for market_key, market_data in markets.items():
        print(f"\n{'=' * 40}")
        print(f"📊 {market_data['name']} ({market_key})")
        print(f"{'=' * 40}")

        if "index_symbol" in market_data:
            print(f"  大盤指數: {market_data['index_symbol']}")

        if "indices" in market_data:
            print(f"\n  主要指數:")
            for name, symbol in market_data["indices"].items():
                print(f"    - {name}: {symbol}")

        print(f"\n  類股與個股:")
        for sector, stocks in market_data.get("sectors", {}).items():
            print(f"\n  【{sector}】({len(stocks)} 檔)")
            for stock in stocks:
                print(f"      {stock}")


def interactive_add_stock():
    """互動式新增股票"""
    print("\n--- 新增股票 ---")

    market = input("市場 (TW/US): ").strip().upper()
    if market not in ["TW", "US"]:
        print("❌ 無效的市場")
        return

    markets = load_markets()
    sectors = list(markets[market].get("sectors", {}).keys())

    if sectors:
        print(f"\n現有類股: {', '.join(sectors)}")

    sector = input("類股名稱 (輸入現有或新建): ").strip()
    if not sector:
        print("❌ 類股名稱不能為空")
        return

    symbol = input("股票代碼: ").strip().upper()
    if not symbol:
        print("❌ 股票代碼不能為空")
        return

    # 自動補上 .TW 後綴
    if market == "TW" and not symbol.endswith(".TW"):
        symbol = f"{symbol}.TW"

    if add_stock(market, sector, symbol):
        print(f"✅ 已新增 {symbol} 到 {market} - {sector}")
    else:
        print(f"❌ 新增失敗（可能已存在）")


def interactive_remove_stock():
    """互動式移除股票"""
    print("\n--- 移除股票 ---")

    market = input("市場 (TW/US): ").strip().upper()
    if market not in ["TW", "US"]:
        print("❌ 無效的市場")
        return

    markets = load_markets()
    sectors = markets[market].get("sectors", {})

    if not sectors:
        print("❌ 該市場沒有類股")
        return

    print(f"\n現有類股: {', '.join(sectors.keys())}")
    sector = input("類股名稱: ").strip()

    if sector not in sectors:
        print("❌ 找不到該類股")
        return

    print(f"\n該類股的股票: {', '.join(sectors[sector])}")
    symbol = input("要移除的股票代碼: ").strip().upper()

    if market == "TW" and not symbol.endswith(".TW"):
        symbol = f"{symbol}.TW"

    if remove_stock(market, sector, symbol):
        print(f"✅ 已從 {sector} 移除 {symbol}")
    else:
        print(f"❌ 移除失敗（可能不存在）")


def interactive_add_sector():
    """互動式新增類股"""
    print("\n--- 新增類股 ---")

    market = input("市場 (TW/US): ").strip().upper()
    if market not in ["TW", "US"]:
        print("❌ 無效的市場")
        return

    sector = input("新類股名稱: ").strip()
    if not sector:
        print("❌ 類股名稱不能為空")
        return

    stocks_input = input("股票代碼 (用逗號分隔，可留空): ").strip()

    stocks = []
    if stocks_input:
        for s in stocks_input.split(","):
            symbol = s.strip().upper()
            if market == "TW" and not symbol.endswith(".TW"):
                symbol = f"{symbol}.TW"
            stocks.append(symbol)

    if add_sector(market, sector, stocks):
        print(f"✅ 已新增類股 {sector}，包含 {len(stocks)} 檔股票")
    else:
        print(f"❌ 新增失敗")


def interactive_remove_sector():
    """互動式移除類股"""
    print("\n--- 移除類股 ---")

    market = input("市場 (TW/US): ").strip().upper()
    if market not in ["TW", "US"]:
        print("❌ 無效的市場")
        return

    markets = load_markets()
    sectors = list(markets[market].get("sectors", {}).keys())

    if not sectors:
        print("❌ 該市場沒有類股")
        return

    print(f"\n現有類股: {', '.join(sectors)}")
    sector = input("要移除的類股名稱: ").strip()

    confirm = input(f"⚠️ 確定要移除 {sector} 及其所有股票嗎？(y/N): ").strip().lower()
    if confirm != 'y':
        print("已取消")
        return

    if remove_sector(market, sector):
        print(f"✅ 已移除類股 {sector}")
    else:
        print(f"❌ 移除失敗")


def export_config():
    """匯出設定"""
    markets = load_markets()
    print(f"\n設定檔路徑: {STOCKS_FILE}")
    print("\n--- JSON 內容 ---")
    print(json.dumps(markets, ensure_ascii=False, indent=2))


def main():
    """主程式"""
    while True:
        show_menu()
        choice = input("\n請選擇 (1-7): ").strip()

        if choice == "1":
            show_all_stocks()
        elif choice == "2":
            interactive_add_stock()
        elif choice == "3":
            interactive_remove_stock()
        elif choice == "4":
            interactive_add_sector()
        elif choice == "5":
            interactive_remove_sector()
        elif choice == "6":
            export_config()
        elif choice == "7":
            print("\n👋 再見！")
            break
        else:
            print("❌ 無效選項")


if __name__ == "__main__":
    main()
