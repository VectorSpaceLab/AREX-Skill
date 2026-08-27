# Benchmark recipes

`moabb.benchmark()` is a convenience orchestration layer. It discovers
pipeline configurations, constructs paradigms, selects datasets, runs the
named evaluation classes, caches results, and optionally delegates analysis.
It is useful for a bounded comparison, but it is not a replacement for making
the generalization claim explicit.

## Smallest useful benchmark

Start with one pipeline directory, one paradigm, one local/fake-compatible
dataset, one evaluation, `plot=False`, and a unique result/output directory:

```python
from moabb import benchmark

results = benchmark(
    pipelines="./sample-pipelines/",
    evaluations=["WithinSession"],
    paradigms=["FakeImageryParadigm"],
    include_datasets=["FakeDataset-imagery-2-2--12-12--4-4--lefthand-righthand--c3-cz-c4"],
    results="./runs/fake-within/results",
    output="./runs/fake-within/analysis",
    overwrite=False,
    suffix="seed42",
    n_jobs=1,
    plot=False,
)
```

Dataset codes are generated from the `FakeDataset` constructor and can vary
with event/session/channel choices. Prefer passing a `FakeDataset` object when
constructing a Python-only smoke benchmark, or list the actual code observed
from `dataset.code`; do not guess a real catalog code. The benchmark wrapper
passes `random_state=42` to its evaluation contexts. `WithinSubject` is not a
valid name in this wrapper; instantiate `WithinSubjectEvaluation` directly.

## Pipeline configuration shape

A YAML file is parsed from a directory or single file. The minimal semantic
shape is:

```yaml
name: Tangent Space LR
paradigms:
  - LeftRightImagery
pipeline:
  - name: Covariances
    from: pyriemann.estimation
    parameters:
      estimator: oas
  - name: TangentSpace
    from: pyriemann.tangentspace
    parameters:
      metric: riemann
  - name: LogisticRegression
    from: sklearn.linear_model
    parameters:
      C: 1.0
```

`name`, `paradigms`, and `pipeline` are required. Each pipeline component has
`name`, importable module `from`, and optional `parameters`. The resulting
components are composed with sklearn `make_pipeline`. The `paradigms` entries
must match exported MOABB paradigm class names used by the benchmark.

For a grid search, add a `param_grid` mapping keyed by the pipeline name. The
parameter keys are normal sklearn pipeline parameter names and values are
candidate lists:

```yaml
name: CSP + LDA grid
paradigms:
  - LeftRightImagery
pipeline:
  - name: CSP
    from: mne.decoding
    parameters:
      n_components: 4
  - name: LinearDiscriminantAnalysis
    from: sklearn.discriminant_analysis
    parameters: {}
param_grid:
  csp_lda:
    csp__n_components: [2, 4]
```

Keep names stable and unique within a paradigm. Duplicate names are rejected.
A grid search may be expensive: run it only after the non-grid recipe works;
use `optuna=True` only with the optional dependency explicitly installed and a
bounded `time_out` in a direct evaluation. The benchmark wrapper passes the
configuration to the evaluation but does not expose a direct `time_out` knob.

## Include/exclude dataset recipes

Use one of these, never both:

```python
include_datasets=["BNCI2014-001"]
# or
include_datasets=[dataset_object]

exclude_datasets=["OneKnownCode"]
```

The list must be non-empty and homogeneous (all strings or all
`BaseDataset` objects), contain no duplicates, and include at least one
compatible dataset for each selected paradigm. Fake dataset codes are accepted
by the benchmark filter. An incompatible entry can be warned about and
removed; an empty compatible set causes the paradigm to be skipped or the
benchmark to fail. Validate the selected dataset codes from the paradigm before
starting a real run.

## Sessions, subjects, and context

- `evaluations=["WithinSession", "CrossSession", "CrossSubject"]` requests
  several protocols and produces an `evaluation` column; this is useful for a
  comparison only if each dataset supports each protocol.
- `n_splits` is forwarded to the underlying evaluation and has its documented
  class-specific meaning. It is not a universal “number of benchmark folds.”
- `contexts` points to a YAML context file with entries for every paradigm
  selected by the pipelines. The file is caller-owned configuration; do not
  rely on an unavailable source checkout copy in a generated skill.
- `include_datasets` and `exclude_datasets` accept codes or objects, not a
  mixture. Use `overwrite=False` when resuming a valid run.

## Bounded learning curve outside benchmark()

The benchmark wrapper does not provide a learning-curve argument. Configure a
normal evaluation directly:

```python
import numpy as np
from moabb.evaluations import WithinSessionEvaluation
from moabb.evaluations.splitters import LearningCurveSplitter

evaluation = WithinSessionEvaluation(
    paradigm=paradigm,
    datasets=[dataset],
    cv_class=LearningCurveSplitter,
    cv_kwargs={
        "data_size": {"policy": "ratio", "value": np.array([0.25, 0.5, 1.0])},
        "n_perms": np.array([3, 2, 1]),
        "test_size": 0.2,
    },
    random_state=42,
    n_jobs=1,
    overwrite=False,
    suffix="curve-v1",
    hdf5_path="./runs/curve-results",
)
results = evaluation.process(pipelines)
```

A ratio must be in `[0, 1]` and strictly increasing. A per-class curve uses
increasing integer counts that fit each training partition. Arrays of
permutation counts must be the same length and non-increasing. Learning-curve
rows carry `data_size` and `permutation`; use the analysis route to summarize
or plot them.

## Optional tracking and outputs

`codecarbon_config` is passed to the optional CodeCarbon tracker. The package
defaults disable file output and log at error level. Enabling tracking adds
runtime and optional output files; treat it as an approved optional workflow.
`plot=True` invokes analysis/plot saving below `output`, so keep plotting and
headless backend concerns in the analysis route. For a reproducibility smoke,
leave both `plot=False` and `codecarbon_config=None`.

Never claim that a benchmark recipe ran simply because a YAML file parsed.
Record: selected pipeline file/config digest, paradigm, dataset codes, protocol
names, seed, `n_jobs`, cache/result paths, overwrite setting, optional extras,
row count, and any skipped/incompatible datasets.
