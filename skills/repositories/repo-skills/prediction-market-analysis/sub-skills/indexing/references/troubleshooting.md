# Indexing Troubleshooting

## `POLYGON_RPC` is missing or invalid

Symptoms:
- Polymarket blockchain-backed collectors fail immediately or cannot fetch logs.

Likely cause:
- The RPC URL was not exported, was blank, or points to a dead endpoint.

Recovery:
- Set `POLYGON_RPC` to a reachable Polygon RPC endpoint.
- Retry only after a direct chain query succeeds.

## Cursor files look wrong

Symptoms:
- A collector resumes at a surprising offset or block.
- The collector appears to skip or repeat a range.

Likely cause:
- The cursor file was edited manually or left behind by a partial run.

Recovery:
- Compare the cursor value with the existing chunk filenames.
- If the cursor is stale, delete it only after confirming the completed chunks already exist.
- Otherwise resume from an explicit start value.

## Duplicate rows or repeated tickers

Symptoms:
- Reruns appear to append the same markets or trades again.

Likely cause:
- A deduplication key was not checked before the rerun.

Recovery:
- Review the collector's dedupe rule first.
- Do not delete chunk files until you know which rows are already present.

## Chunk write interruptions

Symptoms:
- A chunk file is missing or partial after a keyboard interrupt or timeout.

Likely cause:
- The collector was interrupted between fetch and write.

Recovery:
- Inspect the last completed chunk and cursor file.
- Rerun the collector only after deciding whether to resume or rebuild the affected range.

## Slow or failing legacy FPMM collection

Symptoms:
- The FPMM trade collector runs very slowly or times out on large ranges.

Likely cause:
- The RPC query range is too large for a single call.

Recovery:
- Use smaller block ranges.
- Keep the RPC endpoint reachable and avoid assuming a single query will handle very large spans.
