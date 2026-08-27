# Evaluation workflows

Use these recipes to make the information budget and holdout axis explicit.
The code assumes dataset/paradigm/pipeline construction has already been
handled by the sibling routes. Real dataset constructors can download data;
the fake recipe is the safe offline substitute.

## 1. Offline deterministic evaluation

This is a compact shape check, not a scientific result:

```python
from mne.decoding import Vectorizer
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.pipeline import make_pipeline

from moabb.datasets.fake import FakeDataset
from moabb.evaluations import WithinSessionEvaluation
from moabb.paradigms import FakeImageryParadigm

fake = FakeDataset(
    ["left_hand", "right_hand"],
    n_subjects=2,
    n_sessions=2,
    n_runs=1,
    n_events=12,
    duration=4,
    seed=7,
)
paradigm = FakeImageryParadigm()
pipe = make_pipeline(Vectorizer(), LinearDiscriminantAnalysis())
evaluation = WithinSessionEvaluation(
    paradigm=paradigm,
    datasets=[fake],
    random_state=13,
    n_jobs=1,
    overwrite=True,
    suffix="offline_smoke",
    hdf5_path="./moabb-smoke-results",
)
results = evaluation.process({"vectorizer_lda": pipe})
assert not results.empty
assert set(results["subject"]) == {"1", "2"} or set(results["subject"]) == {1, 2}
```

Use the bundled `scripts/evaluation_smoke.py` instead when the caller wants a
repeatable command that cleans up its temporary HDF5 output. The fake dataset
is generated locally and has no meaningful benchmark performance.

## 2. Manual splitter audit

The data extraction side of an evaluation returns `X`, `y`, and `metadata`.
For a splitter audit, keep the metadata index aligned with `X` and verify the
axis that is meant to be held out:

```python
from moabb.evaluations.splitters import CrossSubjectSplitter

splitter = CrossSubjectSplitter(random_state=13)
for train_idx, test_idx in splitter.split(y, metadata):
    train_subjects = set(metadata.loc[train_idx, "subject"])
    test_subjects = set(metadata.loc[test_idx, "subject"])
    assert train_subjects.isdisjoint(test_subjects)
```

For `CrossSessionSplitter`, perform the same check per subject and assert the
session sets are disjoint. For `WithinSubjectSplitter`, assert the subject sets
are equal and understand that sessions are intentionally pooled. For
`WithinSessionSplitter`, each test fold should have one subject and one
session, while other trials from that same session can be in training.

Avoid this leakage pattern:

```python
# Wrong for a cross-subject claim: a random trial split can place one person's
# trials in both train and test.
train_test_split(X, y, random_state=13)
```

If a custom CV class is used, select its grouping deliberately. `groups="subject"`
means subject-level holdout only when the underlying sklearn CV consumes
`groups`. `groups=["subject", "session"]` changes the unit to a compound
subject-session group. A callable is useful for a reproducible, explicitly
recorded target selection, but it must return one group label per metadata row.

## 3. Cross-subject information budgets

Use source-only transfer for the ordinary generalization claim:

```python
from moabb.evaluations import CrossSubjectEvaluation, CrossSubjectMode

evaluation = CrossSubjectEvaluation(
    paradigm=paradigm,
    datasets=[fake],
    cs_mode=CrossSubjectMode.TRAIN,
    random_state=13,
    n_jobs=1,
    overwrite=True,
    suffix="cross_subject_train_only",
    hdf5_path="./cross-subject-results",
)
results = evaluation.process({"vectorizer_lda": pipe})
```

Use a named target-access mode only when the method is designed for it and the
report records the mode:

```python
evaluation = CrossSubjectEvaluation(
    paradigm=paradigm,
    datasets=[fake],
    cs_mode=CrossSubjectMode.TRAIN_AND_TARGET_UNLABELED_20P,
    # same deterministic/storage controls as above
)
```

The 20% mode returns a train/calibration/test protocol per target
subject-session pair. The calibration slice is not source training and the
remaining target trials are scored. Pipeline steps must request
`X_target_unlabeled` using sklearn metadata routing to consume it. Labeled
20/50% modes similarly require an explicit `X_target_labeled` plus
`y_target_labeled` request. The full unlabeled mode is transductive and must
not be described as source-only.

`TRAIN_TRIALWISE` prevents a target block from being passed to prediction as a
whole. It uses frozen fitted estimators and leave-one-out prediction; the
paradigm scorer must be the built-in `accuracy` or `roc_auc`. Custom scorers or
`scoring=None` are rejected rather than silently violating the trialwise
contract.

## 4. Learning curves

Use `LearningCurveSplitter` as the `cv_class` of an evaluation. The two
supported policies are:

- `ratio`: `value` is strictly increasing fractions in `[0, 1]`;
- `per_class`: `value` is strictly increasing integer samples per class and
  cannot exceed the smallest class in a training partition.

`n_perms` can be one integer or an array matching `value`; array values must be
monotonically non-increasing so small training sizes receive at least as many
permutations as larger sizes. `test_size` defaults to `0.2`; provide an
integer `random_state`. Example:

```python
import numpy as np
from moabb.evaluations import WithinSessionEvaluation
from moabb.evaluations.splitters import LearningCurveSplitter

data_size = {"policy": "per_class", "value": np.array([2, 4, 8])}
evaluation = WithinSessionEvaluation(
    paradigm=paradigm,
    datasets=[fake],
    random_state=13,
    cv_class=LearningCurveSplitter,
    cv_kwargs={"data_size": data_size, "n_perms": np.array([4, 3, 2])},
    n_jobs=1,
    overwrite=True,
    suffix="learning_curve",
    hdf5_path="./learning-curve-results",
)
results = evaluation.process({"vectorizer_lda": pipe})
assert {"data_size", "permutation"} <= set(results.columns)
```

A too-small subset can contain one class. MOABB skips that split with a
`RuntimeWarning`; do not turn the resulting curve into a score without noting
which points were skipped. Keep curve points and permutations in the result
rows; aggregate in the analysis route, not inside the splitter.

## 5. Custom metadata grouping

All stock sklearn CV classes are not group-aware. A group argument is only
forwarded to classes that consume `groups`. Use a group-aware class for a
protected axis:

```python
from sklearn.model_selection import GroupKFold
from moabb.evaluations import CrossSubjectEvaluation

evaluation = CrossSubjectEvaluation(
    paradigm=paradigm,
    datasets=[fake],
    cv_class=GroupKFold,
    n_splits=2,
    groups="subject",
    random_state=13,
)
```

For a one-fold target selection, the splitter supports callable `cv_kwargs`,
for example `CrossSubjectSplitter(cv_class=PredefinedSplit,
test_fold=lambda md: ...)`. Keep the predicate in a named function in a
reproducibility record rather than a lambda embedded in a persisted pipeline;
MOABB warns that lambda representations are not stable cache identities.

## 6. Configuration and execution sequence

1. Use a unique result base/suffix for each combination of evaluation class,
   dataset selection, pipeline version, and target-access mode.
2. Run `n_jobs=1`, `overwrite=False`, and `error_score="raise"` first.
3. Check `results.shape`, key columns, held-out groups, and whether any
   `error_score` rows were produced.
4. Only then enable `save_model`, grid search, optional caching, or parallel
   workers. Store `CacheConfig` under a data-cache directory separate from
   the HDF5 result directory.
5. For a benchmark wrapper, use `evaluations=["WithinSession"]`, one paradigm,
   one fake/local dataset, `plot=False`, and a small pipeline directory before
   adding real datasets or multiple protocols.
