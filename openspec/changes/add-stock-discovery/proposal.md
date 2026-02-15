# Change: Add Dynamic Stock Discovery

## Why
The bot currently only analyzes a fixed list of stocks from `stocks.json`. It cannot detect emerging volume or momentum leaders outside this watchlist, limiting its usefulness for spotting new opportunities.

## What Changes
- New `modules/stock_discovery.py` module with `StockDiscovery` class
- US discovery via `yf.screen("most_actives")` and `yf.screen("day_gainers")`
- TW discovery via a broader scanning universe (~50 major stocks not in the watchlist)
- Rate-limited sequential fetching (0.3s delay per new symbol)
- New Discord report section for discovered stocks
- New `--no-discovery` CLI flag to opt out
- Discovery skipped in `--quick` mode

## Impact
- Affected specs: new `stock-discovery` capability
- Affected code: `modules/stock_discovery.py` (new), `modules/discord_bot.py`, `main.py`
