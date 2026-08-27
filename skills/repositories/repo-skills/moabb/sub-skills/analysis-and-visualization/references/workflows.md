# Analysis workflows

These recipes are intentionally offline-first. They assume evaluation output
already exists and do not download datasets or rerun a benchmark.

## 1. Validate and inspect a result table

1. Obtain a DataFrame with `store.to_dataframe()` or the evaluation return.
2. Copy it before filtering and record metric, paradigm, evaluation protocol,
   dataset list, pipeline list, and row count.
3. Check required columns and numeric score values. Confirm the score range and
   whether it is accuracy, ROC-AUC, or another metric.
4. Check per-dataset `n_classes` and `samples_test` consistency before using
   `chance_by_chance`.
5. Check duplicate and incomplete pairs:

   ```python
   unit = ["dataset", "subject", "pipeline"]
   duplicates = df.duplicated(unit).sum()
   pair_counts = df.groupby(["dataset", "subject"])["pipeline"].nunique()
   ```

   Duplicate rows require an explicit aggregation decision. Pair counts less
   than the selected pipeline count mean a paired comparison will have fewer
   units than expected.

## 2. Compute metric-aware chance and plots

For a multiclass accuracy table:

```python
from moabb.analysis.chance_level import chance_by_chance
from moabb.analysis.plotting import distribution_plot, score_plot

levels = chance_by_chance(df, alpha=[0.05, 0.01])
fig, _ = score_plot(df, chance_level=levels)
fig.savefig("scores.svg", bbox_inches="tight")
fig2, _ = distribution_plot(df, chance_level=levels)
fig2.savefig("distributions.svg", bbox_inches="tight")
```

For binary ROC-AUC, use an explicit `chance_level=0.5` and explain that the
binomial adjusted values are not being used as AUC thresholds:

```python
fig, _ = score_plot(df, pipelines=["P0", "P1"], chance_level=0.5)
```

For a metric whose null is not known, omit a chance line and report the metric
separately rather than silently defaulting to 0.5.

## 3. Compare pipelines across datasets

```python
from moabb.analysis.meta_analysis import (
    compute_dataset_statistics,
    find_significant_differences,
)
from moabb.analysis.plotting import meta_analysis_plot, paired_plot, summary_plot

stats = compute_dataset_statistics(df, perm_cutoff=20)
p_values, effects = find_significant_differences(stats, perm_cutoff=20)
fig_pair = paired_plot(df, "P0", "P1", chance_level=0.5)
fig_matrix = summary_plot(p_values, effects, p_threshold=0.05)
fig_meta = meta_analysis_plot(stats, "P0", "P1")
```

Use the same subject/dataset pairing and pipeline names in every call. Inspect
`stats["nsub"]`, not just p-values. The exact permutation helper uses all sign
permutations for small samples and 10,000 seeded random permutations above its
internal small-sample threshold; choose and record `seed` when calling the
lower-level helper directly.

## 4. Create a report folder

`analyze` is a convenience report builder, not a full statistical audit:

```python
from moabb.analysis import analyze

analyze(df, "./reports", name="within_session", plot=True)
```

Before the call, ensure `./reports` exists and is writable. Afterward verify
`within_session/data.csv` equals the intended filtered table, `stats.csv` has
`p`/`smd`/`nsub`, and PDFs exist when plotting was requested. For a chance-aware
report, call `analyze` for the raw/stats artifacts and save separate figures
from `score_plot(..., chance_level=...)` with a manifest documenting metric,
chance choice, alpha, and data filtering.

Do not promise deterministic `info.txt`: it contains current time and machine
information. Keep generated reports outside the runtime skill tree.

## 5. Generate timelines without network data

```python
import matplotlib
matplotlib.use("Agg")
from moabb.analysis.timeline import (
    class_balance_svg,
    extract_stimulus_timeline,
    session_structure_svg,
    stimulus_timeline_svg,
)
from moabb.datasets.fake import FakeDataset

ds = FakeDataset(paradigm="imagery", n_sessions=2)
timeline = extract_stimulus_timeline(ds)
svg = stimulus_timeline_svg(ds, show_annotations=False)
class_svg = class_balance_svg(ds)
session_svg = session_structure_svg(ds)
```

Check for `None` before writing optional SVGs. `FakeDataset` validates the
rendering contract only. Real protocol timing depends on dataset metadata and
may be approximate or use a generic fallback; preserve `timeline.notes` and
`is_approximate` in a report.

## 6. Optional neural signatures

Treat Plotly signatures as a separate, explicitly selected workflow. First
probe `import plotly`; if absent, continue with Matplotlib plots and state that
interactive HTML was skipped. If present, use a small synthetic/fake dataset
and an explicit output directory, then verify returned paths and HTML content.
Do not use a failed Plotly import as a reason to fail core score, statistics,
or timeline analysis.

## Difficult verification cases

### Binary/multiclass chance mismatch

Create two otherwise identical DataFrames: one with `n_classes=2` and a score
labeled ROC-AUC, and one with `n_classes=4` and a score labeled accuracy. The
analysis route should select explicit 0.5 for ROC-AUC, use `chance_by_chance`
for multiclass accuracy, and refuse/flag a table whose `n_classes` or metric
metadata are inconsistent. Verify that adjusted binomial thresholds are not
presented as AUC significance thresholds.

### Headless output and optional dependency failure

Run the bundled smoke helper with `MPLBACKEND=Agg` and a `FakeDataset`. Verify
score/distribution/paired outputs and timeline SVGs are non-empty, rerun with
Plotly hidden/uninstalled behavior simulated, and pass a missing output path.
The expected result is successful core Matplotlib/timeline output, a clear
optional-Plotly status, and a nonzero actionable error for the invalid path.
