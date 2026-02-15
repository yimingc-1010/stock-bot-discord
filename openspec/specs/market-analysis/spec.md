# Capability: Market Analysis

## Purpose
Performs technical analysis on market indices, computing indicators and producing a trend score with directional classification.

## Requirements

### Requirement: Technical Indicator Calculation
The system SHALL calculate the following technical indicators from OHLCV data:
- Simple Moving Average (SMA) for periods 5, 20, and 60
- Exponential Moving Average (EMA)
- Relative Strength Index (RSI) with 14-period default, overbought at 70, oversold at 30
- MACD with fast=12, slow=26, signal=9, including histogram
- Support and resistance levels from a 20-day lookback
- Volume ratio (current volume vs 20-day average)

#### Scenario: Calculate indicators for a valid index
- **WHEN** `analyze_index("^TWII", "加權指數", period="3mo")` is called with at least 60 bars of data
- **THEN** a `MarketAnalysis` dataclass is returned containing all computed indicators

#### Scenario: Insufficient data
- **WHEN** the fetched data has fewer than 60 bars
- **THEN** `None` is returned

### Requirement: Trend Scoring
The system SHALL compute a trend score in the range −100 to +100 based on:
- Moving average alignment: up to ±30 points
- RSI levels: up to ±25 points
- MACD histogram direction: up to ±25 points
- Recent price change: up to ±20 points

#### Scenario: Strong bullish score
- **WHEN** the computed score is ≥ 50
- **THEN** trend direction is `STRONG_BULLISH`

#### Scenario: Bullish score
- **WHEN** the computed score is ≥ 20 and < 50
- **THEN** trend direction is `BULLISH`

#### Scenario: Neutral score
- **WHEN** the computed score is between −20 and 20 (exclusive)
- **THEN** trend direction is `NEUTRAL`

#### Scenario: Bearish score
- **WHEN** the computed score is ≤ −20 and > −50
- **THEN** trend direction is `BEARISH`

#### Scenario: Strong bearish score
- **WHEN** the computed score is ≤ −50
- **THEN** trend direction is `STRONG_BEARISH`

### Requirement: Market Shortcuts
The system SHALL provide convenience methods for common market analyses:
- `analyze_taiwan_market()` for the TWII index
- `analyze_us_markets()` for S&P 500, Dow Jones, Nasdaq Composite, and Philadelphia Semiconductor indices

#### Scenario: Analyze Taiwan market
- **WHEN** `analyze_taiwan_market()` is called
- **THEN** a single `MarketAnalysis` for `^TWII` is returned

#### Scenario: Analyze US markets
- **WHEN** `analyze_us_markets()` is called
- **THEN** a list of `MarketAnalysis` objects for `^GSPC`, `^DJI`, `^IXIC`, and `^SOX` is returned
