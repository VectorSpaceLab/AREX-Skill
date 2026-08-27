# Operating workflows

This reference describes observable controller operations. It deliberately does
not reproduce backend, GPU, provider, tool, or durable-record manuals.

## 1. First-run workflow for a novice

### Prepare the brief

Create a project directory with a human-owned `PROJECT_BRIEF.md`. Include:

- **Goal:** model/task and a measurable target.
- **Codebase/data:** training entry point or permission to create one, data source,
  and expected output/log locations.
- **Constraints:** GPU or scheduler limit, maximum run duration/epochs, allowed
  changes, and reproducibility requirements.
- **Search plan:** a small baseline and conditional next experiments.
- **Success/stop criteria:** what counts as improvement, when to report, and when
  to stop a weak branch.

Do not use the brief as a transient command queue. Do not ask the worker to infer
unknown flags or paths; require it to inspect the project first.

### Validate without side effects

From the installed generated skill tree, run:

```bash
python scripts/check_project.py --project /path/to/project
```

To validate a named project config:

```bash
python scripts/check_project.py \
  --project /path/to/project \
  --config configs/experiment.yaml \
  --json
```

The checker only reads the brief/config and prints checks. It does not create
`workspace`, import the controller, call a provider, invoke a scheduler, inspect
GPUs, download data, or start training. A default `config.yaml` that is absent is
reported as optional; an explicitly supplied missing config is an error.

### Bounded launch

Start with one cycle and the required dry-run setting:

```bash
python -m core.loop \
  --project /path/to/project \
  --config config.yaml \
  --gpu 0 \
  --max-cycles 1
```

The command is long-running only after validation and initialization. The
controller reads the config under the project directory, loads the brief, and
creates its configured workspace. The `--max-cycles` value is a process-level
override; it does not rewrite YAML.

Expected high-level log shape:

```text
AutoResearcher starting ...
=== Cycle 1 ===
THINK phase starting...
EXECUTE phase starting...       # only for non-wait plans
Monitoring experiment ...       # only after an authoritative launch
REFLECT phase starting...       # after execution/monitoring
```

A worker launch is not proof of success. Require a structured PID/job id and log
path, then inspect terminal status and metrics after monitoring.

### Inspect the handoff

After a cycle, read these project-local outputs:

```text
autoresearcher.log
workspace/state.json
workspace/MEMORY_LOG.md
workspace/experiments.jsonl       # if the ledger is enabled
workspace/DEAD_ENDS.md             # if the journal is enabled
workspace/INSIGHTS.md              # if the journal is enabled
```

For a first run, report: cycle number, action, dry-run result, launch identity,
log path, terminal state, final metrics, milestone/decision, and the next step.
If a field is absent, say it is absent rather than filling it from prose.

## 2. Expert one-cycle workflow

1. Run `check_project.py` and preserve its JSON/text output in the session notes.
2. Inspect `state.json` and determine whether the last state is genuinely active.
3. Inspect the latest log and durable result record before changing the brief.
4. Select a finite cap and ensure `experiment.mandatory_dry_run` is true.
5. For local execution, ensure the requested GPU policy is compatible with the
   project. For SSH/Slurm, stop here and have the backend skill validate transport
   fields first.
6. Start the loop. Do not manually run the worker's training command in parallel.
7. During training, use backend-aware status checks; do not ask the leader to poll
   every few seconds. The intended monitor is zero-LLM-cost.
8. At reflection, compare to the brief's baseline and success criterion. Record
   the exact terminal state and metric source in the handoff.
9. If another cycle is justified, keep the next task narrow and bounded. If the
   goal is reached, stop the controller and report; do not let an unbounded cap
   turn a reached target into more experiments.

## 3. Human steering workflow

Create a non-empty directive atomically as far as the host shell permits:

```bash
printf '%s\n' \
  'Stop tuning augmentation. Re-run the last trusted baseline with seed 2.' \
  > /path/to/project/workspace/HUMAN_DIRECTIVE.md
```

The next cycle consumes it before THINK. The leader input labels it `Human
Directive (HIGHEST PRIORITY)`. On successful consumption the controller renames
it into `workspace/directive_archive/` with a second-resolution timestamp. A
fresh directive is therefore one-cycle input, not permanent project policy.

To make the rule permanent, update `PROJECT_BRIEF.md` only with human approval;
workers are forbidden to modify it. Do not edit `state.json` or `MEMORY_LOG.md`
to inject commands. The current Python CLI does **not** accept `--directive` even
though some older examples show it; a file is the supported steering mechanism.

A directive disables the repeated-plan fallback for that cycle. Use this when the
human intentionally wants to retry or deliberately pivot, and state the desired
success criterion in the directive so the next reflection can close the loop.

## 4. Stop and restart workflow

### Stop the controller

Send SIGINT (interactive Ctrl-C) or SIGTERM to the controller process. The signal
handler marks the controller as not running and the loop exits at its next safe
control point. There is no universal `--stop` flag.

### Verify the child separately

A controller stop does not itself prove that a local child or scheduler job was
cancelled. Inspect `state.json`, the training log, and the selected execution
backend. If `status` is still `running`, use the backend's documented cancellation
operation; never guess that a scheduler job id is a local PID. Only then restart.

### Restart conservatively

- Keep the existing `.cycle_counter`; it is the continuity signal.
- Do not delete `state.json`, the ledger, or journals to clear a stale display.
- Start with `--max-cycles 1` and a clear directive if the previous run was
  interrupted or ambiguous.
- Confirm that the first new state update has a newer `updated_at` and a new
  cycle number before lifting the cap.

## 5. Stale-state and repeated-plan recovery

Use this decision sequence:

```text
state says running
       │
       ├─ backend proves child alive ──> monitor; do not launch a second worker
       │
       └─ child absent/terminal ───────> inspect log and terminal state
                                             │
                                             ├─ useful new evidence ──> reflect/report
                                             └─ same no-progress plan ─> wait or directive pivot
```

The fallback signature includes action, worker, normalized task, and normalized
hypothesis. With no directive, an `experiment` plan that repeats at or beyond the
configured threshold becomes a `wait` result with a reason such as:

```text
Fallback triggered after 3 no-progress cycles on the same plan.
Backing off to avoid empty loops until new signal arrives.
```

This is an anti-burn backoff, not a proof that the experiment is impossible. Add
new evidence or a human directive before trying again. A stale `running` state
must be resolved by backend evidence, not by deleting state or launching a twin.

## 6. Slurm-selection mismatch workflow

If `execution.mode: slurm` is selected but the user expects local PID behavior:

1. Stop before launching. The controller is local, but training is submitted to
   Slurm through the configured login path.
2. Explain that `state.json.pid` carries the Slurm job id; `sacct` is the liveness
   authority. It is not safe to use `kill -0 <pid>` or local `kill` as the test.
3. Require `ssh_host`, `remote_workspace`, `slurm_partition`, and `slurm_time`.
   Check GPU allocation using `slurm_gpus_per_job` or `slurm_gres`.
4. Explain that `--gpu` is ignored in Slurm mode; GPU selection is scheduler
   allocation, not `CUDA_VISIBLE_DEVICES` pinning by the controller.
5. Either switch explicitly to `execution.mode: local` and validate local PID
   expectations, or continue with the backend workflow. Never silently reinterpret
   a scheduler job id as a process id.

## 7. Handoff template

Use a concise, evidence-linked handoff:

```text
Project: <directory name>
Cycle: <state.cycle> | action: <experiment|wait|report>
Dry-run: <passed/failed/not observed>
Launch: <pid/job id or none> | log: <path or absent>
Outcome: <status> | terminal_state: <value or absent>
Metrics: <state.last_metrics or absent>
Reflection: <last_milestone>; next: <suggested_next_step>
Safety: <directive archived? stale child? fallback? scheduler caveat?>
```

Never call a run successful merely because `experiment_launched` is true; a
failed terminal state and empty metrics must be handed off as failure.
