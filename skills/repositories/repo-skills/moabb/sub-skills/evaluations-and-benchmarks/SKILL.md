---
name: evaluations-and-benchmarks
description: "Choose a MOABB generalization protocol and splitter, then run
  deterministic evaluations, learning curves, or bounded benchmark recipes with
  safe result caching and reproducibility controls."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# Evaluations and benchmarks

Use this route when the task is to define **what must generalize**, split
MOABB trial metadata without leakage, run a fitted sklearn-compatible pipeline,
configure result/model/data caches, or compare pipelines with a bounded
benchmark. Start with [workflows](references/workflows.md); use the API tables
for exact knobs and [troubleshooting](references/troubleshooting.md) for cache,
parallel, dependency, and data failures.

## Boundaries and handoff

- Route dataset discovery, download directories, providers, and raw/BIDS data
  handling to [dataset-management](../dataset-management/SKILL.md).
- Route paradigm selection, epoch windows, preprocessing, and pipeline
  construction to [paradigms-and-pipelines](../paradigms-and-pipelines/SKILL.md).
- Route result statistics, chance levels, plots, and report folders to
  [analysis-and-visualization](../analysis-and-visualization/SKILL.md).
- The root [moabb router](../../SKILL.md) owns installation and cross-cutting
  import diagnosis. This route owns evaluation-time configuration and result
  semantics; it does not acquire real datasets or promise paper-scale runs.

Network downloads, real-dataset examples, Optuna, CodeCarbon, and long
benchmark jobs are reference-only unless the caller explicitly approves their
cost, network, and optional dependencies. The bundled smoke is offline and
uses only a tiny deterministic `FakeDataset`.

## Protocol decision

Write the claim before writing code. “Generalizes to unseen trials in the same
recording” is not “generalizes to a future session,” and neither is “generalizes
to an unseen subject.” Use this minimum mapping:

| Claim | Evaluation | Default split and data exposure | Minimum data |
|---|---|---|---|
| New trials, same subject/session | `WithinSessionEvaluation` | Stratified 5-fold within every subject × session; folds are aggregated | labeled trials per class in each session |
| New session, same subject | `CrossSessionEvaluation` | Leave-one-session-out within each subject | at least 2 sessions per subject |
| New trials across all sessions, same subject | `WithinSubjectEvaluation` | Stratified 5-fold pooling that subject’s sessions | labeled trials per class per subject |
| Unseen subject | `CrossSubjectEvaluation` | Leave-one-subject-out; source subjects train, held-out subject scores | more than 1 subject |

A cross-subject claim must use `CrossSubjectEvaluation` or
`CrossSubjectSplitter(groups="subject")`. Never replace it with a random
trial split, `WithinSubjectEvaluation`, or a custom grouping that puts trials
from the target subject into training. Inspect `metadata["subject"]` in every
fold and assert train/test subject sets are disjoint before interpreting a
score. Sessions may remain mixed within a held-out subject unless the claim
explicitly asks for subject-session transfer.

## Core workflow

1. Route dataset and paradigm preparation first; obtain a compatible dataset,
   paradigm, and sklearn estimator/pipeline. For a no-network check, use the
   `FakeDataset` recipe in [workflows](references/workflows.md).
2. Pick exactly one generalization target from the table. Check
   `evaluation.is_valid(dataset)` and expect construction to reject/remove
   incompatible datasets. Cross-session needs `n_sessions > 1`; cross-subject
   needs more than one subject.
3. Instantiate an evaluation with an explicit `random_state`, `n_jobs=1` for
   a first reproducible run, a unique `suffix`/`hdf5_path`, and `overwrite=False`
   unless replacing a deliberately identified result file.
4. Call `evaluation.process({"stable name": sklearn_pipeline},
   param_grid=None)` and inspect the returned `pandas.DataFrame`. The primary
   score is `score`; multi-metric scorers add `score_<name>`. Rows identify
   dataset, subject, session, and pipeline; within-session and within-subject
   aggregate ordinary folds, while learning-curve metadata stays in columns.
5. Scale only after the tiny run is correct: increase `n_jobs`, add datasets,
   or choose a benchmark recipe. Keep the protocol, data exposure, seed,
   pipeline versions, and result location beside any reported score.

For manual split inspection, use `splitter.split(y, metadata)` and treat the
returned values as **metadata index labels**, not guaranteed positional
indices. Slice with `X[indices]` only when the metadata index is the matching
zero-based array index; otherwise reset/align the metadata deliberately.

## Determinism and storage rules

- Set `random_state` on the evaluation and any custom splitter that shuffles;
  `WithinSessionSplitter` and `WithinSubjectSplitter` default to 5 folds and
  `shuffle=True`, while `CrossSessionSplitter` defaults to leave-one-group-out
  with `shuffle=False`. Use `n_splits` on within evaluations to change the
  inner fold count; on cross-subject it selects `GroupKFold` folds when set,
  otherwise `None` means leave-one-subject-out.
- Start with `n_jobs=1`. Parallel workers fit independent folds; increase it
  only after memory and deterministic output are understood. Grid-search work
  is also parallelized and can multiply resource use.
- Result storage is HDF5 under a result directory. `hdf5_path` is a base
  directory, not an HDF5 filename; `suffix` separates runs. `overwrite=True`
  truncates the selected `results/<Paradigm>/<Evaluation>/results_<suffix>.hdf5`
  file, so use it only with an intentional, isolated path.
- `cache_config` controls dataset raw/epoch/array caching and is separate from
  evaluation result caching. `save_model=True` requires `hdf5_path`; models are
  placed below `Models_<Evaluation>` (or `GridSearch_<Evaluation>`). Do not
  publish a score without recording whether data caching, model saving, or a
  parameter search was active.
- A collision or empty HDF5 result is a recoverable storage problem, not a
  reason to silently change the protocol. Stop competing writers, preserve a
  copy if needed, use a new run-specific base path/suffix, and rerun with
  `overwrite=True` only after deciding that the old file is disposable. See
  [troubleshooting](references/troubleshooting.md).

## Advanced routes

- Cross-subject target access is an information-budget choice. The default
  `CrossSubjectMode.TRAIN` is source-only. The `TRAIN_TRIALWISE` preset scores
  one target trial at a time and supports only `accuracy` or `roc_auc`. The
  unlabeled 20/50/full and labeled 20/50 presets expose target calibration as
  documented in [workflows](references/workflows.md); label-calibrated modes
  are not source-only results.
- Custom splitters use `cv_class` and `cv_kwargs`. `groups` may be a metadata
  column, a list of columns forming a compound key, or a callable receiving
  metadata. Use group-aware sklearn CV when protecting a group; document the
  resulting holdout axis. `CrossDatasetSplitter` is an advanced splitter for
  leave-dataset-out checks, not a replacement for the four evaluation classes.
- Learning curves use `LearningCurveSplitter` as `cv_class`, with
  `cv_kwargs={"data_size": {"policy": "ratio"|"per_class", "value": ...},
  "n_perms": ...}`. Values must increase strictly; permutation counts must
  be non-increasing as data sizes grow. Results include `data_size` and
  `permutation`.
- `benchmark()` is a convenience wrapper for YAML/directory or list-of-dict
  pipelines and the `WithinSession`, `CrossSession`, and `CrossSubject`
  evaluation names. It fixes the evaluation seed to 42 and writes both result
  HDF5 data and optional analysis output. Use [benchmark-recipes](references/benchmark-recipes.md)
  for bounded configurations; the wrapper does not expose `WithinSubject`.

## Verification

Run the safe helper from any working directory:

```bash
python /path/to/skills/disco/moabb/sub-skills/evaluations-and-benchmarks/scripts/evaluation_smoke.py --tiny-fixture
```

It must report a non-empty deterministic DataFrame, two subjects, two
sessions, and no network access. The helper is not a benchmark-quality score.
Use focused package tests only in a separately approved repository
verification phase; they are evidence rather than runtime dependencies. Real-data
evaluation and benchmark recipes remain network or expensive candidates. The
bundled smoke is the preferred offline check for this runtime graph.

For deeper contracts, follow [api-reference](references/api-reference.md),
[workflows](references/workflows.md), [benchmark-recipes](references/benchmark-recipes.md),
and [troubleshooting](references/troubleshooting.md).
