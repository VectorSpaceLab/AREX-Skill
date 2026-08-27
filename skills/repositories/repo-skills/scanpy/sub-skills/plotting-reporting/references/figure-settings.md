# Figure Settings, Saving, and Headless Operation

Scanpy plotting is Matplotlib-based. In automated agents, scripts, CI, and servers without a display, configure Matplotlib before importing `pyplot`, disable automatic display, save explicit figure objects, and close figures after writing.

## Headless-safe setup

Set the backend first:

```python
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import scanpy as sc
```

Then use non-interactive Scanpy calls:

```python
sc.settings.autoshow = False
ax = sc.pl.umap(adata, color="cluster", show=False)
ax.figure.savefig("umap_cluster.png", dpi=200, bbox_inches="tight")
plt.close(ax.figure)
```

Use `scripts/scanpy_headless_plot_smoke.py` to verify a minimal environment can render Scanpy plots with `Agg` and a tiny synthetic `AnnData`.

## `show`, `return_fig`, `ax`, and `save`

| Pattern | Recommended use | Return behavior |
| --- | --- | --- |
| `show=False` | Scripts, tests, agents, and post-processing | Many Scanpy functions return a Matplotlib `Axes`, list of axes, axes dict/grid, or plot object depending on API. |
| `return_fig=True` | Full figure/object customization | Embedding APIs can return a `Figure`; dotplot/matrixplot/stacked violin return Scanpy plot class objects. |
| `ax=...` | Draw a single panel into an existing Matplotlib axis | Use only for one-panel calls. Multi-panel embedding calls reject `ax`. |
| `save=True` or `save='suffix'` | Maintaining old Scanpy-style saves | Uses Scanpy-managed names under `sc.settings.figdir`; prefer explicit `savefig` for new code. |
| `show=None` | Interactive notebooks using Scanpy defaults | Uses `sc.settings.autoshow`; avoid in CI and non-interactive agents. |

When `save` is a string, Scanpy appends it to the plot-specific write key and detects `.svg`, `.pdf`, or `.png` extensions. Files are written under `sc.settings.figdir`; when no extension is supplied, Scanpy uses `sc.settings.file_format_figs`. For exact paths, always save from the returned Matplotlib or plot object.

## `sc.settings` plotting fields

| Setting | Purpose | Agent guidance |
| --- | --- | --- |
| `sc.settings.figdir` | Directory used by Scanpy autosave and `save=` | Set to a caller-provided output directory only when maintaining Scanpy-managed saving. |
| `sc.settings.autoshow` | Whether plots display by default | Set `False` in scripts, CI, and non-interactive agents. |
| `sc.settings.autosave` | Whether plots save automatically by default | Usually keep `False`; explicit saving is clearer. |
| `sc.settings.plot_suffix` | Suffix appended to Scanpy-managed filenames | Useful only when using `save=` or autosave. |
| `sc.settings.file_format_figs` | Default extension for Scanpy-managed saving | Set with `sc.set_figure_params(format='png')` or assign directly. |
| `sc.settings.verbosity` | Logging verbosity | Increase when diagnosing warnings or file output. |

## `sc.set_figure_params`

Use `sc.set_figure_params(...)` for session-level Scanpy/Matplotlib defaults:

```python
sc.set_figure_params(
    dpi=100,
    dpi_save=200,
    frameon=False,
    vector_friendly=True,
    fontsize=12,
    format="png",
    transparent=False,
)
```

Common choices:

- `dpi` affects displayed notebook figures.
- `dpi_save` affects saved figure resolution through Scanpy-managed saves and Matplotlib defaults.
- `frameon` controls default frames around scatter plots.
- `vector_friendly=True` can make vector exports smaller by rasterizing dense scatter points within vector files.
- `format` sets `sc.settings.file_format_figs` for Scanpy-managed saves.
- `facecolor` and `transparent` control figure backgrounds.

## Robust export recipes

Single-axis embedding:

```python
ax = sc.pl.umap(adata, color="cluster", show=False)
ax.set_title("Clusters")
ax.figure.savefig("clusters.png", dpi=200, bbox_inches="tight")
plt.close(ax.figure)
```

Multi-panel embedding:

```python
axes = sc.pl.umap(adata, color=["cluster", "GeneA"], show=False)
fig = axes[0].figure if isinstance(axes, list) else axes.figure
fig.savefig("umap_panels.png", dpi=200, bbox_inches="tight")
plt.close(fig)
```

Class-backed dotplot:

```python
plot = sc.pl.dotplot(adata, markers, groupby="cluster", return_fig=True)
plot.style(cmap="Reds").legend(colorbar_title="Mean expression")
plot.make_figure()
plot.fig.savefig("marker_dotplot.png", dpi=200, bbox_inches="tight")
plt.close(plot.fig)
```

Legacy Scanpy-managed saving:

```python
from pathlib import Path
sc.settings.figdir = Path("figures")
sc.settings.autoshow = False
sc.settings.file_format_figs = "png"
sc.pl.umap(adata, color="cluster", save="_clusters.png")
```

This writes into `sc.settings.figdir` with a plot-specific prefix plus suffix. Use explicit `savefig` when exact output paths matter.

## Batch plotting hygiene

- Pass `show=False` for every plotting call in loops.
- Save each figure immediately and close it.
- Avoid global `autosave=True` in libraries because it can produce unexpected files.
- Avoid mixing `layer` with `use_raw=True`; choose one expression source per figure.
- Pass explicit palettes or set `adata.uns[f'{key}_colors']` when categorical colors must remain stable across figures.
- Capture warnings in automated reporting; Scanpy warnings often identify missing keys, deprecated `save=`, or save/display behavior.
