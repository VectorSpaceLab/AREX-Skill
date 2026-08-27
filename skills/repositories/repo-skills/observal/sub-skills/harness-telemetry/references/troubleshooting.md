# Harness Telemetry Troubleshooting

Use this playbook for failures owned by harness registry/adapters, scan/doctor, hook specs, session push/reconcile, parsers, ingest checkpoints, and local durable outbox behavior.

## First classify the failure

| User symptom | Start here | Primary owner |
|---|---|---|
| `observal scan` misses a harness or component | Scan/config section | CLI adapter, registry paths, `cmd_scan.py` display path |
| `observal doctor` reports missing/stale hooks | Doctor/hook section | CLI adapter `patch_hooks`, `cmd_doctor.py`, hook spec or extension source |
| Hook runs but no trace appears | Missing-session decision tree | Adapter source resolution, outbox, auth, ingest, parser |
| `observal reconcile` finds nothing | Reconcile/source section | Adapter `discover_session_sources`, session helper paths, `--since` window |
| Raw records are stored but trace detail is wrong | Parser section | `services/session_parsers/*`, `ingest_classify.py`, `session_ingest.py` extractors |
| Pull/install writes wrong config | Config generation section | Server harness adapter, registry paths/keys, CLI pull rewrite |
| Layer hash or managed-file attribution is wrong | Layer section | Adapter managed patterns, `observal_cli/layer.py` globs |

## Install/import failures

### Hook command cannot import `observal_cli`

Signals:

- Host hook logs show `ModuleNotFoundError: observal_cli`.
- Hook command uses a bare `python`/`python3` that is not the Observal CLI environment.
- Telemetry works from the terminal but not from the harness process.

Checks:

```bash
python -c "import observal_cli; print('ok')"
observal doctor patch --harness <harness-id> --dry-run --output json
```

Expected: Python import prints `ok`; doctor dry run shows the command it would install or reports no change.

Fixes:

- Ensure the hook spec uses the current interpreter (`sys.executable`) or a safe `PYTHONPATH` fallback when building local hook commands.
- Ensure `observal agent pull` rewrites server-generated generic hook commands to the local interpreter before writing files.
- Prefer `python -m observal_cli.hooks.session_push --harness <id>` for new hook specs.
- Do not add a new harness-specific push module unless the host requires a special stdout protocol; keep transport in the shared session engine.

### Pull writes a stale hook entrypoint

Signals:

- Generated config references a module that does not exist in `observal_cli/hooks/`.
- Doctor patch uses `observal_cli.hooks.session_push --harness <id>`, but `observal agent pull --dry-run` shows a different legacy module.

Fixes:

- Update the server harness adapter to emit the shared entrypoint.
- Or add a CLI adapter `rewrite_hooks(...)`/`rewrite_agent_profile(...)` path that replaces only Observal-managed hook commands with the current shared entrypoint and local interpreter.
- Add a test that `observal agent pull --harness <id> --dry-run --output json` contains the current command.

## CLI/API/auth failures

### Doctor or reconcile says auth/session delivery is not configured

Checks:

```bash
observal auth status
observal auth whoami
observal ops telemetry status
```

Expected: authenticated user, reachable server, and telemetry status output. `reconcile` requires a configured `server_url`, usable token, and `user_id` in the CLI config.

Fixes:

- Run `observal auth login` before `doctor patch` or `reconcile`.
- If status works but ingest returns 401, check that the same authenticated user owns the outbox destination; pending rows are server/user-bound.
- If a refresh token exists, the shared exporter will try one access-token refresh before marking the post failed.

### Ingest endpoint rejects a batch

Signals:

- Reconcile JSON reports `rejected` rows.
- `~/.observal/telemetry_buffer.rejected.jsonl` grows.
- HTTP status is 400, 409, 413, 415, or 422.

Likely causes and fixes:

- 409: source line at an acknowledged index changed. Preserve source and cursor state; do not overwrite the canonical row. Investigate transcript rewrite/truncation.
- 413/422: batch line too large, too many lines, unordered byte offsets, missing `hashed_line_count` with `session_hash`, or invalid final metadata. Check payload construction in `sessions/base.py`.
- 400/415: malformed request shape or content type. Check hook bridge/wrapper output and request JSON.

## Config and hook failures by harness

| Harness | Common symptom | Cause | Fix/check |
|---|---|---|---|
| Claude Code | Hooks never fire | `.claude/settings.json` has `disableAllHooks: true` or stale legacy Observal hook groups | `observal doctor`; run `observal doctor cleanup --harness claude-code --dry-run --yes --output json`, then patch. |
| Kiro | Doctor says hooks missing after patch | Kiro hooks are per pulled agent; generic doctor patch only repairs lockfile-backed agent profiles | Pull the Kiro agent again or ensure lockfile has the Kiro agent id/name/scope; hook command must carry `OBSERVAL_AGENT_ID`. |
| Cursor | Doctor patched but scan hook status is inconclusive | Cursor adapter hook detection may not be the authoritative doctor check | Inspect doctor output and the Cursor hooks file; verify `beforeSubmitPrompt` and `stop` commands invoke `session_push --harness cursor`. |
| Codex | Hooks configured but not firing | `codex_hooks = false` or missing from config | `observal doctor patch --harness codex --dry-run --output json`; expected dry-run indicates enabling `codex_hooks`. |
| Copilot VS Code | Windows hook exits or path with spaces fails | VS Code uses PowerShell `command`; wrapper path/interpreter not resolved | Ensure `.github/hooks/run_hook.ps1` exists and invokes `observal_cli.hooks.session_push --harness copilot --json-response`. |
| Copilot CLI | Sessions unattributed | Hook lacks `OBSERVAL_AGENT_ID` or project moved outside lockfile match | Re-pull the agent so `rewrite_hooks` injects per-agent attribution; verify lockfile entry. |
| OpenCode | Plugin installed but no events | Plugin missing/stale, built-in agent ignored, or lockfile has no matching agent | `observal doctor patch --harness opencode`; confirm pulled agent name exists in lockfile and is not a built-in OpenCode agent. |
| Antigravity | Stop hook has no session id | Native Stop payload can omit conversation id | Adapter caches previous session id; check prior PreInvocation fired and bridge returned host-required JSON. |
| Goose | Hook stalls or plugin ignored | Matcher is invalid, plugin disabled, or plugin not registered/discovered | Goose rules should omit `matcher`; run `observal doctor patch --harness goose`; restart Goose; check disabled plugin settings. |
| Pi | Extension installed but not active | Pi needs reload/restart or legacy npm package remains | Run doctor patch; restart Pi or use host reload; doctor removes legacy `npm:observal-pi` registration. |

## Missing sessions after doctor patch

Use this decision tree in order.

### 1. Verify hook installation and host restart

```bash
observal doctor
observal doctor patch --harness <harness-id> --dry-run --output json
```

Expected: doctor no longer warns about missing/stale instrumentation, or dry run reports the exact change still needed. Restart the harness after patching; several hosts load hooks/plugins only at session start.

### 2. Verify local source exists

Run a dry-run reconcile scoped to the harness:

```bash
observal reconcile --harness <harness-id> --since 168 --dry-run --output json
```

Expected outcomes:

- `would_push`: source has new bytes after local cursor.
- `would_finalize`: source is fully uploaded but lacks final metadata.
- `up_to_date`: local cursor and server checkpoint agree.
- `skipped` with `source path unavailable`: adapter could not resolve a readable source path.

If `discovered` is zero, check the harness-specific source map in `references/telemetry-pipeline.md`, the `--since` window, and adapter `is_installed()` detection.

### 3. Verify outbox state

```bash
observal ops telemetry status
```

Expected: pending count drains after a successful reconcile. If pending remains:

- Server unreachable or transient 5xx: retry later; pending data remains durable.
- Auth/user/server changed: pending rows are bound to the original destination/user.
- Permanent rejection: inspect the rejected JSONL file and status code before retrying.
- Outbox full: resolve disk/capacity; do not delete unacknowledged records unless the user explicitly accepts data loss.

### 4. Recover from server checkpoint

Reconcile non-dry-run fetches the authenticated server checkpoint before replaying:

```bash
observal reconcile --harness <harness-id> --since 168 --output json
```

If a session reports `checkpoint_mismatch`, the server's acknowledged byte offset cannot be mapped to a local newline boundary. Preserve the source transcript and `~/.observal` state. A changed/truncated local transcript cannot safely prove already acknowledged bytes.

### 5. Verify parser and trace visibility

```bash
observal ops traces --limit 5
```

If raw source rows were ingested but trace detail is empty or malformed, switch to `references/session-parsers.md` and run the parser/ingest tests for that harness.

## Reconcile/source-discovery failures

Symptoms:

- `reconcile --dry-run` discovers no sources, but the harness has recent sessions.
- Sources are found for home scope but not project scope, or vice versa.
- Subagent/delegated sessions are missing.

Checks:

- Confirm adapter `home_markers` and `is_installed()` agree with the host's real install layout.
- Confirm `discover_session_sources(since_hours=...)` uses modification times on the source that actually changes.
- For JSONL sources, ignore incomplete final lines but count complete non-empty lines.
- For subagents, use `related_session_sources(...)` or parent id relationships instead of independent guessing.
- For Goose, do not write to or checkpoint Goose's SQLite database; export read-only to the Observal mirror.
- For VS Code Copilot, ensure hook payloads are materialized into stable local JSONL source records before network delivery.

Focused tests:

```bash
cd observal-server && uv run pytest ../tests/test_session_reconcile.py -q
cd observal-server && uv run pytest ../tests/test_session_delivery.py -q
```

Expected: dry-run has no network side effects; background recovery and public reconcile use adapter sources and shared drain.

## Optional dependency and local-dev failures

| Dependency/surface | Symptom | Fix |
|---|---|---|
| TOML parser for Codex scan | Codex MCP scan returns empty in older Python environments | Prefer Python with `tomllib`; otherwise ensure packaged optional TOML parser is installed in the dev environment. |
| PyYAML for Goose scan/server config | Import error or Goose config parse failure | Run tests through the project environment, e.g. `cd observal-server && uv run pytest ...`. |
| `httpx` in hooks | Hook cannot post or refresh token | Ensure the hook command uses the Observal CLI environment, not a random system Python. |
| `orjson`/`xxhash` server ingest | Server import/test failure | Use the server environment; do not vendor parser fallbacks in harness code. |
| SQLite file access | Goose/Copilot session discovery fails | Open host databases read-only with timeouts; fail soft on locked/unreadable DBs. |

## Parser/display failures

| Symptom | Cause | Fix |
|---|---|---|
| Unknown harness KeyError at ingest | Registry key missing or typo in request `harness` | Add the registry entry or fix hook payload harness id. |
| Parser id KeyError | `session_parser` not registered in `_PARSERS`/`_CLASSIFIERS` | Register the id and add tests. |
| Empty trace despite source rows | Classifier skips real records or display parser returns no events | Narrow skip rules; use `basic_event` fallback for unknown records. |
| Tool calls/results unpaired | Wrong id field or missing parent merge map | Add pairing logic and parser tests with call/result order variations. |
| Token/model missing | Usage extractor missing or stale | Update `_USAGE_EXTRACTORS` and add test cases in `tests/test_session_ingest.py`. |
| User prompts include wrapper XML/tags | Host wrapper not stripped | Add parser-specific cleanup like Cursor XML or Antigravity `<USER_REQUEST>` handling. |

## Config generation failures

Symptoms:

- `observal agent pull --harness <id> --dry-run --output json` writes wrong paths or wrong MCP key.
- Pull escapes the target directory or writes user-scope files unexpectedly.
- Hook components install but scripts are not in the harness hook directory.
- Model names are invalid for the target harness.

Checks:

```bash
cd observal-server && uv run pytest ../tests/test_harness_config_e2e.py -q
cd observal-server && uv run pytest ../tests/test_harness_refactor_baseline.py -q
```

Fixes:

- Correct registry `agent_profile`, `mcp_config`, `mcp_servers_key`, `skills`, and `hooks` paths before patching adapters.
- Keep serialization/formatting in the server adapter: JSON/TOML/YAML/Markdown shape should be harness-owned.
- Keep local interpreter/path rewrites in CLI adapter/pull code because the server cannot know the user's CLI install path.
- Add compatibility warnings when an agent requires a capability the harness lacks.

## Layer and managed-file failures

Symptoms:

- Layer hash does not change after editing a harness agent/skill/hook file.
- Observal-installed files appear as user drift or user files appear as Observal-managed.
- Sessions have no layer hash even when hooks work.

Checks/fixes:

- Add or correct `HARNESS_LAYER_CONFIGS` user/project globs in `observal_cli/layer.py`.
- Add adapter `managed_agent_profiles`, `managed_skills`, and `managed_mcp_files` patterns.
- Override `get_observal_managed_files(...)` for complex layouts.
- Keep layer hash fail-soft; telemetry delivery must continue when layer scanning fails.

Verification:

```bash
cd observal-server && uv run pytest ../tests/test_cli_harness_adapters.py::TestManagedLayerFiles -q
cd observal-server && uv run pytest ../tests/test_session_delivery.py::test_build_payload_caches_layer_metadata_and_evicts_it_on_stop -q
```

Expected: managed paths are attributed correctly and layer hash cache is evicted on Stop.

## Workflow-level failure prevention

When adding or promoting a harness, do not stop after registry/config generation passes. A harness is not operational until all of these have been checked:

- Registry entry and model catalog are present.
- CLI and server adapters are registered by `load_all.py`.
- Scan sees home/project components and fails soft on absent installs.
- Doctor can patch and cleanup, or the absence of a dedicated hook spec is intentional and documented.
- Layer globs and managed file attribution are present.
- Hook command uses the shared session engine or a justified bridge/native extension.
- Session source discovery works for hooks and reconcile.
- Server parser/read path and ingest classifier/timestamp/usage/uuid extraction are registered.
- Delivery tests cover offline outbox retention, checkpoint recovery, finalization, and permanent rejection.
- User-visible verification commands have clear expected signals.
