# Capability: Data Fetching

## Purpose
Retrieves stock market data from Yahoo Finance with intelligent caching to minimize API calls.

## Requirements

### Requirement: Single Stock Data Retrieval
The system SHALL fetch historical OHLCV data for a given stock symbol using Yahoo Finance, with configurable period and interval.

#### Scenario: Fetch 3-month daily data for a Taiwan stock
- **WHEN** `get_stock_data("2330.TW", period="3mo", interval="1d")` is called
- **THEN** a pandas DataFrame with Open, High, Low, Close, Volume columns is returned

#### Scenario: Symbol not found
- **WHEN** `get_stock_data` is called with an invalid symbol
- **THEN** `None` is returned and a warning is logged

### Requirement: Batch Stock Retrieval
The system SHALL fetch historical data for multiple symbols in a single call via `get_multiple_stocks`.

#### Scenario: Fetch multiple stocks
- **WHEN** `get_multiple_stocks(["2330.TW", "2317.TW"], period="3mo", interval="1d")` is called
- **THEN** a dict mapping each symbol to its DataFrame is returned, skipping any that failed

### Requirement: Stock Metadata Retrieval
The system SHALL fetch stock metadata (name, sector, PE ratio, market cap) via `get_stock_info`.

#### Scenario: Retrieve stock info
- **WHEN** `get_stock_info("2330.TW")` is called
- **THEN** a dict containing shortName, sector, trailingPE, marketCap (and other available fields) is returned

### Requirement: Real-Time Quote
The system SHALL fetch the latest real-time price quote via `get_realtime_quote`.

#### Scenario: Get current price
- **WHEN** `get_realtime_quote("AAPL")` is called
- **THEN** a dict with current price and related quote data is returned

### Requirement: In-Memory Caching
The system SHALL cache fetched data in memory for 15 minutes to reduce Yahoo Finance API calls. Cache keys SHALL include the symbol, period, and interval.

#### Scenario: Cache hit within 15 minutes
- **WHEN** the same symbol/period/interval is requested within 15 minutes of a previous fetch
- **THEN** cached data is returned without making a new API call

#### Scenario: Cache expiry
- **WHEN** the same symbol/period/interval is requested after 15 minutes
- **THEN** fresh data is fetched from Yahoo Finance and the cache is updated

#### Scenario: Manual cache clear
- **WHEN** `clear_cache()` is called
- **THEN** all cached data is removed
