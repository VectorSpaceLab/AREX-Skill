# AlphaGPT Dashboard Reference

This reference covers AlphaGPT's Streamlit dashboard files:

- `dashboard/app.py`: Streamlit UI, metrics, tabs, refresh controls, and emergency STOP button.
- `dashboard/data_service.py`: `DashboardService` for wallet balance, portfolio state, strategy metadata, market overview SQL, and log tail reads.
- `dashboard/visualizer.py`: Plotly helpers for portfolio PnL bars and market liquidity/volume scatter plots.

The dashboard is a monitor and control surface, not a trading-decision engine. Treat live strategy choices and execution safety as `live-strategy`, raw DB ingestion as `data-pipeline`, and formula training or formula repair as `factor-mining`.

## Launch workflow

1. Ensure the AlphaGPT source import roots are available in the Python process (`dashboard`, `data_pipeline`, `model_core`, `execution`, and `strategy_manager`). AlphaGPT is a source tree, not a packaged distribution, so launches normally happen from a working copy or an equivalent source deployment.
2. Install the core requirements that include Streamlit, Plotly, pandas, SQLAlchemy, psycopg2, Solana SDK, and solders. Streamlit `1.61.1` was verified during inspection. If execution-layer imports fail because a newer Solana SDK no longer exposes `TokenAccountOpts`, use the compatible operational pin that was verified for this repo: `solana==0.36.12` with `websockets==15.0.1`.
3. Decide whether this is a fixture check or a live monitor:
   - Fixture check: run [the fixture generator](../scripts/alpha_gpt_dashboard_fixture.py) into the directory where the dashboard process will read local state files. This creates only local JSON/log files and does not contact a DB, RPC endpoint, or network.
   - Live monitor: provide read-only access to the expected Postgres tables and a Solana RPC URL. A wallet private key is only needed if a real wallet balance should be displayed; absent or invalid wallet credentials degrade to `Unknown` / `0.0 SOL` behavior rather than a transaction.
4. Start the dashboard with `streamlit run dashboard/app.py` from the directory that should contain `portfolio_state.json`, `best_meme_strategy.json`, `strategy.log`, and `STOP_SIGNAL`. The service reads these files relative to the process current working directory, not relative to `dashboard/app.py`.
5. Do not use a live Streamlit server as the default verification requirement. The safe default is `streamlit --version`, fixture generation, JSON shape validation, and static review of the UI/data-service code.

## Environment and read-only service prerequisites

`DashboardService.__init__` creates two clients:

- A SQLAlchemy engine from environment variables: `DB_USER`, `DB_PASSWORD`, `DB_HOST`, and `DB_NAME`; defaults are `postgres`, `password`, `localhost`, and `crypto_quant`. The URL uses PostgreSQL on port `5432`.
- A Solana RPC client from `QUICKNODE_RPC_URL`, defaulting to the public mainnet endpoint.

The dashboard's normal data reads are read-only:

- `get_wallet_balance()` calls the Solana RPC `get_balance` method for the derived wallet address. It does not sign or submit transactions.
- `get_market_overview(limit=50)` runs a SQL `SELECT` query. It does not create tables or insert/update rows.
- `load_portfolio()`, `load_strategy_info()`, and `get_recent_logs()` read local files.

Operational gates still matter: a real live view requires a reachable DB, tables populated by the data pipeline, a usable RPC endpoint, compatible Solana dependencies, and local state/log files written by the strategy runner. Route table creation and ingestion issues to `data-pipeline`; route runner lifecycle and wallet/trading controls to `live-strategy`.

## UI layout and controls

### Sidebar

- **Wallet Status**: displays `SOL Balance` from `DashboardService.get_wallet_balance()`. If the private key is absent/invalid or RPC lookup fails, the service returns `0.0`.
- **Refresh Data**: calls `st.rerun()` and reloads dashboard data from the same sources.
- **EMERGENCY STOP**: writes a file named `STOP_SIGNAL` in the dashboard process current working directory, with file contents `STOP`, then displays an error banner. The live runner's default stop file name is also `STOP_SIGNAL`, but a custom runner stop path or different working directory can prevent the runner from seeing the button's file.

### Top metrics

After creating the service, `app.py` loads:

- `portfolio_df = svc.load_portfolio()`
- `market_df = svc.get_market_overview()`
- `strategy_data = svc.load_strategy_info()`

The dashboard then displays:

- **Open Positions**: number of rows in `portfolio_df`, displayed as `N / 5`.
- **Total Invested**: sum of `initial_cost_sol` across portfolio rows.
- **Unrealized PnL (Est)**: `(amount_held * highest_price).sum() - total_invested` when positions exist.
- **Active Strategy**: hard-coded metric label `AlphaGPT-v1` with `strategy_data` displayed as help text.

### Tabs

- **Portfolio**: table columns `symbol`, `entry_price`, `highest_price`, `amount_held`, `pnl_pct`, and `is_moonbag`; plus `plot_pnl_distribution(portfolio_df)`.
- **Market Scanner**: `plot_market_scatter(market_df)` plus the raw `market_df` table.
- **Logs**: last 20 lines from `strategy.log`, rendered as text code.

### Auto-refresh

At the bottom of `app.py`, the dashboard sleeps briefly, then a checkbox labeled `Auto-Refresh (30s)` defaults to enabled. When enabled, the app sleeps 30 seconds and calls `st.rerun()`. Disable the checkbox when manually inspecting a frozen fixture or when repeated DB/RPC reads are undesirable.

## Local input file shapes

### `portfolio_state.json`

`DashboardService.load_portfolio()` expects a JSON object whose values are position records. The keys are normally token addresses. Missing file means an empty portfolio; malformed JSON is not caught and can stop the dashboard.

Required fields for the native dashboard table and metrics:

```json
{
  "TokenAddressOrKey": {
    "token_address": "TokenAddressOrKey",
    "symbol": "MEME",
    "entry_price": 0.0000012,
    "entry_time": 1730000000.0,
    "amount_held": 1250000.0,
    "initial_cost_sol": 1.5,
    "highest_price": 0.0000018,
    "is_moonbag": false
  }
}
```

`load_portfolio()` computes `pnl_pct = (highest_price - entry_price) / entry_price` when both price fields exist. Keep `entry_price` positive to avoid divide-by-zero or misleading infinite values.

### `best_meme_strategy.json`

The training engine writes the best formula as a JSON list, for example:

```json
[0, 6, 7]
```

The live strategy runner also accepts a compatibility object with a `formula` field:

```json
{"formula": [0, 6, 7], "score": 1.23, "note": "fixture"}
```

The dashboard only displays this JSON as help text on the `Active Strategy` metric. It does not validate formula grammar; route formula validation or training questions to `factor-mining`.

### `strategy.log`

`DashboardService.get_recent_logs(n=50)` reads `strategy.log` from the current working directory and returns the last `n` lines. `app.py` asks for 20 lines. Missing file produces an empty log panel caption.

## Market overview query

The verified service signature is:

```python
DashboardService.get_market_overview(self, limit=50)
```

It issues this logical query:

```sql
SELECT t.symbol, o.address, o.close, o.volume, o.liquidity, o.fdv, o.time
FROM ohlcv o
JOIN tokens t ON o.address = t.address
WHERE o.time = (SELECT MAX(time) FROM ohlcv)
ORDER BY o.liquidity DESC
LIMIT {limit}
```

Expected returned columns:

| Column | Used by | Notes |
| --- | --- | --- |
| `symbol` | table and Plotly color/hover | Required by `plot_market_scatter`. |
| `address` | table | Token address from `ohlcv`. |
| `close` | table | Latest close price. |
| `volume` | table and Plotly y-axis | Should be positive for log-scale scatter. |
| `liquidity` | table and Plotly x-axis | Sort key and log-scale x-axis. |
| `fdv` | table and Plotly bubble size | Should be non-negative; positive values render better. |
| `time` | table | Latest OHLCV timestamp selected by max time. |

If the DB is unreachable, the SQL fails, the tables are empty, the join has no matching tokens, or the latest OHLCV rows have zero/negative log-axis values, the Market Scanner can be blank even though the dashboard code is functioning.

## Plotly visualizer input contracts

`plot_pnl_distribution(portfolio_df)` expects:

- `portfolio_df.empty` is allowed and returns an empty figure.
- Non-empty data must include `symbol` and `pnl_pct`.
- Positive `pnl_pct` bars are green; zero or negative bars are red.

`plot_market_scatter(market_df)` expects:

- `market_df.empty` is allowed and returns an empty figure.
- Non-empty data must include `liquidity`, `volume`, `fdv`, and `symbol`.
- `liquidity` and `volume` are plotted on log axes, so non-positive values can disappear or trigger Plotly warnings.

## Expected empty states

- Missing `portfolio_state.json` or an empty JSON object: `No active positions. The bot is scanning...`
- Missing or invalid `best_meme_strategy.json`: strategy help falls back to `{"formula": "Not Trained Yet"}`.
- DB query exception or no latest market rows: `No market data found in DB. Is the Data Pipeline running?`
- Missing `strategy.log`: `No logs found or log file path incorrect.`
- Missing/invalid private key or RPC balance failure: sidebar balance displays `0.0000 SOL`.
- Empty DataFrames passed to visualizers: empty Plotly figures, not a crash.

These empty states are acceptable for offline verification and initial fixture checks. Treat them as operational clues, not as proof that the dashboard is broken.
