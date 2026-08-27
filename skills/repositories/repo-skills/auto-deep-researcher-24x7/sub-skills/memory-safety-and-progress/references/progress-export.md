# Progress reports and Obsidian/local export

Use this reference to interpret the existing status/report/export surfaces. The
export path is optional and must not become a second source of truth.

## Status and report surfaces

For a status request, the status skill reads and presents:

1. `PROJECT_BRIEF.md` as the goal.
2. `workspace/MEMORY_LOG.md` for key results and recent decisions.
3. `.cycle_counter` for cycles completed.
4. Process and log status through the configured execution backend.
5. GPU/resource information through that backend (route GPU interpretation to
   `gpu-and-resource-operations`).
6. `workspace/HUMAN_DIRECTIVE.md` if a pending directive exists.

For a structured progress report, combine the memory log with recent valid
ledger records and journal tails. The report sections are current status,
recent experiments, key insights, next steps, and blockers. Include ledger
validity and safety warnings when present; do not fill a missing metric with
zero or infer success from an absent log.

These are user-facing routes, not extra persistence layers:

```text
/experiment-status [--project <project>]
/progress-report
```

If a caller asks to install or change these source skills, route that request
to `skills-and-installation` rather than editing this sub-skill.

## Exact exporter constructor and methods

The runtime exporter contract is:

```python
ObsidianExporter(
    config: dict,
    project_dir: str | Path,
    backend: Optional[ExecutionBackend] = None,
)
```

Methods:

```python
is_enabled() -> bool
refresh_all(memory: MemoryManager, cycle_count: int) -> dict
refresh_dashboard(memory: MemoryManager, cycle_count: int) -> dict
append_daily_entry(
    memory: MemoryManager,
    cycle_count: int,
    event_type: str = "cycle_complete",
    reflection: Optional[dict] = None,
    directive: Optional[str] = None,
) -> dict
```

If `obsidian.enabled` is false, all export methods return a disabled status and
make no export write. `refresh_all` refreshes the dashboard and appends a
manual-refresh daily entry. `append_daily_entry` does not append a normal
`cycle_complete` event when `auto_append_daily` is false, but a manual refresh
still works. The exporter reads state defensively: invalid JSON state becomes
an empty state for rendering, and must be reported as an inspection warning
rather than announced as a healthy idle result.

## Target selection and file names

Configuration keys and defaults:

```yaml
obsidian:
  enabled: false
  vault_path: ""
  project_subdir: "DeepResearcher/{project_name}"
  dashboard_note: "Dashboard.md"
  daily_dir: "Daily"
  auto_append_daily: true
  local_fallback_dir: "progress_tracking"
```

- With a non-empty `vault_path`, target
  `<vault_path>/<project_subdir formatted with project_name>`. The dashboard
  uses `dashboard_note` (normally `Dashboard.md`); daily notes are under
  `<daily_dir>/YYYY-MM-DD.md`.
- With an empty `vault_path`, target
  `<workspace>/<local_fallback_dir>`. The dashboard is `Dashboard.txt`; daily
  notes are under the configured daily directory as `YYYY-MM-DD.txt`.
- `vault_path` is expanded with the platform user-home expansion by the
  exporter. The project-local fallback is the safe default when no vault is
  configured.

Dashboard content includes the project goal, refresh time, output target,
current status, cycle count, recent decisions, a best-result line, latest log
snapshot, pending directive, and suggested next step. Status formatting is:

| State snapshot | Rendered status |
|---|---|
| `running` plus a live pid | `TRAINING (PID ..., <hours>)` |
| `completed` | `COMPLETED` |
| `error` | `ERROR` |
| `failed` with terminal state | `FAILED (<terminal_state>)` |
| `failed` without useful terminal state | `FAILED` |
| `no_pid` | `FAILED (no PID)` |
| other/missing | `IDLE` |

A known failed state must therefore be visible in a dashboard; never replace it
with `IDLE` because a process is no longer alive.

Daily entries contain event time/cycle, rendered status, best/new result,
latest metrics, decision, consumed directive, and blocker. Existing daily
content is appended to, not rewritten into a summary.

## CLI flags and safe usage

The project export CLI accepts:

```bash
python -m core.obsidian --project <project>
python -m core.obsidian --project <project> --dashboard-only
python -m core.obsidian --project <project> --daily-only
```

The default refreshes both dashboard and daily entry. `--dashboard-only` and
`--daily-only` select one operation; use one at a time. If export is disabled,
the CLI prints an instruction to enable it and exits without writing notes.
This sub-skill deliberately does **not** bundle or invoke a vault-mutating
exporter. For a read-only audit, use `scripts/inspect_progress_state.py`.

## Truthful export workflow

Before an enabled export:

1. Read current `state.json`, the counter, memory log, and current journals.
2. Confirm that a failed terminal outcome is present and remains failure.
3. Refresh the dashboard from the current snapshot.
4. Append a daily event with the current cycle and blocker.
5. Report the exact target category (vault or local fallback), operation status,
   and any write error.

When export is unavailable or disabled, report the state directly and label
export as disabled/unavailable. Do not claim that a vault note was refreshed.
