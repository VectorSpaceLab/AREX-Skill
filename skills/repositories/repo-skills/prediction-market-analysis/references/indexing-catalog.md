# Indexing Catalog

This repo exposes 6 indexers discoverable through `src.common.indexer.Indexer.load()`.
Use this catalog when deciding what data collector to run or when adding a new one.

## Kalshi indexers

### `kalshi_markets`

- Source: Kalshi trade API markets endpoint.
- Output: `data/kalshi/markets/`.
- Cursor: `data/kalshi/.backfill_cursor`.
- Storage: `ParquetStorage`, chunked market files.
- Notes: appends deduplicated market snapshots and resumes from cursor when present.

### `kalshi_trades`

- Source: Kalshi trade API trades endpoint.
- Output: `data/kalshi/trades/`.
- Cursor: `data/kalshi/.backfill_trades_cursor`.
- Notes: filters tickers from the markets directory, ignores low-volume tickers below the built-in threshold, deduplicates trade IDs, and fetches concurrently.

## Polymarket indexers

### `polymarket_markets`

- Source: Polymarket Gamma API.
- Output: `data/polymarket/markets/`.
- Cursor: `data/polymarket/.backfill_offset`.
- Notes: offset-based pagination with chunked Parquet output.

### `polymarket_trades`

- Source: Polygon logs from the CTF Exchange and NegRisk CTF Exchange contracts.
- Output: `data/polymarket/trades/`.
- Cursor: `data/polymarket/.backfill_block_cursor`.
- Notes: backfills block ranges, stores per-range Parquet chunks, and saves progress after each completed block chunk.

### `polymarket_blocks`

- Source: Polygon block timestamps.
- Output: `data/polymarket/blocks/`.
- Notes: samples every 100 blocks and interpolates timestamps to fill each bucket.

### `polymarket_fpmm_trades`

- Source: legacy FPMM logs from the Polygon chain.
- Output: `data/polymarket/legacy_trades/`.
- Cursor: `data/polymarket/.legacy_backfill_block_cursor`.
- Notes: decodes buy/sell topics, filters to USDC-collateralized markets, and parallelizes chunk fetches.

## Shared data sources and env vars

| Signal | Meaning |
| --- | --- |
| `POLYGON_RPC` | Required RPC URL for chain-based Polymarket indexers. |
| `POLYMARKET_START_BLOCK` | Default CTF Exchange start block. |
| `FPMM_START_BLOCK` | Default legacy FPMM start block. |
| `CTF_EXCHANGE` / `NEGRISK_CTF_EXCHANGE` | Contract addresses used by the Polymarket trade collector. |
| `FPMM_FACTORY` | Factory address used by the legacy FPMM collector. |

## Common indexing patterns

- Kalshi indexers are cursor-based and can resume after interruption.
- Polymarket trade and legacy-trade indexers are block-range based and can resume from cursor files.
- Block indexing is intentionally approximate and uses interpolation to avoid hitting every block.
- Legacy FPMM indexing is the most RPC-intensive workflow and can be slow on large ranges.

## What to watch for

- Missing `POLYGON_RPC` breaks all blockchain-backed Polymarket collectors.
- An invalid or stale cursor can cause a resume to jump to the wrong place.
- Chunk files are appended, not rewritten from scratch, so deduplication matters.
- The Polymarket markets and trades workflows rely on the dataset's expected directory names.
