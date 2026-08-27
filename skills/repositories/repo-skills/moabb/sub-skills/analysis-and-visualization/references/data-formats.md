# Data formats and invariants

## Accepted result table

The canonical input is the DataFrame returned by `Results.to_dataframe()`.
`Results._to_dataframe_from_file` supplies these fields from the HDF5 store:

| Column | Type/meaning | Required for |
|---|---|---|
| `score` | numeric metric value, usually a proportion in `[0, 1]` | every statistics/plot/report operation |
| `time` | numeric evaluation time | provenance and optional summaries |
| `samples` | numeric training/sample count | provenance |
| `samples_test` | numeric test-trial/sample count | adjusted chance only |
| `n_classes` | numeric class count | chance only |
| `subject` | subject identifier | paired/session collapse |
| `session` | session identifier | preserving source granularity |
| `channels` | channel count | provenance |
| `n_sessions` | dataset session count | provenance |
| `dataset` | stable dataset code/name | grouping, chance, statistics |
| `pipeline` | stable display/name label | grouping, paired comparison |
| `carbon_emission` | optional kg CO2 measurement | emissions plots/summaries |
| `codecarbon_task_name` | optional CodeCarbon task id | emissions provenance |

Older files may lack `samples_test` or `n_classes`; the reader adds those
columns with `NaN`, but `chance_by_chance` will then fail or produce invalid
interpretation. Additional columns configured in `Results(additional_columns=...)`
are preserved and can be used as metadata, not assumed as core schema.

A minimal offline fixture for plot/statistics work should include:

```text
dataset, pipeline, subject, session, score, samples_test, n_classes
D0,      P0,      1,       0,       0.70, 50,          3
```

For paired tests, provide one row per pipeline for every intended
`(dataset, subject)` unit. If sessions are repeated, the implementation first
averages numeric columns across sessions; do not interpret that as a fold-level
sample size.

## Metric and chance contract

MOABB paradigms choose scoring metrics. The paper-results documentation notes
that the benchmark reports binary motor-imagery scenarios with ROC-AUC and
multiclass scenarios with accuracy. Therefore:

- `n_classes == 2` does not by itself prove the metric is accuracy; inspect the
  paradigm/evaluation scoring property and the result-producing route.
- For ROC-AUC, 0.5 is the null reference, but a binomial count threshold from
  `adjusted_chance_level` is not a general AUC significance test.
- For balanced binary accuracy, 0.5 is also the theoretical null, but the
  adjusted threshold requires the `samples_test` count to represent independent
  test decisions.
- For multiclass accuracy, use `1 / n_classes` as theoretical chance and only
  use adjusted binomial thresholds when class balance, trial count, and score
  interpretation justify it.
- Do not compare raw scores from different metrics or different chance models
  as if they were one scale. Keep metric and class-count columns in the report.

`chance_by_chance` takes the first `n_classes` and `samples_test` value per
dataset group. Before calling it, check each dataset has one consistent value:

```python
required = {"dataset", "samples_test", "n_classes"}
missing = required.difference(df.columns)
if missing:
    raise ValueError(f"chance metadata missing: {sorted(missing)}")
assert df.groupby("dataset")["n_classes"].nunique().max() == 1
assert df.groupby("dataset")["samples_test"].nunique().max() == 1
```

The helper returns proportions; plotting helpers multiply scores and chance
levels by 100 for display.

## Statistics shape

`collapse_session_scores(df)` groups by `pipeline`, `dataset`, and `subject`
and averages numeric columns. Its output is the input to a within-dataset
pivot with subjects as rows and pipelines as columns. `compute_dataset_statistics`
returns a long table whose meaningful fields are:

- `dataset`: dataset group;
- `pipe1`, `pipe2`: ordered pipeline pair;
- `p`: one-tailed paired p-value for that dataset;
- `smd`: signed standardized mean difference (`pipe1 - pipe2`);
- `nsub`: number of subject rows used.

`find_significant_differences(stats)` returns two square DataFrames indexed by
pipeline names. Preserve their matching index/columns when calling
`summary_plot(P, T)`.

Missing values, incomplete pairs, duplicate rows, and a pipeline label that
collapses to the same shortened name can change the analysis. Report the
filtering and effective `nsub`; do not silently impute or treat missing pairs
as failures.

## Report folder contract

For `analyze(df, out_path, name="analysis", plot=False)`:

```text
out_path/                       # must already exist and be a string
└── analysis/
    ├── info.txt                # date, system, CPU
    ├── data.csv                # exact DataFrame passed to analyze
    └── stats.csv               # compute_dataset_statistics output
```

With `plot=True`, `scores.pdf` and `ordering.pdf` are added. The function
creates `out_path/name` if absent and appends to `info.txt` if reused. It does
not make `out_path` itself, does not validate a metric-specific chance level,
and does not return the path; retain the expected path in the caller and
check it after completion.

## Timeline model

`StimulusTimeline.phases` is a list of `TimelinePhase` records with seconds
(`onset_s`, `duration_s`), while `annotations` contains start/end seconds and a
label. `total_duration_s` is the normalized total. `is_approximate=True` or
notes indicate fallback/derived metadata; preserve that signal in reports.
Class-balance and session-structure charts may return `None` when dataset
metadata cannot support a meaningful diagram. A `FakeDataset` is suitable for
offline API/smoke checks; it is not evidence about a real dataset protocol.

## CSV/JSON conversion boundary

The repository converter is not a general result serializer: it expects a
specific documentation CSV whose first data field contains backticks, removes
that decoration, emits only `{"data": rows}`, and always writes a same-stem
JSON file. It has no stable MOABB result schema, does not preserve headers,
and is therefore reference-only. For a controlled conversion, explicitly map
columns with pandas and write a versioned schema; do not invoke the source
converter from a generated skill.
