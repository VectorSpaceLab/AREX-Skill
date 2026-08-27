---
name: indexing
description: "Guide Kalshi and Polymarket market, trade, block, and legacy
  backfill workflows."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# indexing

Use this sub-skill for data-collection workflows that write Parquet chunks and resume from cursor files.
It covers both API-based and blockchain-based collectors.

## Use this route when

- The user wants to backfill markets, trades, blocks, or legacy FPMM data.
- The user wants to resume a partially completed run.
- The user wants to understand the shape of a cursor file or chunked Parquet output.
- The user wants to add a new indexer subclass.

## Scope

### Included

- Kalshi market and trade backfills.
- Polymarket market, trade, block, and legacy FPMM backfills.
- Cursor files, chunk naming, deduplication, and resume behavior.
- `KalshiClient`, `PolymarketClient`, `PolygonClient`, and `Indexer.load()`.

### Excluded

- Analysis and chart output workflows, which belong to `sub-skills/analysis/`.
- Dataset packaging and host-tool installation, which belong to `sub-skills/data-ops/`.

## Read first

- `../../references/indexing-catalog.md` for the full indexer list.
- `../../references/api-reference.md` for the client and base-class APIs.
- `../../references/data-layout.md` for chunk paths, cursor files, and helper files.
- `../../references/troubleshooting.md` for cross-cutting failures.

## Core workflow

1. Identify the indexer name and required inputs.
2. Confirm the cursor file and output directory state.
3. Provide any required env vars, especially `POLYGON_RPC` for blockchain-backed collectors.
4. Run the indexer through `uv run main.py index` or directly from the Python class.
5. Verify that the expected Parquet chunks and cursor files were updated.

## Indexer families

### Kalshi

- `kalshi_markets` backfills market snapshots into chunked Parquet files.
- `kalshi_trades` fetches trades for markets discovered from the market parquet tree and skips already-processed tickers.

Important details:

- Markets use `ParquetStorage` for chunking and deduplication.
- Trades run concurrently and dedupe by `trade_id`.
- `kalshi_trades` only considers markets above the built-in volume threshold.

### Polymarket markets and trades

- `polymarket_markets` paginates the Gamma API with an offset cursor.
- `polymarket_trades` backfills CTF and NegRisk `OrderFilled` logs by block range.

Important details:

- The trade indexer stores progress after each completed block chunk.
- The trade indexer writes chunked Parquet files under `data/polymarket/trades/`.
- The market indexer writes an offset cursor and chunked market files.

### Polymarket blocks

- `polymarket_blocks` builds a block-to-timestamp lookup.
- It samples every 100 blocks and interpolates the values to fill each bucket.
- The output feeds analyses that need approximate timestamps for trade blocks.

### Polymarket legacy FPMM trades

- `polymarket_fpmm_trades` decodes `FPMMBuy` and `FPMMSell` logs from the Polygon chain.
- It filters to USDC-collateralized markets.
- It is the most RPC-intensive collector in the repo.

## Adding or fixing an indexer

- Subclass `Indexer`.
- Set `name` and `description` in `__init__`.
- Keep the fetch/resume/save loop explicit so interruption points are easy to reason about.
- Write Parquet chunks with predictable names.
- Save or update a cursor file only after the relevant unit of work is safely completed.
- Prefer small helper methods for decoding logs, chunking ranges, or deduplicating existing rows.

## Common failure patterns

- Missing `POLYGON_RPC` for chain-backed collectors.
- Invalid cursor files that point to the wrong offset or block.
- Duplicate rows when the collector is rerun without deduplication.
- Chunk files that are partially written because a run was interrupted.
- Slow or failing RPC queries when the block range is too large.

## Helpful helper

- `../../scripts/catalog.py --indexers` lists the indexer names without opening the interactive menu when run through the repo environment.
