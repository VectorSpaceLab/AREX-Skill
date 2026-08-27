# Mesa visualization troubleshooting

Start by separating Python import/signature health from browser/front-end health. The bundled `scripts/check_visualization_stack.py` is safe to run first because it does not start a Solara server or open a browser.

## Missing visualization extras

Symptoms:

- `ModuleNotFoundError: No module named 'solara'`
- `ModuleNotFoundError: No module named 'altair'`
- `ModuleNotFoundError: No module named 'matplotlib'`
- `mesa.visualization` import fails before your model code runs.

Actions:

1. Install visualization extras for the environment that will run the dashboard: `mesa[viz]`.
2. Use `mesa[rec]` when you also need the recommended network dependency bundle.
3. Re-run `python scripts/check_visualization_stack.py --imports viz --pretty` or `--require-viz --strict` and inspect JSON before debugging browser UI.
4. Use `--imports network` or `--require-network` when network-space readiness matters.
5. Do not use browser/e2e tests as the baseline readiness check; they require extra front-end tooling.

Notes:

- Mesa's visualization modules import optional packages eagerly. A missing `solara` or `altair` can block `SolaraViz`, `SpaceRenderer`, or component-builder imports.
- If an older Mesa version lacks the verified signatures in this sub-skill, upgrade Mesa rather than adapting new code to older visualization APIs.

## Solara import succeeds but the front-end is blank or unstable

Symptoms:

- Python imports work, but the notebook cell displays nothing.
- A browser page opens but stays blank.
- Solara widgets appear but controls do not update plots.

Actions:

1. Confirm the Python side first with `scripts/check_visualization_stack.py`.
2. Confirm the dashboard creates a `page = SolaraViz(...)` object and that the notebook cell returns `page` as the final expression.
3. For custom components, call `update_counter.get()` inside the component so Solara observes model updates.
4. Use Matplotlib's object-oriented API (`Figure`, `ax.*`) inside custom components instead of pyplot state.
5. Reduce `use_threads` complexity while debugging. If threaded play skips plot updates, increase `play_interval`.
6. Treat browser or Playwright tests as optional follow-up checks after Python imports, signatures, and safe component construction pass.

## `model_params` constructor mismatch

Critical warning: `SolaraViz` resets models by calling `type(model)(**model_parameters.value)`. The model constructor must accept keyword arguments matching `model_params` keys.

Symptoms:

- `ValueError: Missing required model parameter: ...`
- `ValueError: Invalid model parameter: ...`
- A model works when instantiated manually with positional arguments but fails after pressing Reset.
- A slider/select value is ignored after reset.

Actions:

1. Make the model constructor keyword-compatible:

   ```python
   class MyModel(Model):
       def __init__(self, *, width=20, height=20, n_agents=50, rng=None):
           super().__init__(rng=rng)
   ```

2. Ensure every editable and fixed `model_params` key is accepted by `__init__`, a scenario object handled by the model, `seed`/`rng`, or `**kwargs`.
3. Do not pass raw Solara widget objects as `model_params` values. Use Mesa's `Slider`, primitive fixed values, or widget spec dictionaries.
4. If using scenarios, keep model constructor support for a `scenario=` keyword unless your model explicitly converts scenario fields.
5. Route constructor or step semantics to [model-core](../../model-core/SKILL.md) if fixing the visualization layer requires model API changes.

## Portrayal style errors

Symptoms and fixes:

- `ValueError: Specify either 'color' or 'colormap', not both.` Use exactly one on `PropertyLayerStyle`.
- `ValueError: Specify one of 'color' or 'colormap'`. Supply one style route for every property layer you display.
- Negative marker `size` or negative scalar `color` on `AgentPortrayalStyle` raises `ValueError`; clamp or validate data before creating the style.
- Dict-based agent portrayal emits deprecation warnings. Return `AgentPortrayalStyle` instead.
- Dict-based property-layer portrayal is legacy. Prefer a callable returning `PropertyLayerStyle` or `None` per layer name.
- `tooltip` is ignored by Matplotlib. Use Altair if tooltips are required.
- Matplotlib image markers require valid runtime file paths and can be performance-intensive. Do not rely on image paths from external examples.
- Altair maps common Matplotlib marker aliases to Altair shapes. Unsupported marker values may warn or fall back; choose common shapes for browser dashboards.
- Passing `edgecolors` / `linewidths` in both portrayal and drawing kwargs can conflict; keep those settings in one place.

## Empty plots or missing DataCollector reporters

Symptoms:

- Plot component renders empty axes.
- `KeyError` or missing-column errors when plotting a measure.
- Plot updates lag behind model state.

Actions:

1. Confirm `model.datacollector` exists and implements `get_model_vars_dataframe()`.
2. Confirm the measure name passed to `make_plot_component` exactly matches a model reporter column.
3. Ensure the model calls `datacollector.collect(self)` at initialization or in every `step()` before the plot is expected to update.
4. Use a dict or list for multiple measures only after all columns exist.
5. Route reporter creation and collection-frequency questions to [analysis-experiments](../../analysis-experiments/SKILL.md).

## Backend choice and space limitations

Choose Matplotlib when:

- You need image markers, custom `Axes` calls, static/headless rendering, or hex-grid property-layer overlays.
- You want to debug rendering without browser interactivity.

Choose Altair when:

- You need browser-native charts, tooltips, interactive time-series plots, or chart post-processing.
- You prefer declarative chart configuration.

Common backend mistakes:

- Passing a Matplotlib `Axes` post-processing function to an Altair backend, or returning an Altair `Chart` from a Matplotlib post-process hook.
- Using Altair for hex-grid property-layer visualization. Switch to Matplotlib.
- Using the simple Altair `make_space_component` path for a space type it does not support. Prefer `SpaceRenderer` for richer space support.
- Reusing a renderer after manually constructing a new model instance. Recreate the renderer so it points at the new `grid` or `space`.
- Calling `SpaceRenderer(model, backend=None)` or any backend other than `"matplotlib"` or `"altair"`.

Route space topology, property-layer creation, and cell/neighbor design issues to [spaces](../../spaces/SKILL.md).

## Command console issues

Symptoms:

- `CommandConsole` does not appear in the main component grid.
- Console code cannot access helper objects.

Actions:

- This is expected layout: if included in `components`, `CommandConsole` is moved to the sidebar.
- Expose helper objects with `additional_imports={"name": object}` in `SolaraViz`.
- Keep the console optional and expose only trusted objects; it is an interactive Python console for the dashboard session.

## Browser/e2e checks are optional

Browser-based checks are useful only after the Python stack and component construction are healthy. They usually require Solara front-end support plus browser automation tooling, so they are not a baseline requirement for this sub-skill. Use them only when a task explicitly asks for browser-level behavior, screenshots, or end-to-end interaction checks.
