# Mesa visualization API reference

This reference distills the runtime visualization API surface needed for Mesa dashboards and safe debugging. It is self-contained; do not depend on external examples or source files while using it.

## Public imports

Common entry points are available from the visualization namespace:

```python
from mesa.visualization import (
    CommandConsole,
    Slider,
    SolaraViz,
    SpaceRenderer,
    make_plot_component,
    make_space_component,
)
from mesa.visualization.components import AgentPortrayalStyle, PropertyLayerStyle
```

`JupyterViz` is an alias of `SolaraViz`.

## Verified signatures

Use these signatures when checking compatibility with the installed Mesa version:

```python
SolaraViz(model, renderer=None, components=[], *, play_interval=100, render_interval=1, model_params=None, name=None, use_threads=False, **console_kwargs)
make_space_component(agent_portrayal=None, property_layer_portrayal=None, post_process=None, backend="matplotlib", **space_drawing_kwargs)
make_plot_component(measure, post_process=None, backend="matplotlib", page=0, **plot_drawing_kwargs)
SpaceRenderer(model, backend="matplotlib")  # backend must be "matplotlib" or "altair"
CommandConsole(model=None, additional_imports=None)
```

### `SolaraViz`

- `model` must be an initialized model instance or a Solara reactive containing an initialized model. Passing a model class is rejected.
- `renderer` is optional. If provided, it should be a `SpaceRenderer`; its rendered space component is inserted before the other components on page 0.
- `components` may contain component callables, Solara components, `(component, page)` tuples, or `"default"`. If a component is not paired with a page, page 0 is used.
- `components="default"` builds a default Altair space visualization on page 0.
- `play_interval` is milliseconds between automatic steps; `render_interval` is the number of model steps to advance per render update.
- `use_threads=True` runs stepping and visualization update work in separate threads. Increase `play_interval` if plots skip updates.
- If `CommandConsole` appears in `components`, it is moved into the sidebar. Pass `additional_imports` through `console_kwargs`, for example `SolaraViz(model, components=[CommandConsole], additional_imports={"np": np})`.

## Component builders

### `make_space_component`

`make_space_component(...)` returns a component function suitable for `components=[...]` in `SolaraViz`.

- `agent_portrayal(agent)` should return an `AgentPortrayalStyle` instance. Dict portrayals still work in some paths but are deprecated.
- `property_layer_portrayal` is a property-layer style specification. For rich property-layer control, prefer `SpaceRenderer.setup_property_layer(...)`.
- `backend` may be `"matplotlib"` or `"altair"`.
- `post_process` is called with a Matplotlib `Axes` for Matplotlib or an Altair `Chart` for Altair.
- Extra `space_drawing_kwargs` are forwarded to the backend space drawer. Examples include Matplotlib line styling (`color`, `linestyle`, `linewidth`, `alpha`) and Altair grid/chart styling (`grid_color`, `grid_dash`, `grid_width`, `grid_opacity`, `title`, `width`, `height`).

### `make_plot_component`

`make_plot_component(...)` returns a `(component, page)` tuple suitable for `components=[...]` in `SolaraViz`.

- `measure` may be a metric name string, a list/tuple of metric names, or a `{metric_name: color}` dictionary.
- The component reads `model.datacollector.get_model_vars_dataframe()` and plots the selected model-level columns.
- `page` controls the page/tab. Non-sequential page numbers create empty intermediate tabs, so prefer sequential pages.
- Matplotlib plot kwargs include `save_format`. Altair plot kwargs include `grid`.
- Match `post_process` to the backend: mutate/return an `Axes` for Matplotlib, or return a modified Altair `Chart`.

## Portrayal styles

### `AgentPortrayalStyle`

`AgentPortrayalStyle` is a dataclass for agent markers. Fields and defaults:

| Field | Default | Notes |
| --- | --- | --- |
| `x`, `y` | `None` | If both are `None`, renderers infer position from `agent.cell.position` / `agent.cell.coordinate` for discrete spaces or `agent.position` for continuous spaces. Set explicitly only when you need manual placement. |
| `color` | `"tab:blue"` | Accepts strings, tuples, or non-negative scalar values. Negative scalar colors raise `ValueError`. |
| `marker` | `"o"` | Matplotlib marker string/object or, for Matplotlib only, a valid image-file marker path. Altair maps common Matplotlib markers to Altair shapes. |
| `size` | `50` | Marker size; negative numeric values raise `ValueError`. |
| `zorder` | `1` | Draw ordering. Larger values appear above lower values. |
| `alpha` | `1.0` | Opacity. |
| `edgecolors` | `None` | Edge color for markers. Do not also pass conflicting drawing kwargs. |
| `linewidths` | `1.0` | Edge line width. |
| `tooltip` | `None` | Supported by Altair; ignored by Matplotlib with a warning. |

Use `style.update((field, value), ...)` for conditional changes. Updating an unknown field raises `AttributeError`.

### `PropertyLayerStyle`

`PropertyLayerStyle` is a dataclass for property-layer heatmaps/overlays. Fields and defaults:

| Field | Default | Notes |
| --- | --- | --- |
| `colormap` | `None` | Use for varying data. May be a named colormap. Mutually exclusive with `color`. |
| `color` | `None` | Use for a single-color overlay whose alpha is scaled by values. Mutually exclusive with `colormap`. |
| `alpha` | `0.8` | Overlay transparency. |
| `colorbar` | `True` | Shows legend/colorbar when supported. |
| `vmin`, `vmax` | `None` | Optional normalization bounds; otherwise inferred from layer data. |

Exactly one of `color` or `colormap` must be supplied. Supplying both or neither raises `ValueError`.

## `SpaceRenderer`

`SpaceRenderer` is the preferred API for layered space visuals.

- It looks for `model.grid` first, then `model.space`.
- Supported drawers include orthogonal grids, hex grids, networks, continuous spaces, and Voronoi grids.
- `setup_structure(**kwargs)` records space/grid drawing options and returns `self`.
- `setup_agents(agent_portrayal, **kwargs)` records the agent portrayal and agent drawing options and returns `self`.
- `setup_property_layer(property_layer_portrayal)` accepts a callable returning `PropertyLayerStyle`, a `PropertyLayerStyle` instance, or a legacy dict. Callable style is preferred.
- `draw_structure()`, `draw_agents()`, and `draw_property_layer()` draw individual layers and cache their backend output.
- `render()` draws any configured layers not already drawn and returns `self`.
- `post_process` may be set to a callable. Matplotlib receives an `Axes`; Altair receives a `Chart`.
- Recreate the renderer when manually replacing the model instance. `SolaraViz` handles its reset path; custom code should avoid keeping cached meshes tied to an old model.

Backend reminders:

- Matplotlib is best for static/headless rendering, Matplotlib image markers, direct `Axes` customization, and hex-grid property layers.
- Altair is best for browser-native charts, tooltips, and interactive line plots.
- The simple Altair space component is narrower than `SpaceRenderer`; use `SpaceRenderer` when network, Voronoi, hex, or richer property-layer behavior matters.

## User parameters and widgets

`model_params` controls the sidebar widgets and reset-time constructor kwargs.

Accepted value types are:

| Value form | Behavior |
| --- | --- |
| `Slider(label, value, min, max, step, dtype=None)` | Numeric slider. Float values or `dtype=float` create a float slider; otherwise an int slider. |
| `{"type": "SliderInt", "value": ..., "min": ..., "max": ..., "step": ..., "label": ...}` | Integer slider dict. |
| `{"type": "SliderFloat", ...}` | Float slider dict. |
| `{"type": "Select", "value": ..., "values": [...], "label": ...}` | Dropdown/select widget. |
| `{"type": "Checkbox", "value": bool, "label": ...}` | Boolean checkbox. |
| `{"type": "InputText", "value": ..., "label": ...}` | Text input; Mesa attempts int/float conversion on change. Useful for seeds. |
| Primitive `int`, `float`, `bool`, or `str` | Fixed constructor value; no editable widget. |

Critical contract: `SolaraViz` creates reset models as `type(model)(**model_parameters.value)`. Therefore the model constructor must accept keyword arguments matching `model_params` keys, accepted scenario fields handled by the model, `seed`/`rng`, or `**kwargs`. Positional-only model setup is not compatible with SolaraViz resets.
