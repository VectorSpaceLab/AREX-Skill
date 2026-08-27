---
name: "scikit-plot"
description: "Routes scikit-plot requests for metric curves, estimator
  diagnostics, clustering elbow plots, PCA visualizations, and legacy factory
  compatibility."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# scikit-plot

Use this root skill when the task is about the `scikitplot` plotting library itself: confusion matrices, ROC and precision-recall curves, KS statistics, calibration curves, cumulative gain and lift curves, feature importance, learning curves, elbow curves, PCA visualizations, or old `classifier_factory` / `clustering_factory` compatibility code.

This root skill is a router. Read the focused sub-skill for the plotting family you need, then come back here only for install guidance, environment compatibility, or cross-cutting troubleshooting.

## Install and smoke

The public package name is `scikit-plot` and the import name is `scikitplot`.

For PyPI use against this 0.3.7 snapshot:

```bash
python -m pip install "scikit-plot==0.3.7" "scipy<1.11" "matplotlib<3.9"
```

For a local checkout of the package source:

```bash
python -m pip install -e .
```

If you are already in a modern scientific stack and imports or first plots fail, use the compatibility window verified for this repository:

- `scipy<1.11`
- `matplotlib<3.9`

After install, run the root smoke check:

```bash
python scripts/check_environment.py
```

That helper imports the package, prints the version, and runs a tiny Agg-backed confusion-matrix smoke.

## Route map

| User need | Read next |
| --- | --- |
| Confusion matrix, ROC, precision-recall, KS, calibration, cumulative gain, lift, silhouette | `sub-skills/metrics/SKILL.md` |
| Feature importance or learning-curve plots | `sub-skills/estimators/SKILL.md` |
| Elbow curves for clusterers | `sub-skills/clustering/SKILL.md` |
| PCA component variance or 2-D projection | `sub-skills/decomposition/SKILL.md` |
| `classifier_factory`, `clustering_factory`, or deprecated `plotters` usage | `sub-skills/legacy-factories/SKILL.md` |

## What this root owns

- Install and compatibility notes for the 0.3.7 snapshot.
- The package-level smoke check.
- Routing to the five workflow sub-skills.
- Cross-cutting troubleshooting that applies before you know the exact plot family.

## What this root does not own

- Exact API signatures for plot functions.
- Long workflows or examples.
- Legacy method-injection details.
- Sub-skill-specific troubleshooting.

## Read next

- `references/workflow-map.md` for a compact capability map.
- `references/troubleshooting.md` for version-compatibility and import failures.
- `references/repo-provenance.md` to decide whether this skill still matches the checkout.
- `scripts/check_environment.py` to verify the install quickly.

## Fast selection hints

- If the user names a plot family, route by the plot name rather than by the module name.
- If the user says “legacy factory” or “deprecated plotters”, route to `legacy-factories`.
- If the user only wants to know whether the package is installed, the root smoke script is enough.
- If the user is trying to fix a failure, read root troubleshooting first, then the sub-skill troubleshooting page for the plot family.
