# Troubleshooting

This page covers failures that can affect more than one workflow.
Workflow-specific issues belong in the nearest sub-skill troubleshooting file.

## Installation and import issues

### `uv sync` or editable install succeeded, but `src` still does not import

Likely causes:

- You ran the command from a directory that does not have the repo root on the import path.
- The environment was created, but the repository itself was not made visible to Python.
- The local checkout is missing a repo-root path entry in the environment.

Recovery:

- Run the bundled catalog helper or the repo CLI from the repository root.
- If you are in a fresh shell, confirm the repo root is on the import path or use the environment helper that adds it.
- Recheck with the environment Python and `python -I` from outside the checkout.

### `python -m pip` is missing in the prepared environment

Some uv-managed environments may not include `pip` even though package management and checks still work.
Use the uv-equivalent checks from the prepared environment instead of assuming `pip` is present.

## Analysis workflow issues

### Analysis discovery returns zero results

Likely causes:

- `Analysis.load()` was called from the wrong current working directory.
- The path argument pointed at the wrong source root.
- The analysis files are present but not importable because the repo root is not visible.

Recovery:

- Pass an explicit `src/analysis` path rooted at the repo checkout.
- Use `scripts/catalog.py` to confirm the analysis list.

### Analysis runs return empty data or no figure

Likely causes:

- The expected `data/kalshi/` or `data/polymarket/` tree is missing.
- The dataset contains no finalized/resolved markets for the query.
- A helper file such as `fpmm_collateral_lookup.json` or the block lookup files is missing.

Recovery:

- Check the data layout reference.
- Confirm the required directories and helper files exist.
- For comparison analyses, verify both Kalshi and Polymarket inputs are present.

### Headless plotting failures

Likely causes:

- The environment is using a GUI backend on a headless host.

Recovery:

- Use a non-interactive matplotlib backend such as Agg when testing or running in CI.
- Close figures after save operations to avoid resource leaks.

## Indexing workflow issues

### `POLYGON_RPC` missing or invalid

Likely causes:

- Blockchain-backed Polymarket indexers cannot reach the RPC endpoint.

Recovery:

- Set `POLYGON_RPC` to a reachable Polygon RPC URL before running those indexers.
- Retry only after the RPC endpoint is reachable and the host can make outbound calls.

### Cursor corruption or bad resume position

Likely causes:

- A cursor file was edited manually, truncated, or left from a failed partial run.

Recovery:

- Inspect the cursor file and compare it with the completed chunk files.
- Delete the stale cursor only if you are sure the completed output already exists.
- Resume from an explicit start block or offset if the cursor cannot be trusted.

### Duplicate or partially written Parquet chunks

Likely causes:

- An indexer was interrupted between chunk writes.
- The existing dataset already contains records for the same ticker or trade ID.

Recovery:

- Confirm the deduplication keys used by the indexer before deleting anything.
- Re-run the collector only after checking which chunks were already written.

## Data-ops workflow issues

### `zstd` or a downloader is missing

Likely causes:

- The host does not have the required extraction or download tool.

Recovery:

- Install `zstd` and one of `aria2c`, `curl`, or `wget` with the system package manager.
- On an interactive setup path, use the repo's tool-install helper only if host mutation is acceptable.

### Packaging does not remove `data/`

This is expected from the code path. The packaging helper creates `data.tar.zst` but leaves the original tree in place.
If you need to clean the source directory, do it explicitly after you have confirmed the archive is correct.

## Interactive CLI issues

### The menu commands fail in a non-TTY session

Likely causes:

- `main.py analyze` and `main.py index` open interactive menus by default.

Recovery:

- Use the bundled catalog helper first to list valid names.
- Pass an explicit analysis name where supported.
- Run the workflow from a terminal if you want the interactive menus.
