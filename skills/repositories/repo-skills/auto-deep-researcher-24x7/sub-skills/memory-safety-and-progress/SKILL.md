---
name: memory-safety-and-progress
description: "Preserve truthful experiment context with bounded memory, append-only history, safety signals, gates, and read-only progress inspection."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Memory, safety, and progress

Use this sub-skill when an experiment loop needs to **remember what happened,
avoid repeating dead ends, detect unsafe/stale progress, or report status**.
It is an operating guide for the project state contract; it is not the loop
orchestration guide and it does not launch experiments, inspect GPUs, install
skills, or mutate an Obsidian vault.

## Operating rules

1. Treat `PROJECT_BRIEF.md` as frozen Tier 1 context. Never rewrite it as a
   side effect of logging or compaction.
2. Use `workspace/MEMORY_LOG.md` for bounded milestones and recent decisions.
   Use the ledger and journals for durable, append-only detail; do not pretend
   that a compacted memory log is the complete history.
3. Record every cycle outcome in `workspace/experiments.jsonl` when the ledger
   is enabled. One JSON object per line is the recovery boundary.
4. Keep `DEAD_ENDS.md` and `INSIGHTS.md` append-only. Rotation moves the full
   old file to a uniquely named `.bak`; never delete an archive to make a
   rotation appear successful.
5. Interpret safety, stagnation, and phase-gate results as signals. They are
   advisory: stop, back off, change direction, or ask for a human decision;
   do not fabricate a result from a signal.
6. A known failed terminal outcome stays failed everywhere. In particular,
   Slurm `TIMEOUT`, `CANCELLED`, `OUT_OF_MEMORY`, `NODE_FAIL`, and similar
   terminal states must remain failed in state, ledger, and dashboards.
7. For inspection, run the bundled read-only script. It reads a supplied
   project and emits checks; it never writes state, journals, exports, or
   archives.

## First response to a progress request

- Read the brief, memory log, counter, state, ledger tail, journal tails, and
  cycle-time file if present.
- Report missing, malformed, stale, or unreadable files explicitly.
- Separate **observed** values (ledger/state) from **derived** values
  (best metric, stagnation, gate, rate-limit wait).
- If `state.status == "failed"`, show the terminal state and do not downgrade
  it to `completed`, `idle`, or “probably okay”.
- If history is malformed, preserve the original bytes and use the valid
  records only; recovery is append-first, not rewrite-first.

## Quick inspection

From this skill directory, use:

```bash
python scripts/inspect_progress_state.py --project <project>
```

Useful bounded variants are `--format json`, `--ledger-tail 10`,
`--journal-tail 1200`, `--metric-key acc`, `--metric-direction higher_better`,
`--gate-threshold 0.8`, `--max-cycles-per-hour 6`, and `--now <unix-seconds>`.
Add `--workspace <relative-or-absolute-workspace>` when the project does not
use the default `workspace` directory. The script only reads; it is safe for
triage and synthetic fixtures.

## Choose the right state mechanism

| Need | Mechanism | Truth boundary |
|---|---|---|
| Frozen goal and constraints | `PROJECT_BRIEF.md` | Human/project input |
| Small context for the next think step | `MEMORY_LOG.md` | Bounded, lossy view |
| Every cycle and outcome | `experiments.jsonl` | Append-only event history |
| “Do not retry this” | `DEAD_ENDS.md` | Append-only, rotated |
| Durable observation | `INSIGHTS.md` | Append-only, rotated |
| Current process/result snapshot | `state.json` | Mutable current state |
| Restart-safe cycle number | `.cycle_counter` | Plain integer |
| Anti-burn starts | `.cycle_times` | JSON list of timestamps |

Read the linked references for exact constructors, fields, formulas, output
formats, recovery actions, and failure handling:

- [memory-ledger-journal.md](references/memory-ledger-journal.md)
- [safety-and-gates.md](references/safety-and-gates.md)
- [progress-export.md](references/progress-export.md)
- [troubleshooting.md](references/troubleshooting.md)

## Handoff boundaries

Route core THINK/EXECUTE/REFLECT orchestration to
`autonomous-experiments`. Route GPU discovery, utilization, and resource
reservation to `gpu-and-resource-operations`. Route source skill installation
or importing to `skills-and-installation`. This sub-skill may interpret their
reported state, but must not silently take over those responsibilities.

When a report is requested, include: project goal; cycle count; current state;
latest valid ledger records; metric direction and best value; stagnation and
phase-gate verdicts with their parameters; journal tails and archive presence;
active violations and rate-limit wait; export target/status; and unresolved
file or backend errors. A missing metric is “no metric yet”, not zero. An
indeterminate backend outcome is “unknown”, not success.
