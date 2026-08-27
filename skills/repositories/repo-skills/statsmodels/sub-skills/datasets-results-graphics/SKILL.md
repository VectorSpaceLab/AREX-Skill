---
name: datasets-results-graphics
description: "Use statsmodels datasets, result objects, predictions, summaries,
  robust covariance outputs, saving/loading, graphics, I/O, and local-vs-network
  support workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# Datasets, results, and graphics

Use this sub-skill for support workflows around statsmodels package use: built-in datasets, `get_rdataset` network behavior, result object attributes, prediction frames, summary/export, saving/loading fitted results, diagnostic/statistical graphics, table I/O, and `webdoc`.

## Workflow

1. Prefer built-in datasets or user-provided local data for reproducible examples. Treat `get_rdataset` as network-dependent.
2. Fit the model through the owning model sub-skill, then use result attributes for computation and summaries/plots for presentation.
3. For graphics in automation, set a noninteractive Matplotlib backend before importing pyplot.
4. Use bundled smoke helpers for minimal environment/result checks instead of broad example runners.

## Read or run

- Read [references/data-and-results.md](references/data-and-results.md) for built-in datasets, result attributes, predictions, summaries, robust covariance, and save/load.
- Read [references/graphics-and-io.md](references/graphics-and-io.md) for plot functions, headless plotting, summary export, pickle/I/O, and `webdoc`.
- Read [references/troubleshooting.md](references/troubleshooting.md) for network datasets, plot backend, prediction shape, summary-as-data, and pickle compatibility pitfalls.
- Run [scripts/smoke_results_graphics.py](scripts/smoke_results_graphics.py) for a local Longley/synthetic fit, prediction, summary, and headless figure smoke check.

## Boundaries

- Route model choice and fit setup to [linear-and-formula-models](../linear-and-formula-models/SKILL.md), [discrete-and-count-models](../discrete-and-count-models/SKILL.md), or [time-series-analysis](../time-series-analysis/SKILL.md).
- Route hypothesis-test choice and residual diagnostic interpretation to [statistical-tests-and-diagnostics](../statistical-tests-and-diagnostics/SKILL.md).
- This sub-skill owns how to operationalize outputs after fitting: tables, predictions, plots, serialization, and data source safety.
