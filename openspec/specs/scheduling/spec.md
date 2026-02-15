# Capability: Scheduling & Orchestration

## Purpose
Orchestrates the full analysis pipeline with multiple execution modes, market selection, and automated scheduling via CLI and GitHub Actions.

## Requirements

### Requirement: CLI Execution Modes
The system SHALL support three execution modes via the `--mode` argument:
- `once` (default): Run analysis once and send to Discord
- `schedule`: Start a continuous scheduler that runs at configured times
- `print`: Run analysis and output to terminal only (no Discord)

#### Scenario: Default once mode
- **WHEN** `python main.py` is run without `--mode`
- **THEN** analysis runs once, results are sent to Discord, and the process exits

#### Scenario: Print mode
- **WHEN** `python main.py --mode print` is run
- **THEN** analysis results are printed to the terminal and no Discord messages are sent

#### Scenario: Schedule mode
- **WHEN** `python main.py --mode schedule` is run
- **THEN** the process starts a long-running scheduler that polls every 60 seconds and sends a startup notification to Discord

### Requirement: Market Selection
The system SHALL support market filtering via the `--market` argument:
- `all` (default): Analyze both Taiwan and US markets
- `tw`: Taiwan market only
- `us`: US market only

#### Scenario: Taiwan only
- **WHEN** `python main.py --market tw` is run
- **THEN** only the Taiwan market (^TWII index and TW sectors) is analyzed

### Requirement: Quick Mode
The system SHALL support a `--quick` flag that runs index-only analysis without sector scanning or individual stock analysis.

#### Scenario: Quick update
- **WHEN** `python main.py --quick` is run
- **THEN** only market index analyses are performed and sent; sector and stock analyses are skipped

### Requirement: Webhook Override
The system SHALL allow overriding the Discord webhook URL via the `--webhook` CLI argument.

#### Scenario: Custom webhook
- **WHEN** `python main.py --webhook https://discord.com/api/webhooks/...` is run
- **THEN** the provided URL is used instead of the configured default

### Requirement: Scheduled Execution
In schedule mode, the system SHALL run analyses at configured times:
- Taiwan market: weekdays at 14:30 (Asia/Taipei timezone)
- US market: weekdays at 05:30 (Asia/Taipei timezone, next day)

The schedule times are configured in `SCHEDULE` settings.

#### Scenario: Taiwan market scheduled run
- **WHEN** the clock reaches 14:30 on a weekday in Asia/Taipei timezone
- **THEN** the Taiwan market analysis is triggered automatically

### Requirement: Analysis Pipeline
The system SHALL execute the full analysis pipeline in order:
1. Fetch market index data and run technical analysis
2. Scan all configured sectors with individual stock analysis
3. Generate market outlook from index and sector data
4. Identify top stocks and buy signals
5. Deliver results via Discord or terminal

#### Scenario: Full Taiwan analysis
- **WHEN** `analyze_taiwan_market()` is called on the StockBot
- **THEN** TWII index analysis, all TW sector scans, market outlook, top stocks, and buy signals are produced

### Requirement: Error Resilience
The system SHALL continue operating when individual analyses fail. In schedule mode, errors SHALL be reported to Discord and the scheduler SHALL continue running.

#### Scenario: Single stock failure in schedule mode
- **WHEN** a stock analysis fails during a scheduled run
- **THEN** the error is logged, an error notification is sent to Discord, and the scheduler continues to the next scheduled run

### Requirement: GitHub Actions Automation
The system SHALL be runnable via GitHub Actions with:
- Taiwan market cron: weekdays at 06:30 UTC (14:30 Taiwan time)
- US market cron: weekdays at 21:30 UTC (05:30 Taiwan time next day)
- Manual trigger with market selection input
- `DISCORD_WEBHOOK_URL` provided via GitHub Secrets

#### Scenario: Scheduled GitHub Actions run for Taiwan
- **WHEN** the GitHub Actions cron fires at 06:30 UTC on a weekday
- **THEN** the Taiwan market analysis is executed and results are sent to the configured Discord webhook
