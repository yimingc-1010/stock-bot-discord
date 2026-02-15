# Capability: Sector Scanning

## Purpose
Analyzes individual stocks and aggregates results by sector, producing strength scores and buy signals.

## Requirements

### Requirement: Individual Stock Analysis
The system SHALL analyze a single stock and produce a `StockAnalysis` dataclass containing price, change percentage, volume ratio, RSI, MACD histogram, SMA values, trend score, strength score, and buy signal flag.

#### Scenario: Analyze a valid stock
- **WHEN** `analyze_stock("2330.TW", "半導體", period="3mo")` is called
- **THEN** a `StockAnalysis` with all computed fields is returned

#### Scenario: Stock data unavailable
- **WHEN** data fetching fails for the given symbol
- **THEN** `None` is returned and a warning is logged

### Requirement: Strength Scoring
The system SHALL compute a strength score from 0 to 100 for each stock, starting from a base of 50 and adding:
- Price change contribution: ±20 points (4x multiplier)
- Volume ratio bonus: +15 points when volume exceeds the 20-day average
- RSI health: ±10 points (healthy range is 40–70)
- Trend score contribution: ±15 points (0.15x multiplier)
- Price vs SMA20 position: ±10 points

#### Scenario: High-strength stock
- **WHEN** a stock has positive price change, high volume, healthy RSI, positive trend, and price above SMA20
- **THEN** the strength score is above 70

#### Scenario: Score clamping
- **WHEN** the raw computed score exceeds 100 or falls below 0
- **THEN** the score is clamped to the range 0–100

### Requirement: Buy Signal Detection
The system SHALL flag a stock as a buy signal when at least 3 of the following 5 criteria are met:
1. Price above SMA5 which is above SMA20 (bullish MA alignment)
2. RSI between 40 and 70 (healthy momentum zone)
3. MACD histogram > 0 (positive momentum)
4. Volume ratio > 1.2 (above-average volume)
5. Price change between 1% and 7% (moderate gain, not chasing)

#### Scenario: Buy signal triggered
- **WHEN** a stock meets 3 or more of the 5 criteria
- **THEN** `buy_signal` is set to `True`

#### Scenario: No buy signal
- **WHEN** a stock meets fewer than 3 criteria
- **THEN** `buy_signal` is set to `False`

### Requirement: Sector Aggregation
The system SHALL scan all stocks in a sector using parallel processing (ThreadPoolExecutor, max 5 workers), compute average sector metrics, and return a `SectorAnalysis` sorted by strength score descending.

#### Scenario: Scan a sector with multiple stocks
- **WHEN** `scan_sector("半導體", ["2330.TW", "2303.TW", "2454.TW"])` is called
- **THEN** a `SectorAnalysis` with averaged metrics and a `top_stocks` list sorted by strength is returned

### Requirement: Cross-Sector Ranking
The system SHALL provide:
- `get_top_stocks(sector_analyses, top_n=10)` — top N stocks across all sectors by strength
- `get_buy_signals(sector_analyses)` — all stocks with active buy signals

#### Scenario: Get top 10 stocks
- **WHEN** `get_top_stocks(analyses, top_n=10)` is called
- **THEN** the 10 highest-strength stocks across all sectors are returned, sorted descending
