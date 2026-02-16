# Change: Add Business Cycle Analysis (Izaax Method)

## Why
The bot currently performs only technical analysis (price/volume indicators). It lacks macroeconomic context, which is critical for determining overall market positioning. The Izaax (愛榭客) business cycle investment method uses US macro data to classify the economy into four phases (Recovery, Growth, Boom, Recession), each with distinct allocation guidance. Adding this gives users a "big picture" overlay on top of the existing technical signals.

## What Changes
- New `modules/macro_fetcher.py` — fetches US macroeconomic indicators from FRED via `pandas-datareader` (no API key required)
- New `modules/cycle_analyzer.py` — implements the Izaax 4-phase business cycle classifier using macro indicators
- New Discord embed section — single compact dashboard showing current cycle phase, key indicators with trend arrows, and position suggestion
- New `--no-macro` CLI flag to skip macro analysis
- New dependency: `pandas-datareader>=0.10.0`

## Impact
- Affected specs: new `business-cycle` capability
- Affected code: `modules/macro_fetcher.py` (new), `modules/cycle_analyzer.py` (new), `modules/discord_bot.py`, `main.py`, `requirements.txt`
- Macro analysis runs only for US market (`--market us` or `--market all`); skipped for Taiwan-only runs
