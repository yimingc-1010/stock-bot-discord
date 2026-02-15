#!/usr/bin/env python3
"""
股市推播機器人 - 主程式
透過 Yahoo Finance 分析股市並推播到 Discord
"""

import sys
import argparse
import schedule
import time
from datetime import datetime
import logging

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('stock_bot.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

# 導入模組
from config.settings import DISCORD_WEBHOOK_URL, MARKETS, SCHEDULE
from modules.data_fetcher import DataFetcher
from modules.market_analyzer import MarketAnalyzer
from modules.sector_scanner import SectorScanner
from modules.predictor import TrendPredictor
from modules.discord_bot import DiscordNotifier
from modules.stock_discovery import StockDiscovery


class StockBot:
    """股市推播機器人"""

    def __init__(self, webhook_url: str = None, enable_discovery: bool = True):
        """
        初始化機器人

        Args:
            webhook_url: Discord Webhook URL (可選，預設使用設定檔)
            enable_discovery: 是否啟用動態發現功能
        """
        self.webhook_url = webhook_url or DISCORD_WEBHOOK_URL
        self.fetcher = DataFetcher()
        self.analyzer = MarketAnalyzer(self.fetcher)
        self.scanner = SectorScanner(self.fetcher)
        self.predictor = TrendPredictor(self.fetcher)
        self.notifier = DiscordNotifier(self.webhook_url)
        self.enable_discovery = enable_discovery
        self.discovery = StockDiscovery(self.fetcher, self.scanner)

        logger.info("股市推播機器人初始化完成")

    def analyze_taiwan_market(self):
        """分析台股市場"""
        logger.info("開始分析台股市場...")

        # 大盤分析
        tw_index = self.analyzer.analyze_taiwan_market()

        # 類股分析
        tw_sectors = self.scanner.scan_all_sectors(MARKETS["TW"]["sectors"])

        # 市場展望
        tw_outlook = None
        if tw_index:
            tw_outlook = self.predictor.generate_market_outlook(
                "台股", tw_index, tw_sectors
            )

        # 取得強勢個股
        top_tw_stocks = self.scanner.get_top_stocks(tw_sectors, top_n=5)
        buy_signals = self.scanner.get_buy_signals(tw_sectors)

        return {
            "index": tw_index,
            "sectors": tw_sectors,
            "outlook": tw_outlook,
            "top_stocks": top_tw_stocks,
            "buy_signals": buy_signals
        }

    def analyze_us_market(self):
        """分析美股市場"""
        logger.info("開始分析美股市場...")

        # 主要指數分析
        us_indices = self.analyzer.analyze_us_markets()

        # 類股分析
        us_sectors = self.scanner.scan_all_sectors(MARKETS["US"]["sectors"])

        # 市場展望 (使用 S&P 500 作為主要參考)
        us_outlook = None
        sp500 = us_indices.get("^GSPC")
        if sp500:
            us_outlook = self.predictor.generate_market_outlook(
                "美股", sp500, us_sectors
            )

        # 取得強勢個股
        top_us_stocks = self.scanner.get_top_stocks(us_sectors, top_n=5)
        buy_signals = self.scanner.get_buy_signals(us_sectors)

        return {
            "indices": us_indices,
            "sectors": us_sectors,
            "outlook": us_outlook,
            "top_stocks": top_us_stocks,
            "buy_signals": buy_signals
        }

    def run_analysis(self, market: str = "all"):
        """
        執行市場分析

        Args:
            market: 市場選擇 ("tw", "us", "all")
        """
        logger.info(f"執行 {market} 市場分析...")

        try:
            if market in ["tw", "all"]:
                tw_result = self.analyze_taiwan_market()
            else:
                tw_result = None

            if market in ["us", "all"]:
                us_result = self.analyze_us_market()
            else:
                us_result = None

            # 動態發現
            discoveries = {}
            if self.enable_discovery:
                try:
                    discoveries = self.discovery.discover(market=market, top_n=10)
                except Exception as e:
                    logger.warning(f"動態發現失敗: {e}")

            return {
                "tw": tw_result,
                "us": us_result,
                "discoveries": discoveries,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"分析過程發生錯誤: {e}")
            raise

    def send_daily_report(self, market: str = "all"):
        """
        發送每日報告

        Args:
            market: 市場選擇 ("tw", "us", "all")
        """
        logger.info("開始產生每日報告...")

        try:
            result = self.run_analysis(market)

            # 準備資料
            tw_index = result["tw"]["index"] if result.get("tw") else None
            us_indices = result["us"]["indices"] if result.get("us") else {}
            tw_sectors = result["tw"]["sectors"] if result.get("tw") else []
            us_sectors = result["us"]["sectors"] if result.get("us") else []
            tw_outlook = result["tw"]["outlook"] if result.get("tw") else None
            us_outlook = result["us"]["outlook"] if result.get("us") else None

            # 合併強勢股
            all_top_stocks = []
            if result.get("tw"):
                all_top_stocks.extend(result["tw"]["top_stocks"])
            if result.get("us"):
                all_top_stocks.extend(result["us"]["top_stocks"])

            # 按強度排序
            all_top_stocks.sort(key=lambda x: x.strength_score, reverse=True)

            # 發送報告
            self.notifier.send_daily_report(
                tw_index_analysis=tw_index,
                us_analyses=us_indices,
                tw_sectors=tw_sectors,
                us_sectors=us_sectors,
                tw_outlook=tw_outlook,
                us_outlook=us_outlook,
                top_stocks=all_top_stocks[:10]
            )

            # 發送動態發現報告
            discoveries = result.get("discoveries", {})
            if discoveries:
                self.notifier.send_discovery_report(discoveries)

            logger.info("每日報告發送完成")

        except Exception as e:
            logger.error(f"發送報告時發生錯誤: {e}")
            self.notifier.send_message(
                content=f"⚠️ 報告產生失敗: {str(e)}"
            )

    def send_quick_update(self, market: str = "all"):
        """
        發送快速更新 (僅大盤)

        Args:
            market: 市場選擇
        """
        logger.info("發送快速更新...")

        try:
            if market in ["tw", "all"]:
                tw_index = self.analyzer.analyze_taiwan_market()
                if tw_index:
                    self.notifier.send_market_analysis(
                        {"^TWII": tw_index}, "台股"
                    )

            if market in ["us", "all"]:
                us_indices = self.analyzer.analyze_us_markets()
                if us_indices:
                    self.notifier.send_market_analysis(us_indices, "美股")

            logger.info("快速更新發送完成")

        except Exception as e:
            logger.error(f"快速更新失敗: {e}")

    def start_scheduler(self):
        """啟動排程器"""
        logger.info("啟動排程器...")

        # 台股收盤後分析 (台灣時間 14:30)
        schedule.every().monday.at(SCHEDULE["tw_market_close"]).do(
            self.send_daily_report, market="tw"
        )
        schedule.every().tuesday.at(SCHEDULE["tw_market_close"]).do(
            self.send_daily_report, market="tw"
        )
        schedule.every().wednesday.at(SCHEDULE["tw_market_close"]).do(
            self.send_daily_report, market="tw"
        )
        schedule.every().thursday.at(SCHEDULE["tw_market_close"]).do(
            self.send_daily_report, market="tw"
        )
        schedule.every().friday.at(SCHEDULE["tw_market_close"]).do(
            self.send_daily_report, market="tw"
        )

        # 美股收盤後分析 (台灣時間約 05:30，次日執行)
        schedule.every().tuesday.at(SCHEDULE["us_market_close"]).do(
            self.send_daily_report, market="us"
        )
        schedule.every().wednesday.at(SCHEDULE["us_market_close"]).do(
            self.send_daily_report, market="us"
        )
        schedule.every().thursday.at(SCHEDULE["us_market_close"]).do(
            self.send_daily_report, market="us"
        )
        schedule.every().friday.at(SCHEDULE["us_market_close"]).do(
            self.send_daily_report, market="us"
        )
        schedule.every().saturday.at(SCHEDULE["us_market_close"]).do(
            self.send_daily_report, market="us"
        )

        logger.info("排程設定完成")
        logger.info(f"  台股分析時間: 週一至週五 {SCHEDULE['tw_market_close']}")
        logger.info(f"  美股分析時間: 週二至週六 {SCHEDULE['us_market_close']}")

        # 通知啟動
        self.notifier.send_message(
            content="🤖 **股市推播機器人已啟動**\n自動排程分析已開始運行"
        )

        # 執行排程
        while True:
            schedule.run_pending()
            time.sleep(60)

    def print_analysis(self, market: str = "all"):
        """
        輸出分析結果到終端機 (不發送到 Discord)

        Args:
            market: 市場選擇
        """
        result = self.run_analysis(market)

        print("\n" + "=" * 60)
        print("股市分析報告")
        print("=" * 60)

        if result.get("tw"):
            tw = result["tw"]
            print("\n【台股市場】")

            if tw["index"]:
                idx = tw["index"]
                print(f"\n大盤: {idx.name}")
                print(f"  收盤: {idx.current_price:,.2f}")
                print(f"  漲跌: {idx.price_change:+,.2f} ({idx.price_change_pct:+.2f}%)")
                print(f"  趨勢: {idx.trend.value} (分數: {idx.trend_score})")
                print(f"  RSI: {idx.rsi:.1f}")

            if tw["sectors"]:
                print("\n類股排行:")
                for i, sector in enumerate(tw["sectors"][:5], 1):
                    print(f"  {i}. {sector.name}: {sector.strength_score:.0f} ({sector.avg_change_pct:+.2f}%)")

            if tw["outlook"]:
                outlook = tw["outlook"]
                print(f"\n市場展望: {outlook.overall_direction.value}")
                print(f"建議策略: {outlook.recommended_strategy}")

        if result.get("us"):
            us = result["us"]
            print("\n【美股市場】")

            if us["indices"]:
                for symbol, idx in us["indices"].items():
                    print(f"\n{idx.name}:")
                    print(f"  收盤: {idx.current_price:,.2f}")
                    print(f"  趨勢: {idx.trend.value}")

            if us["sectors"]:
                print("\n類股排行:")
                for i, sector in enumerate(us["sectors"][:5], 1):
                    print(f"  {i}. {sector.name}: {sector.strength_score:.0f}")

        # 動態發現
        discoveries = result.get("discoveries", {})
        if discoveries:
            print("\n【📡 市場雷達 — 量能動能領先股】")
            for mkt, stocks in discoveries.items():
                if stocks:
                    mkt_name = "台股" if mkt == "tw" else "美股"
                    print(f"\n{mkt_name}:")
                    for i, stock in enumerate(stocks[:5], 1):
                        print(
                            f"  {i}. {stock.symbol} ({stock.name}): "
                            f"強度 {stock.strength_score:.0f} | "
                            f"漲跌 {stock.price_change_pct:+.2f}% | "
                            f"量能 {stock.volume_ratio:.1f}x"
                        )

        print("\n" + "=" * 60)


def main():
    """主程式進入點"""
    parser = argparse.ArgumentParser(
        description="股市推播機器人 - 透過 Yahoo Finance 分析股市並推播到 Discord"
    )

    parser.add_argument(
        "--mode", "-m",
        choices=["once", "schedule", "print"],
        default="once",
        help="執行模式: once=執行一次並發送, schedule=排程模式, print=僅輸出不發送"
    )

    parser.add_argument(
        "--market", "-k",
        choices=["tw", "us", "all"],
        default="all",
        help="分析市場: tw=台股, us=美股, all=全部"
    )

    parser.add_argument(
        "--webhook", "-w",
        help="Discord Webhook URL (覆蓋設定檔)"
    )

    parser.add_argument(
        "--quick", "-q",
        action="store_true",
        help="快速模式 (僅大盤分析)"
    )

    parser.add_argument(
        "--no-discovery",
        action="store_true",
        help="停用動態股票發現功能"
    )

    args = parser.parse_args()

    # 初始化機器人（快速模式或明確停用時關閉發現功能）
    enable_discovery = not args.no_discovery and not args.quick
    bot = StockBot(webhook_url=args.webhook, enable_discovery=enable_discovery)

    if args.mode == "schedule":
        # 排程模式
        bot.start_scheduler()

    elif args.mode == "print":
        # 僅輸出模式
        bot.print_analysis(market=args.market)

    else:
        # 執行一次模式
        if args.quick:
            bot.send_quick_update(market=args.market)
        else:
            bot.send_daily_report(market=args.market)


if __name__ == "__main__":
    main()
