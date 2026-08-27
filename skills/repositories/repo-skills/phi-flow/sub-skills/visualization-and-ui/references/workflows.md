# Visualization workflows

## Public surface summary

The current `phi.vis` package exports the following user-facing visualization entry points:

- `show(...)`
- `plot(...)`
- `close(...)`
- `control(...)`
- `show_hist(...)`
- `load_scalars(...)`
- `plot_scalars(...)` (deprecated wrapper)
- `overlay(...)`
- `write_image(...)` / `savefig(...)`

There is no public `view()` symbol in `phi.flow` or `phi.vis` in this version. Replace stale `view(...)` examples with `show(...)` or `plot(...)`.

## Renderer choices

| Renderer | Best for | Returns | Notes |
| --- | --- | --- | --- |
| Matplotlib | stable script output, tests, saved images, most 1D/2D plots | `matplotlib.figure.Figure` | Good default for headless use; pair with `MPLBACKEND=Agg` in automation. |
| Plotly | browser / notebook display, 3D figures, interactive inspection | `plotly.graph_objs.Figure` | Requires Plotly; Dash is the web UI note, but plain `plot(..., lib="plotly")` is the key rendering path. |
| Console / ascii | legacy text UI references | text-like figure object is not reliably available in this version | Current public `plot(lib="console")` is not a stable working path; treat console docs as stale unless the package version is updated. |

## Static field, tensor, and geometry plots

Use `plot()` when you want the figure object and `show()` when you want the display side effect.

```python
import phi.vis as vis
from phi.field import CenteredGrid
from phi.geom import Box
from phi import math

field = CenteredGrid(
    lambda x: math.sin(x.vector[0] * 6.283185307179586),
    0,
    x=64,
    y=32,
    bounds=Box(x=1, y=1),
)

fig = vis.plot(field, lib="matplotlib", show_color_bar=False, title="Field")
vis.write_image("field.png", fig, close=True)
```

Use Plotly when you need browser-friendly viewing or 3D figures:

```python
fig = vis.plot(field, lib="plotly", show_color_bar=False)
fig.write_html("field.html")
vis.close(fig)
```

### Useful plot layout arguments

- `row_dims` and `col_dims`: split batch dimensions into a grid of subplots.
- `overlay`: draw several fields in the same subplot.
- `animate`: animate a time dimension.
- `same_scale`: share axis limits across subplots.
- `log_dims`: logarithmic axes.
- `title`, `size`, `color`, `alpha`, `err`, `frame_time`, `repeat`.

### Practical defaults

- Prefer `show_color_bar=False` for dense subplot grids.
- Use `same_scale=False` only when figures need independent axes.
- For large batched inputs, slice first or increase `max_subfigures` deliberately.

## Figure lifecycle

1. Create the figure with `vis.plot(...)`.
2. Save or inspect the returned native figure.
3. Close it with `vis.close(fig)`.
4. When reusing the most recent figure, `vis.close()` without arguments closes the last `phi.vis` figure.

Avoid importing the figure closer from `phi.flow` through a wildcard import; that name can resolve to a different math helper.

## Quick display

`show()` shares the same live signature family as `plot()`.

- `vis.show(field)` plots and displays immediately.
- `vis.show(lib="matplotlib")` displays the most recent figure created by `vis.plot(...)`.

Use `show()` in interactive notebooks or local scripts where a display backend is available. For automation, prefer `plot()` plus `close()`.

## Histograms

Use `show_hist()` for a quick histogram of a tensor:

```python
hist = math.random_uniform(math.spatial(samples=128))
vis.show_hist(hist)
```

If you need a saved figure or custom layout, build the histogram yourself and pass the result through `plot()` instead.

## Scene-backed scalar curves

`load_scalars(scene, name, ...)` reads scalar logs written as `log_<name>.txt` inside a `Scene` directory.

### Single curve

```python
from phi.field import Scene
import phi.vis as vis

scene = Scene.at("path/to/sim_000000")
loss = vis.load_scalars(scene, "loss")
fig = vis.plot(loss, lib="matplotlib", title="Loss")
```

### Multiple scenes

`load_scalars()` only accepts one scene or one scene path at a time. To load many scenes, map over them:

```python
from phi import math
losses = math.map(lambda s: vis.load_scalars(s, "loss"), scenes)
```

### Time-based curves

Use `x="time"` when the scene also contains `log_step_time.txt`. The helper accumulates step times into a time axis.

### Signature note

The current signature exposes `prefix` and `suffix`, but the live source reads the default `log_<name>.txt` pattern directly. Keep the default naming unless you have verified the exact file names in your target package version.

## Deprecated scalar plotting wrapper

`plot_scalars()` still works as a convenience wrapper over Matplotlib scalar plots, but it is deprecated.

Recommended migration:

1. `curve = vis.load_scalars(scene, "loss")`
2. `fig = vis.plot(curve, lib="matplotlib")`
3. `vis.close(fig)`

If you must keep `plot_scalars()`, pass a concrete color choice such as `colors=0` or a color string in the verified version.

## Controls

`control()` is for top-level script assignments only:

```python
learning_rate = vis.control(1e-3, (1e-5, 1e-1), description="Learning rate", log=True)
```

Rules:

- use it in an assignment statement
- only pass `int`, `float`, `bool`, or `str`
- keep the variable in script scope so the GUI or application harness can discover it
- do not depend on `control()` to create a standalone viewer; there is no public `view()` launcher in this version

## Routing hints

- If the user wants a script-only smoke check, use the bundled `plot_smoke.py` helper.
- If the user wants guidance on stale docs, point them from `view()` examples to `show()` and `plot()`.
- If the user wants a scene log plot, prefer `load_scalars()` and `plot()` over `plot_scalars()`.
