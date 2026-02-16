## 1. Data Layer
- [x] 1.1 Add `fredapi>=0.5.0` to `requirements.txt` (switched from pandas-datareader due to FRED CSV endpoint being blocked)
- [x] 1.2 Create `modules/macro_fetcher.py` with `MacroFetcher` class (uses fredapi with FRED API key)
- [x] 1.3 Implement FRED data retrieval for all 10 indicator series (IPMAN replaces NAPM which is unavailable on FRED)
- [x] 1.4 Implement 24-hour in-memory caching for macro data
- [x] 1.5 Add `__main__` standalone test block to `macro_fetcher.py`

## 2. Analysis Layer
- [x] 2.1 Create `modules/cycle_analyzer.py` with `CycleAnalyzer` class
- [x] 2.2 Define `CyclePhase` enum (RECOVERY, GROWTH, BOOM, RECESSION) and `CycleAnalysis` dataclass
- [x] 2.3 Implement indicator trend detection (rising/falling/stable based on recent data points)
- [x] 2.4 Implement 4-phase scoring logic with confidence level
- [x] 2.5 Implement position allocation suggestion per phase
- [x] 2.6 Add `__main__` standalone test block to `cycle_analyzer.py`

## 3. Presentation Layer
- [x] 3.1 Add `send_cycle_analysis()` method to `modules/discord_bot.py` (single dashboard embed)
- [x] 3.2 Implement phase-dependent color coding and indicator trend arrows

## 4. Integration
- [x] 4.1 Import and wire `MacroFetcher` + `CycleAnalyzer` in `main.py`
- [x] 4.2 Add `--no-macro` CLI flag
- [x] 4.3 Add cycle analysis to `send_daily_report()` (US market only)
- [x] 4.4 Add cycle analysis to `print_analysis()` terminal output
- [x] 4.5 Update `config/settings.example.py` with `FRED_API_KEY` setting
- [x] 4.6 Update `.github/workflows/stock-analysis.yml` to pass `FRED_API_KEY` secret
