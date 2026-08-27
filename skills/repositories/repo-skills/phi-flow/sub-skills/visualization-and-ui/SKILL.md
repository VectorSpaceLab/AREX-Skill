---
name: visualization-and-ui
description: "Route plotting, display, UI controls, and scene-backed scalar
  visualization through the current phi.vis public APIs."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# Visualization and UI

Use this sub-skill when a task involves rendering fields, tensors, geometries, histograms, animations, scalar training logs, or interactive display/control surfaces through `phi.vis`.

## First decisions

1. **Use the current public surface.** Prefer `import phi.vis as vis`. `from phi.flow import *` gives `show`, `plot`, and `control`, but not `vis.close`, `load_scalars`, `plot_scalars`, `show_hist`, `overlay`, or `write_image`; import `phi.vis` explicitly whenever you need the figure closer or scalar-log helpers.
2. **Do not call `view()`.** Current `phi.flow` and `phi.vis` do not export a public `view` symbol. Older visualization, Dash, and console docs still contain `view(...)` examples; translate those to `vis.show(...)` or `vis.plot(...)` and keep any `control(...)` calls as script-level assignment declarations.
3. **Choose a renderer deliberately.** Use Matplotlib for stable static/headless 1D and 2D plots, Plotly for browser/notebook-friendly and 3D plots, and treat console/ascii plotting as unavailable for verification-critical workflows in this version.
4. **Close figures in scripts and tests.** Store the result of `vis.plot(...)`, save or inspect it, then call `vis.close(fig)`. For `vis.show(...)`, expect a display side effect; avoid it in headless automation unless `MPLBACKEND=Agg` is set.
5. **Use scene scalars through `load_scalars()`.** Prefer `curve = vis.load_scalars(scene, "loss")` followed by `vis.plot(curve, ...)`. `plot_scalars()` remains available but is deprecated and Matplotlib-only.

## Verified public entry points

- `vis.show(*fields, lib=None, row_dims=None, col_dims=batch, animate=None, overlay="overlay", title=None, size=None, same_scale=True, log_dims="", show_color_bar=True, color=None, alpha=1.0, err=0.0, frame_time=100, repeat=True, plt_params=None, max_subfigures=20)`
- `vis.plot(...)` has the same live signature family as `show(...)` and returns a native figure object or animation instead of immediately displaying it.
- `vis.close(figure=None)` closes a figure created by `vis.plot()`; without an argument, it closes the most recent `phi.vis` figure.
- `vis.show_hist(data, bins=math.instance(bins=20), weights=1, same_bins=None)` builds a histogram and displays it through `show()`.
- `vis.control(value, range=None, description="", **kwargs)` only accepts primitive `int`, `float`, `bool`, or `str` values and must be used in a variable assignment statement.
- `vis.load_scalars(scene, name, prefix="log_", suffix=".txt", x="steps", entries_dim=(iterationˢ), batch_dim=(batchᵇ))` reads `log_<name>.txt` curves from a single scene path or `Scene`.
- `vis.plot_scalars(*args, **kwargs)` delegates to the Matplotlib scalar plot helper and emits a deprecation warning; use `load_scalars()` plus `plot()` for new code.

## Route by task

- **Static field/tensor/geometry figure:** read [workflows.md](references/workflows.md#static-field-tensor-and-geometry-plots), then use `vis.plot(..., lib="matplotlib")` or `lib="plotly"`.
- **Quick human display:** use `vis.show(field_or_tensor, lib="matplotlib" | "plotly")`; for an existing figure, call `vis.show(lib=...)` only after a previous `vis.plot()`.
- **Animations:** pass `animate="time"` or another dimension to `vis.plot()` / `vis.show()` and set `frame_time`; prefer Plotly or notebook display for interactive review, Matplotlib for script-side objects.
- **Subplots / batches:** use `row_dims`, `col_dims`, `overlay`, `title`, `same_scale`, `max_subfigures`, and `size`; for many batches, slice or raise `max_subfigures` deliberately.
- **Scalar logs from scenes:** read [workflows.md](references/workflows.md#scene-backed-scalar-curves); keep log files named `log_<name>.txt`.
- **Controls:** keep `learning_rate = vis.control(...)` near the top-level script scope; do not rely on `control()` alone to launch a GUI.
- **Problems or stale examples:** read [troubleshooting.md](references/troubleshooting.md).

## Smoke check

Run the bundled smoke helper in an environment where `phiflow` is installed:

```bash
python sub-skills/visualization-and-ui/scripts/plot_smoke.py
```

The helper verifies the `show`/`plot` signature family, absence of public `view()`, Matplotlib and Plotly figure creation, `control()` assignment semantics, histogram display path, scene scalar loading, deprecated `plot_scalars()`, and figure cleanup.
