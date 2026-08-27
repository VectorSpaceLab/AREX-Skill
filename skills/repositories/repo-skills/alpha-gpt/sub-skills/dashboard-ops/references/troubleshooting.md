# Dashboard Troubleshooting

Use this guide when AlphaGPT's Streamlit dashboard imports incorrectly, renders empty panels, cannot identify a wallet, fails DB reads, cannot find local state/log files, or when the emergency STOP button behavior is unclear.

## Streamlit import or version problems

Symptoms:

- `streamlit: command not found`
- `ModuleNotFoundError: No module named 'dashboard'`, `plotly`, `sqlalchemy`, `solana`, or `solders`
- Solana import errors mentioning `TokenAccountOpts`
- App starts in a Python environment that differs from the one where requirements were installed

Checks and fixes:

1. Run `python -m streamlit --version` or `streamlit --version` in the same environment that will launch the dashboard. Streamlit `1.61.1` was verified for this repository.
2. Install the core requirements, not only Streamlit and Plotly. `dashboard/data_service.py` imports pandas, SQLAlchemy, dotenv, solders, and solana even before the UI has rendered all panels.
3. If Solana SDK latest resolution breaks `TokenAccountOpts`, use the verified compatibility pin: `solana==0.36.12` with `websockets==15.0.1`.
4. Launch from a context where the AlphaGPT source import roots are visible. The repo is not packaged as a distribution, so a generic environment with only third-party packages installed is not enough.
5. Do not treat a live browser session as the first verification step. Prefer the fixture script, `python -m streamlit --version`, and static import checks before connecting DB/RPC services.

## Dashboard renders but is mostly empty

This is often expected when the live runner and data pipeline are not active.

Panel-specific causes:

- Portfolio tab: no `portfolio_state.json`, empty JSON object, or no open positions.
- Market Scanner tab: no DB connection, empty `ohlcv`, no matching `tokens` join rows, no latest timestamp, or query exception.
- Logs tab: no `strategy.log` in the dashboard process current working directory.
- Wallet metric: no usable private key or RPC failure, causing balance fallback to `0.0 SOL`.

Fast offline check:

1. Generate fixture files with [the bundled fixture script](../scripts/alpha_gpt_dashboard_fixture.py).
2. Confirm the files are in the same directory from which the dashboard process is launched.
3. Inspect the JSON with `python -m json.tool portfolio_state.json` and `python -m json.tool best_meme_strategy.json`.
4. If the fixture portfolio renders but live data is empty, route data-population work to `data-pipeline` and live runner/state work to `live-strategy`.

## Unknown wallet or `0.0000 SOL` balance

`DashboardService._get_wallet_address()` derives a public key from `SOLANA_PRIVATE_KEY`. It supports JSON byte arrays and base58 strings. Any parsing failure returns `Unknown`; `get_wallet_balance()` then catches RPC/public-key errors and returns `0.0`.

Interpretation:

- For offline dashboard checks, `Unknown` / `0.0 SOL` is acceptable and safer than loading credentials.
- For live monitoring, confirm that `SOLANA_PRIVATE_KEY` is present, correctly encoded, and belongs to the intended wallet.
- Confirm `QUICKNODE_RPC_URL` or the default RPC endpoint is reachable and compatible with the Solana client.
- Do not paste or log private keys into troubleshooting notes. Route wallet funding, transaction safety, and live execution decisions to `live-strategy`.

## DB query failures or empty market overview

`DashboardService.get_market_overview(self, limit=50)` swallows SQL exceptions and returns an empty DataFrame, so the dashboard may only show the warning `No market data found in DB`.

Common causes:

- Incorrect `DB_USER`, `DB_PASSWORD`, `DB_HOST`, or `DB_NAME`.
- PostgreSQL is down or not listening on port `5432`.
- `psycopg2` is missing even though SQLAlchemy is installed.
- Tables `ohlcv` or `tokens` do not exist.
- `ohlcv` has no rows, so `MAX(time)` is null.
- `tokens` rows do not join to `ohlcv.address`.
- Latest rows have zero or negative `liquidity`/`volume`, causing log-scale scatter issues even if the table has data.

Suggested checks:

1. Verify credentials and read-only connection outside Streamlit with a safe `SELECT 1` or a metadata-only table check.
2. Check that `tokens(address, symbol)` and `ohlcv(address, close, volume, liquidity, fdv, time)` contain recent rows.
3. Run a narrowed version of the market query with a small `LIMIT`.
4. If tables are missing or stale, route to `data-pipeline`; the dashboard should not be used to create schema or ingest data.

## Missing or malformed local files

The dashboard reads local files from the process current working directory.

### `portfolio_state.json`

- Missing file: empty portfolio state, no crash.
- Empty JSON object: empty portfolio state.
- Malformed JSON: not caught by `load_portfolio()` and can crash the app.
- Missing table columns such as `symbol`, `entry_price`, `highest_price`, `amount_held`, `initial_cost_sol`, or `is_moonbag`: can crash metrics or table rendering.
- `entry_price` equal to zero: can create invalid `pnl_pct` values.

Fix: regenerate a known-good fixture or repair the state shape to match the portfolio schema in [dashboard reference](dashboard-reference.md).

### `best_meme_strategy.json`

- Missing file or invalid JSON: falls back to `{"formula": "Not Trained Yet"}`.
- Dashboard does not validate formula tokens; it only shows this JSON as help text.
- If the live runner cannot consume the strategy file, route to `factor-mining` for formula-file validation or `live-strategy` for runner compatibility.

### `strategy.log`

- Missing file: empty log panel caption.
- Very large file: dashboard reads all lines and keeps only the tail, so consider rotating logs outside the dashboard.
- Different runner working directory: dashboard may tail the wrong or absent log file.

## Plotly chart failures

Portfolio PnL chart needs `symbol` and `pnl_pct`. The dashboard computes `pnl_pct` only when both `highest_price` and `entry_price` are present in the portfolio state.

Market scatter needs `symbol`, `liquidity`, `volume`, and `fdv`. Because it uses log axes for `liquidity` and `volume`, zero or negative values can lead to missing points or warnings. DB-side data cleanup belongs to `data-pipeline`.

## Auto-refresh loops or repeated service reads

The checkbox `Auto-Refresh (30s)` defaults to enabled. When enabled, the app sleeps and reruns every 30 seconds. Disable it when:

- inspecting a fixture,
- debugging one specific DB/RPC query,
- avoiding repeated RPC/DB reads, or
- reading logs that change too quickly for manual inspection.

The `Refresh Data` button is a manual `st.rerun()` and does not bypass DB/RPC or local file prerequisites.

## Emergency STOP button side effect

The dashboard STOP button performs one local filesystem action:

```text
write file: STOP_SIGNAL
file contents: STOP
```

Important caveats:

- The write happens in the dashboard process current working directory.
- The live strategy runner defaults to the same filename, but it can be configured with a different stop path. If paths or working directories differ, the button will not stop the runner.
- The runner checks the stop file between lifecycle steps, logs that the stop was received, and may rewrite the file to `STOPPED` after consuming it.
- The button does not cancel an already-submitted blockchain transaction, reverse fills, close positions, or modify the DB.
- A stale `STOP_SIGNAL` file present before starting the runner can stop the runner immediately.

For live shutdown policy, position liquidation, or execution safety, route to `live-strategy`. The dashboard sub-skill only documents the button's local file side effect.
