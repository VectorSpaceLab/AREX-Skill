# Decomposition API reference

Source anchors: `scikitplot/decomposition.py`, `docs/decomposition.rst`, `scikitplot/tests/test_decomposition.py`, and the PCA example programs.

Both functions return the Matplotlib `Axes` they draw on. If `ax=None`, scikit-plot creates a new figure and axes.

## `plot_pca_component_variance`

```python
plot_pca_component_variance(
    clf,
    title='PCA Component Explained Variances',
    target_explained_variance=0.75,
    ax=None,
    figsize=None,
    title_fontsize='large',
    text_fontsize='medium',
)
```

Verified behavior:

- `clf` must have `explained_variance_ratio_`; an unfitted `PCA` raises `TypeError`.
- The function plots cumulative explained variance, starting at zero.
- `target_explained_variance` is located with `numpy.searchsorted` and highlighted when it falls within the available components.
- Values outside `[0, 1]` do not crash in the native tests, but interpret them carefully.
- `ax` reuses an existing axes; `figsize` is used only when creating a new one.

## `plot_pca_2d_projection`

```python
plot_pca_2d_projection(
    clf,
    X,
    y,
    title='PCA 2-D Projection',
    biplot=False,
    feature_labels=None,
    ax=None,
    figsize=None,
    cmap='Spectral',
    title_fontsize='large',
    text_fontsize='medium',
)
```

Verified behavior:

- `clf` must be fitted and implement `transform(X)`.
- The transformed matrix must provide at least two columns because the function plots dimensions 0 and 1.
- `y` labels are used to split points by class with `numpy.unique`.
- `biplot=True` draws arrows from the first two component rows in `clf.components_`.
- If `feature_labels` is supplied for a biplot, it is indexed by feature position; keep it the same length as the original feature dimension.
- `cmap` accepts a Matplotlib colormap name or colormap object.

## Related compatibility route

The deprecated `scikitplot.plotters` module still has PCA helper names in this snapshot. For old imports or migration questions, route to `../../legacy-factories/SKILL.md`; for new code, prefer `scikitplot.decomposition`.
