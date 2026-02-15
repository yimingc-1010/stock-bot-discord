## ADDED Requirements

### Requirement: US Stock Discovery
The system SHALL discover volume and momentum leaders in the US market by querying Yahoo Finance screener endpoints (`most_actives`, `day_gainers`), excluding stocks already in the configured watchlist, and returning up to `top_n` results ranked by strength score.

#### Scenario: Discover US movers
- **WHEN** `discover_us_movers(top_n=10)` is called
- **THEN** up to 10 `StockAnalysis` objects are returned for US stocks not already in `MARKETS["US"]`, sorted by strength score descending

#### Scenario: Yahoo screener unavailable
- **WHEN** the yfinance screener API fails or returns no results
- **THEN** an empty list is returned and a warning is logged

### Requirement: TW Stock Discovery
The system SHALL discover volume and momentum leaders in the Taiwan market by scanning a predefined broader universe of ~50 major TW stocks (beyond the watchlist), filtering by volume ratio > 1.5 and positive momentum, and returning up to `top_n` results ranked by strength score.

#### Scenario: Discover TW movers
- **WHEN** `discover_tw_movers(top_n=10)` is called
- **THEN** up to 10 `StockAnalysis` objects are returned for TW stocks not already in `MARKETS["TW"]`, sorted by strength score descending

### Requirement: Rate Limiting
The system SHALL introduce a 0.3-second delay between individual stock data fetches for newly discovered symbols to avoid Yahoo Finance rate limiting.

#### Scenario: Sequential fetching with delay
- **WHEN** discovery fetches data for 20 candidate stocks
- **THEN** each fetch is separated by at least 0.3 seconds

### Requirement: Discovery CLI Control
The system SHALL support a `--no-discovery` CLI flag that disables discovery. Discovery SHALL also be skipped when `--quick` mode is active.

#### Scenario: No discovery flag
- **WHEN** `python main.py --no-discovery` is run
- **THEN** no discovery is performed and the report omits the discovery section

#### Scenario: Quick mode skips discovery
- **WHEN** `python main.py --quick` is run
- **THEN** discovery is not executed

### Requirement: Discovery Discord Report
The system SHALL send discovered stocks as a separate Discord embed section with an informational blue color (0x0099FF) and a distinct title, separate from the main watchlist analysis.

#### Scenario: Discovery results in daily report
- **WHEN** discovery finds stocks and `send_daily_report` is called
- **THEN** a "市場雷達" section is included in the Discord report showing discovered stocks with their strength scores and analysis notes
