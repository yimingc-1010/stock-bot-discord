# Project Context

## Purpose
Stock Bot (股市推播機器人) — An automated stock market analysis system that analyzes Taiwan (TWSE) and US markets using Yahoo Finance data, runs technical analysis with trend scoring and buy-signal detection, and delivers rich reports to Discord via webhooks.

## Tech Stack
- **Language:** Python 3.11+
- **Data:** yfinance (Yahoo Finance), pandas, numpy
- **Notifications:** Discord Webhooks via requests
- **Scheduling:** schedule library, GitHub Actions (cron)
- **Configuration:** Python settings module + runtime-editable JSON (stocks.json)

## Project Conventions

### Code Style
- Modules live in `modules/` with one class per file
- Dataclasses for all structured results (MarketAnalysis, StockAnalysis, SectorAnalysis, PricePrediction)
- Enums for categorical values (TrendDirection, PredictionConfidence, PredictionDirection)
- Chinese-language user-facing strings (Discord messages, risk warnings); English for code identifiers and logs
- Logging via stdlib `logging` (INFO level, dual console + file handler)

### Architecture Patterns
- **Pipeline:** DataFetcher → MarketAnalyzer → SectorScanner → TrendPredictor → DiscordNotifier
- Each module is independently testable via `if __name__ == "__main__":` blocks
- Graceful degradation: individual failures return `None`; batch operations skip failed items
- 15-minute in-memory cache in DataFetcher to reduce API calls
- ThreadPoolExecutor (max 5 workers) for parallel stock analysis in SectorScanner

### Testing Strategy
- No formal test suite yet; each module has a standalone `__main__` block for manual testing
- Run individual modules directly: `python modules/<module>.py`

### Git Workflow
- Simple main-branch workflow; work directly on `main`
- GitHub Actions for automated scheduled runs (not for CI/CD of code changes)

## Domain Context
- **Taiwan market (TW):** Symbols suffixed with `.TW` (e.g., `2330.TW`). Index: `^TWII`. Trading hours: 09:00–13:30 UTC+8.
- **US market (US):** Standard ticker symbols. Indices: `^GSPC`, `^DJI`, `^IXIC`, `^SOX`. Trading hours: 09:30–16:00 ET.
- Technical indicators: SMA (5/20/60), RSI (14-period, 70/30 thresholds), MACD (12/26/9), volume ratio (20-day).
- Trend score: −100 to +100, mapped to 5-level TrendDirection enum.
- Buy signals: 3-of-5 criteria (MA alignment, RSI health, MACD positive, volume surge, moderate price change).

## Important Constraints
- Yahoo Finance rate limits — mitigated by 15-minute caching
- Discord webhook rate limits — messages sent sequentially with delays
- No persistent database; all data is fetched on demand
- `DISCORD_WEBHOOK_URL` must be kept secret (GitHub Secrets for Actions, excluded from git)

## External Dependencies
- **Yahoo Finance API** (via yfinance) — market data provider
- **Discord Webhook** — notification delivery
- **GitHub Actions** — scheduled automation (Taiwan: 14:30 UTC+8 weekdays, US: 05:30 UTC+8 weekdays)
