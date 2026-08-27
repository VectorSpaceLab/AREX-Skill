---
name: data-pipeline
description: "Configure, validate, and operate AlphaGPT's safe OHLCV ingestion pipeline."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Data Pipeline

Use this sub-skill when the task is about AlphaGPT market-data ingestion:
Birdeye or DexScreener provider behavior, Postgres/Timescale schema, OHLCV table
contents, `.env` configuration, safe preflight checks, or diagnosing empty/noisy
ingestion runs.

## Do not route here for

- Formula mining after OHLCV data is available; use [factor-mining](../factor-mining/SKILL.md).
- Live trading, risk controls, wallet execution, or portfolio state; use [live-strategy](../live-strategy/SKILL.md).
- Streamlit dashboard display over already-ingested rows; use [dashboard-ops](../dashboard-ops/SKILL.md).

## Read or run

1. Read [references/data-pipeline-reference.md](references/data-pipeline-reference.md) for the full data-flow map, provider behavior, DB tables, configuration values, and live-run gate.
2. Read [references/troubleshooting.md](references/troubleshooting.md) when a run reports a missing API key, cannot connect to Postgres, warns about TimescaleDB, selects zero tokens, or fails provider imports.
3. Run [scripts/alpha_gpt_schema_preview.py](scripts/alpha_gpt_schema_preview.py) to preview the `tokens` and `ohlcv` DDL without making any network request or database connection.
4. For cross-workflow import/env checks, run the root [environment checker](../../scripts/alpha_gpt_env_check.py) with `--scope data`.
5. For install and dependency pin notes, read [../../references/install-and-operations.md](../../references/install-and-operations.md).

## Safe default workflow

1. Confirm the task only needs offline review unless the user explicitly asks for live ingestion.
2. Inspect expected env vars: `BIRDEYE_API_KEY`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`, and `DB_NAME`.
3. Preview the schema with the bundled script instead of touching a database.
4. Check the filter policy before blaming the provider: default liquidity is `500000.0`, minimum FDV is `10000000.0`, `MAX_FDV` is unlimited, chain is `solana`, and timeframe is `1m`.
5. Verify whether the user is on the paid Birdeye path: paid mode requests up to 500 trending tokens, otherwise the code path is designed for a smaller limit.
6. Only after authorization, run the native pipeline against a disposable or explicit target database.

## Core runtime facts

- `DataManager.pipeline_sync_daily(self)` discovers candidates, filters by liquidity/FDV, upserts token metadata, fetches OHLCV in batches, and inserts candles.
- `DBManager.init_schema(self)` creates `tokens` and `ohlcv`; it attempts a Timescale hypertable and falls back to standard Postgres if unavailable.
- `BirdeyeProvider.get_trending_tokens(self, limit=100)` returns normalized token dictionaries with address, symbol, name, decimals, liquidity, and FDV.
- `BirdeyeProvider.get_token_history(self, session, address, days=7, liquidity=None, fdv=None)` returns formatted candle records with source `birdeye`.
- `DexScreenerProvider` exists, but the default daily sync does not use it as a full Birdeye replacement.

## Quick route map

| User intent | Read/run | Notes |
| --- | --- | --- |
| "What env vars/config does the data pipeline need?" | [references/data-pipeline-reference.md](references/data-pipeline-reference.md) | Covers `.env` values and code constants. |
| "Show the schema without touching DB." | [scripts/alpha_gpt_schema_preview.py](scripts/alpha_gpt_schema_preview.py) | Deterministic, standard-library only. |
| "Can I run the daily Birdeye sync?" | [references/data-pipeline-reference.md](references/data-pipeline-reference.md) | Requires explicit network/DB authorization. |
| "Why did it ingest no rows?" | [references/troubleshooting.md](references/troubleshooting.md) | Check API key, provider response, paid/free limit, liquidity/FDV filters, and DB insert path. |
| "How do Timescale and Postgres differ here?" | [references/data-pipeline-reference.md](references/data-pipeline-reference.md) | Hypertable creation is best-effort. |

## Verification stance

Native `data_pipeline/run_pipeline.py` is a skip-network/DB-write candidate. Use
schema preview, environment checks, and static review as default verification.
Do not run live ingestion unless the user supplies/authorizes API access,
network use, and a target database.
