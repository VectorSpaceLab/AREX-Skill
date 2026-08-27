# Feature and Target Visualizer Troubleshooting

Start with package-wide install/import/display issues in [root troubleshooting](../../../references/troubleshooting.md). This file focuses on feature and target diagnostic failures.

## Headless Matplotlib or missing output files

Symptoms:

- Plot code hangs waiting for a GUI.
- No PNG is written in CI or an agent shell.
- Multiple plots overlap in one figure.

Fixes:

1. Set a non-interactive backend before importing pyplot:

   ```python
   import matplotlib
   matplotlib.use("Agg")
   import matplotlib.pyplot as plt
   ```

2. Create a fresh figure/axes for each visualizer.
3. Save with `visualizer.show(outpath="name.png", clear_figure=True)`.
4. Call `plt.close(fig)` after saving.
5. Font warnings usually do not mean the plot failed; verify that the output file exists and is non-empty.

## Optional pandas support is absent or unreliable

Symptoms:

- DataFrame/Series examples fail because pandas is not installed.
- Feature names are numeric indices instead of column names.
- String column selection in `JointPlot(columns="name")` fails after conversion.

Fixes:

- Convert to arrays and pass names explicitly:

  ```python
  X_array = X_dataframe.to_numpy()
  y_array = y_series.to_numpy()
  feature_names = list(X_dataframe.columns)

  viz = Rank2D(features=feature_names)
  viz.fit(X_array, y_array)
  viz.transform(X_array)
  ```

- For `FeatureCorrelation`, use `labels=feature_names`.
- For `JointPlot`, use integer `columns` after converting to arrays, or keep a real DataFrame when selecting by string column names.

## Bad feature matrix shape or feature-name length

Symptoms:

- `tuple index out of range` from a one-dimensional `X`.
- `number of supplied feature names does not match the number of columns in the training data`.
- PCA raises a component-count error.

Fixes:

- Feature visualizers need a 2D feature matrix with shape `(n_samples, n_features)` unless a specific `JointPlot` mode says otherwise.
- Ensure `len(features) == X.shape[1]` for `Rank1D`, `Rank2D`, `RadialVisualizer`, `ParallelCoordinates`, `PCA`, and `Manifold`.
- For PCA/Manifold 3D projections, ensure at least three usable feature dimensions and enough samples.
- For one-dimensional feature-vs-target analysis, use `JointPlot(columns=<single feature>)` or reshape explicitly.

## Class names, labels, and color mapping are wrong

Symptoms:

- `number of specified classes does not match number of unique values in target`.
- `discovered N classes in the data, does not match the N labels specified`.
- `Target needs to be label encoded` or unknown class-color errors.
- Legends show numeric classes when human names were expected.

Fixes:

- Pass `classes=[...]` to feature-space/projection visualizers and `labels=[...]` to `ClassBalance`.
- The length must match the unique values in `y`; for encoded targets, use labels ordered consistently with the encoder/classes.
- Use `target_type="discrete"` when numeric class ids are being mistaken for continuous values in `PCA` or `Manifold`.
- Use `target_type="continuous"` for regression-like colorbars.
- Keep the same label convention when moving from `ClassBalance` to [classifier visualizers](../../classifier-visualizers/SKILL.md).

## Rank1D and Rank2D errors

Symptoms:

- `'<name>' is unrecognized ranking method`.
- Correlation matrices contain `nan` values.
- Covariance/correlation colors look dominated by one scale.

Fixes:

- `Rank1D` supports `algorithm="shapiro"`.
- `Rank2D` supports `"pearson"`, `"covariance"`, `"spearman"`, and `"kendalltau"`.
- Remove or impute missing values before ranking.
- Avoid constant columns for correlation methods; they can produce undefined correlations.
- Standardize features before covariance-style comparisons when scales differ.

## RadialVisualizer and ParallelCoordinates issues

Symptoms:

- Plot is unreadable due to too many rows or features.
- `ParallelCoordinates(normalize="foo")` raises an unrecognized normalization error.
- `sample` or `shuffle` type errors occur.

Fixes:

- For `ParallelCoordinates`, use `normalize="standard"`, `"minmax"`, `"maxabs"`, `"l1"`, or `"l2"`; use `None` to disable.
- Use `sample=<int>` or a fraction `0 < sample <= 1`.
- Set `shuffle=True, random_state=<seed>` when sampling should be random and reproducible.
- Use `fast=True` for very large row counts, accepting that density detail is reduced.
- Treat missing values before plotting; `RadialVisualizer` filters rows with NaNs and may warn.

## PCA errors or surprising projections

Symptoms:

- `instance is not fitted yet, please call fit` when calling `transform`.
- `Projection dimensions must be either 2 or 3`.
- `heatmap and colorbar are not compatible with 3d projections`.
- A 3D plot is missing 3D axes warnings.

Fixes:

- Call `fit(X, y)` before `transform(X, y)`, or call `fit_transform(X, y)`.
- Use `projection=2` or `projection=3` only.
- Do not combine `projection=3` with `heatmap=True`.
- Prefer `projection=2` for automated reports.
- Keep `scale=True` unless features are already deliberately scaled.
- If numeric labels are intended as classes, pass `target_type="discrete"` through PCA `**kwargs`.

## Manifold is slow, unsupported, or fails to transform

Symptoms:

- Manifold learning runs for too long or consumes too much memory.
- `requires data to be simultaneously fit and transformed, use fit_transform instead`.
- `could not create manifold for '<value>'`.
- Warning about default `n_neighbors`.

Fixes:

- Prefer PCA first. Use Manifold only after reducing rows/features.
- Supported string names are `"lle"`, `"ltsa"`, `"hessian"`, `"modified"`, `"isomap"`, `"mds"`, `"spectral"`, and `"tsne"`; otherwise pass a real sklearn transformer.
- Use `fit_transform(X, y)` for `"mds"`, `"spectral"`, and `"tsne"`; these do not support the separate `transform()` path in this API surface.
- Set `n_neighbors` explicitly for neighbor-based algorithms. Very small datasets and large neighbor counts can fail.
- Set `random_state` for stochastic algorithms and report reproducibility limits.
- Do not run full manifold algorithm sweeps in routine verification; use a tiny sample or the bundled smoke script instead.

## JointPlot column and histogram errors

Symptoms:

- `when self.columns is None specify either X and y as 1D arrays or X as a matrix with 2 columns`.
- `when self.columns is a single index, y must be specified`.
- `contains too many indices or is invalid for joint plot`.
- Histogram layout fails or is too crowded.

Fixes:

- With `columns=None`, pass either a two-column `X` and no `y`, or one-dimensional `X` plus one-dimensional `y`.
- With one selected column, pass `y`.
- With two selected columns, pass exactly two indices or column names.
- Use `hist=False` if marginal axes cause compatibility or layout issues.
- Use `kind="hex"`/`"hexbin"` for dense pairs; use `kind="scatter"` when the legend/correlation label matters.

## ClassBalance target errors

Symptoms:

- `fit has changed to only require a 1D array, y since version 0.9`.
- `'<target type>' target type not supported, only binary and multiclass`.
- Label-count mismatch.

Fixes:

- Call `ClassBalance().fit(y_train)` or `ClassBalance().fit(y_train, y_test)`. Do not call `fit(X, y)`.
- Use only binary or multiclass classification targets.
- For continuous targets, use `BalancedBinningReference` or another regression-oriented diagnostic instead.
- If labels are supplied, verify the number and ordering against the target classes.

## BalancedBinningReference target errors

Symptoms:

- `y needs to be an array or Series with one dimension`.
- Bins look unhelpful due to skew or outliers.

Fixes:

- Pass a one-dimensional numeric target.
- Adjust `bins` and consider transforming or clipping extreme values before plotting.
- Use the stored `bin_edges_` as reference points, not as a guarantee of statistically optimal bins.

## FeatureCorrelation errors

Symptoms:

- `Method <name> not implement; choose from ...`.
- `Feature index is out of range`.
- `<feature> not in labels`.
- Both `feature_index` and `feature_names` were specified.

Fixes:

- Supported methods are `"pearson"`, `"mutual_info-regression"`, and `"mutual_info-classification"`.
- Use `labels=feature_names` when selecting by `feature_names` and `X` is not a DataFrame.
- If both `feature_index` and `feature_names` are provided, `feature_index` takes precedence; supply only one selector to avoid confusion.
- Pass `random_state` through `fit()` for mutual information reproducibility, e.g. `viz.fit(X, y, random_state=42)`.
- Watch for constant or non-numeric features with Pearson correlation; clean or encode data before plotting.
