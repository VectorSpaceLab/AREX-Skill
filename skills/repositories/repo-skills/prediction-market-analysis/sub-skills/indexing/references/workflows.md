# Indexing Workflows

## Running an indexer

1. Confirm the target data directory and cursor file state.
2. Set any required env vars, especially `POLYGON_RPC`.
3. Run `uv run main.py index` and choose the desired collector, or call the class directly.
4. Verify the expected chunk files and cursor file after the run.

## Resume rules

- Cursor files record the last safe checkpoint, not necessarily the final row written.
- A completed run may delete the cursor file.
- If a cursor looks wrong, compare it against the existing chunk files before deleting anything.

## Kalshi-specific notes

- Market backfills use `ParquetStorage` and deduplicate by ticker.
- Trade backfills reuse the markets tree to decide which tickers to fetch.
- Trade fetching is concurrent and can skip already processed tickers.

## Polymarket-specific notes

- Market collection is offset-based.
- Trade collection is block-range based and handles both CTF and NegRisk contract addresses.
- Block collection interpolates timestamps from sampled blocks.
- Legacy FPMM collection is log-decoding heavy and should be treated as the most expensive RPC workflow.

## Adding a new indexer

- Make the work unit small enough that interruption recovery is practical.
- Save progress only after the work unit is complete.
- Choose chunk names and cursor semantics that are easy to inspect by hand.
- If the collector depends on an external API or RPC, document the required env vars and rate limits.
