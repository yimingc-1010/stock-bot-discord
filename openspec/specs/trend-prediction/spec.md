# Capability: Trend Prediction

## Purpose
Generates price forecasts for individual stocks and overall market outlooks using pivot points, Fibonacci levels, and pattern recognition.

## Requirements

### Requirement: Pivot Point Calculation
The system SHALL calculate classical pivot points (Pivot, R1/R2/R3, S1/S2/S3) from the most recent bar's high, low, and close prices.

#### Scenario: Compute pivot points
- **WHEN** `calculate_pivot_points(data)` is called with valid OHLCV data
- **THEN** a dict with keys pivot, r1, r2, r3, s1, s2, s3 is returned

### Requirement: Fibonacci Level Calculation
The system SHALL calculate Fibonacci retracement and extension levels using a 60-day lookback window to identify the swing high and low.

#### Scenario: Compute Fibonacci levels
- **WHEN** `calculate_fibonacci_levels(data, lookback=60)` is called
- **THEN** retracement levels at 23.6%, 38.2%, 50%, 61.8%, and 78.6% are returned

### Requirement: Price Pattern Detection
The system SHALL detect the following patterns:
- Golden cross (SMA5 crosses above SMA20)
- Death cross (SMA5 crosses below SMA20)
- Breakout (price within 2% of 20-day high or low)
- Consecutive win/loss streaks (4+ days)

#### Scenario: Golden cross detected
- **WHEN** the 5-day SMA crosses above the 20-day SMA in the most recent bars
- **THEN** the pattern list includes "黃金交叉" (golden cross)

#### Scenario: Breakout detected
- **WHEN** the current price is within 2% of the 20-day high
- **THEN** the pattern list includes a breakout signal

### Requirement: Price Target Generation
The system SHALL generate a `PricePrediction` dataclass with target price, high/low range, direction, and confidence level. Price targets are derived from:
- Weekly volatility (annualized volatility / sqrt(52))
- Expected move adjusted by trend direction (bullish: +1.5x/−0.5x, bearish: +0.5x/−1.5x)
- Capped by pivot points and Fibonacci levels

#### Scenario: Bullish prediction
- **WHEN** the trend score indicates bullish conditions
- **THEN** the target price is above the current price, high range is +1.5x expected move, low range is −0.5x expected move

#### Scenario: Bearish prediction
- **WHEN** the trend score indicates bearish conditions
- **THEN** the target price is below the current price, high range is +0.5x expected move, low range is −1.5x expected move

### Requirement: Prediction Confidence
The system SHALL assign confidence levels based on:
- **HIGH:** |score| ≥ 3 AND volatility < 30%
- **MEDIUM:** |score| ≥ 2
- **LOW:** otherwise

#### Scenario: High confidence prediction
- **WHEN** the absolute score is 3 or higher and volatility is below 30%
- **THEN** confidence is `HIGH`

### Requirement: Risk Warnings
The system SHALL generate risk warning strings for dangerous conditions:
- Volatility > 40%: high volatility risk
- RSI > 75: severely overbought
- RSI < 25: severely oversold
- Neutral direction: unclear direction, suggest waiting

#### Scenario: High volatility warning
- **WHEN** annualized volatility exceeds 40%
- **THEN** a "高波動風險" warning is included in the prediction

### Requirement: Market Outlook
The system SHALL generate a `MarketOutlook` dataclass summarizing overall market conditions from index analysis and sector analyses, including outlook direction, key factors, and recommendations.

#### Scenario: Generate market outlook
- **WHEN** `generate_market_outlook("台股", index_analysis, sector_analyses)` is called
- **THEN** a `MarketOutlook` with direction, summary, key factors, and risk warnings is returned
