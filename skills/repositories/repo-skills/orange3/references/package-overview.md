# Orange3 package overview

Orange3 is both a Python data-mining library and the Orange Canvas visual-programming application. The same data objects and model/evaluation objects are used by API code and by widgets.

## Install surfaces

Common public install paths:

```bash
# Conda is the recommended path for end users and compiled dependencies
conda install -c conda-forge orange3

# Pip install needs PyQt before running the GUI in many environments
python -m pip install PyQt6 PyQt6-WebEngine
python -m pip install Orange3
```

For development or a local checkout, install Qt first and then install Orange3 in editable mode:

```bash
python -m pip install -r requirements-pyqt.txt
python -m pip install -e .
```

Orange3 requires modern Python and compiled scientific dependencies (`numpy`, `scipy`, `scikit-learn`, `pandas`, `openTSNE`, `xgboost`, Qt bindings, and Orange Canvas/widget dependencies). Use an isolated environment.

## Runtime entry points

- `orange-canvas` launches Orange Canvas.
- `python -m Orange.canvas` launches the same application entry point.
- `python -m Orange.canvas --help` or `orange-canvas --help` prints CLI flags.
- Important flags include `--no-discovery`, `--force-discovery`, `--no-welcome`, `--no-splash`, `--log-level`, `--stylesheet`, `--config`, `--no-shadow`, `--clear-widget-settings`, and `--clear-all`.
- `Orange.canvas.run` provides an experimental non-interactive `.ows` workflow runner. Use it only for short deterministic workflows.

## Package map

| Surface | Main modules | Skill owner |
| --- | --- | --- |
| Data model and file I/O | `Orange.data`, `Orange.data.io`, `Orange.data.pandas_compat`, `Orange.preprocess`, `Orange.data.sql` | `data-preparation` |
| Supervised learners and evaluation | `Orange.base`, `Orange.classification`, `Orange.regression`, `Orange.modelling`, `Orange.evaluation` | `supervised-modeling` |
| Exploration and unsupervised analysis | `Orange.distance`, `Orange.clustering`, `Orange.projection`, `Orange.statistics`, `Orange.misc.DistMatrix` | `exploration-visualization` |
| GUI widgets and Canvas | `Orange.widgets`, `Orange.widgets.gui`, `Orange.widgets.settings`, `Orange.widgets.utils`, `Orange.canvas` | `widget-development` |

## Widget category map

Orange's core widget entry point exposes these categories:

- Data: load, inspect, select, edit, reshape, sample, transform, and save tables.
- Transform: transform-domain and feature construction style widgets discovered through the Orange widget package.
- Visualize: plots, projections, model visualizers, and visual diagnostics.
- Model: supervised learner widgets plus model load/save surfaces.
- Evaluate: model scoring, predictions, confusion matrix, ROC/lift/calibration plots, and related evaluation widgets.
- Unsupervised: distance, clustering, projection, and unsupervised exploratory widgets.

Widget guidance should preserve the widget's input/output signal contract. API guidance should preserve object contracts (`Table`, `Learner`, `Model`, `Results`, `DistMatrix`) rather than describing GUI labels only.

## Object flow cheat sheet

- File/API/SQL input produces `Orange.data.Table`.
- Preprocessing transforms or creates a new `Table` or a `Preprocess` object.
- Model widgets and API learners produce `Learner` and fitted `Model` objects.
- Evaluation creates `Orange.evaluation.Results` and score arrays.
- Distance APIs and widgets produce `Orange.misc.DistMatrix`.
- Visualization widgets may emit `Selected Data`, `Annotated Data`, projections, distances, models, or reports depending on the widget.
- Canvas workflows serialize widget nodes, links, and settings in `.ows` files.

## Native verification surfaces

When a later verification pass needs native evidence, use safe, focused cases that match the skill owner:

- Data: file/table/domain/preprocess API tests and data-widget smoke cases.
- Supervised modeling: learner/evaluation API cases and `Test and Score` / `Predictions` widget cases.
- Exploration/visualization: distance/projection/clustering API cases and scatter/k-Means/distance-map widget cases.
- Widget development: widget discovery, widget helper tests, and `.ows` workflow-loading cases.

SQL cases require backend packages plus live PostgreSQL or SQL Server credentials and should remain optional unless the user explicitly requests SQL.

## See also

- Root troubleshooting: [`troubleshooting.md`](troubleshooting.md)
- Source baseline: [`repo-provenance.md`](repo-provenance.md)
