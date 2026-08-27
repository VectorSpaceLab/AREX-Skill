# Data Pipeline Reference

## Purpose

Read this reference before configuring or operating AlphaGPT's market-data ingestion path. It distills the relevant runtime behavior so a future agent can plan safely without reopening source files or accidentally contacting Birdeye or Postgres.

## What This Pipeline Owns

The data pipeline discovers Solana tokens, filters candidates, fetches OHLCV candles, and stores results in Postgres/Timescale-compatible tables. Its live path is asynchronous and has side effects:

1. Load configuration values, including `.env` values.
2. Connect to Postgres and initialize schema.
3. Fetch trending tokens from Birdeye.
4. Filter candidates by liquidity and FDV.
5. Fetch OHLCV history for selected tokens.
6. Upsert token metadata and bulk insert OHLCV records.

Formula mining consumes the stored data later; live trading and dashboard display are separate workflows.

## Environment Variables and Configuration Values

Only a subset of `Config` values are read directly from environment variables. The rest are code constants unless the caller edits configuration or deliberately overrides `Config` before constructing pipeline objects.

| Name | Default | Used by | Notes |
| --- | --- | --- | --- |
| `DB_USER` | `postgres` | Postgres DSN | Loaded from environment. |
| `DB_PASSWORD` | `password` | Postgres DSN | Loaded from environment; do not rely on this placeholder for real deployments. |
| `DB_HOST` | `localhost` | Postgres DSN | Loaded from environment. |
| `DB_PORT` | `5432` | Postgres DSN | Loaded from environment. |
| `DB_NAME` | `crypto_quant` | Postgres DSN | Loaded from environment. |
| `DB_DSN` | derived | `asyncpg.create_pool` | Built as `postgresql://DB_USER:DB_PASSWORD@DB_HOST:DB_PORT/DB_NAME`. |
| `BIRDEYE_API_KEY` | empty string | Birdeye request header | Required for the live runner; absence causes the runner to log an error and return before DB work. |
| `BIRDEYE_BASE_URL` | `https://public-api.birdeye.so` | Birdeye endpoints | Override only for compatible Birdeye API hosts or controlled mocks. |
| `CHAIN` | `solana` | token metadata, DexScreener filtering | Stored in `tokens.chain`; DexScreener details filter checks this chain. |
| `TIMEFRAME` | `1m` | Birdeye OHLCV query | Source comment notes `15min` is also supported. Confirm account/API support before increasing request volume. |
| `MIN_LIQUIDITY_USD` | `500000.0` | candidate filter | Tokens below this liquidity are discarded. |
| `MIN_FDV` | `10000000.0` | candidate filter | Tokens below this FDV are discarded. |
| `MAX_FDV` | infinity | candidate filter | Tokens above this FDV are discarded. Useful for excluding very large tokens. |
| `BIRDEYE_IS_PAID` | `True` | trending token limit | `True` makes the daily sync request up to 500 trending tokens; `False` uses 100. |
| `USE_DEXSCREENER` | `False` | currently not used by daily sync | The provider exists, but `DataManager.pipeline_sync_daily` does not branch on this flag. |
| `CONCURRENCY` | `20` | Birdeye history semaphore | Upper bound for concurrent OHLCV requests inside `BirdeyeProvider`. |
| `HISTORY_DAYS` | `7` | Birdeye history default | Default lookback for `get_token_history`; shorter windows reduce request/insert volume. |

## Provider Flow

### Birdeye trending discovery

`BirdeyeProvider.get_trending_tokens(self, limit=100)` requests `/defi/token_trending` with `sort_by=rank`, `sort_type=asc`, `offset=0`, and the supplied `limit`. It returns dictionaries with:

- `address`
- `symbol`
- `name`
- `decimals`
- `liquidity`
- `fdv`

Non-200 responses and exceptions are logged and converted to an empty list.

### Candidate filtering

`DataManager.pipeline_sync_daily(self)` uses a limit of 500 when `BIRDEYE_IS_PAID` is true and 100 otherwise. It then keeps only candidates satisfying:

```text
liquidity >= MIN_LIQUIDITY_USD
fdv >= MIN_FDV
fdv <= MAX_FDV
```

If no candidate passes, the method logs that no tokens passed the filter and returns without token upsert or OHLCV fetch.

### OHLCV history fetch

`BirdeyeProvider.get_token_history(self, session, address, days=7, liquidity=None, fdv=None)` requests `/defi/ohlcv` with:

- `address`: token address.
- `type`: `TIMEFRAME`.
- `time_from`: current time minus `days`.
- `time_to`: current time.

Each returned item is converted into a tuple matching the `ohlcv` table columns:

```text
(time, address, open, high, low, close, volume, liquidity, fdv, source)
```

The timestamp is converted from `unixTime`. Missing candle liquidity/FDV falls back to the snapshot values supplied from the trending token. `source` is the literal string `birdeye`.

For HTTP 429, the provider waits two seconds and retries the same address. Because this retry is recursive and still uses the configured concurrency, reduce `CONCURRENCY`, selected-token count, or `HISTORY_DAYS` when repeated 429s occur.

### DexScreener status

`DexScreenerProvider` can batch query token details and choose the most liquid pair for each base token, but the daily pipeline does not use it by default. Its `get_trending_tokens` and `get_token_history` methods are effectively stubs in the selected workflow. Do not promise DexScreener OHLCV backfill unless the code is extended.

## Database Schema

Use [../scripts/alpha_gpt_schema_preview.py](../scripts/alpha_gpt_schema_preview.py) to print the same schema without DB access.

### `tokens`

| Column | Type | Notes |
| --- | --- | --- |
| `address` | `TEXT PRIMARY KEY` | Token address. |
| `symbol` | `TEXT` | Updated on conflict. |
| `name` | `TEXT` | Inserted, but not updated on conflict by the default upsert. |
| `decimals` | `INT` | Inserted token decimals. |
| `chain` | `TEXT` | Default workflow uses `solana`. |
| `last_updated` | `TIMESTAMP DEFAULT NOW()` | Refreshed on token upsert. |

Token metadata is written with `INSERT ... ON CONFLICT(address) DO UPDATE SET symbol = EXCLUDED.symbol, last_updated = NOW()`.

### `ohlcv`

| Column | Type | Notes |
| --- | --- | --- |
| `time` | `TIMESTAMP NOT NULL` | Candle timestamp. |
| `address` | `TEXT NOT NULL` | Token address. |
| `open` | `DOUBLE PRECISION` | Candle open. |
| `high` | `DOUBLE PRECISION` | Candle high. |
| `low` | `DOUBLE PRECISION` | Candle low. |
| `close` | `DOUBLE PRECISION` | Candle close. |
| `volume` | `DOUBLE PRECISION` | Candle volume. |
| `liquidity` | `DOUBLE PRECISION` | Candle or snapshot liquidity. |
| `fdv` | `DOUBLE PRECISION` | Candle or snapshot fully diluted valuation. |
| `source` | `TEXT` | Default value written by Birdeye path is `birdeye`. |
| primary key | `(time, address)` | Duplicate candles conflict on rerun. |

After creating `ohlcv`, the initializer attempts `create_hypertable('ohlcv', 'time', if_not_exists => TRUE)`. If the TimescaleDB extension is unavailable, it logs a warning and continues with standard Postgres. It also creates `idx_ohlcv_address` on `ohlcv(address)`.

OHLCV writes use `copy_records_to_table` rather than an upsert. A duplicate `(time, address)` can raise a unique-violation path; the implementation catches that case instead of updating existing candles.

## Safe Live-Run Procedure

Do not run this procedure unless the user explicitly wants live network and database writes.

1. **Preview schema offline.** From the generated skill tree, run:

   ```bash
   python sub-skills/data-pipeline/scripts/alpha_gpt_schema_preview.py --format sql
   ```

   Review the DDL and decide whether the target database may receive these tables, index, and optional Timescale hypertable conversion.

2. **Choose a staging database first.** Create or select a Postgres database dedicated to AlphaGPT testing. Enable TimescaleDB only if desired; standard Postgres is accepted by the initializer.

3. **Set only required secrets in the runtime environment.** Provide `BIRDEYE_API_KEY` and the `DB_*` values. Avoid committing `.env` files or credentials.

4. **Reduce blast radius for first runs.** Prefer conservative settings: lower selected-token count, shorter `HISTORY_DAYS`, and smaller `CONCURRENCY`. The defaults can request many OHLCV histories when paid Birdeye mode is enabled.

5. **Run a read-only config/import preflight.** A safe preflight can import `data_pipeline.config`, print non-secret values, and confirm the API key is present without printing it. Do not connect to DB in this step.

6. **Run the live module only after authorization.** The live command is:

   ```bash
   python -m data_pipeline.run_pipeline
   ```

   It checks for `BIRDEYE_API_KEY`, connects to Postgres, initializes schema, fetches network data, upserts `tokens`, and inserts `ohlcv` rows.

7. **Validate results with read-only SQL.** Suggested checks:

   ```sql
   SELECT COUNT(*) AS token_count FROM tokens;
   SELECT COUNT(*) AS candle_count, MIN(time) AS first_candle, MAX(time) AS last_candle FROM ohlcv;
   SELECT source, COUNT(*) FROM ohlcv GROUP BY source ORDER BY COUNT(*) DESC;
   SELECT address, COUNT(*) AS candles FROM ohlcv GROUP BY address ORDER BY candles DESC LIMIT 10;
   ```

8. **Record live-service limits separately.** Credentials, rate limits, network availability, and DB reachability are operational prerequisites. They should not be treated as offline skill-verification failures.

## Validation Checklist

Before a live run:

- `BIRDEYE_API_KEY` is set, not printed, and belongs to the intended Birdeye account tier.
- `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`, and `DB_NAME` point to a disposable or approved database.
- Core data-pipeline dependencies are installed: `aiohttp`, `asyncpg`, `loguru`, and `python-dotenv`.
- `TIMEFRAME`, `HISTORY_DAYS`, `CONCURRENCY`, and paid/free token limit are appropriate for the API quota.
- Liquidity and FDV filters are intentionally strict enough for the task but not so strict that `selected_tokens` is always empty.
- The operator understands that `tokens` upserts but `ohlcv` does not update duplicate candles.
- TimescaleDB is optional; a warning about missing `create_hypertable` is not by itself fatal.

After a live run:

- Logs show nonzero raw candidates from Birdeye, unless the API returned no usable data.
- Logs show selected-token count after filters; zero means no OHLCV requests were made.
- `tokens` count increases or refreshes as expected.
- `ohlcv` has rows with `source='birdeye'`, plausible time bounds, and expected candle counts per address.
- Any 429s, network errors, or duplicate-key behavior are captured and remediated before treating data as complete.
