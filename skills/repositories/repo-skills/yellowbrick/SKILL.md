---
name: yellowbrick
description: "Use Yellowbrick visual diagnostics for scikit-learn models,
  feature/target analysis, clustering, model selection, text visualizers,
  datasets, styles, and contrib extensions."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Yellowbrick Repo Skill

Use this skill when a task asks how to use Yellowbrick, troubleshoot Yellowbrick
visualizers, create saved diagnostic plots for scikit-learn workflows, load
Yellowbrick example datasets, or adapt Yellowbrick-style visual checks in a
headless agent environment.

Yellowbrick visualizers usually wrap scikit-learn estimators or transform data
and render Matplotlib figures. Start from the shared lifecycle reference, then
open the focused sub-skill for the task family.

## Quick install and import check

For the repository snapshot covered by this skill, use a Python scientific stack
with Matplotlib and scikit-learn. Yellowbrick 1.5 has no GPU requirement.

```bash
python -m pip install yellowbrick
python - <<'PY'
import yellowbrick
print(yellowbrick.__version__)
PY
```

If normal scikit-learn classifiers or regressors are rejected as the wrong
estimator type, read `references/troubleshooting.md`; this snapshot works best
with a pre-1.4 scikit-learn compatibility stack.

For headless agents and CI, set a non-interactive backend before importing
`pyplot` or running bundled smoke scripts:

```python
import matplotlib
matplotlib.use("Agg", force=True)
```

## Shared workflow

1. Choose a visualizer from the route map below.
2. Prepare `X`, `y`, class labels, feature names, and any train/test split.
3. Instantiate the visualizer, often with a scikit-learn estimator and `ax` or
   style arguments.
4. Call the Yellowbrick lifecycle method: `fit`, `transform`/`fit_transform`,
   `score`, then `show(outpath=...)` for saved reports.
5. Validate with a bundled smoke helper when adapting a workflow in a new
   environment.

Read `references/visualizer-patterns.md` for lifecycle, axes, style, pipeline,
and headless rendering details. Read `references/troubleshooting.md` for
install/import, optional dependency, dataset, Matplotlib, and estimator-type
failures. Read `references/testing-and-validation.md` when creating a smoke
check or comparing against native Yellowbrick tests.

## Route map

- Classification reports, confusion matrices, ROC/PR curves, threshold tuning,
  class prediction errors, and class balance: read
  `sub-skills/classifier-visualizers/SKILL.md`.
- Regression residuals, prediction error, Cook's distance, and alpha selection:
  read `sub-skills/regressor-visualizers/SKILL.md`.
- Feature ranking, RadViz, parallel coordinates, PCA, manifold projections,
  joint plots, target binning, class balance, and feature-target correlation:
  read `sub-skills/feature-target-visualizers/SKILL.md`.
- Clustering diagnostics, k selection, silhouette/intercluster plots,
  validation/learning curves, CV scores, RFECV, feature importances, and
  dropping curves: read `sub-skills/cluster-model-selection/SKILL.md`.
- Yellowbrick dataset loaders/cache controls and text visualizers such as
  frequency distribution, t-SNE, UMAP, dispersion, word correlation, and POS
  tags: read `sub-skills/text-and-datasets/SKILL.md`.
- Experimental contrib visualizers, missing-value plots, decision boundaries,
  third-party estimator wrappers, pre-predicted outputs, and statsmodels
  adapters: read `sub-skills/contrib-and-extensions/SKILL.md`.

## Bundled shared script

Run `scripts/check_yellowbrick_visualizer.py --outdir <dir>` to verify that the
current environment can import Yellowbrick, use Matplotlib `Agg`, and create
small classifier, regressor, and cluster diagnostic PNGs from synthetic data.
This script is safe, deterministic, offline, and independent of the original
repository checkout.

## Provenance and freshness

Read `references/repo-provenance.md` before deciding whether this skill is
current for another checkout. If the source commit, package version, public API,
or dirty-state baseline differs, refresh the repo skill before relying on exact
signatures or compatibility notes.
