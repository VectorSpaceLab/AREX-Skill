# Mesa visualization workflows

These recipes are safe patterns for authoring browser/notebook dashboards and debugging visual components without relying on external examples.

## 1. Basic SolaraViz dashboard

Use this when you already have a Mesa model instance and want a space view plus one or more plots.

```python
from mesa.visualization import Slider, SolaraViz, SpaceRenderer, make_plot_component
from mesa.visualization.components import AgentPortrayalStyle


def agent_portrayal(agent):
    return AgentPortrayalStyle(color="tab:blue", size=50)

model_params = {
    "rng": {"type": "InputText", "value": 42, "label": "Random Seed"},
    "n_agents": Slider("Agents", value=50, min=1, max=200, step=1),
    "width": 20,
    "height": 20,
}

model = MyModel(n_agents=50, width=20, height=20, rng=42)
renderer = (
    SpaceRenderer(model, backend="matplotlib")
    .setup_agents(agent_portrayal)
    .render()
)

CountPlot = make_plot_component("AgentCount", page=1)
page = SolaraViz(model, renderer, components=[CountPlot], model_params=model_params)
page
```

Checklist:

- Instantiate the model with keyword arguments.
- Make every `model_params` key acceptable to `MyModel.__init__`, the model scenario, `seed`/`rng`, or `**kwargs`.
- Use the exact reporter name in `make_plot_component`.

## 2. Dynamic agent portrayal

Use agent attributes to change visual style per step. Prefer returning `AgentPortrayalStyle`; dict portrayals are legacy.

```python
from mesa.visualization.components import AgentPortrayalStyle


def agent_portrayal(agent):
    style = AgentPortrayalStyle(color="tab:orange", size=40, marker="o")
    if getattr(agent, "wealth", 0) > 0:
        style.update(("color", "tab:blue"), ("size", 90))
    if getattr(agent, "is_alert", False):
        style.update(("edgecolors", "black"), ("linewidths", 2), ("zorder", 3))
    return style
```

Guidance:

- Leave `x` and `y` as `None` unless you need manual placement; renderers infer common Mesa positions.
- Use `tooltip={...}` for Altair dashboards; Matplotlib ignores tooltips.
- For Matplotlib image markers, use a path that exists in the runtime project, not a path copied from an example checkout.
- For Altair, prefer common marker names such as `"circle"`, `"square"`, `"diamond"`, `"triangle-up"`, or Matplotlib aliases Mesa maps to them.

## 3. Plots from `DataCollector`

`make_plot_component` consumes `model.datacollector.get_model_vars_dataframe()`.

```python
GiniPlot = make_plot_component("Gini")
PopulationPlot = make_plot_component({"Wolves": "tab:orange", "Sheep": "tab:cyan"}, page=1)
MultiPlot = make_plot_component(["Susceptible", "Infected", "Recovered"], backend="altair", grid=True)
```

Matplotlib post-processing receives an `Axes`:

```python
def style_axes(ax):
    ax.set_title("Gini over time")
    ax.set_xlabel("Step")
    ax.set_ylabel("Gini")
    ax.legend(loc="best")

GiniPlot = make_plot_component("Gini", post_process=style_axes)
```

Altair post-processing receives a `Chart` and must return a chart:

```python
def style_chart(chart):
    return chart.properties(width=450, height=350).configure_legend(orient="right")

StatePlot = make_plot_component({"Infected": "red", "Recovered": "gray"}, backend="altair", post_process=style_chart)
```

If the plot is empty or raises on a missing column, route metric/report creation to [analysis-experiments](../../analysis-experiments/SKILL.md).

## 4. `SpaceRenderer` with structure, agents, and property layers

Use `SpaceRenderer` when you need explicit layer control or property layers.

```python
from mesa.visualization import SpaceRenderer
from mesa.visualization.components import AgentPortrayalStyle, PropertyLayerStyle


def agent_portrayal(agent):
    return AgentPortrayalStyle(color="tab:red" if agent.energy < 1 else "tab:green", size=35)


def property_layer_portrayal(layer_name):
    if layer_name == "elevation":
        return PropertyLayerStyle(colormap="viridis", alpha=0.6, colorbar=True)
    if layer_name == "hazard":
        return PropertyLayerStyle(color="red", alpha=0.5, vmin=0, vmax=1, colorbar=True)
    return None

renderer = (
    SpaceRenderer(model, backend="matplotlib")
    .setup_structure(color="gray", linestyle=":", linewidth=0.8, alpha=0.5)
    .setup_agents(agent_portrayal)
    .setup_property_layer(property_layer_portrayal)
)
renderer.render()
```

Backend-specific notes:

- Matplotlib structure kwargs are ordinary line/figure styling options such as `color`, `linestyle`, `linewidth`, `alpha`, `figsize`, and `dpi`.
- Altair structure kwargs include grid/chart styling such as `grid_color`, `grid_dash`, `grid_width`, `grid_opacity`, `title`, `width`, and `height`.
- Property-layer portrayals should return `PropertyLayerStyle` or `None` per layer name.
- Hex-grid property layers should use the Matplotlib backend.
- If you manually create a new model instance, also recreate the renderer so cached meshes reference the new space.

## 5. Component layout, pages, command console, and custom components

`components` accepts bare component callables on page 0 or `(component, page)` tuples. `make_plot_component` already returns a `(component, page)` pair.

```python
SpaceGraph = make_space_component(agent_portrayal, backend="matplotlib")
CountPlot = make_plot_component("AgentCount", page=1)

page = SolaraViz(
    model,
    components=[SpaceGraph, CountPlot],
    model_params=model_params,
    name="My Mesa Dashboard",
)
```

Custom components must be Solara components and should subscribe to Mesa's update counter:

```python
import solara
from matplotlib.figure import Figure
from mesa.visualization.utils import update_counter


@solara.component
def WealthHistogram(model):
    update_counter.get()
    fig = Figure()
    ax = fig.subplots()
    ax.hist([agent.wealth for agent in model.agents], bins=10)
    ax.set_title("Agent wealth")
    solara.FigureMatplotlib(fig)
```

Use the object-oriented Matplotlib API (`Figure`, `ax.*`) inside Solara components; avoid pyplot stateful calls in custom components.

To add the optional command console:

```python
import numpy as np
from mesa.visualization import CommandConsole

page = SolaraViz(
    model,
    renderer,
    components=[CountPlot, CommandConsole],
    model_params=model_params,
    additional_imports={"np": np},
)
```

When included in `components`, `CommandConsole` appears in the sidebar. Expose only trusted objects in `additional_imports`.

## 6. Safe headless validation

Use the bundled script to inspect an installed Mesa visualization stack without launching a server, opening a browser, importing runtime examples, or running e2e tests.

```bash
python scripts/check_visualization_stack.py --imports all --pretty
python scripts/check_visualization_stack.py --require-viz --strict
python scripts/check_visualization_stack.py --imports network --require-network
```

Useful JSON fields:

- `status`: `ok`, `degraded`, or `failed`.
- `mesa`: top-level Mesa import and version.
- `core.mesa_visualization`: package-root visualization import health.
- `core.imports`: import health for `SolaraViz`, `SpaceRenderer`, `make_space_component`, `make_plot_component`, `AgentPortrayalStyle`, and `PropertyLayerStyle`.
- `core.signatures`: signature compatibility for the same runtime objects.
- `core.portrayal_styles`: dataclass field presence for `AgentPortrayalStyle` and `PropertyLayerStyle`.
- `core.style_runtime_checks`: quick style behavior checks such as update mutation and validation failures.
- `network`: extra checks when `--require-network` is used.
- `required_failures` and `strict_failures`: why the probe failed when a requirement is not met.
- `optional_imports`: requested optional dependency imports and versions.

Use `--imports viz` for `solara`, `matplotlib`, and `altair`, `--imports network` for `networkx`, and `--imports all` for the full optional set. `--require-viz` and `--require-network` convert those readiness checks into required gates. `--strict` returns a non-zero exit code on missing requested imports, core visualization API failures, or signature mismatches.
