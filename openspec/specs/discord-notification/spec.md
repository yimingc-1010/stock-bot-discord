# Capability: Discord Notification

## Purpose
Delivers analysis results to Discord via webhooks using rich embed formatting with color coding and structured layouts.

## Requirements

### Requirement: Webhook Message Delivery
The system SHALL send messages to a configured Discord webhook URL using HTTP POST requests. The webhook URL is loaded from `DISCORD_WEBHOOK_URL` in settings.

#### Scenario: Successful send
- **WHEN** `send_message(content, embeds)` is called with a valid webhook URL
- **THEN** the message is delivered to Discord and the method returns `True`

#### Scenario: Invalid webhook URL
- **WHEN** the webhook URL is the placeholder value "YOUR_DISCORD_WEBHOOK_URL_HERE"
- **THEN** the message is not sent and a warning is logged

#### Scenario: HTTP error
- **WHEN** Discord returns an HTTP error status
- **THEN** an exception is raised and the error is logged

### Requirement: Color-Coded Embeds
The system SHALL use color coding to visually indicate market conditions:
- Bullish: green (0x00FF00)
- Bearish: red (0xFF0000)
- Neutral: yellow (0xFFFF00)
- Informational: blue (0x0099FF)
- Warning: orange (0xFF9900)

#### Scenario: Bullish analysis embed
- **WHEN** a market analysis with bullish trend is sent
- **THEN** the embed color is green (0x00FF00)

### Requirement: Emoji Trend Indicators
The system SHALL prefix trend descriptions with emoji indicators:
- STRONG_BULLISH: rocket
- BULLISH: chart increasing
- NEUTRAL: right arrow
- BEARISH: chart decreasing
- STRONG_BEARISH: collision

#### Scenario: Strong bullish trend display
- **WHEN** a STRONG_BULLISH trend is displayed
- **THEN** the trend text is prefixed with the rocket emoji

### Requirement: Report Types
The system SHALL support the following report message types:
- `send_market_analysis` — index analysis with technical indicators
- `send_sector_analysis` — sector rankings with strength scores
- `send_stock_recommendations` — top stocks and buy signals
- `send_prediction` — individual stock price predictions
- `send_market_outlook` — overall market forecast
- `send_daily_report` — complete daily report combining all of the above

#### Scenario: Send daily report
- **WHEN** `send_daily_report(...)` is called with full analysis data
- **THEN** multiple embed messages are sent sequentially covering all report sections

### Requirement: Rich Embed Fields
Each embed SHALL include structured fields with:
- Title and description with timestamps
- Inline fields for technical indicators (RSI, MACD, volume)
- Support/resistance levels
- Moving average positions
- Analysis summaries
- Footer disclaimers noting this is not investment advice

#### Scenario: Market analysis embed structure
- **WHEN** `send_market_analysis` is called
- **THEN** the embed includes fields for price, change, trend score, RSI, MACD, volume ratio, support, resistance, and moving averages
