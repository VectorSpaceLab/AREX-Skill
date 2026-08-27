---
name: app-callback-workflows
description: "Use for Plotly Dash app layouts, callbacks, pages, assets,
  configuration, clientside callbacks, Jupyter display, CSP, and app-level
  debugging."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Dash App and Callback Workflows

Use this sub-skill when a task is about using Dash as an application framework:
creating layouts, registering callbacks, debugging ID/dependency validation,
configuring pages/assets, or moving work into clientside callbacks.

## Start here

1. For layout and callback API details, read
   [references/callbacks-and-layouts.md](references/callbacks-and-layouts.md).
2. For pages, URL prefixes, assets, dev tools, Jupyter, and CSP, read
   [references/pages-assets-and-config.md](references/pages-assets-and-config.md).
3. For browser-side callback functions, read
   [references/clientside-callbacks.md](references/clientside-callbacks.md).
4. For common failures, read
   [references/troubleshooting.md](references/troubleshooting.md).
5. Run [scripts/smoke_dash_app.py](scripts/smoke_dash_app.py) for a no-browser
   import/layout/callback smoke check and
   [scripts/smoke_pages_app.py](scripts/smoke_pages_app.py) for a page-registry
   smoke check.

## Main routes

### Build a basic app

Use `Dash`, component modules, and a component tree:

```python
from dash import Dash, html, dcc

app = Dash(__name__)
app.layout = html.Div([
    dcc.Input(id="input", value="initial"),
    html.Div(id="output"),
])
```

Important rules:

- Layout children must be Dash components, strings, numbers, `None`, or lists of
  those values. Raw arbitrary dicts are not valid component children.
- Component IDs can be strings or dictionaries. Use dictionary IDs for
  pattern-matching callbacks.
- If a layout is generated dynamically, either ensure callback components exist
  in the initial validation layout or configure dynamic-layout behavior
  deliberately.

### Register server-side callbacks

Use `@app.callback` when you have an app object and `@dash.callback` when you
need module-level callback registration. Core dependency classes are `Output`,
`Input`, and `State`.

```python
from dash import Input, Output, State, callback, no_update
from dash.exceptions import PreventUpdate

@callback(Output("output", "children"), Input("input", "value"), State("store", "data"))
def update(value, stored):
    if value is None:
        raise PreventUpdate
    if value == "keep":
        return no_update
    return f"{value}: {stored}"
```

Use [callback troubleshooting](references/troubleshooting.md) when callbacks do
not fire, fire too early, reference missing components, or form circular
dependencies.

### Use pattern-matching IDs

Route to dictionary IDs and wildcards when components are generated from data:

```python
from dash import MATCH, ALL, Input, Output

@app.callback(
    Output({"type": "row-output", "index": MATCH}, "children"),
    Input({"type": "row-input", "index": MATCH}, "value"),
)
def per_row(value):
    return value
```

Use `MATCH` for one-to-one dynamic pairs, `ALL` for all matching components, and
`ALLSMALLER` when a callback needs earlier indexed values.

### Inspect callback context

Use `dash.ctx` or `dash.callback_context` inside callbacks for trigger metadata:

- `ctx.triggered_id` gives the component ID that triggered the callback.
- `ctx.triggered_prop_ids` maps changed `id.property` strings to IDs.
- `ctx.args_grouping` is useful with flexible callback signatures.
- `ctx.response` lets a callback set response cookies/headers in supported
  backends.
- `ctx.websocket` is only available for WebSocket callbacks; route those tasks
  to [server backends and async](../server-backends-and-async/SKILL.md).

### Use pages, assets, and URL prefixes

Use `Dash(__name__, use_pages=True)` plus `dash.register_page` and
`dash.page_container` for multi-page apps. Read
[pages-assets-and-config.md](references/pages-assets-and-config.md) before
changing URL prefixes, asset loading, or Jupyter display behavior.

### Move simple work clientside

Use clientside callbacks for simple browser-side transformations, browser
storage access, or UI work that should avoid a server round trip. Read
[clientside-callbacks.md](references/clientside-callbacks.md) for namespace
registration, `no_update`, `PreventUpdate`, and `set_props` behavior.

## Route elsewhere

- Background callbacks, async callbacks, WebSocket callbacks, backend classes,
  Dash hooks, and MCP: [server-backends-and-async](../server-backends-and-async/SKILL.md).
- Component generation, renderer internals, React resource loading, and
  `dash_component_api`: [component-renderer-development](../component-renderer-development/SKILL.md).
- Running Dash tests or choosing commands: [testing-and-maintenance](../testing-and-maintenance/SKILL.md).

## Validation checklist

Before declaring an app/callback fix complete:

- The app imports `Dash`, `html`, `dcc`, and dependency classes from `dash`.
- Every callback component ID exists in the layout, validation layout, or a
  deliberate dynamic-layout configuration.
- Callback return shape matches the Output grouping.
- Browser console is clean for browser-backed tasks.
- If assets, pages, or URL prefixes changed, the generated URLs use
  `app.get_asset_url`, `dash.get_relative_path`, or the app's configured
  prefix-aware helpers.
