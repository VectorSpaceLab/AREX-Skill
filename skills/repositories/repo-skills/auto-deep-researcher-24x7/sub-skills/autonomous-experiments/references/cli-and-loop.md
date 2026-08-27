# CLI and loop contract

## Public command surface

The current `python -m core.loop` parser accepts exactly these options:

| Option | Type/default | Effect |
|---|---|---|
| `--project PATH` | required string | Project directory. The controller resolves it and uses it as the root for the brief, config, log, and workspace. |
| `--config PATH` | `config.yaml` | Config filename/path interpreted under `--project`; missing files load as an empty config. |
| `--max-cycles N` | unset | Process-only override of `agent.max_cycles`; positive values stop after the persisted count reaches N. `-1` means unlimited. |
| `--gpu DEVICES` | unset | Sets `CUDA_VISIBLE_DEVICES` before loop construction. It is an opaque string such as `0` or `0,1`; it is not a scheduler allocation mechanism. |
| `--check` | false | Prints Python/project/status information and exits before constructing the loop. `--project` remains required by the parser. |

Examples:

```bash
python -m core.loop --project /path/to/project --check
python -m core.loop --project /path/to/project --config config.yaml --max-cycles 3
python -m core.loop --project /path/to/project --gpu 0 --max-cycles 1
```

There is no current `--directive` or `--stop` parser option. Documentation that
shows `--directive "..."` is stale relative to the parser. Use the directive file
contract in [workflows](workflows.md), and use SIGINT/SIGTERM plus backend-specific
child cancellation for stopping.

## Effective defaults

The following values are the repository defaults when the corresponding config
section/key is absent. The checker reports the same effective values without
constructing the controller:

```yaml
project.workspace: workspace
agent.max_cycles: -1
agent.max_steps_per_cycle: 3
agent.cooldown_interval: 300
agent.no_progress_fallback_threshold: 3
agent.max_cycles_per_hour: 0
monitor.poll_interval: 900
monitor.zero_llm: true
experiment.mandatory_dry_run: true
experiment.max_parallel: 1
ledger.enabled: true
ledger.recent_in_context: 5
stagnation.enabled: true
stagnation.threshold_cycles: 3
journal.enabled: true
safety.enabled: true
safety.fail_threshold: 3
safety.stale_state_hours: 6
gates.enabled: false
```

The root sample config also documents the effective memory caps (brief 3,000
characters, rolling log 2,000, milestones 1,200, recent decisions 15), a
15-minute monitor interval, and local execution. `experiment.mandatory_dry_run`
is an operational contract: the worker instructions require a tiny dry-run
before launch, while the controller does not independently execute or verify a
training command. Keep it true and reject any worker report that omits the
check.

`project.brief` is documented in the sample config, but the current memory
manager reads the fixed project-root file `PROJECT_BRIEF.md`; changing that key
does not redirect the brief. With a non-default `project.workspace`, the loop's
state, directive, ledger, and journal paths follow the configured directory,
but the rolling `MEMORY_LOG.md` remains under the literal project `workspace/`.
Use the default name unless this split has been deliberately validated.

## Cycle state machine

A cycle is serialized as follows:

```text
start
  │ increment and persist workspace/.cycle_counter
  ▼
planning ──THINK──> wait ──> waiting ──> smart cooldown ──> next cycle
  │
  └───────────────> experiment/report ──EXECUTE──> optional monitor
                                                   │
                                                   ▼
                                                REFLECT
                                                   │
                                                   ▼
                                             next cycle
```

The `wait` branch is the only explicit action branch in the controller. It writes
`status: waiting`, `suggested_next_step` from the reason, and enters cooldown.
For every other action, including the leader schema's `report`, execution is
entered. A `report` action therefore must not be treated as a built-in final
report/stop command; inspect the worker result and reflection. `experiment` is
the normal action and is expected to contain a worker type and self-contained task.

### THINK input

The leader receives:

- `PROJECT_BRIEF.md` (truncated to the configured brief cap),
- rolling memory,
- cycle number,
- optional directive labeled highest priority,
- optional advisory signals from ledger/journals/safety/gates.

The expected JSON keys are:

```json
{
  "action": "experiment|wait|report",
  "agent": "code|idea|writing",
  "task": "self-contained worker task",
  "hypothesis": "what should be learned",
  "success_criteria": "how to judge it",
  "milestone": "optional result",
  "decision": "short decision summary"
}
```

Workers are stateless between dispatches. The leader context is reset at the
start of every cycle so a stale conversation cannot silently accumulate across
cycles. The configured `max_steps_per_cycle` limits worker dispatches, not
concurrent training jobs; the supported operating pattern is one worker at a
time.

### EXECUTE and monitor handoff

The worker must explore before editing, obey protected-file rules, dry-run first,
and use the launch tool for a long-running training process. The structured
launch tool result is authoritative for `pid` and `log_file`; prose PID scraping
is only a compatibility fallback. When no launch occurs, the controller still
passes the execution result to REFLECT.

After an authoritative launch, the controller writes `running`, then waits with
zero LLM calls. It carries monitor output into reflection as:

```json
{
  "experiment_status": "completed|failed|...",
  "terminal_state": "backend-specific terminal state or empty",
  "training_logs": "tail text",
  "final_metrics": {},
  "pid": 123,
  "log_file": "logs/exp.log"
}
```

Do not normalize a backend failure into `completed`; the terminal state is part
of the result handoff and is also used by the durable ledger path.

## Observable `workspace/state.json` signals

State is a JSON object updated in place. Fields are additive, so old values can
remain visible until a later update. Interpret the main fields as follows:

| Signal | Meaning | Safe response |
|---|---|---|
| `cycle` | Current persisted cycle number | Compare with `.cycle_counter`; do not reset by deletion. |
| `status: planning` | THINK is active or beginning | Do not launch a second controller. |
| `status: waiting` | Explicit wait or repeated-plan fallback | Read `suggested_next_step`; wait or steer. |
| `status: running` | A child was reported launched | Verify PID versus scheduler job id and backend liveness. |
| terminal status | Monitor observed completion/failure | Use `terminal_state`, log tail, and metrics. |
| `status: error` | Controller cycle exception | Read `last_error`; respect backoff before retrying. |
| `pid` | Local process id or Slurm job id | Never assume local-PID semantics in Slurm mode. |
| `log_file` | Training log associated with the result | Confirm it exists through the backend before interpreting. |
| `updated_at` | Unix timestamp of the latest update | A stale timestamp is a warning, not liveness proof. |
| `last_directive` | Consumed directive text (or empty) | Check archive for the durable copy. |
| `last_training_logs` | Monitor log tail | Use as a clue; prefer complete log parsing for claims. |
| `last_metrics` | Monitor-extracted metric map | Empty is an explicit absence of metrics. |
| `terminal_state` | Backend terminal reason/state | Preserve exact value in the report. |
| `last_milestone` / `last_decision` | REFLECT outputs | These are the next-cycle handoff, not independent validation. |
| `suggested_next_step` | Reason/decision/task for the next action | Follow only after checking the terminal evidence. |
| `last_error` | Bounded error text, cleared after success reflection | Fix the cause; do not blindly repeat. |

The controller also persists `.cycle_counter`. When `max_cycles_per_hour` is
positive it maintains `.cycle_times` and throttles starts; zero disables that
rate limit and avoids creating the file.

## Directives and archival details

The controller checks `workspace/HUMAN_DIRECTIVE.md` once at cycle start. It
strips whitespace; empty content is ignored and is not archived. Non-empty content
is renamed into `workspace/directive_archive/` as:

```text
directive_YYYYmmdd_HHMMSS.md
```

The timestamp is local wall-clock time with one-second precision. Treat an
existing same-second archive name as a collision risk: inspect the archive before
placing another directive, and do not intentionally queue multiple directives in
one second. The consumed content is sent to THINK with highest priority and the
file is no longer re-read on later cycles. If an archive collision is observed,
preserve the evidence and stop for human review rather than assuming both
messages were retained.

## Scheduler distinction

For `execution.mode: local`, a launch PID is a local process identity and the
backend can use PID-oriented checks. For `ssh`, controller state remains local
while tool-visible operations and training use the configured remote workspace.
For `slurm`, training is submitted through the scheduler, `pid` carries the job
id, `sacct` is authoritative, and `--gpu` is ignored. Require scheduler fields
before launch; this sub-skill does not duplicate backend command or cancellation
protocols.
