## ADDED Requirements

### Requirement: Macro Indicator Retrieval
The system SHALL fetch the following US macroeconomic indicators from FRED via pandas-datareader (no API key required):
- ISM Manufacturing Index (NAPM)
- Initial Jobless Claims (ICSA)
- Nonfarm Payrolls (PAYEMS)
- Real Retail Sales (RSXFS)
- Personal Consumption Expenditure (PCE)
- Personal Savings Rate (PSAVERT)
- UMich Consumer Sentiment (UMCSENT)
- 10Y-2Y Treasury Yield Spread (T10Y2Y)
- CPI All Urban Consumers (CPIAUCSL)
- Real Gross Private Domestic Investment (GPDIC1)

Data SHALL be cached in memory for 24 hours to avoid redundant requests.

#### Scenario: Fetch all macro indicators successfully
- **WHEN** `MacroFetcher.fetch_all()` is called
- **THEN** a dict mapping indicator names to their latest values and recent trend data is returned

#### Scenario: FRED data unavailable
- **WHEN** pandas-datareader fails to connect to FRED
- **THEN** `None` is returned and a warning is logged; the rest of the analysis pipeline continues without macro data

#### Scenario: Cache hit within 24 hours
- **WHEN** `fetch_all()` is called within 24 hours of a previous successful fetch
- **THEN** cached data is returned without making new network requests

### Requirement: Business Cycle Phase Classification
The system SHALL classify the current US economic phase into one of four stages using the Izaax method:
- **Recovery (復甦期):** ISM rising from below 45, yield spread normalizing, jobless claims declining from peak
- **Growth (成長期):** Nonfarm payrolls in steady growth, savings rate declining, ISM above 50
- **Boom (榮景期):** PCE growth exceeds income growth, CPI accelerating, savings rate at lows
- **Recession (衰退期):** Yield curve inverted then re-steepening with rising unemployment, retail sales negative YoY

The classification SHALL include a confidence level (HIGH, MEDIUM, LOW) based on how many indicators align with the identified phase.

#### Scenario: Clear growth phase
- **WHEN** ISM is above 50, nonfarm payrolls are growing, savings rate is declining, and no recession signals are present
- **THEN** the phase is classified as GROWTH with HIGH confidence

#### Scenario: Conflicting signals
- **WHEN** indicators point to different phases (e.g., ISM above 50 but yield curve inverted)
- **THEN** the phase with the highest score is selected with LOW confidence

### Requirement: Position Allocation Suggestion
The system SHALL provide an allocation suggestion based on the classified phase:
- Recovery: "全力做多（建議持股 100%）"
- Growth: "穩定持股"
- Boom: "分批減碼（持股 70%→50%→30%）"
- Recession: "避險，持有公債/現金"

#### Scenario: Recovery phase suggestion
- **WHEN** the cycle is classified as RECOVERY
- **THEN** the suggestion is "全力做多（建議持股 100%）"

### Requirement: Indicator Trend Detection
The system SHALL determine the trend direction (rising, falling, stable) for each macro indicator by comparing recent values to prior periods. Trend arrows (↑, ↓, →) SHALL be displayed alongside current values.

#### Scenario: ISM rising trend
- **WHEN** the latest ISM value is higher than the value from 3 months ago
- **THEN** the ISM trend is marked as rising (↑)

### Requirement: Cycle Analysis Discord Dashboard
The system SHALL send a single compact Discord embed for the business cycle analysis containing:
- Current phase name with phase-dependent color (green=Recovery, blue=Growth, orange=Boom, red=Recession)
- Confidence level
- Key indicator values with trend arrows
- Position allocation suggestion
- Data date attribution in footer

#### Scenario: Dashboard embed in daily report
- **WHEN** `send_daily_report` is called with US market enabled and macro data available
- **THEN** a "🔄 景氣循環分析" embed is included in the Discord report

### Requirement: Macro Analysis CLI Control
The system SHALL support a `--no-macro` CLI flag that disables macro/cycle analysis. Macro analysis SHALL only run when the US market is included in the analysis scope.

#### Scenario: No macro flag
- **WHEN** `python main.py --no-macro` is run
- **THEN** no macro data is fetched and no cycle analysis embed is included

#### Scenario: Taiwan only skips macro
- **WHEN** `python main.py --market tw` is run
- **THEN** macro/cycle analysis is not executed (US-only feature)
