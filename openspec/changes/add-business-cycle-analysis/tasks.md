## 1. Data Layer
- [ ] 1.1 Add `pandas-datareader>=0.10.0` to `requirements.txt`
- [ ] 1.2 Create `modules/macro_fetcher.py` with `MacroFetcher` class
- [ ] 1.3 Implement FRED data retrieval for all 10 indicator series
- [ ] 1.4 Implement 24-hour in-memory caching for macro data
- [ ] 1.5 Add `__main__` standalone test block to `macro_fetcher.py`

## 2. Analysis Layer
- [ ] 2.1 Create `modules/cycle_analyzer.py` with `CycleAnalyzer` class
- [ ] 2.2 Define `CyclePhase` enum (RECOVERY, GROWTH, BOOM, RECESSION) and `CycleAnalysis` dataclass
- [ ] 2.3 Implement indicator trend detection (rising/falling/stable based on recent data points)
- [ ] 2.4 Implement 4-phase scoring logic with confidence level
- [ ] 2.5 Implement position allocation suggestion per phase
- [ ] 2.6 Add `__main__` standalone test block to `cycle_analyzer.py`

## 3. Presentation Layer
- [ ] 3.1 Add `send_cycle_analysis()` method to `modules/discord_bot.py` (single dashboard embed)
- [ ] 3.2 Implement phase-dependent color coding and indicator trend arrows

## 4. Integration
- [ ] 4.1 Import and wire `MacroFetcher` + `CycleAnalyzer` in `main.py`
- [ ] 4.2 Add `--no-macro` CLI flag
- [ ] 4.3 Add cycle analysis to `send_daily_report()` (US market only)
- [ ] 4.4 Add cycle analysis to `print_analysis()` terminal output
- [ ] 4.5 Update `config/settings.example.py` with macro-related settings if needed
