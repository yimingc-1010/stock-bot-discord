<!-- OPENSPEC:START -->
# OpenSpec Instructions

These instructions are for AI assistants working in this project.

Always open `@/openspec/AGENTS.md` when the request:
- Mentions planning or proposals (words like proposal, spec, change, plan)
- Introduces new capabilities, breaking changes, architecture shifts, or big performance/security work
- Sounds ambiguous and you need the authoritative spec before coding

Use `@/openspec/AGENTS.md` to learn:
- How to create and apply change proposals
- Spec format and conventions
- Project structure and guidelines

Keep this managed block so 'openspec update' can refresh the instructions.

<!-- OPENSPEC:END -->

# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Stock Bot (股市推播機器人) - A Python-based automated stock market analysis bot that analyzes Taiwan and US markets using Yahoo Finance data and sends reports to Discord via Webhook.

## Running the Application

```bash
# Install dependencies
pip install -r requirements.txt

# Execute analysis and send to Discord
python main.py

# Print to terminal only (no Discord)
python main.py --mode print

# Start continuous scheduler
python main.py --mode schedule

# Market selection
python main.py --market tw    # Taiwan only
python main.py --market us    # US only

# Quick mode (indices only)
python main.py --quick

# Interactive launcher
bash run.sh
```

## Testing Individual Modules

Each module has a `if __name__ == "__main__":` block for standalone testing:

```bash
python modules/data_fetcher.py
python modules/market_analyzer.py
python modules/sector_scanner.py
python modules/predictor.py
python modules/discord_bot.py
```

## Architecture

**Data Pipeline:** DataFetcher → MarketAnalyzer → SectorScanner → TrendPredictor → DiscordNotifier

### Core Modules

- **data_fetcher.py** - Yahoo Finance data retrieval with 15-minute caching
- **market_analyzer.py** - Technical analysis engine (SMA, EMA, RSI, MACD, trend scoring)
- **sector_scanner.py** - Sector & stock screening with strength scoring (0-100) and buy signal detection
- **predictor.py** - Trend prediction using pivot points, fibonacci levels, and price patterns
- **discord_bot.py** - Discord Webhook notifications with rich embeds
- **main.py** - StockBot orchestrator class with CLI argument parsing

### Key Data Classes

- `MarketAnalysis` - Complete index analysis with trend direction
- `StockAnalysis` - Individual stock metrics and signals
- `SectorAnalysis` - Aggregated sector performance
- `PricePrediction` - Stock price forecast with confidence levels

### Configuration

- **config/settings.py** - Active configuration (Discord webhook, market stocks, technical parameters)
- **config/settings.example.py** - Template for new installations
- Technical parameters: SMA (5/20/60), RSI (14-period, 70/30 thresholds), MACD (12/26/9)

## GitHub Actions

Workflow at `.github/workflows/stock-analysis.yml` runs automated analysis:
- Taiwan market: Weekdays 06:30 UTC (14:30 Taiwan time)
- US market: Weekdays 21:30 UTC (05:30 Taiwan time next day)
- Requires `DISCORD_WEBHOOK_URL` secret
