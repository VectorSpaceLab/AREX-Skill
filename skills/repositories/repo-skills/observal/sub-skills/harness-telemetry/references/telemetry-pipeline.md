# Telemetry Pipeline Reference

Observal session telemetry is a source-record pipeline. Harness hooks, extensions, and reconciliation all discover stable raw records; the CLI or native extension durably spools them before network delivery; the server stores raw rows, parses them through the registered harness parser, and advances a contiguous checkpoint.

## End-to-end flow

1. A harness writes or exposes a transcript source: JSONL, SQLite-backed rows mirrored to JSONL, or native extension messages converted to JSONL-compatible records.
2. A hook, plugin, extension event, or `observal reconcile` wakes delivery.
3. The harness adapter resolves a `SessionSource` with `harness`, `session_id`, optional `path`, `cwd`, optional `cursor_key`, and optional `parent_session_id`.
4. The exporter reads only complete non-empty records after the current byte/line cursor. Incomplete trailing JSONL lines stay local.
5. The batch is written to the durable local outbox before any network request.
6. The exporter posts to `POST /api/v1/ingest/session` with raw lines, source indexes, end-byte offsets, harness id, attribution, layer hash, and optional final integrity metadata.
7. The server classifies and stores raw source rows, refreshes session aggregates, advances the highest contiguous checkpoint, and returns `acknowledged_line` plus `acknowledged_offset`.
8. The exporter deletes acknowledged outbox rows and advances local cursor state only after that contiguous acknowledgement.
9. On finalization, the exporter hashes complete source history and the server requests repair from a line offset if it detects gaps or hash mismatch.

Reconciliation is not a separate ingest system. It uses the same adapter discovery, outbox, acknowledgement, checkpoint recovery, and parser code as hook delivery.

## Shared Python hook entrypoint

Most Python-backed harness hooks should invoke:

```text
python -m observal_cli.hooks.session_push --harness <harness-id>
```

`observal_cli/hooks/session_push.py` handles:

- JSON stdin parsing with errors swallowed so telemetry never breaks the host harness.
- Adapter lookup via `ensure_loaded()` and `get_adapter(harness)`.
- `resolve_session_source(...)` and optional related session sources.
- `session_extra_fields(...)` such as Kiro credits.
- `session_extra_records(...)` such as Cursor Stop-event usage rows.
- `defer_session_delivery()` for hooks that must return quickly.
- Detached workers for outbox drain, finalization, and aged recovery.
- Stable-file waits before final hash/audit passes.

Thin bridges are acceptable only when the host requires a specific stdout response or runtime wrapper. Current bridge examples are Antigravity's required JSON response and legacy Copilot bridge modules. New hooks should prefer the shared `session_push --harness ...` command unless the host contract proves a bridge is required.

## Durable local outbox and cursor state

The shared Python exporter uses:

| Local state | Purpose |
|---|---|
| `~/.observal/telemetry_buffer.db` | SQLite durable outbox; records are inserted before delivery and deleted only after acknowledgement. |
| `~/.observal/sync_state.json` | Per-source byte offset, source line count, and finalization status. |
| `~/.observal/telemetry_buffer.rejected.jsonl` | Quarantined permanently rejected payloads, so invalid batches do not block later sessions. |
| `~/.observal/sync.log` | Fail-soft delivery and checkpoint diagnostic messages. |

Outbox invariants:

- Capacity is capped at 256 MiB; capacity failure is explicit and does not evict unacknowledged records.
- Re-enqueueing the same source range with identical records is idempotent.
- Re-enqueueing the same source range with different content is rejected locally.
- Pending batches are bound to destination server and authenticated user.
- Older pending records drain before newly discovered source records.
- A partial acknowledgement does not advance the cursor beyond the contiguous server checkpoint.
- Permanent HTTP rejections such as 400, 409, 413, 415, and 422 are quarantined; transient network/server failures remain pending.

## Ingest API and server acknowledgement

The ingest route is `POST /api/v1/ingest/session` under `observal-server/api/routes/ingest.py`.

Request fields that matter for harness telemetry:

- `session_id`, `harness`, `agent_id`, `agent_version`, `layer_hash`.
- `lines`: raw source records, up to 1000 per request.
- `start_offset`: zero-based source line index for the first line.
- `end_byte_offsets`: absolute byte offsets at record boundaries.
- `hook_event`: lifecycle wake-up that caused this upload.
- `final`, `total_line_count`, `total_offset`, `session_hash`, `hashed_line_count`: finalization/audit metadata.
- `total_credits`: Kiro durable credit metadata.
- `parent_session_id`: subagent/delegated session relationship.

The checkpoint route is `GET /api/v1/ingest/session/checkpoint?session_id=...&harness=...`. The CLI uses it to recover missing, corrupt, or stale local cursor state before replaying source ranges.

Expected acknowledgement fields:

- `acknowledged_line`: highest contiguous stored source line.
- `acknowledged_offset`: corresponding byte offset.
- `integrity_ok`: present only on final uploads.
- `repair_from_line`: if present, rewind and replay from that source line.

## Current harness source map

| Harness | Wake-up/install mechanism | Source resolved by adapter or extension | Delivery behavior |
|---|---|---|---|
| Claude Code | `.claude/settings.json` UserPromptSubmit and Stop hooks | `~/.claude/projects/<project>/<session>.jsonl`, plus subagent JSONL files | Shared Python exporter; related subagents delivered with parent. |
| Kiro | Hooks embedded in each pulled Kiro agent JSON | `~/.kiro/sessions/cli/<session>.jsonl` plus companion `<session>.json` for cwd/agent/credits | Shared exporter; per-agent `OBSERVAL_AGENT_ID`; aged recovery does not force finality. |
| Cursor | Doctor/pull hook config under `.cursor` or user Cursor hooks | Cursor transcript path from payload, fallback under `~/.cursor/projects/...`; subagents discovered separately | Hook spools and defers network delivery; Stop can add synthetic usage line. |
| Codex | `~/.codex/hooks.json` and `codex_hooks = true` | `~/.codex/sessions/**/*.jsonl`, session id parsed from filename when needed | Shared exporter; finalizer on Stop. |
| Copilot VS Code | `.github/hooks/observal.json` plus PowerShell wrapper when needed | Hook payload materialized under `~/.observal/session_sources/copilot/<session>.jsonl` | Spool-first and detached network delivery. |
| Copilot CLI | Copilot hook JSON files | `~/.copilot/session-state/<uuid>/events.jsonl`, discovered via `session-store.db` or glob | Shared exporter with Copilot parser id. |
| OpenCode | In-process TypeScript plugin `observal-plugin.ts` | Plugin converts OpenCode messages to Claude-Code-compatible source records | Native plugin outbox and acknowledgement protocol; parser delegates to Claude Code format. |
| Antigravity | Named `observal-telemetry` hook entry | `brain/<conversation>/.system_generated/logs/transcript.jsonl` under Antigravity config | Bridge returns host-required JSON and routes delivery through shared exporter. |
| Goose | Goose plugin under `.agents/plugins/observal/` | Read-only `sessions.db` rows mirrored to `~/.observal/sessions/goose/<session>.jsonl` | Hook only spools/mirrors; detached network drain; `SessionEnd` finalizes. |
| Pi | Bundled TypeScript extension | Pi extension source records and outbox | Native extension outbox; server parser handles Pi JSONL shape. |

## Attribution and layer hash

Attribution order in `observal_cli/sessions/base.py`:

1. Adapter-specific `resolve_session_agent_identity(...)` can return an exact `(agent_id, version)` or an explicit `(None, None)`.
2. `OBSERVAL_AGENT_ID` is preferred when present; it is resolved through the Observal lockfile, first scoped to the harness and then globally.
3. If the adapter requires explicit identity, missing UUID leaves the session unattributed.
4. `OBSERVAL_AGENT_NAME` or a Claude Code `agent-setting` line can provide a name fallback.
5. Otherwise the lockfile may match by current working directory.

Kiro requires explicit attribution because its session JSONL does not reliably identify the pulled registry agent. OpenCode plugin attribution uses active OpenCode agent names and the lockfile. Copilot CLI and Kiro hook builders can inject `OBSERVAL_AGENT_ID` into generated commands. Do not guess agent identity from cwd when the adapter marks it unsafe.

Layer hash computation is best-effort and fail-soft. It scans detected harness files through `observal_cli/layer.py`, caches a hash per session, and evicts it when a Stop upload finalizes. If layer scanning fails, session delivery continues with no layer hash.

## Reconciliation workflow

Use reconciliation when hooks were installed late, the machine was offline, the server was down, an outbox has pending records, or a recent trace is missing.

Preview:

```bash
observal reconcile --dry-run --output json
observal reconcile --harness kiro --since 24 --dry-run --output json
```

Expected signal: JSON has `dry_run: true`, `targets`, and a `summary` with `would_push`, `would_finalize`, `up_to_date`, `skipped`, and `errors`. Dry run does not drain the outbox or contact ingest.

Deliver:

```bash
observal reconcile --output json
observal reconcile --harness goose --since 720 --output json
```

Expected signal: JSON summary distinguishes `pushed`, `finalized`, `queued`, and `rejected`; human output reports delivered/finalized or queued sessions.

Implementation signals:

- `cmd_reconcile_cli.py` validates auth before side effects.
- Non-dry-run drains the durable outbox before scanning sources.
- Targets are all installed adapters unless `--harness` is supplied.
- Each adapter's `discover_session_sources(since_hours=...)` controls source discovery.
- Every source recovers the authenticated server checkpoint before final delivery.

## Fast missing-session check

1. Confirm auth and server target:

   ```bash
   observal auth status
   observal ops telemetry status
   ```

   Expected: authenticated user/server; telemetry status shows outbox counts and last sync.

2. Inspect local harness setup:

   ```bash
   observal doctor
   observal scan --harness <harness-id> --output json
   ```

   Expected: doctor has no missing/stale hook warnings for the target harness; scan sees the harness or relevant components. For Kiro, a pulled agent must carry UUID-attributed hooks.

3. Preview recovery:

   ```bash
   observal reconcile --harness <harness-id> --since 168 --dry-run --output json
   ```

   Expected: `would_push` or `would_finalize` if there are undelivered source records; `up_to_date` when local cursor and server checkpoint agree.

4. Push and inspect traces:

   ```bash
   observal reconcile --harness <harness-id> --since 168 --output json
   observal ops traces --limit 5
   ```

   Expected: delivered/finalized summary and a recent trace for the harness if source records parsed successfully.

5. If records remain pending, preserve `~/.observal/telemetry_buffer.db`, `sync_state.json`, and the source transcript while investigating server reachability, auth identity, rejected batches, or checkpoint mismatch.
