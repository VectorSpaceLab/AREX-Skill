# Data Layout

This repo works with Parquet data under `data/` and writes analysis artifacts to `output/`.
The dataset is large, so treat the directory layout as an explicit contract.

## Top-level paths

| Path | Purpose | Notes |
| --- | --- | --- |
| `data/kalshi/markets/` | Kalshi market snapshots | Chunked Parquet files. |
| `data/kalshi/trades/` | Kalshi trade history | Chunked Parquet files with trade IDs. |
| `data/polymarket/markets/` | Polymarket market snapshots | Chunked Parquet files. |
| `data/polymarket/trades/` | Polymarket CTF Exchange trade history | Chunked Parquet files. |
| `data/polymarket/legacy_trades/` | Legacy Polymarket FPMM trades | Chunked Parquet files. |
| `data/polymarket/blocks/` | Polygon block-to-timestamp lookup | Chunked Parquet files. |
| `data/polymarket/fpmm_collateral_lookup.json` | FPMM collateral metadata | Used to keep only USDC-collateralized legacy markets. |
| `output/` | Analysis outputs | PNG, PDF, CSV, JSON, and GIF artifacts. |
| `data.tar.zst` | Packaged dataset archive | Written by packaging commands. |

## Cursor and progress files

| Path | Used by | Notes |
| --- | --- | --- |
| `data/kalshi/.backfill_cursor` | Kalshi markets indexer | Stores the current market cursor. |
| `data/kalshi/.backfill_trades_cursor` | Kalshi trades indexer | Stores the last processed ticker/trade progress. |
| `data/polymarket/.backfill_offset` | Polymarket markets indexer | Stores the current Gamma API offset. |
| `data/polymarket/.backfill_block_cursor` | Polymarket trades indexer | Stores the last completed block range. |
| `data/polymarket/.legacy_backfill_block_cursor` | Polymarket legacy trade indexer | Stores the last completed legacy block range. |
| `data/.download_complete` | Dataset download helper | Marks a completed download/extract cycle. |

## File naming patterns

- Kalshi market chunks: `markets_<start>_<end>.parquet`
- Kalshi trade chunks: `trades_<start>_<end>.parquet`
- Polymarket market chunks: `markets_<start>_<end>.parquet`
- Polymarket trade chunks: `trades_<start>_<end>.parquet`
- Polymarket legacy trade chunks: `trades_<start>_<end>.parquet`
- Polymarket block chunks: `blocks_<start>_<end>.parquet`

## Schema summary

Use `docs/SCHEMAS.md` for full field lists. The fields most analysis workflows rely on are:

### Kalshi markets

- `ticker`, `event_ticker`, `market_type`, `title`, `status`
- `yes_bid`, `yes_ask`, `no_bid`, `no_ask`, `last_price`
- `volume`, `volume_24h`, `open_interest`, `result`
- `created_time`, `open_time`, `close_time`, `_fetched_at`

### Kalshi trades

- `trade_id`, `ticker`, `count`
- `yes_price`, `no_price`, `taker_side`
- `created_time`, `_fetched_at`

### Polymarket markets

- `id`, `condition_id`, `question`, `slug`
- `outcomes`, `outcome_prices`, `clob_token_ids`
- `volume`, `liquidity`, `active`, `closed`
- `end_date`, `created_at`, `market_maker_address`, `_fetched_at`

### Polymarket CTF trades

- `block_number`, `transaction_hash`, `log_index`, `order_hash`
- `maker`, `taker`, `maker_asset_id`, `taker_asset_id`
- `maker_amount`, `taker_amount`, `fee`
- `_fetched_at`, `_contract`

### Polymarket legacy FPMM trades

- `block_number`, `transaction_hash`, `log_index`, `fpmm_address`
- `trader`, `amount`, `fee_amount`, `outcome_index`, `outcome_tokens`
- `is_buy`, `timestamp`, `_fetched_at`

### Polymarket blocks

- `block_number`, `timestamp`

## Environment variables that affect layout

- `POLYGON_RPC` is required for blockchain-backed Polymarket indexers.
- `POLYMARKET_START_BLOCK` sets the default CTF Exchange start block.
- The code also uses an internal legacy FPMM start block constant for older trades.

## Practical notes

- Most analyses expect closed or finalized markets and may return empty results if the dataset is incomplete.
- The comparison analysis needs both Kalshi and Polymarket data plus the block lookup and collateral lookup files.
- The packaging workflow writes an archive from `data/`; it does not rename or move the source directory.
