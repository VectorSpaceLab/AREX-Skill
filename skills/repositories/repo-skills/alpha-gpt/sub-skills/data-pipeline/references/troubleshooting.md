# Data Pipeline Troubleshooting

## Purpose

Use this file when AlphaGPT's data ingestion path is unsafe to run, refuses to start, returns no rows, or fails around Birdeye, Postgres/Timescale, dependencies, or rate limits.

## Missing `BIRDEYE_API_KEY`

**Symptoms**

- Live runner logs `BIRDEYE_API_KEY is missing in .env`.
- No database connection or schema initialization happens.
- Birdeye requests return unauthorized responses when a bad key is supplied.

**Likely causes**

- `.env` was not loaded from the process working directory.
- The environment variable is unset or empty.
- The key belongs to a tier that cannot serve the requested endpoint/limit.

**Recovery**

1. Confirm presence without printing the secret value: check only whether `BIRDEYE_API_KEY` is non-empty.
2. Confirm `BIRDEYE_BASE_URL` is the expected compatible Birdeye API host.
3. For first live runs, set `BIRDEYE_IS_PAID` conservatively or reduce the requested limit in code if the account tier is uncertain.
4. If authorization still fails, stop and ask the user for a valid API key or explicit permission to use a mock provider. Do not bypass by scraping another source.

## Postgres or TimescaleDB Problems

**Symptoms**

- `asyncpg.create_pool` raises connection, authentication, DNS, or timeout errors.
- Schema initialization logs a TimescaleDB warning.
- `tokens` exists but `ohlcv` remains empty.
- Reruns encounter duplicate candle conflicts.

**Likely causes**

- `DB_*` values point to the wrong host, port, database, or credentials.
- The database does not exist or is not reachable from the runtime host.
- TimescaleDB extension is not installed or not enabled.
- OHLCV duplicates conflict on `(time, address)` because the pipeline bulk-inserts rather than upserting candles.

**Recovery**

1. Use [../scripts/alpha_gpt_schema_preview.py](../scripts/alpha_gpt_schema_preview.py) to preview DDL without connecting to the database.
2. Verify the target database with a read-only or disposable connection before running the live pipeline.
3. Treat a TimescaleDB `create_hypertable` warning as non-fatal if standard Postgres is acceptable. Install/enable TimescaleDB only when hypertable behavior is required.
4. If duplicate candles are expected, either truncate the staging table before rerun, narrow the history window, or implement an explicit OHLCV upsert before relying on repeated live syncs.
5. If schema creation partially succeeded, inspect `tokens`, `ohlcv`, and `idx_ohlcv_address` before rerunning so the next run does not hide an earlier setup problem.

## Birdeye Rate Limits and Network Errors

**Symptoms**

- Logs include HTTP `429` for token history.
- Runs are slow because the provider sleeps and retries individual addresses.
- Trending fetch logs a non-200 status or returns an empty candidate list.
- OHLCV rows are much fewer than expected.

**Likely causes**

- `CONCURRENCY` is too high for the key tier or current API limits.
- `BIRDEYE_IS_PAID=True` selects a 500-token discovery limit against a lower-tier key.
- `HISTORY_DAYS` and `TIMEFRAME='1m'` request too many candles.
- Network, DNS, proxy, or API service availability is unstable.

**Recovery**

1. Reduce request volume: lower `CONCURRENCY`, shorten `HISTORY_DAYS`, and use the 100-token discovery path when paid entitlement is uncertain.
2. Retry only after confirming the previous run did not leave partial rows that would create duplicate conflicts.
3. Check whether the trending endpoint returns raw candidates before debugging filters or DB writes.
4. If persistent 429s occur, stop live execution and ask the user whether to wait for quota reset, use a smaller allowlist, or provide a higher-tier key.

## Empty `selected_tokens`

**Symptoms**

- Logs show raw candidates were found, followed by `Tokens selected after filtering: 0`.
- The run logs `No tokens passed the filter. Relax constraints in Config.`
- `tokens` and `ohlcv` do not receive new rows from that run.

**Likely causes**

- `MIN_LIQUIDITY_USD` or `MIN_FDV` is too high for the current market/API response.
- `MAX_FDV` excludes all high-cap candidates.
- Birdeye returned missing or zero `liquidity`/`fdv`, which the provider converts to `0.0`.
- The API key/tier or endpoint does not return the expected metadata fields.

**Recovery**

1. Inspect aggregate counts of raw candidates and non-secret metadata ranges in a controlled diagnostic, not by printing API keys.
2. Relax one filter at a time: liquidity first, then minimum FDV, then maximum FDV.
3. Keep a record of filter values used for any downstream model or strategy comparison; changing filters changes the training universe.
4. Do not treat an empty selection as a DB failure unless raw candidates and filter passes were confirmed.

## Dependency and Import Issues

**Symptoms**

- `ModuleNotFoundError` for `data_pipeline` or provider modules.
- `ModuleNotFoundError` for `aiohttp`, `asyncpg`, `loguru`, or `dotenv`.
- Full-repo import checks fail around Solana classes even though the data pipeline itself is being investigated.

**Likely causes**

- AlphaGPT is a source tree with import roots, not an installed package distribution.
- The process is not running with the repository root or equivalent source path importable.
- Core requirements were not installed.
- Broad installation of the full requirements can resolve to a Solana version whose API differs from the execution layer's expectations.

**Recovery**

1. For data-pipeline-only work, install or verify the core packages used here: `aiohttp`, `asyncpg`, `loguru`, and `python-dotenv`.
2. Ensure the AlphaGPT source import roots are importable before running `python -m data_pipeline.run_pipeline`.
3. Do not install `requirements-optional.txt` for this workflow; those dependencies belong to excluded experimental scripts.
4. If a full-repo import smoke is required and Solana imports fail, use the known-compatible family around `solana==0.36.12` with `websockets==15.0.1`. This is usually not necessary for schema preview or data-pipeline-only diagnostics.
5. Keep local environment paths, activation commands, and private interpreter names out of runtime notes and user-facing reports.

## Unsafe Live-Run Requests

**Symptoms**

- A prompt asks to "just run the pipeline" without specifying credentials, database target, or write authorization.
- A request mixes data ingestion with live trading or dashboard operations.

**Recovery**

1. Explain that the daily runner performs network calls and database writes.
2. Offer the offline schema preview and configuration checklist first.
3. Ask for explicit authorization, target DB identity, credential availability, and acceptable request volume before running live ingestion.
4. Route formula mining, live strategy, execution, or dashboard display questions to their owning sub-skills instead of expanding this data-pipeline scope.
