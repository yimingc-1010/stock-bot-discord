## Context
The Izaax business cycle method classifies the US economy into 4 phases using macro indicators. This change adds macro data fetching and cycle classification to the existing stock bot pipeline. The bot currently has no macroeconomic awareness — all analysis is price/volume-based technical analysis.

## Goals / Non-Goals
- **Goals:**
  - Fetch ~10 key macro indicators from FRED (via pandas-datareader, no API key)
  - Classify current business cycle phase: Recovery, Growth, Boom, Recession
  - Display a compact dashboard embed in the daily Discord report
  - Provide position allocation suggestion per the Izaax framework
- **Non-Goals:**
  - Not a backtesting or prediction engine
  - Not replacing existing technical analysis — this is an overlay
  - Not tracking every indicator Izaax mentions — focused on the most actionable ones

## Decisions

### Data Source: pandas-datareader + FRED
- **Why:** No API key required, works immediately in GitHub Actions without additional secrets
- **Alternative considered:** fredapi (more robust, but requires FRED API key registration + secret management)

### Module Structure: Two Modules
- `macro_fetcher.py` — pure data retrieval with caching (similar pattern to `data_fetcher.py`)
- `cycle_analyzer.py` — classification logic, phase detection, signal scoring
- **Why separated:** Fetcher can be reused independently; analyzer logic is complex enough to warrant its own module

### Cycle Phase Classification: Score-Based
Each phase has characteristic indicator patterns. The analyzer scores evidence for each phase and selects the highest-confidence match:

| Phase | Key Signals |
|-------|------------|
| Recovery (復甦) | ISM rising from <45, yield spread normalizing, jobless claims declining from peak |
| Growth (成長) | Nonfarm payrolls steady growth, savings rate declining, ISM >50 |
| Boom (榮景) | PCE growth > income growth (overconsumption), CPI accelerating, savings rate low |
| Recession (衰退) | Yield curve inverted then re-steepening + unemployment rising, retail sales negative YoY |

### Indicator Set (10 series from FRED)

| Indicator | FRED Code | Category | Update Frequency |
|-----------|-----------|----------|------------------|
| ISM Manufacturing | NAPM | Investment | Monthly |
| Initial Jobless Claims | ICSA | Labor | Weekly |
| Nonfarm Payrolls | PAYEMS | Labor | Monthly |
| Real Retail Sales | RSXFS | Consumption | Monthly |
| Personal Consumption Expenditure | PCE | Consumption | Monthly |
| Personal Savings Rate | PSAVERT | Consumption | Monthly |
| UMich Consumer Sentiment | UMCSENT | Confidence | Monthly |
| 10Y-2Y Treasury Spread | T10Y2Y | Policy | Daily |
| CPI (All Urban) | CPIAUCSL | Inflation | Monthly |
| Real Private Investment | GPDIC1 | Investment | Quarterly |

### Caching Strategy
- Macro data changes slowly (most are monthly). Cache for 24 hours (vs 15 min for stock data).
- Store fetched data in memory dict keyed by series code + fetch date.

### Discord Output: Single Dashboard Embed
- Title: "🔄 景氣循環分析 — Izaax Method"
- Color: phase-dependent (green=Recovery, blue=Growth, orange=Boom, red=Recession)
- Fields: phase name, confidence, key indicators with ↑/↓/→ arrows, position suggestion
- Footer: data source attribution and last update timestamps

## Risks / Trade-offs
- **FRED data lag:** Most indicators are released with 1-4 week delay. The bot shows the latest available, not real-time.
  - Mitigation: Display the data date alongside values.
- **pandas-datareader reliability:** Less maintained than fredapi. FRED API may change.
  - Mitigation: Wrap all fetches in try/except; gracefully degrade if macro data unavailable.
- **Phase classification is heuristic:** No single indicator perfectly signals a phase transition.
  - Mitigation: Use multi-indicator scoring with confidence level. Display "Transitional" when signals conflict.

## Open Questions
- Should the bot track macro indicator changes over time (e.g., "ISM improved from 48.2 to 50.1 this month") or just show the latest snapshot?
