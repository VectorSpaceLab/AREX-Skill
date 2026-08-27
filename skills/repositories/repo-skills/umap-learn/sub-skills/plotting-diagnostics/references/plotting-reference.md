# Plotting Reference

`umap.plot` is optional. The base `umap` package and base embedding workflows do not require the plotting stack.

## Dependency Contract

The package's plotting import error recommends:

```bash
pip install "umap-learn[plot]"
```

or:

```bash
conda install pandas matplotlib datashader bokeh holoviews colorcet scikit-image
```

Project metadata for the `plot` extra also lists `seaborn` and `dask`. The `umap.plot` import path imports pandas, matplotlib, datashader, bokeh, holoviews, colorcet, and scikit-image support.

Use `../scripts/check_plotting_stack.py` from this sub-skill directory, or `sub-skills/plotting-diagnostics/scripts/check_plotting_stack.py` from the root skill directory, to report missing optional pieces.

## Fitted Mapper Expectations

Most helpers expect a fitted mapper with a 2D embedding.

Shared checks:

- `embedding_` or `embedding` exists.
- Embedding shape is `(n_samples, 2)`.
- `labels` and `values` have length `n_samples` before any subset is applied.
- `subset_points` has length `n_samples` and should be applied consistently to labels, values, and hover data.
- `hover_data` is a pandas dataframe with one row per embedding row before subsetting. Each column becomes a tooltip field in the small-data Bokeh path.

Additional helper-specific state:

- `connectivity` and `nearest_neighbour_distribution` need a fitted mapper with `graph_`.
- `diagnostic` uses fitted training data and internal neighbor state, including `_raw_data` and neighbor search state.
- `interactive` needs row-aligned `labels`, `values`, and `hover_data`; hover/search is limited for the large-data datashaded path.

## API Signatures

```python
points(umap_object, points=None, labels=None, values=None, theme=None, cmap='Blues', color_key=None, color_key_cmap='Spectral', background='white', width=800, height=800, show_legend=True, subset_points=None, ax=None, alpha=None)
```

- Static 2D embedding plot.
- `labels` is categorical; `values` is continuous. They are mutually exclusive.
- `points` can override the mapper embedding when you intentionally plot an external 2D coordinate array.
- Automatically switches to datashader when point count is large relative to the requested image size.
- Returns a matplotlib axis.

```python
connectivity(umap_object, edge_bundling=None, edge_cmap='gray_r', show_points=False, labels=None, values=None, theme=None, cmap='Blues', color_key=None, color_key_cmap='Spectral', background='white', width=800, height=800)
```

- Plots the fitted fuzzy graph connectivity over the embedding.
- `edge_bundling` supports `None` or `'hammer'`.
- `show_points=True` overlays embedding points.
- Hammer bundling can be expensive; try no bundling first.
- Returns a matplotlib axis.

```python
diagnostic(umap_object, diagnostic_type='pca', nhood_size=15, local_variance_threshold=0.8, ax=None, cmap='viridis', point_size=None, background='white', width=800, height=800, return_diagnostics=False, plot_result=True)
```

- Supported diagnostic types: `pca`, `ica`, `vq`, `local_dim`, `neighborhood`, and `all`.
- `pca`, `ica`, and `vq` color by a 3D projection of the original training data.
- `local_dim` estimates local dimension from fitted neighborhoods.
- `neighborhood` compares high-dimensional and embedded neighborhoods.
- `return_diagnostics=True` returns numeric diagnostic values; `plot_result=False` disables plotting.

```python
interactive(umap_object, labels=None, values=None, hover_data=None, tools=None, theme=None, cmap='Blues', color_key=None, color_key_cmap='Spectral', background='white', width=800, height=800, point_size=None, subset_points=None, interactive_text_search=False, interactive_text_search_columns=None, interactive_text_search_alpha_contrast=0.95, alpha=None)
```

- Builds an interactive Bokeh view for small datasets.
- Large datasets use a datashaded HoloViews path; hover data and text search are not preserved there.
- If `interactive_text_search=True`, search columns default to hover-data columns plus `label` when labels exist.
- If `tools` already includes a Bokeh HoverTool, automatic hover tooltips are not added.
- Returns a Bokeh figure/layout for small data or a HoloViews datashaded object for large data.

```python
nearest_neighbour_distribution(umap_object, bins=25, ax=None)
```

- Plots a histogram of average nearest-neighbour distances from the fitted graph.
- Returns a matplotlib axis.

```python
show(plot_to_show)
```

- Displays a matplotlib axis, Bokeh figure, or HoloViews dynamic map.
- Raises `ValueError` for unsupported objects.

## Themes and Color Inputs

Themes: `fire`, `viridis`, `inferno`, `blue`, `red`, `green`, `darkblue`, `darkred`, `darkgreen`.

Use:

- `labels=` for discrete categories.
- `values=` for continuous values.
- `color_key=` for explicit category-to-color mappings.
- `color_key_cmap=` for generated categorical color maps.
- `cmap=` for continuous values or density shading.

## Recipes

### Static labeled embedding

```python
mapper = umap.UMAP(random_state=42).fit(X)
ax = umap.plot.points(mapper, labels=y, theme='fire')
```

### Values and subsets

```python
mask = scores > 0.5
ax = umap.plot.points(mapper, values=scores, subset_points=mask, cmap='viridis')
```

### Connectivity

```python
ax = umap.plot.connectivity(mapper, show_points=True)
```

Use `edge_bundling='hammer'` only when the graph is small enough for the extra cost.

### Diagnostics without rendering

```python
diag = umap.plot.diagnostic(
    mapper,
    diagnostic_type='neighborhood',
    return_diagnostics=True,
    plot_result=False,
)
```

### Interactive hover and search

```python
import pandas as pd

hover_data = pd.DataFrame({
    'row_id': range(mapper.embedding_.shape[0]),
    'label': y,
})

umap.plot.output_file('plot.html')
plot = umap.plot.interactive(
    mapper,
    labels=y,
    hover_data=hover_data,
    interactive_text_search=True,
    interactive_text_search_columns=['label'],
    point_size=3,
)
umap.plot.show(plot)
```

For notebooks, call `umap.plot.output_notebook()` instead of `output_file`.

### Plain embedding fallback

When `umap.plot` is unavailable but matplotlib is installed:

```python
import matplotlib.pyplot as plt
plt.scatter(mapper.embedding_[:, 0], mapper.embedding_[:, 1], c=labels, s=5)
```

If no plotting backend is available, save `mapper.embedding_`, labels, and values for another environment.

