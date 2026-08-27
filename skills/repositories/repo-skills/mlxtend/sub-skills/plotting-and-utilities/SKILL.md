---
name: plotting-and-utilities
description: "Use mlxtend plotting helpers, packaged data loaders, file IO,
  text, math, and small utility helpers."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Plotting and utilities

Use this sub-skill when the task is to create Matplotlib visualizations with `mlxtend.plotting`, load bundled or local toy datasets from `mlxtend.data`, group local files, tokenize or generalize text/name strings, run combinatorics or vector-space helpers, or use small utilities such as `Counter`, `check_Xy`, and `format_kwarg_dictionaries`.

## Read first

- [references/api-reference.md](references/api-reference.md) for verified signatures, return objects, and API-specific constraints.
- [references/workflows.md](references/workflows.md) for headless plotting, decision regions, confusion matrices, heatmaps, scatter/PCA/SFS plots, dataset loaders, file grouping, text, math, and utility recipes.
- [references/data-formats.md](references/data-formats.md) for accepted plotting inputs, dataset shapes, local MNIST files, file-group schemas, tokenizer/name outputs, and utility array contracts.
- [references/troubleshooting.md](references/troubleshooting.md) for display/backend failures, figure/Axes return pitfalls, decision-region filler errors, dataset path/shape problems, file glob quirks, tokenizer/name edge cases, and math/counting validation gaps.
- [scripts/plotting_utilities_smoke.py](scripts/plotting_utilities_smoke.py) to smoke-test the installed plotting/data/file/text/math/utils APIs on deterministic CPU examples.

## Route here for

- `mlxtend.plotting`: decision regions, confusion-matrix plots, learning curves, heatmaps, checkerboards, ECDFs, scatter plots, scatterplot matrices, PCA correlation graphs, linear-regression plots, SFS metric plots, enrichment plots, stacked bars, and border cleanup.
- `mlxtend.data`: `iris_data`, `wine_data`, `autompg_data`, `boston_housing_data`, `mnist_data`, `loadlocal_mnist`, `three_blobs_data`, and `make_multiplexer_dataset`.
- `mlxtend.file_io`: `find_files` and `find_filegroups` on local directories.
- `mlxtend.text`: word/emoticon tokenizers plus `generalize_names` and `generalize_names_duplcheck`.
- `mlxtend.math`: `factorial`, `num_combinations`, `num_permutations`, `vectorspace_orthonormalization`, and `vectorspace_dimensionality`.
- `mlxtend.utils`: `Counter`, `check_Xy`, `format_kwarg_dictionaries`, and the small testing helper `assert_raises` when diagnosing expected exceptions.

## Boundaries and sibling routes

- Do not teach estimator fitting, stacking, voting, or Kmeans here. Route classifier/regressor/cluster construction to [../estimators-and-ensembles/SKILL.md](../estimators-and-ensembles/SKILL.md); plotting recipes may assume a fitted estimator or use a tiny dummy predictor only to demonstrate a plotting API.
- Do not choose evaluation metrics, statistical tests, validation splitters, or produce confusion matrices here. Route metric/test choice and `mlxtend.evaluate` arrays to [../evaluation-and-validation/SKILL.md](../evaluation-and-validation/SKILL.md), then return here only to visualize an existing matrix or curve.
- Do not produce selector metric dictionaries here. Route feature selection and `SequentialFeatureSelector.get_metric_dict()` creation to [../feature-workflows/SKILL.md](../feature-workflows/SKILL.md), then return here for `plot_sequential_feature_selection`.
- Do not route market-basket mining here; plotting or file helpers around mined outputs are in scope, but mining itself belongs to [../frequent-patterns/SKILL.md](../frequent-patterns/SKILL.md).

## Operating rules

1. In headless jobs, set `MPLBACKEND=Agg` or call `matplotlib.use("Agg")` before importing `matplotlib.pyplot`; save figures instead of calling `plt.show()`.
2. Check each plotting helper's return type before saving or modifying a plot: some return `Axes`, some return `(fig, ax)`, some return `Figure`, and `scatter_hist` returns the scatter artist.
3. For decision regions, use a fitted object with `.predict`, numeric 2D `X`, 1D integer `y`, and explicit `filler_feature_values` for any non-plotted features.
4. Dataset helpers return NumPy arrays and never download remote files; `loadlocal_mnist` requires local IDX/ubyte image and label files.
5. Keep file IO examples in a temporary directory and expect returned paths, not open file handles.

## Safe smoke

From this sub-skill directory or any environment with mlxtend installed:

```bash
MPLBACKEND=Agg python scripts/plotting_utilities_smoke.py --task all
```

The script uses tiny arrays, packaged datasets, and temporary files only; it writes no persistent artifacts and does not depend on a source checkout.
