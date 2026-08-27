# Cascade and Evolution Troubleshooting

## `cascade.healthy` is false

Read `reasons` in `/health`. Alert-worthy conditions include repeated drain failures, optimize failure streaks, or stale version cleanup. `failed_permanent` is informational data-quality backlog and does not by itself make operational health false.

## Retryable vs permanent failed rows

- Retryable failures: usually transient embedding/network/provider problems. Run `everos cascade fix --apply` after the provider is healthy.
- Permanent failures: malformed Markdown or unsupported content. Edit the Markdown and re-save so watcher/scanner re-enqueues it.

## LanceDB schema drift

Startup may fail with a schema drift message. Correct recovery is `everos cascade rebuild` with the server stopped. Do not just delete `.index/lancedb`; done rows may be skipped and the index can come back empty.

## Server lock blocks rebuild/backfill

`rebuild` and backfill phases that touch OME need exclusive access. Stop `everos server start` first. `cascade sync` is the safe command to run alongside a live server.

## File watcher misses changes

WSL/network mounts and exhausted inotify watches can miss events. The scanner eventually catches changes, but for deterministic local operation run `everos cascade sync`. On Linux, raise `fs.inotify.max_user_watches` for large roots.

## Too many open files

Long-running LanceDB workloads can hit file descriptor ceilings. Raise the OS/process limit and keep the configured LanceDB index cache bounded. On macOS/Linux, check `ulimit -n` before server start.

## Backfill provider failures

Backfill can fail or abort when embedding, rerank, or LLM providers are missing or the user declines cost. Treat exit code and summary as authoritative; do not resume expensive phases without user approval.
