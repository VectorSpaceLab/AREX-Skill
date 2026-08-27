# Function Interface API Reference

## Purpose

Use this when choosing classic seaborn functions and their major parameters. Signatures were checked against the generated skill's source snapshot and live package inspection.

## Relational Plots

```python
sns.scatterplot(data=None, *, x=None, y=None, hue=None, size=None, style=None, palette=None, hue_order=None, hue_norm=None, sizes=None, size_order=None, size_norm=None, markers=True, style_order=None, legend="auto", ax=None, **kwargs)
sns.lineplot(data=None, *, x=None, y=None, hue=None, size=None, style=None, units=None, weights=None, estimator="mean", errorbar=("ci", 95), n_boot=1000, seed=None, orient="x", sort=True, err_style="band", ax=None, **kwargs)
sns.relplot(..., kind="scatter", row=None, col=None, height=5, aspect=1, facet_kws=None, **kwargs)
```

- Use `scatterplot` for independent point observations and `lineplot` for ordered trends or repeated measurements.
- `units` draws separate lines without legend entries, useful for repeated observations.
- `weights` participates in selected aggregation paths; do not assume every estimator supports it.
- `relplot` wraps `scatterplot`/`lineplot` in a `FacetGrid` and creates its own figure.

## Distribution Plots

```python
sns.histplot(data=None, *, x=None, y=None, hue=None, weights=None, stat="count", bins="auto", multiple="layer", element="bars", kde=False, cbar=False, ax=None, **kwargs)
sns.kdeplot(data=None, *, x=None, y=None, hue=None, weights=None, fill=None, multiple="layer", common_norm=True, common_grid=False, cumulative=False, bw_method="scott", bw_adjust=1, levels=10, thresh=0.05, gridsize=200, cut=3, clip=None, ax=None, **kwargs)
sns.ecdfplot(data=None, *, x=None, y=None, hue=None, weights=None, stat="proportion", complementary=False, ax=None, **kwargs)
sns.rugplot(data=None, *, x=None, y=None, hue=None, height=0.025, expand_margins=True, ax=None, **kwargs)
sns.displot(..., kind="hist", rug=False, row=None, col=None, height=5, aspect=1, **kwargs)
```

- Use `histplot` for counts/proportions/densities over bins.
- Use `kdeplot` for smoothed density estimates; singular or nearly constant data can warn or fail.
- `cumulative=True` in the object/stat KDE path requires SciPy. For classic `kdeplot`, SciPy improves behavior and compatibility.
- `displot` is figure-level and returns a `FacetGrid`.
- `distplot` is deprecated; replace it with `histplot` or `displot` plus `kde=True` when needed.

## Categorical Plots

```python
sns.stripplot(..., jitter=True, dodge=False, native_scale=False, formatter=None, ax=None, **kwargs)
sns.swarmplot(..., dodge=False, native_scale=False, warn_thresh=0.05, ax=None, **kwargs)
sns.boxplot(..., fill=True, dodge="auto", width=0.8, gap=0, whis=1.5, native_scale=False, ax=None, **kwargs)
sns.violinplot(..., inner="box", split=False, cut=2, density_norm="area", common_norm=False, native_scale=False, ax=None, **kwargs)
sns.boxenplot(..., width_method="exponential", k_depth="tukey", showfliers=True, native_scale=False, ax=None, **kwargs)
sns.pointplot(..., estimator="mean", errorbar=("ci", 95), markers=<default>, linestyles=<default>, dodge=False, native_scale=False, ax=None, **kwargs)
sns.barplot(..., estimator="mean", errorbar=("ci", 95), width=0.8, dodge="auto", native_scale=False, ax=None, **kwargs)
sns.countplot(..., stat="count", width=0.8, dodge="auto", native_scale=False, ax=None, **kwargs)
sns.catplot(..., kind="strip", row=None, col=None, height=5, aspect=1, legend_out=True, **kwargs)
```

- Use raw-observation plots (`stripplot`, `swarmplot`) when distribution of points matters.
- Use distribution summary plots (`boxplot`, `violinplot`, `boxenplot`) for categorical distributions.
- Use estimate plots (`pointplot`, `barplot`) for point estimates and error bars.
- Use `native_scale=True` when numeric/datetime category spacing should be preserved.
- `catplot` is figure-level and creates a `FacetGrid`.

## Regression Plots

```python
sns.regplot(data=None, *, x=None, y=None, order=1, logistic=False, lowess=False, robust=False, logx=False, x_partial=None, y_partial=None, truncate=True, ax=None, **kwargs)
sns.residplot(data=None, *, x=None, y=None, lowess=False, order=1, robust=False, ax=None, **kwargs)
sns.lmplot(data, *, x=None, y=None, hue=None, col=None, row=None, order=1, logistic=False, lowess=False, robust=False, height=5, aspect=1, facet_kws=None, **kwargs)
```

- Ordinary linear regression uses NumPy/pandas paths.
- `logistic=True`, `lowess=True`, and `robust=True` require statsmodels.
- Regression options are mutually exclusive in key combinations; do not combine `lowess`, `logistic`, `robust`, `logx`, and polynomial order blindly.
- `lmplot` is figure-level and requires a DataFrame-style `data` argument.

## Matrix Plots

```python
sns.heatmap(data, *, vmin=None, vmax=None, cmap=None, center=None, robust=False, annot=None, fmt=".2g", linewidths=0, cbar=True, square=False, xticklabels="auto", yticklabels="auto", mask=None, ax=None, **kwargs)
sns.clustermap(data, *, method="average", metric="euclidean", z_score=None, standard_scale=None, figsize=(10, 10), row_cluster=True, col_cluster=True, row_linkage=None, col_linkage=None, row_colors=None, col_colors=None, mask=None, **kwargs)
```

- `heatmap` draws a rectangular matrix on an axes and can use masks/annotations.
- `clustermap` creates its own `ClusterGrid`, requires SciPy, and optionally uses fastcluster for performance.
- For `mask`, use the same shape as the plotted matrix.
