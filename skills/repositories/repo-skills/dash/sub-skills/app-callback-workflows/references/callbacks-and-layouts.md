# Callbacks and Layouts

## When to read

Read this for Dash app construction, layout/component rules, callback dependency
objects, callback context, partial updates, and pattern-matching callbacks.

## Layouts

A Dash layout is a tree of components and primitive children:

```python
from dash import Dash, html, dcc

app = Dash(__name__)
app.layout = html.Div([
    html.H1("Example"),
    dcc.Input(id="input", value="Dash"),
    html.Div(id="output"),
])
```

Facts to rely on:

- Built-in component modules are imported from `dash`: `from dash import html,
  dcc, dash_table`.
- Components serialize to JSON-like objects with `type`, `namespace`, and
  `props`; the renderer resolves React components from that pair.
- Components can have string IDs or dictionary IDs. Dictionary IDs support
  wildcard matching.
- A dynamic layout can be a callable assigned to `app.layout`; it is evaluated
  when the layout is served.
- Use `validation_layout` or `suppress_callback_exceptions=True` when callbacks
  reference components that are not in the initial layout because pages or
  conditional rendering add them later.

## Callback dependencies

| Object | Meaning | Notes |
| --- | --- | --- |
| `Output(component_id, property, allow_duplicate=False)` | Property a callback writes | Output supports `MATCH` and `ALL`; duplicate outputs need explicit handling. |
| `Input(component_id, property, allow_optional=False)` | Property that triggers a callback | Supports `MATCH`, `ALL`, and `ALLSMALLER`. |
| `State(component_id, property, allow_optional=False)` | Property read without triggering | Use State to break unnecessary callback triggering. |
| `ClientsideFunction(namespace, function_name)` | Reference to a JS function under `window.dash_clientside` | Namespace cannot start with `_dashprivate_` and cannot be `PreventUpdate` or `no_update`. |

## Callback registration

Use `@app.callback` when the app object is available:

```python
from dash import Input, Output

@app.callback(Output("output", "children"), Input("input", "value"))
def update(value):
    return f"Value: {value}"
```

Use `@dash.callback` in modules where the app instance should not be imported:

```python
from dash import callback, Input, Output

@callback(Output("output", "children"), Input("input", "value"))
def update(value):
    return value
```

Useful callback keyword arguments include:

- `prevent_initial_call=True`: skip initial execution for a callback.
- `on_error=callable`: convert exceptions into a custom output or logging path.
- `api_endpoint="/path"`: expose a callback through a direct HTTP endpoint.
- `optional=True`: mark dependencies optional for initial layout checks.
- `background=True`, `websocket=True`, `persistent=True`, `mcp_enabled=...`:
  route to [server backends and async](../../server-backends-and-async/SKILL.md)
  because these change runtime behavior.

## Return control

Use these primitives when a callback should not update normally:

```python
from dash import no_update, Patch
from dash.exceptions import PreventUpdate

@app.callback(Output("out", "children"), Input("input", "value"))
def update(value):
    if value is None:
        raise PreventUpdate       # update nothing
    if value == "unchanged":
        return no_update          # preserve this output
    return value
```

`Patch` is for partial property updates, commonly large list/dict-like props.
Use it when the callback should modify a subset instead of returning a full
replacement object.

## Callback context

Inside callbacks, use `dash.ctx` or `dash.callback_context`:

```python
from dash import ctx

@app.callback(Output("out", "children"), Input("a", "n_clicks"), Input("b", "n_clicks"))
def route(a, b):
    if ctx.triggered_id == "a":
        return "A clicked"
    if ctx.triggered_id == "b":
        return "B clicked"
    return "Initial"
```

Useful context properties:

| Property | Use |
| --- | --- |
| `triggered` | Backward-compatible list of trigger records. It is falsy on initial call. |
| `triggered_id` | ID of the component that triggered the callback; may be a dict for pattern IDs. |
| `triggered_prop_ids` | Map of `id.property` keys to component IDs. Use for multiple trigger props. |
| `args_grouping` | Flexible callback argument metadata, including IDs and trigger booleans. |
| `outputs_grouping` | Output grouping metadata. |
| `record_timing` | Add server timing entries for dev tools. |
| `response` | Access backend response object for cookies/headers. |
| `custom_data` | Data injected by hooks. |
| `websocket` | WebSocket callback interface; see the server backend sub-skill. |

## Pattern-matching callbacks

Use dictionary IDs when components are generated dynamically:

```python
from dash import MATCH, ALL, Input, Output, State

@app.callback(
    Output({"type": "item-output", "index": MATCH}, "children"),
    Input({"type": "item-input", "index": MATCH}, "value"),
)
def update_one(value):
    return value

@app.callback(
    Output("summary", "children"),
    Input({"type": "item-input", "index": ALL}, "value"),
)
def summarize(values):
    return ", ".join(v or "" for v in values)
```

Decision guide:

- `MATCH`: one generated input maps to one generated output with the same key
  set.
- `ALL`: collect every component matching the key pattern.
- `ALLSMALLER`: compare a dynamic component with previous/lower-indexed
  components.

## Layout and callback validation

Dash validates callbacks against the layout by default. If a callback references
components not present during initial validation:

1. Prefer a `validation_layout` containing every possible component shape.
2. Use `suppress_callback_exceptions=True` only when the app intentionally has
   dynamic pages or dynamic layout branches.
3. Consider `allow_optional=True` for dependencies that are truly optional at
   initial render.
4. For pages, ensure page modules register layouts and route metadata before the
   app starts serving.

## Minimal no-browser checks

Use the bundled script:

```bash
python path/to/app-callback-workflows/scripts/smoke_dash_app.py --mode callback --json
```

This checks importability, component serialization, callback registration, and a
simple callback function without starting a server or opening a browser.
