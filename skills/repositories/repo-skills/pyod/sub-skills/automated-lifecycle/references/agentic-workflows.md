# Agentic ADEngine Workflows

This reference explains how an agent should drive PyOD's session workflow and
interpret `InvestigationState` without relying on PyOD's packaged `od-expert`
skill files being installed.

## Session state fields

`engine.start(...)`, `engine.plan(...)`, `engine.run(...)`, and
`engine.analyze(...)` mutate and return an `InvestigationState` object with these
fields:

| Field | Meaning |
|---|---|
| `phase` | Current phase: `profiled`, `planned`, `detected`, or `analyzed`. |
| `iteration` | Iteration counter; first run is `0`, every `iterate` call increments it. |
| `history` | List of dicts with `phase`, `action`, `iteration`, `timestamp`, and `detail`. |
| `data` | Reference to the original input data; not copied. |
| `profile` | Dict from `profile_data`. |
| `plans` | List of DetectionPlan dicts. The session planner returns up to three plans. |
| `results` | List of per-detector results. Success entries include scores, labels, threshold, runtime, and fitted detector. Error entries include `status="error"` and `error`. |
| `consensus` | Dict or `None`. Successful multi-detector runs include consensus `scores`, `labels`, `n_detectors`, `agreement`, and `disagreements`. |
| `analysis` | Dict or `None`. After `analyze`, includes consensus analysis, per-detector analyses, `best_detector`, `best_detector_index`, and `summary`. |
| `quality` | Dict or `None`. After `analyze`, includes `separation`, `agreement`, `stability`, `overall`, `verdict`, and `explanation`. |
| `next_action` | Dict telling the caller what to do next. Always check `next_action["action"]` before proceeding. |

Possible next-action values include `plan`, `run`, `analyze`, `report_to_user`,
`confirm_with_user`, `iterate`, `recover_detector_failure`, and `done`. The dict
always includes a `reason`; it may also include `summary`, `confidence`,
`suggestion`, `proposed_change`, `failed_detectors`, or `suggested_replacements`.

## Happy-path session

```python
from pyod.utils.ad_engine import ADEngine

engine = ADEngine(random_state=42)
state = engine.start(X, data_type="tabular")
assert state.next_action["action"] == "plan"

state = engine.plan(state, priority="balanced", constraints={"max_detectors": 3})
assert state.next_action["action"] == "run"

state = engine.run(state)
assert state.next_action["action"] in {"analyze", "recover_detector_failure", "confirm_with_user"}

if state.next_action["action"] == "recover_detector_failure":
    # Recover now or continue with successful detectors; see recovery section.
    pass

state = engine.analyze(state)
if state.next_action["action"] == "report_to_user":
    report = engine.report(state, format="text")
elif state.next_action["action"] == "iterate":
    # Use quality/consensus diagnostics before rerunning.
    pass
```

`engine.investigate(X, data_type=None, priority="balanced")` is the one-shot
shortcut for `start -> plan -> run -> analyze`. Use it when the task does not
need an intermediate user confirmation.

## Planning knobs

`engine.plan(state, priority="balanced", constraints=None)` wraps
`plan_detection` and flattens the primary plan plus alternatives into
`state.plans`.

Common constraints:

```python
{"max_detectors": 1}                    # cap at one detector
{"max_detectors": 2}                    # cap at two detectors
{"exclude_detectors": ["IForest"]}      # avoid a detector by exact name
```

`max_detectors` is capped at `3`. Re-planning from a later phase clears stale
`results`, `consensus`, `analysis`, and `quality`.

## Run and recovery behavior

`engine.run(state)` requires `state.phase == "planned"`. It attempts each plan:

- Success entry: `status="success"`, `detector_name`, scores, labels, threshold,
  runtime, and detector object.
- Failure entry: `status="error"`, `detector_name`, `error`, and the failed plan.
  The run logs a warning but does not stop the whole session.

After `run`:

| Condition | `next_action` | Agent action |
|---|---|---|
| All detectors fail | `confirm_with_user` | Pause. Ask about data format, optional extras, or detector family. |
| Some detectors fail | `recover_detector_failure` | Either run recovery or proceed to analysis with successful detectors. |
| One or more detectors succeed, no failures | `analyze` | Continue to `engine.analyze(state)`. |

Recover failed detectors immediately with:

```python
state = engine.iterate(state, {"action": "recover"})
state = engine.run(state)
```

`recover` is the only `iterate` action accepted in `detected` phase. It replaces
failed detector slots using `state.next_action["suggested_replacements"]` when
available or replans with failed and successful names excluded.

## Analyze and quality diagnostics

`engine.analyze(state)` requires `phase == "detected"` and computes:

- Per-detector analyses aligned with `state.results`.
- Consensus analysis with `n_anomalies`, `anomaly_ratio`, score distribution,
  top anomalies, and summary.
- `best_detector` selected from successful results.
- Quality diagnostics:
  - `separation`: descriptive score gap between predicted outliers and inliers.
  - `agreement`: mean pairwise rank agreement between detectors; low agreement is
    a strong caution signal.
  - `stability`: cutoff-gap diagnostic; low values mean the flagged set is
    sensitive to contamination or threshold changes.
  - `overall` and `verdict`: heuristic summary (`high`, `medium`, `low`).

Do not present the quality verdict as proof. It is label-free and descriptive.
For medical, fraud, safety, legal, or other high-stakes decisions, report caveats
and ask for labels or domain validation.

## Iteration patterns

Structured feedback executes immediately from `analyzed` phase:

```python
state = engine.iterate(state, {"action": "adjust_contamination", "value": 0.05})
state = engine.iterate(state, {"action": "exclude", "detectors": ["IForest"]})
state = engine.iterate(state, {"action": "include", "detectors": ["ECOD"]})
state = engine.iterate(state, {"action": "rerun"})
```

After a successful structured iteration, `state.phase == "planned"` and
`state.next_action["action"] == "run"`; run and analyze again.

Natural-language feedback is parsed conservatively:

| User wording | Proposed action | Confidence behavior |
|---|---|---|
| `without` / `exclude` plus a known detector name | `exclude` that detector | High confidence, auto-applied. |
| `false positive` / `too many` | lower contamination | Medium confidence; usually asks confirmation. |
| `missed` / `false negative` | raise contamination | Medium confidence; usually asks confirmation. |
| `rerun` / `again` | rerun same plan | High confidence, auto-applied. |
| Ambiguous wording | rerun shell | Low confidence, sets `confirm_with_user`. |

When `next_action["action"] == "confirm_with_user"`, show the proposed change and
ask the user before applying it.

## Reporting

```python
text_report = engine.report(state, format="text")
json_report = engine.report(state, format="json")
```

`report` requires `phase == "analyzed"` and at least one successful detector.
Text format returns Markdown. JSON format returns a native dict with:

- `session.consensus`: score/label lists, detector count, agreement,
  disagreements.
- `session.quality` and `session.comparison`.
- `best_detector.name`, scores, labels, threshold, and per-detector analysis.

For a single-detector, non-session result, use `generate_report` from the API
reference instead.

## Hindsight validation and calibration diagnostics

When labels become available after an unsupervised run:

```python
validation = engine.validate(state, y)
```

`validate` requires an analyzed state and returns consensus metrics,
per-detector metrics, best-detector metrics, a consensus-vs-best comparison,
false positives, and false negatives. The label vector length must match the
consensus length.

For contamination calibration before iterating:

```python
diag = engine.contamination_diagnostics(state, threshold_sweep=[0.01, 0.03, 0.05])
```

The diagnostic is read-only and returns the effective contamination, flagged
rate, score percentiles, and optional threshold-sweep rows.

## Od-expert activation path for agents

PyOD ships a packaged `od-expert` agent skill that lets Claude Code or Codex run
an ADEngine investigation through natural conversation. The packaged skill is an
activation layer around the same APIs described here:

1. Triage modality from observable data properties.
2. Check common pitfalls: feature scaling, contamination mismatch, missing
   optional extras, single-detector overconfidence, raw-score misuse, and deep
   learning on tiny data.
3. Decide whether to ask before running: high-stakes context, ambiguous
   modality, labels mentioned, unknown contamination, low agreement, unstable
   cutoff, or suspiciously clean results.
4. Run ADEngine planning and multi-detector consensus.
5. Re-check quality diagnostics and report assumptions/caveats.

Install or inspect this activation path with the CLI commands in
[cli-and-mcp.md](cli-and-mcp.md). This generated repo skill is separate from the
packaged `od-expert` skill: use this file for operating guidance even when the
packaged skill has not been installed into an external agent.
