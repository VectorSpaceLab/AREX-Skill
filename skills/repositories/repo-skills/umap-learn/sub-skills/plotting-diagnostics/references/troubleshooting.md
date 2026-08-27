# Plotting Troubleshooting

## Symptoms and Recovery

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ImportError: umap.plot requires ...` | Optional plotting stack is missing | Install `pip install "umap-learn[plot]"` or `conda install pandas matplotlib datashader bokeh holoviews colorcet scikit-image`. Keep base UMAP workflows running without the plot extra. |
| Base `import umap` fails before plotting | Required runtime dependency is missing | Repair the base package/runtime first; this sub-skill only covers optional plotting once UMAP itself imports. |
| Object has no embedding attribute | Mapper was not fitted, or a raw array was passed where a fitted mapper is required | Fit with `mapper = umap.UMAP(...).fit(X)`, or pass explicit 2D `points=` only to `points`. |
| `Plotting is currently only implemented for 2D embeddings` | Mapper has `n_components` other than 2, or explicit points are not 2D | Route fitting decisions to `../core-embedding/SKILL.md` and use a 2D embedding for built-in plots. |
| `Labels must have a label for each sample` | Label array length differs from plotted rows | Compare `len(labels)` with `mapper.embedding_.shape[0]` before subsetting; apply the same subset mask to labels. |
| `Values must have a value for each sample` | Continuous values length differs from plotted rows | Compare `len(values)` with embedding rows before subsetting; apply the same subset mask to values. |
| `Size of subset points ... does not match number of input points` | `subset_points` length is not `n_samples` | Build a boolean mask or index selection from the original row order used to fit the mapper. |
| Hover text appears on the wrong points | `hover_data` row order or subset does not match the plotted embedding | Build hover data with one row per fitted sample, keep a row id column, and apply the same subset mask. |
| Search widget appears but does not find expected rows | Wrong `interactive_text_search_columns` or missing string-like fields | Pass searchable hover-data columns explicitly and include labels when needed. |
| No hover/search in a large interactive plot | The implementation switched to the datashaded HoloViews path | Subsample for hover/search, reduce width/height only if appropriate, or accept datashaded aggregate output. |
| Interactive plot does not display | Bokeh output mode was not configured | Use `umap.plot.output_notebook()` in notebooks or `umap.plot.output_file("plot.html")` in scripts before `umap.plot.show(plot)`. |
| `umap.plot.show` rejects the object type | Object is not a supported matplotlib axis, Bokeh figure, or HoloViews dynamic map | Pass the exact return value from `points`, `connectivity`, `diagnostic`, `interactive`, or `nearest_neighbour_distribution`, or use the backend's native display function. |
| Connectivity is very slow | Edge bundling, especially `edge_bundling='hammer'`, is expensive | Start with `edge_bundling=None`; sample rows or reduce graph size before hammer bundling. |
| Diagnostic fails on a saved coordinate array | Diagnostics need fitted mapper internals | Keep the fitted mapper object with `graph_`, `_raw_data`, and neighbor state, or refit. |
| Colors are misleading | Categories were passed as continuous values or continuous values as labels | Use `labels=` for categorical colors and `values=` for continuous maps. |
| Plot is too dense or misleading | Overplotting or inappropriate marker size | Let datashader handle large datasets, lower point alpha for small data, or use subsets for exploratory debugging. |

## Minimal Debug Sequence

1. Run:

   ```bash
   python sub-skills/plotting-diagnostics/scripts/check_plotting_stack.py --report
   ```

2. Verify base mapper state:

   ```python
   hasattr(mapper, 'embedding_'), mapper.embedding_.shape
   ```

3. Check row alignment before plotting:

   ```python
   n = mapper.embedding_.shape[0]
   assert len(labels) == n
   assert len(hover_data) == n
   assert len(subset_points) == n
   ```

4. Start from `umap.plot.points(mapper)` before adding labels, values, subsets, hover data, search, or edge bundling.
5. If optional extras cannot be installed, use `mapper.embedding_` as the stable fallback and plot/export it outside `umap.plot`.

## Interactive Hover Data with Subsets

A safe row-alignment pattern:

```python
hover_data = source_frame.assign(row_id=range(len(source_frame)))[['row_id', 'label', 'title']]
mask = source_frame['split'].eq('validation').to_numpy()

plot = umap.plot.interactive(
    mapper,
    labels=source_frame['label'].to_numpy(),
    hover_data=hover_data,
    subset_points=mask,
    interactive_text_search=True,
    interactive_text_search_columns=['label', 'title'],
)
```

Do not build `hover_data` after filtering unless you also filter the embedding and all labels/values the same way.

## Optional Dependency Policy

- Missing plot extras are not a base UMAP failure.
- Keep native `test_plot.py` optional unless the plot extra is installed.
- Do not install TensorFlow, Keras, TBB, GPU runtimes, or parametric extras for plotting-only failures.
