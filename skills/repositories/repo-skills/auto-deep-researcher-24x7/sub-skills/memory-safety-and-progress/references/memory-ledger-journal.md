# Memory, ledger, and journal contracts

This reference is the durable operating contract for state that survives a
controller restart. All paths below are relative to the supplied project or
its configured workspace; do not substitute a hidden or machine-specific
prefix.

## Storage map

| File | Role | Mutation policy |
|---|---|---|
| `PROJECT_BRIEF.md` | Tier 1 frozen goal/reference | Read-only to the loop |
| `workspace/MEMORY_LOG.md` | Tier 2 bounded context | Rewritten by compaction |
| `workspace/experiments.jsonl` | One JSON object per cycle | Append-only |
| `workspace/DEAD_ENDS.md` | Failed approaches | Append-only; rotate to `.bak` |
| `workspace/INSIGHTS.md` | Durable observations | Append-only; rotate to `.bak` |
| `workspace/state.json` | Current mutable snapshot | JSON object, updated in place |
| `workspace/.cycle_counter` | Restart-safe cycle count | Plain decimal integer |
| `workspace/.cycle_times` | Recent cycle-start timestamps | JSON list, used by throttling |

The configured workspace may differ from `workspace`; inspect the current
runtime before assuming every file follows the override. In particular, the
current loop's state/directive/ledger/journal paths use the configured workspace,
while `MemoryManager` keeps `MEMORY_LOG.md` under the literal project
`workspace/`. A project brief is capped when read, not rewritten.

## Exact constructors and methods

The current Python contracts are:

```python
MemoryManager(
    project_dir: Path,
    brief_max: int = 3000,
    log_max: int = 2000,
    milestone_max: int = 1200,
    max_recent: int = 15,
)
```

It exposes `get_brief() -> str`, `get_log() -> str`,
`get_full_context() -> str`, `log_milestone(entry: str)`, and
`log_decision(entry: str)`. Construction creates the workspace log directory
and initializes a missing log as:

```text
# Memory Log

## Key Results

## Recent Decisions
```

`get_full_context()` returns a `## Project Brief` block followed by a
`## Memory Log` block. `log_milestone` timestamps entries as `[MM-DD HH:MM]`
and drops the oldest milestone when the milestone section exceeds its cap.
`log_decision` uses the same timestamp shape and retains only the last
`max_recent` decisions. The final log write applies the total `log_max` cap,
removing oldest milestones first and then oldest decisions while retaining the
section skeleton as far as possible. Empty or missing source files yield an
empty string rather than invented content.

```python
ExperimentLedger(workspace: Path, filename: str = "experiments.jsonl")
```

Methods are `record(*, cycle: int, hypothesis: str = "", action: str = "",
status: str = "", metrics: Optional[dict] = None, pid: Optional[int] = None,
log_file: str = "", conclusion: str = "", ts: Optional[float] = None)`,
`all() -> list[dict]`, `recent(n: int = 5) -> list[dict]`,
`summary(n: int = 5) -> str`, and
`best_metric(metric_key: str, direction: str = "higher_better")`.
`record` normalizes numeric cycle and timestamp, stringifies text, truncates
hypothesis and conclusion to 500 characters, and uses `{}` for `None` metrics.
A filesystem append error is logged and returns `None`; it must not crash the
loop.

The pure helpers are:

```python
best_metric(entries: list[dict], metric_key: str,
            direction: str = "higher_better") -> Optional[float]
detect_stagnation(entries: list[dict], metric_key: str,
                   direction: str = "higher_better",
                   threshold_cycles: int = 3,
                   min_delta: float = 0.0) -> dict
check_phase_gate(entries: list[dict], metric_key: str, threshold: float,
                 direction: str = "higher_better") -> dict
```

```python
ResearchJournal(workspace: Path, max_chars: int = 4000)
```

It exposes `append_dead_end(entry: str, ts: str = None)`,
`append_insight(entry: str, ts: str = None)`,
`dead_ends_tail(max_chars: int = 1500)`, and
`insights_tail(max_chars: int = 1500)`. Empty/whitespace entries are ignored.
The underlying append-only document also accepts a string `max_chars` for
`tail`, coercing it to an integer; unreadable files return an empty tail.

## Ledger line contract and malformed data

A normal line has this shape (fields may contain empty values):

```json
{"ts": 1710000000.0, "cycle": 7, "action": "experiment", "status": "failed", "hypothesis": "try lower lr", "metrics": {}, "pid": 42, "log_file": "logs/exp.log", "conclusion": "[TIMEOUT] retry with lower lr"}
```

`all()` reads line by line. Blank lines, invalid JSON, and valid non-object
JSON values are skipped. A malformed line is not repaired or removed, so the
valid records before and after it remain recoverable and future records can be
appended. Non-dict `metrics` are treated as empty by `summary` and ignored by
metric extraction. Numeric-looking metrics are converted with `float`; values
that cannot convert are ignored. `recent(0)` and `summary(0)` return empty
results.

When recording a completed cycle, prefer the monitor's actual
`experiment_status` over the generic launch status. If it is `failed` and a
terminal state exists, prefix the conclusion with `[<terminal_state>]`. A
failed run with no metric remains a failed ledger record; do not synthesize a
metric from a log message.

## Journal append and rotation

Each entry is written as `- [YYYY-MM-DD HH:MM] text`. Once a live journal's
byte size is greater than `max_chars`, rotation:

1. Reads the entire live document.
2. Chooses `<stem>.<timestamp>.bak`, adding `.1`, `.2`, ... if that name exists.
3. Writes the complete pre-rotation content to the backup.
4. Replaces the live file with its title, a marker naming the backup, and the
   most recent half of the old content.

The backup is the history boundary. The live tail is only a context window.
If rotation itself encounters an OS error, the original live file is retained
and the failure is logged; never clear the file manually as a first response.
Use the archive list plus live tail when reconstructing a report.

Concrete expected fixture after a small-cap rotation:

```text
workspace/
  DEAD_ENDS.md
  DEAD_ENDS.2026-06-01_1000.bak
  INSIGHTS.md
```

The live `DEAD_ENDS.md` starts with `# Dead Ends`, contains a rotation marker,
and retains the newest entries. The `.bak` contains the full earlier file,
including its header and all entries written before rotation.

## Reporting recipe

For a truthful context block, load the brief and live memory log, then report
ledger validity (`valid_lines`, `malformed_lines`, total valid entries), the
latest ledger records, and journal tail/archive counts separately. State that
the memory log is lossy when its caps have removed older entries; archives and
the ledger are the durable history. Never imply that a missing tail means the
experiment did not happen.
