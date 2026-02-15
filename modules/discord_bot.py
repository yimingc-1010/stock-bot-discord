"""
Discord 推播模組
透過 Webhook 發送股市分析報告到 Discord
"""

import requests
import json
from typing import Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass
import logging

from .market_analyzer import MarketAnalysis, TrendDirection
from .sector_scanner import SectorAnalysis, StockAnalysis
from .predictor import PricePrediction, MarketOutlook, PredictionDirection

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DiscordNotifier:
    """Discord 通知發送器"""

    def __init__(self, webhook_url: str):
        """
        初始化 Discord 通知器

        Args:
            webhook_url: Discord Webhook URL
        """
        self.webhook_url = webhook_url
        self.colors = {
            "bullish": 0x00FF00,      # 綠色
            "bearish": 0xFF0000,      # 紅色
            "neutral": 0xFFFF00,      # 黃色
            "info": 0x0099FF,         # 藍色
            "warning": 0xFF9900,      # 橘色
        }

    def _get_trend_emoji(self, trend: TrendDirection) -> str:
        """獲取趨勢對應的 emoji"""
        emoji_map = {
            TrendDirection.STRONG_BULLISH: "🚀",
            TrendDirection.BULLISH: "📈",
            TrendDirection.NEUTRAL: "➡️",
            TrendDirection.BEARISH: "📉",
            TrendDirection.STRONG_BEARISH: "💥",
        }
        return emoji_map.get(trend, "❓")

    def _get_direction_emoji(self, direction: PredictionDirection) -> str:
        """獲取預測方向對應的 emoji"""
        emoji_map = {
            PredictionDirection.STRONG_UP: "🚀",
            PredictionDirection.UP: "📈",
            PredictionDirection.NEUTRAL: "➡️",
            PredictionDirection.DOWN: "📉",
            PredictionDirection.STRONG_DOWN: "💥",
        }
        return emoji_map.get(direction, "❓")

    def _get_trend_color(self, trend: TrendDirection) -> int:
        """獲取趨勢對應的顏色"""
        if trend in [TrendDirection.STRONG_BULLISH, TrendDirection.BULLISH]:
            return self.colors["bullish"]
        elif trend in [TrendDirection.STRONG_BEARISH, TrendDirection.BEARISH]:
            return self.colors["bearish"]
        return self.colors["neutral"]

    def send_message(self, content: str = None, embeds: List[Dict] = None) -> bool:
        """
        發送訊息到 Discord

        Args:
            content: 純文字內容
            embeds: 嵌入式訊息列表

        Returns:
            是否發送成功
        """
        if not self.webhook_url or self.webhook_url == "YOUR_DISCORD_WEBHOOK_URL_HERE":
            logger.warning("Discord Webhook URL 尚未設定")
            return False

        payload = {}
        if content:
            payload["content"] = content
        if embeds:
            payload["embeds"] = embeds

        try:
            response = requests.post(
                self.webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            logger.info("Discord 訊息發送成功")
            return True
        except Exception as e:
            logger.error(f"發送 Discord 訊息失敗: {e}")
            return False

    def send_market_analysis(
        self,
        analyses: Dict[str, MarketAnalysis],
        market_name: str = "市場"
    ) -> bool:
        """
        發送大盤分析報告

        Args:
            analyses: 指數分析結果字典
            market_name: 市場名稱

        Returns:
            是否發送成功
        """
        now = datetime.now().strftime("%Y-%m-%d %H:%M")

        embeds = []

        # 標題 embed
        header_embed = {
            "title": f"📊 {market_name}大盤分析報告",
            "description": f"更新時間: {now}",
            "color": self.colors["info"]
        }
        embeds.append(header_embed)

        # 各指數 embed
        for symbol, analysis in analyses.items():
            emoji = self._get_trend_emoji(analysis.trend)
            color = self._get_trend_color(analysis.trend)

            # 漲跌符號
            change_sign = "+" if analysis.price_change >= 0 else ""

            embed = {
                "title": f"{emoji} {analysis.name}",
                "color": color,
                "fields": [
                    {
                        "name": "收盤價",
                        "value": f"{analysis.current_price:,.2f}",
                        "inline": True
                    },
                    {
                        "name": "漲跌",
                        "value": f"{change_sign}{analysis.price_change:,.2f} ({change_sign}{analysis.price_change_pct:.2f}%)",
                        "inline": True
                    },
                    {
                        "name": "趨勢判定",
                        "value": f"{analysis.trend.value} (分數: {analysis.trend_score})",
                        "inline": True
                    },
                    {
                        "name": "技術指標",
                        "value": (
                            f"RSI: {analysis.rsi:.1f}\n"
                            f"MACD 柱: {analysis.macd_histogram:+.2f}\n"
                            f"量能: {analysis.volume_ratio:.1f}x"
                        ),
                        "inline": True
                    },
                    {
                        "name": "均線位置",
                        "value": (
                            f"5MA: {analysis.sma_5:,.2f}\n"
                            f"20MA: {analysis.sma_20:,.2f}\n"
                            f"60MA: {analysis.sma_60:,.2f}"
                        ),
                        "inline": True
                    },
                    {
                        "name": "支撐/壓力",
                        "value": (
                            f"支撐: {analysis.support_level:,.2f}\n"
                            f"壓力: {analysis.resistance_level:,.2f}"
                        ),
                        "inline": True
                    },
                    {
                        "name": "📝 分析摘要",
                        "value": analysis.analysis_summary,
                        "inline": False
                    }
                ]
            }
            embeds.append(embed)

        return self.send_message(embeds=embeds)

    def send_sector_analysis(
        self,
        sector_analyses: List[SectorAnalysis],
        market_name: str = "市場"
    ) -> bool:
        """
        發送類股分析報告

        Args:
            sector_analyses: 類股分析結果列表
            market_name: 市場名稱

        Returns:
            是否發送成功
        """
        now = datetime.now().strftime("%Y-%m-%d %H:%M")

        embeds = []

        # 標題
        header_embed = {
            "title": f"🏭 {market_name}類股強弱分析",
            "description": f"更新時間: {now}\n按強度分數排序，分數越高越強勢",
            "color": self.colors["info"]
        }
        embeds.append(header_embed)

        # 類股排行
        sector_lines = []
        for i, sector in enumerate(sector_analyses[:8], 1):
            emoji = self._get_trend_emoji(sector.trend)
            change_sign = "+" if sector.avg_change_pct >= 0 else ""
            sector_lines.append(
                f"{i}. {emoji} **{sector.name}** | "
                f"強度: {sector.strength_score:.0f} | "
                f"漲跌: {change_sign}{sector.avg_change_pct:.2f}%"
            )

        ranking_embed = {
            "title": "📊 類股排行榜",
            "description": "\n".join(sector_lines),
            "color": self.colors["info"]
        }
        embeds.append(ranking_embed)

        # 強勢類股詳情
        strong_sectors = [s for s in sector_analyses if s.strength_score >= 60][:3]
        for sector in strong_sectors:
            stock_lines = []
            for stock in sector.top_stocks[:3]:
                change_sign = "+" if stock.price_change_pct >= 0 else ""
                stock_lines.append(
                    f"• **{stock.symbol}** {stock.name}\n"
                    f"  漲跌: {change_sign}{stock.price_change_pct:.2f}% | "
                    f"強度: {stock.strength_score:.0f}\n"
                    f"  {stock.analysis_note}"
                )

            embed = {
                "title": f"🔥 強勢類股: {sector.name}",
                "description": "\n".join(stock_lines),
                "color": self.colors["bullish"],
                "fields": [
                    {
                        "name": "類股統計",
                        "value": f"平均漲幅: {sector.avg_change_pct:+.2f}% | 多方股數: {sector.bullish_count}/{sector.stock_count}",
                        "inline": False
                    }
                ]
            }
            embeds.append(embed)

        return self.send_message(embeds=embeds)

    def send_stock_recommendations(
        self,
        stocks: List[StockAnalysis],
        title: str = "強勢個股推薦"
    ) -> bool:
        """
        發送個股推薦

        Args:
            stocks: 個股分析列表
            title: 標題

        Returns:
            是否發送成功
        """
        now = datetime.now().strftime("%Y-%m-%d %H:%M")

        embeds = []

        header_embed = {
            "title": f"💎 {title}",
            "description": f"更新時間: {now}\n以下為符合篩選條件的強勢個股",
            "color": self.colors["info"]
        }
        embeds.append(header_embed)

        for stock in stocks[:10]:
            change_sign = "+" if stock.price_change_pct >= 0 else ""
            buy_signal = "✅ 買入訊號" if stock.buy_signal else ""

            embed = {
                "title": f"{'🔥' if stock.buy_signal else '📈'} {stock.symbol} - {stock.name}",
                "color": self.colors["bullish"] if stock.buy_signal else self.colors["info"],
                "fields": [
                    {
                        "name": "現價",
                        "value": f"{stock.current_price:,.2f}",
                        "inline": True
                    },
                    {
                        "name": "漲跌幅",
                        "value": f"{change_sign}{stock.price_change_pct:.2f}%",
                        "inline": True
                    },
                    {
                        "name": "強度分數",
                        "value": f"{stock.strength_score:.0f}/100",
                        "inline": True
                    },
                    {
                        "name": "RSI",
                        "value": f"{stock.rsi:.1f}",
                        "inline": True
                    },
                    {
                        "name": "量能",
                        "value": f"{stock.volume_ratio:.1f}x",
                        "inline": True
                    },
                    {
                        "name": "類股",
                        "value": stock.sector,
                        "inline": True
                    },
                    {
                        "name": "分析",
                        "value": f"{buy_signal} {stock.analysis_note}",
                        "inline": False
                    }
                ]
            }
            embeds.append(embed)

        return self.send_message(embeds=embeds)

    def send_prediction(
        self,
        prediction: PricePrediction
    ) -> bool:
        """
        發送個股預測

        Args:
            prediction: 價格預測結果

        Returns:
            是否發送成功
        """
        emoji = self._get_direction_emoji(prediction.predicted_direction)

        if prediction.predicted_direction in [PredictionDirection.STRONG_UP, PredictionDirection.UP]:
            color = self.colors["bullish"]
        elif prediction.predicted_direction in [PredictionDirection.STRONG_DOWN, PredictionDirection.DOWN]:
            color = self.colors["bearish"]
        else:
            color = self.colors["neutral"]

        factors_text = "\n".join([f"• {f}" for f in prediction.key_factors])

        embed = {
            "title": f"{emoji} {prediction.symbol} - {prediction.name} 走勢預測",
            "color": color,
            "fields": [
                {
                    "name": "現價",
                    "value": f"{prediction.current_price:,.2f}",
                    "inline": True
                },
                {
                    "name": "預測方向",
                    "value": prediction.predicted_direction.value,
                    "inline": True
                },
                {
                    "name": "信心度",
                    "value": prediction.confidence.value,
                    "inline": True
                },
                {
                    "name": "目標價位區間",
                    "value": f"{prediction.target_price_low:,.2f} ~ {prediction.target_price_high:,.2f}",
                    "inline": True
                },
                {
                    "name": "預測週期",
                    "value": prediction.time_horizon,
                    "inline": True
                },
                {
                    "name": "風險提示",
                    "value": prediction.risk_warning,
                    "inline": True
                },
                {
                    "name": "關鍵因素",
                    "value": factors_text,
                    "inline": False
                },
                {
                    "name": "支撐位",
                    "value": " / ".join([f"{s:,.2f}" for s in prediction.support_levels[:3]]),
                    "inline": True
                },
                {
                    "name": "壓力位",
                    "value": " / ".join([f"{r:,.2f}" for r in prediction.resistance_levels[:3]]),
                    "inline": True
                }
            ],
            "footer": {
                "text": "⚠️ 以上預測僅供參考，投資有風險，請審慎評估"
            }
        }

        return self.send_message(embeds=[embed])

    def send_market_outlook(
        self,
        outlook: MarketOutlook
    ) -> bool:
        """
        發送市場展望

        Args:
            outlook: 市場展望

        Returns:
            是否發送成功
        """
        emoji = self._get_direction_emoji(outlook.overall_direction)

        if outlook.overall_direction in [PredictionDirection.STRONG_UP, PredictionDirection.UP]:
            color = self.colors["bullish"]
        elif outlook.overall_direction in [PredictionDirection.STRONG_DOWN, PredictionDirection.DOWN]:
            color = self.colors["bearish"]
        else:
            color = self.colors["neutral"]

        now = datetime.now().strftime("%Y-%m-%d %H:%M")

        observations = "\n".join([f"• {o}" for o in outlook.key_observations])
        bullish = "\n".join([f"• {b}" for b in outlook.bullish_factors]) or "無"
        bearish = "\n".join([f"• {b}" for b in outlook.bearish_factors]) or "無"

        embed = {
            "title": f"{emoji} {outlook.market_name} 市場展望",
            "description": f"更新時間: {now}",
            "color": color,
            "fields": [
                {
                    "name": "整體方向",
                    "value": outlook.overall_direction.value,
                    "inline": True
                },
                {
                    "name": "信心度",
                    "value": outlook.confidence.value,
                    "inline": True
                },
                {
                    "name": "風險等級",
                    "value": outlook.risk_level,
                    "inline": True
                },
                {
                    "name": "📊 市場觀察",
                    "value": observations,
                    "inline": False
                },
                {
                    "name": "📈 多方因素",
                    "value": bullish,
                    "inline": True
                },
                {
                    "name": "📉 空方因素",
                    "value": bearish,
                    "inline": True
                },
                {
                    "name": "💡 建議策略",
                    "value": outlook.recommended_strategy,
                    "inline": False
                }
            ],
            "footer": {
                "text": "⚠️ 以上分析僅供參考，投資有風險，請審慎評估"
            }
        }

        return self.send_message(embeds=[embed])

    def send_discovery_report(
        self,
        discoveries: Dict[str, List[StockAnalysis]],
    ) -> bool:
        """
        發送市場雷達（動態發現）報告

        Args:
            discoveries: {"tw": [StockAnalysis, ...], "us": [...]}

        Returns:
            是否發送成功
        """
        now = datetime.now().strftime("%Y-%m-%d %H:%M")

        all_stocks: List[StockAnalysis] = []
        for market_stocks in discoveries.values():
            all_stocks.extend(market_stocks)

        if not all_stocks:
            return True  # 沒有發現結果，靜默跳過

        all_stocks.sort(key=lambda x: x.strength_score, reverse=True)

        embeds = []

        header_embed = {
            "title": "📡 市場雷達 — 今日量能動能領先股",
            "description": (
                f"更新時間: {now}\n"
                "以下為觀察名單外，今日量能放大且動能領先的個股"
            ),
            "color": self.colors["info"],
        }
        embeds.append(header_embed)

        for stock in all_stocks[:10]:
            change_sign = "+" if stock.price_change_pct >= 0 else ""

            embed = {
                "title": f"📡 {stock.symbol} - {stock.name}",
                "color": self.colors["bullish"] if stock.buy_signal else self.colors["info"],
                "fields": [
                    {
                        "name": "現價",
                        "value": f"{stock.current_price:,.2f}",
                        "inline": True,
                    },
                    {
                        "name": "漲跌幅",
                        "value": f"{change_sign}{stock.price_change_pct:.2f}%",
                        "inline": True,
                    },
                    {
                        "name": "強度分數",
                        "value": f"{stock.strength_score:.0f}/100",
                        "inline": True,
                    },
                    {
                        "name": "量能",
                        "value": f"{stock.volume_ratio:.1f}x",
                        "inline": True,
                    },
                    {
                        "name": "RSI",
                        "value": f"{stock.rsi:.1f}",
                        "inline": True,
                    },
                    {
                        "name": "分析",
                        "value": stock.analysis_note or "—",
                        "inline": False,
                    },
                ],
            }
            embeds.append(embed)

        return self.send_message(embeds=embeds)

    def send_daily_report(
        self,
        tw_index_analysis: Optional[MarketAnalysis],
        us_analyses: Dict[str, MarketAnalysis],
        tw_sectors: List[SectorAnalysis],
        us_sectors: List[SectorAnalysis],
        tw_outlook: Optional[MarketOutlook],
        us_outlook: Optional[MarketOutlook],
        top_stocks: List[StockAnalysis]
    ) -> bool:
        """
        發送每日完整報告

        Args:
            各項分析結果

        Returns:
            是否發送成功
        """
        success = True
        now = datetime.now().strftime("%Y-%m-%d")

        # 發送開頭
        self.send_message(content=f"# 📈 {now} 每日股市分析報告\n---")

        # 台股大盤分析
        if tw_index_analysis:
            self.send_market_analysis({"^TWII": tw_index_analysis}, "台股")

        # 美股大盤分析
        if us_analyses:
            self.send_market_analysis(us_analyses, "美股")

        # 台股類股分析
        if tw_sectors:
            self.send_sector_analysis(tw_sectors, "台股")

        # 美股類股分析
        if us_sectors:
            self.send_sector_analysis(us_sectors, "美股")

        # 市場展望
        if tw_outlook:
            self.send_market_outlook(tw_outlook)

        if us_outlook:
            self.send_market_outlook(us_outlook)

        # 強勢個股推薦
        if top_stocks:
            self.send_stock_recommendations(top_stocks, "今日強勢個股")

        # 結尾
        self.send_message(
            content=(
                "---\n"
                "⚠️ **免責聲明**: 以上分析僅供參考，不構成投資建議。\n"
                "投資有風險，請依個人風險承受度審慎評估。"
            )
        )

        return success


if __name__ == "__main__":
    # 測試
    notifier = DiscordNotifier("YOUR_WEBHOOK_URL")

    # 測試發送純文字
    notifier.send_message(content="這是測試訊息")
