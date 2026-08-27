---
name: orange3
description: "Route Orange3 data mining, modeling, visualization, and
  widget-development workflows across the Orange data/API and Canvas widget
  surfaces."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Orange3

Use this repo skill when a task involves Orange3 / Orange Data Mining: the `Orange.data.Table` data model, file/SQL ingestion, preprocessing widgets, supervised learners and evaluation, exploratory plots/projections/clustering, or Orange Canvas widget development.

Orange3 combines a Python data-mining library with a Qt Canvas visual-programming application. Start from the user's surface area: API code, GUI widget workflow, `.ows` Canvas workflow, or widget-framework maintenance.

## First decision

1. **Data loading, cleaning, schema repair, SQL, or save/export** → use [`sub-skills/data-preparation/SKILL.md`](sub-skills/data-preparation/SKILL.md).
2. **Classification, regression, fitted models, predictions, or `Orange.evaluation` scoring** → use [`sub-skills/supervised-modeling/SKILL.md`](sub-skills/supervised-modeling/SKILL.md).
3. **Plots, distances, projections, clustering, statistics, or unsupervised widgets** → use [`sub-skills/exploration-visualization/SKILL.md`](sub-skills/exploration-visualization/SKILL.md).
4. **Building, previewing, testing, discovering, or loading Orange widgets / Canvas workflows** → use [`sub-skills/widget-development/SKILL.md`](sub-skills/widget-development/SKILL.md).
5. For install/import, `orange-canvas`, optional SQL, PyQt/headless, or cross-cutting package issues, read [`references/troubleshooting.md`](references/troubleshooting.md).
6. For package architecture, install commands, CLI entry points, and native verification surfaces, read [`references/package-overview.md`](references/package-overview.md).

## Common task signals

Route to this skill when the request mentions any of these signals:

- `Orange`, `Orange3`, Orange Data Mining, Orange Canvas, `orange-canvas`, `.ows`, widgets, widget workflows, or add-ons.
- `Orange.data.Table`, `Domain`, `Variable`, `.tab`, `OWFile`, `OWCSVImport`, `OWSave`, `OWPreprocess`, or `OWSql`.
- Orange learners such as `LogisticRegressionLearner`, `RandomForestLearner`, `TreeLearner`, `KNNLearner`, `SVMLearner`, `MeanLearner`, `ConstantLearner`, or `Orange.modelling` fitters.
- `CrossValidation`, `TestOnTestData`, `Test and Score`, `Predictions`, `CA`, `AUC`, `F1`, `RMSE`, `R2`, or `Results.failed`.
- Scatter Plot, Box Plot, Distributions, Heat Map, Distance Matrix/Map, PCA, MDS, t-SNE, k-Means, DBSCAN, Hierarchical Clustering, Silhouette Plot, FreeViz, Linear Projection, or Radviz.
- `OWWidget`, `Input`, `Output`, `Setting`, `ContextSetting`, `DomainContextHandler`, `WidgetPreview`, `WidgetTest`, widget discovery, or Canvas workflow loading.

## Minimal package check

For a quick installed-package check, run the bundled helper:

```bash
python scripts/orange3_smoke.py --skip-gui
```

If Qt/PyQt is installed and a headless display is needed:

```bash
QT_QPA_PLATFORM=offscreen python scripts/orange3_smoke.py --with-gui
```

A basic manual import check is:

```python
import Orange
from Orange.data import Table
iris = Table("iris")
print(Orange.__version__, len(iris), iris.domain)
```

## Operating rules

- Treat Orange's `Table`/`Domain`/`Variable` model as the shared substrate. Even widget tasks usually pass `Table`, `Learner`, `Model`, `Results`, or `DistMatrix` objects through signals.
- For GUI/widget work, distinguish **method semantics** from **widget framework mechanics**. Use method sub-skills for data/model/visualization behavior and `widget-development` for `OWWidget`, signals, settings, preview, tests, and Canvas workflows.
- SQL support is optional and service-bound. Do not block core Orange3 guidance on PostgreSQL or SQL Server unless the user's task explicitly requires live SQL.
- Use `QT_QPA_PLATFORM=offscreen` for headless widget discovery, widget tests, Canvas workflow loads, or catalog/icon rendering.
- Do not assume CUDA/ROCm/MPS. The selected Orange3 skill scope needs CPU plus GUI dependencies; no accelerator backend is required.
- Do not depend on a source checkout at runtime. Use the bundled references and scripts in this skill plus an installed Orange3 package.

## What this skill does not cover

- Generic scikit-learn or pandas tasks that do not use Orange's data model, widgets, or Canvas.
- Deep-learning GPU training frameworks, LLM workflows, or distributed training unless they are only incidental dependencies of an Orange task.
- Writing or exporting DisCo skills themselves; this is an operating skill for Researcher mode.

## Provenance

See [`references/repo-provenance.md`](references/repo-provenance.md) for the source commit, dirty-state baseline, package version, and relative evidence paths distilled into this skill.
