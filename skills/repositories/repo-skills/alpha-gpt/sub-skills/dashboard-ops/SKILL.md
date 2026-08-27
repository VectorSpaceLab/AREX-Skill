---
name: dashboard-ops
description: "Operate and troubleshoot AlphaGPT's Streamlit dashboard, local
  state inputs, read-only DB/RPC views, Plotly visualizers, and emergency STOP
  control."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Dashboard Ops

Use this sub-skill when the task is to launch, inspect, fixture, or troubleshoot
AlphaGPT's Streamlit monitoring dashboard. It covers the dashboard entrypoint,
`DashboardService`, Plotly visualizers, local state/log files, the market
overview query, auto-refresh behavior, and the emergency STOP button.

## Do not route here for

- Trading decisions, live runner lifecycle, portfolio risk policy, or execution safety; use [live-strategy](../live-strategy/SKILL.md).
- Populating Postgres/Timescale tables or debugging Birdeye/DexScreener ingestion; use [data-pipeline](../data-pipeline/SKILL.md).
- Training, validating, or rewriting formulas in `best_meme_strategy.json`; use [factor-mining](../factor-mining/SKILL.md).

## Read or run

1. Read [references/dashboard-reference.md](references/dashboard-reference.md) for launch workflow, UI layout, local file schemas, market query, visualizer inputs, log tail, auto-refresh, empty states, and read-only service prerequisites.
2. Read [references/troubleshooting.md](references/troubleshooting.md) for Streamlit/import/version errors, empty panels, unknown wallet, DB failures, missing/malformed files, and STOP button caveats.
3. Run [scripts/alpha_gpt_dashboard_fixture.py](scripts/alpha_gpt_dashboard_fixture.py) to create sample `portfolio_state.json`, `best_meme_strategy.json`, and `strategy.log` files in a chosen directory without DB, RPC, or network access.
4. Use the root [environment checker](../../scripts/alpha_gpt_env_check.py) with `--scope dashboard` for import/env checks.
5. Read [../../references/install-and-operations.md](../../references/install-and-operations.md) when dashboard import problems appear to be dependency or Solana-pin related.

## Safe default workflow

1. Decide whether the user needs fixture/offline inspection or a live Streamlit server.
2. For fixture work, write sample state files into an isolated output directory and do not contact DB/RPC.
3. For live dashboard work, confirm the working directory contains or can read `portfolio_state.json`, `best_meme_strategy.json`, and `strategy.log` when expected.
4. Confirm DB env vars before expecting the Market Scanner tab to show rows.
5. Confirm `QUICKNODE_RPC_URL` and wallet/private-key readability only when wallet balance display matters.
6. Warn that the dashboard STOP button writes a local `STOP_SIGNAL`; it only affects a runner watching the same path or configured stop path.
7. Treat an empty panel as a diagnosable state, not automatically a crash.

## Core runtime facts

- `dashboard/app.py` defines a Streamlit page with wallet status, refresh, emergency stop, metrics, Portfolio/Market Scanner/Logs tabs, and optional auto-refresh.
- `DashboardService.get_market_overview(self, limit=50)` queries the latest `ohlcv` time joined with `tokens`, ordered by liquidity.
- `DashboardService.load_portfolio()` reads `portfolio_state.json` and derives `pnl_pct` when price fields exist.
- `DashboardService.load_strategy_info()` displays `best_meme_strategy.json` or a not-trained placeholder.
- `DashboardService.get_recent_logs(n=50)` tails `strategy.log` if present.
- `plot_pnl_distribution(portfolio_df)` expects `symbol` and `pnl_pct`; `plot_market_scatter(market_df)` expects `liquidity`, `volume`, `fdv`, and `symbol`.

## Quick route map

| User intent | Read/run | Notes |
| --- | --- | --- |
| "Create dashboard test files." | [scripts/alpha_gpt_dashboard_fixture.py](scripts/alpha_gpt_dashboard_fixture.py) | No DB/RPC/network; use `--output-dir`. |
| "Why is the portfolio empty?" | [references/troubleshooting.md](references/troubleshooting.md) | Missing file, empty JSON, or no positions can all be valid. |
| "Why is Market Scanner blank?" | [references/dashboard-reference.md](references/dashboard-reference.md) and [references/troubleshooting.md](references/troubleshooting.md) | Check DB join/time assumptions and ingestion. |
| "What does EMERGENCY STOP do?" | [references/dashboard-reference.md](references/dashboard-reference.md) | It writes a local file; it is not a chain transaction canceler. |
| "Can I run Streamlit now?" | [references/dashboard-reference.md](references/dashboard-reference.md) | Confirm env, working directory, and whether live DB/RPC is authorized. |

## Verification stance

The native dashboard is a help-only or tiny-fixture candidate. Prefer static
checks and the bundled fixture generator for verification. Do not require a live
Streamlit server, wallet, DB, RPC endpoint, or network connection unless the
user explicitly authorizes live operational checks and supplies the required
services.
