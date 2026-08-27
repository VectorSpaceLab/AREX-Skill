---
name: legacy-factories
description: "Routes legacy scikit-plot factory-injection and deprecated
  plotters-module requests to safe migration and compatibility guidance."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Legacy factories

Use this sub-skill when the user is maintaining older scikit-plot code that calls `classifier_factory`, `clustering_factory`, or imports plotting helpers from the deprecated `scikitplot.plotters` module.

## Route here

- Inject plotting methods into a classifier instance with `classifier_factory`.
- Inject plotting methods into a clusterer instance with `clustering_factory`.
- Diagnose warnings about missing methods, method-name collisions, or deprecation.
- Migrate old `scikitplot.plotters` imports to current modules.
- Validate compatibility quickly with `scripts/legacy_factories_smoke.py`.

## Prefer modern routes for new work

Use direct module functions for new code:

- Metric curves and silhouette: `../metrics/SKILL.md`.
- Feature importance and learning curves: `../estimators/SKILL.md`.
- Elbow curves: `../clustering/SKILL.md`.
- PCA plots: `../decomposition/SKILL.md`.

The factory layer is useful when the user must preserve old bound-method code, but it is deprecated in this snapshot.

## Inputs to check first

1. A classifier passed to `classifier_factory` must expose `fit`, `score`, and `predict`.
2. Probability-based injected methods also need `predict_proba`.
3. A clusterer passed to `clustering_factory` must expose `fit` and `fit_predict`.
4. Existing methods with the injected names may be overwritten with warnings.
5. The same SciPy/Matplotlib compatibility window from the root skill still applies.

## Reroute

- If the user wants exact behavior of the underlying plot, route to the owning sub-skill after identifying the injected method.
- If the user only needs an import migration from `scikitplot.plotters`, read `references/workflows.md`.
- If a factory warning is the main issue, read `references/troubleshooting.md` before changing model code.

## Read next

- `references/api-reference.md` for injected method names and verified contracts.
- `references/workflows.md` for classifier, clusterer, and deprecated-module migration patterns.
- `references/troubleshooting.md` for missing-method, override, and deprecation failures.
- `scripts/legacy_factories_smoke.py` for a tiny Agg-backed compatibility smoke run.
