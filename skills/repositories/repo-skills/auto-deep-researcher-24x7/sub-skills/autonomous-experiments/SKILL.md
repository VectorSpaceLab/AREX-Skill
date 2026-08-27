---
name: autonomous-experiments
description: "Launch, configure, steer, and safely stop a PROJECT_BRIEF.md-driven THINK→EXECUTE→REFLECT experiment loop."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Autonomous experiments

Use this sub-skill when a Researcher needs to operate the repository's long-running
experiment controller around a project containing `PROJECT_BRIEF.md`: validate a
project, choose local versus scheduler execution, start a bounded trial, steer a
future cycle, interpret state, or recover from a stale/repeating loop.

This is an orchestration skill, not a backend, GPU, provider, tool-protocol, or
memory-manual. Route backend transport and scheduler/job semantics to
`execution-and-monitoring`; route GPU selection to `gpu-and-resource-operations`;
route provider/tool details to `agent-tools-and-providers`; route ledger, journal,
state-inspection, and progress-export APIs to `memory-safety-and-progress`.

## Non-negotiable operating rules

1. Inspect the project and run the bundled read-only validator before starting.
2. Keep `PROJECT_BRIEF.md` frozen. Treat it as the stable goal, constraints,
   search space, and success criteria; use a directive for temporary steering.
3. Require `experiment.mandatory_dry_run: true` and a worker dry-run before any
   real training launch. A failed dry-run is a stop-and-fix event, never a launch.
4. Prefer a finite `--max-cycles` during a first run or recovery. Confirm the
   resulting cycle count and log/state outputs before removing the cap.
5. Only one worker runs at a time. A worker must return the PID/job identifier,
   log file, expected duration, and dry-run result when it launches an experiment.
6. Monitoring while training is intended to be zero-LLM-cost; do not turn a
   polling or status check into an extra planning cycle.
7. A controller stop is not the same as stopping a child training job. After
   SIGINT/SIGTERM, verify the child using the selected backend before re-launching.

## Project contract

Minimum layout:

```text
project/
├── PROJECT_BRIEF.md             # required, human-owned and frozen
├── config.yaml                  # optional; defaults apply when absent
└── workspace/                   # created by the controller when it starts
    ├── MEMORY_LOG.md            # rolling decisions and milestones
    ├── state.json               # current observable controller/experiment state
    └── HUMAN_DIRECTIVE.md       # optional one-cycle steering input
```

The toy example is a useful shape: goal and target metric, code/data entry points,
resource and run limits, candidate variations, and explicit success criteria. Keep
the brief concise (the default context cap is 3,000 characters) and make every
worker task self-contained because workers are stateless between dispatches. The
layout above assumes the default workspace name. If `project.workspace` is
changed, state/directives/ledger use that configured directory, while the current
memory manager still stores `MEMORY_LOG.md` under the literal project
`workspace/`; validate this split before using a non-default workspace.

## Novice workflow: bounded first run

1. Put the goal, metric/threshold, codebase location, constraints, and stop rules
   in `PROJECT_BRIEF.md`; do not put secrets in it.
2. Run `python scripts/check_project.py --project PROJECT_DIR --config config.yaml`.
   Fix errors. A missing default `config.yaml` is acceptable; an explicitly named
   missing config is not.
3. Start a short run with the exact public entry point:

   ```bash
   python -m core.loop --project PROJECT_DIR --config config.yaml \
     --gpu 0 --max-cycles 1
   ```

   `--project` is required. `--config` is resolved under the project directory
   and defaults to `config.yaml`; `--gpu` is optional; `--max-cycles` overrides
   the YAML value for this process. Use `--check` with `--project` to print the
   installation check and exit without entering the loop.
4. Watch `autoresearcher.log`, `workspace/state.json`, and the latest training log.
   Expect `planning`, then `running` or `waiting`, then a terminal status and
   reflection fields. Do not infer success from a PID alone.
5. After the bounded cycle, inspect the result and memory/ledger handoff. Extend
   the cap only after the dry-run, launch, monitor, and reflection are credible.

## Expert workflow: operate one cycle deliberately

**Prepare.** Validate the project, choose `execution.mode`, and set a finite cycle
cap. For `local`, `--gpu` may set `CUDA_VISIBLE_DEVICES`; for `ssh` or `slurm`,
route transport configuration to the backend skill first. In `slurm`, the value
stored in `state.json.pid` is a scheduler job id, not a local PID, and the CLI
`--gpu` value is ignored.

**THINK.** The leader receives the brief, rolling memory, cycle number, and an
optional human directive. It should emit JSON with `action` (`experiment`,
`wait`, or `report`), worker type, task, hypothesis, success criteria, milestone,
and decision. Keep the task minimal and testable; do not dispatch multiple
workers concurrently.

**EXECUTE.** The selected worker explores before editing, changes only allowed
files, performs the mandatory tiny dry-run, and launches only after it passes.
The authoritative launch result is the structured tool result; capture its PID
(or scheduler job id) and log path. The controller then monitors without LLM
calls until completion or a bounded terminal outcome.

**REFLECT and hand off.** Reflection compares metrics with the brief and prior
results, records a milestone/decision, and chooses the next direction. Treat
`completed`, `failed`, `timeout`, or scheduler terminal states as evidence, not
as a generic “launched” result. Check `state.json`, `MEMORY_LOG.md`, and (when
enabled) the append-only experiment/journal records before reporting to the user.
If the leader says `report`, note that the current controller has a special
control-flow branch only for `wait`; `report` is not a guaranteed stop/report
primitive. Verify what the worker and reflection actually produced.

## Steering and stopping

For temporary steering, write a non-empty `workspace/HUMAN_DIRECTIVE.md` and let
the next cycle consume it. The directive is presented as highest-priority leader
context, then renamed into `workspace/directive_archive/directive_YYYYmmdd_HHMMSS.md`.
A directive also bypasses repeated-plan fallback for that cycle. Keep stable rules
in `PROJECT_BRIEF.md`; do not edit protected state or memory files to steer.

The current parser supports only `--project`, `--config`, `--max-cycles`, `--gpu`,
and `--check`. Some README examples advertise `--directive`, but that flag is
not implemented; use the directive file instead. Send SIGINT or SIGTERM to stop
the controller. Then separately verify or cancel the child training job through
its backend before restarting; there is no universal `--stop` command.

## Safe recovery signals

- `planning`: a cycle has started and a directive has been consumed if present.
- `waiting`: leader chose `wait` (or repeated no-progress fallback); inspect
  `suggested_next_step` and allow cooldown rather than launching blindly.
- `running`: `pid`, `log_file`, and `started_at` identify the active run. Under
  Slurm, `pid` is a job id and scheduler state is authoritative.
- terminal status: `status`, `terminal_state`, `last_training_logs`, `last_metrics`,
  and `elapsed_hours` describe the finished/failed run.
- `error`: `last_error` is the bounded failure detail; use error backoff and fix
  the cause before retrying.
- `.cycle_counter` survives controller restarts; `max_cycles` stops when the
  persisted count reaches the configured cap. A stale `running` state is a
  warning, not proof that training is alive.

For a stale state plus repeated identical no-progress plans: stop/refrain from a
new launch, verify the child with the selected backend, inspect the latest log,
place a clear directive if a human decision is needed, and restart with a finite
cap. The fallback changes a repeated `experiment` plan to `wait` after the
configured threshold (default 3) when there is no directive and no progress.

## Bundled operating references

- [Workflows](references/workflows.md): novice, expert, steering, stop, recovery,
  and observable handoff procedures.
- [CLI and loop contract](references/cli-and-loop.md): exact flags, defaults,
  actions, state transitions, and scheduler caveat.
- [Troubleshooting](references/troubleshooting.md): predictable failures and safe
  decisions, including stale state, archive collisions, and `report` semantics.
- [Project validator](scripts/check_project.py): read-only brief/config checker;
  it never imports the controller, launches a process, writes files, or contacts
  a network service.
