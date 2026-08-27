---
name: nannyml
description: "Use NannyML to monitor tabular ML models with performance
  estimation/calculation, drift detection, data-quality checks, chunking,
  thresholds, and CLI automation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# NannyML

Use this repo skill when a task involves the `nannyml` Python package, the `nml` or `nannyml` CLI, post-deployment tabular model monitoring, silent model failure investigation, performance estimation without targets, realized performance monitoring, data drift detection, data-quality alerts, or NannyML YAML configuration.

NannyML is a CPU-oriented Python library for monitoring tabular classification and regression models. It supports confidence-based performance estimation (CBPE) for classification, direct loss estimation (DLE) for regression, realized performance calculation when targets arrive, univariate and multivariate drift detection, data-quality checks, summary statistics, and a configuration-driven CLI runner.

## Quick install and smoke check

```bash
python -m pip install nannyml
python - <<'PY'
import nannyml as nml
print("nannyml", nml.__version__)
print(nml.CBPE)
print(nml.UnivariateDriftCalculator)
PY
```

NannyML depends on LightGBM. If installation or import fails around LightGBM system libraries, cloud filesystem dependencies, CLI rendering, or optional database output, read [references/troubleshooting.md](references/troubleshooting.md).

For a broader local sanity check after installation, run the bundled helper:

```bash
python scripts/check_install.py --check all
```

The helper verifies imports, API signatures, built-in dataset loaders, and CLI help without requiring network access, credentials, GPUs, or external services.

## Route map

| User task or symptom | Read next |
| --- | --- |
| Estimate classification performance without analysis targets using CBPE | [sub-skills/performance-monitoring/SKILL.md](sub-skills/performance-monitoring/SKILL.md) |
| Estimate regression performance without analysis targets using DLE | [sub-skills/performance-monitoring/SKILL.md](sub-skills/performance-monitoring/SKILL.md) |
| Calculate realized performance once targets are available | [sub-skills/performance-monitoring/SKILL.md](sub-skills/performance-monitoring/SKILL.md) |
| Compare estimated and realized performance, or compare performance with drift/data-quality results | [references/results-and-plots.md](references/results-and-plots.md) and [sub-skills/performance-monitoring/SKILL.md](sub-skills/performance-monitoring/SKILL.md) |
| Detect feature, output, or target drift | [sub-skills/drift-monitoring/SKILL.md](sub-skills/drift-monitoring/SKILL.md) |
| Choose univariate drift methods or multivariate PCA/domain-classifier drift | [sub-skills/drift-monitoring/references/methods.md](sub-skills/drift-monitoring/references/methods.md) |
| Rank drifted or unhealthy columns by alert count or correlation with performance | [sub-skills/drift-monitoring/SKILL.md](sub-skills/drift-monitoring/SKILL.md) |
| Decide reference/analysis columns, chunking, thresholds, or built-in datasets | [sub-skills/data-setup/SKILL.md](sub-skills/data-setup/SKILL.md) |
| Monitor missing values, unseen values, numerical ranges, or summary statistics | [sub-skills/data-setup/SKILL.md](sub-skills/data-setup/SKILL.md) |
| Use `nml run`, write YAML config, schedule jobs, or persist calculators/results | [sub-skills/cli-and-automation/SKILL.md](sub-skills/cli-and-automation/SKILL.md) |
| Interpret `Result.filter`, `to_df`, `plot`, `compare`, writer outputs, or Plotly figures | [references/results-and-plots.md](references/results-and-plots.md) |
| Pick a bundled sample dataset for a quick example | [references/datasets.md](references/datasets.md) |
| Check whether this skill is stale for a new checkout or package release | [references/repo-provenance.md](references/repo-provenance.md) |

## Common NannyML workflow shape

Most API workflows follow this pattern:

```python
import nannyml as nml

reference_df, analysis_df, analysis_targets_df = nml.load_synthetic_car_loan_dataset()

calculator_or_estimator = ...  # choose from the route map
calculator_or_estimator = calculator_or_estimator.fit(reference_df)
result = calculator_or_estimator.calculate(analysis_df)  # calculators
# or: result = calculator_or_estimator.estimate(analysis_df)  # estimators

result_df = result.filter(period='analysis').to_df(multilevel=False)
figure = result.filter(period='analysis').plot()
```

Use the reference period to establish the baseline and the analysis period to monitor future or production-like records. Targets are required in reference data for performance estimation and in analysis data only when calculating realized performance or target drift.

## Key public entry points

- `nml.CBPE`: classification performance estimation without analysis targets.
- `nml.DLE`: regression performance estimation without analysis targets.
- `nml.PerformanceCalculator`: realized performance calculation with targets.
- `nml.UnivariateDriftCalculator`: feature, output, or target univariate drift.
- `nml.DataReconstructionDriftCalculator`: multivariate PCA reconstruction-error drift.
- `nml.DomainClassifierCalculator`: multivariate domain-classifier AUROC drift.
- `nml.MissingValuesCalculator`, `nml.UnseenValuesCalculator`, `nml.NumericalRangeCalculator`: data-quality monitors.
- `nml.SummaryStatsAvgCalculator`, `SummaryStatsMedianCalculator`, `SummaryStatsRowCountCalculator`, `SummaryStatsStdCalculator`, `SummaryStatsSumCalculator`: summary-statistic monitors.
- `nml.ConstantThreshold`, `nml.StandardDeviationThreshold`: custom alert thresholds.
- `nml.SizeBasedChunker`, `nml.CountBasedChunker`, `nml.PeriodBasedChunker`, `nml.DefaultChunker`: chunking control.
- `nml.AlertCountRanker`, `nml.CorrelationRanker`: ranking and prioritization.
- `nml.RawFilesWriter`, `nml.PickleFileWriter`, `nml.DatabaseWriter`: output writers; `DatabaseWriter` requires the optional `nannyml[db]` extra.
- `nml` / `nannyml` CLI: configuration-driven monitoring runs.

## Boundaries and non-goals

- This skill is for using NannyML as a monitoring package, not for training the user's original predictive model.
- NannyML workflows are tabular and model-agnostic. Route image, text, LLM, time-series forecasting, and deep-learning training tasks to a package-specific skill for that stack unless the task is explicitly about monitoring tabular model outputs with NannyML.
- Database output is optional. Treat SQLAlchemy-compatible exports as requiring `pip install 'nannyml[db]'` and valid database credentials/connection strings.
- The generated skill is self-contained. Do not require future users to open NannyML's original source checkout or run source-repo tests/examples as part of ordinary runtime use.
