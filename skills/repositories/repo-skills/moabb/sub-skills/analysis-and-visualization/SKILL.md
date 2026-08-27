---
name: analysis-and-visualization
description: "Analyze MOABB result DataFrames or Results stores: validate score
  metadata, compute metric-appropriate chance levels and paired statistics,
  create headless plots and dataset timelines, and build reproducible analysis
  report folders."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# Analysis and visualization

Use this route after an evaluation has produced a MOABB result table. It owns
post-hoc analysis, statistics, plots, timelines, and report-folder assembly. It
does **not** choose datasets, build paradigms/pipelines, or run evaluations.

## Trigger and boundary

Use when the input is a `pandas.DataFrame` returned by
`Results.to_dataframe()` (or an equivalent table with the same columns), or a
`Results` store that must first be converted to a DataFrame. Route evaluation
protocol and result generation to
[Evaluations and benchmarks](../evaluations-and-benchmarks/SKILL.md), acquisition
and dataset metadata to [Dataset management](../dataset-management/SKILL.md),
and model/pipeline construction to
[Paradigms and pipelines](../paradigms-and-pipelines/SKILL.md).

The score is a metric value, not automatically accuracy. Confirm the paradigm
and scoring metric before interpreting a chance line or statistical result.

## Fast route

1. Load `df = results.to_dataframe()` if the source is a `Results` instance.
   Keep a copy and record evaluation, paradigm, metric, dataset, and pipeline
   selection before filtering.
2. Validate the required columns in [Data formats](references/data-formats.md).
   At minimum, analysis needs `dataset`, `pipeline`, `subject`, `session`, and
   numeric `score`; adjusted chance calculations additionally need
   `samples_test` and `n_classes`.
3. Check that the score semantics match the chance model. For balanced binary
   ROC-AUC, 0.5 is a useful null reference. For multiclass accuracy, the
   theoretical reference is `1 / n_classes`; an adjusted binomial threshold is
   meaningful only when the score is a count/proportion of independent test
   decisions, not an arbitrary continuous metric.
4. For paired comparisons, ensure the pipelines share complete dataset/subject
   units. Use `compute_dataset_statistics(df)` and then
   `find_significant_differences(stats)`; inspect `nsub`, `p`, and `smd` rather
   than ranking by means alone.
5. Generate Matplotlib figures, save them explicitly, and close them in batch
   jobs. Set `MPLBACKEND=Agg` before importing plotting modules in headless
   environments.
6. For a report folder, pass an existing string directory to `analyze(df,
   out_path, name="analysis", plot=False)`. It writes `info.txt`, `data.csv`,
   and `stats.csv`; with `plot=True` it also writes `scores.pdf` and
   `ordering.pdf`. Validate the folder and required files after the call.

## Core procedures

### Chance and statistics

- `adjusted_chance_level(n_classes, n_trials, alpha=0.05)` uses the binomial
  inverse survival function. Report both `1 / n_classes` and the adjusted
  threshold, and state what each means.
- `chance_by_chance(df, alpha=0.05)` or a list of alphas groups by `dataset`
  and reads the first `n_classes` and `samples_test` value in each group. Do
  not use it when those columns are missing, inconsistent within a dataset, or
  unrelated to the score metric.
- `collapse_session_scores` averages numeric columns by pipeline, dataset, and
  subject. This is the unit preparation used by the meta-analysis helpers.
- `compute_dataset_statistics` computes per-dataset pairwise p-values/effects;
  it uses permutation tests below `perm_cutoff=20` subjects and Wilcoxon tests
  otherwise. `find_significant_differences` combines dataset-level values and
  returns `(p_value_matrix, effect_matrix)`.

### Plots and style

- Use `score_plot(df, pipelines=None, orientation="vertical", chance_level=...)`
  for per-dataset score points; `distribution_plot` adds violin/KDE context;
  both return `(Figure, color_dict)` and accept a scalar, per-dataset mapping,
  `"auto"`, or the `chance_by_chance` result.
- Use `paired_plot(df, alg1, alg2, chance_level=...)` for subject/dataset paired
  points. Use `summary_plot(P, T, p_threshold=0.05, simplify=True)` for a
  significance/effect matrix and `meta_analysis_plot(stats, alg1, alg2)` for
  dataset-level effects and confidence intervals. See
  [Workflows](references/workflows.md) for a complete order.
- For emissions, call `emissions_summary` or `codecarbon_plot` only when
  `carbon_emission` is present. CodeCarbon is optional; missing measurements
  are not zero emissions.
- Apply `apply_moabb_style(ax, ...)` and `style_legend(ax, ...)` when composing
  custom figures. `set_moabb_defaults()` is global Matplotlib/Seaborn state;
  use it deliberately in reusable applications.

### Timelines and dataset summaries

With a dataset object and metadata available, `extract_stimulus_timeline(ds)`
returns a `StimulusTimeline` containing `TimelinePhase` and
`TimelineAnnotation` records. `plot_stimulus_timeline` returns a Matplotlib
`Figure`; `stimulus_timeline_svg` returns SVG text and closes its temporary
figure. `plot_class_balance` and `plot_session_structure` return a `Figure` or
`None` when metadata is insufficient; their `*_svg` wrappers return SVG text or
`None`. Approximate/generic timelines must be labeled as approximate.

## Report and optional dependency rules

`analyze` creates a local report from the exact DataFrame passed to it; it does
not rerun an evaluation or download data. `plot=True` uses PDF output and the
default 0.5 plot reference, so compute and save metric-specific chance-aware
figures separately when needed. Avoid overwriting an existing report name
unless the caller explicitly wants append/replace behavior.

Neural signatures are optional Plotly workflows. Importing the direct module
is possible without Plotly, but figure generation calls a guarded dependency
check and requires `moabb[interactive]`/Plotly. Keep these HTML artifacts out
of the core Matplotlib report and label any network/data acquisition as
external and unverified.

The repository's `results/csv_json_results_converter.py` is **reference-only**:
it assumes a documentation-specific first-column backtick format, silently
rewrites the first field, derives output beside the input, and has no stable
schema or output option. Do not copy it into runtime use. Use pandas
`read_csv`/`to_json` with an explicit schema when conversion is actually needed.
For a deterministic offline smoke check, use
[`scripts/smoke_analysis.py`](scripts/smoke_analysis.py).

## Checks before handoff

- Confirm all runtime links resolve inside this skill, its root, or a sibling
  route; never link back to the source checkout.
- Run the smoke helper with `MPLBACKEND=Agg` into an existing temporary output
  directory, inspect SVG headers and CSV columns, and test its invalid-output
  error path. Focused package tests may be run separately when explicitly
  approved; they are evidence, not runtime dependencies.
- Keep statistical assumptions, missing pairs, optional dependencies, and
  omitted long-running/network workflows explicit. Do not treat a plot as
  evidence that an evaluation was valid.

See [API reference](references/api-reference.md), [data formats](references/data-formats.md),
[workflows](references/workflows.md), and [troubleshooting](references/troubleshooting.md).
