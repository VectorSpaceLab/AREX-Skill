# Clientside Callbacks

## When to read

Read this when a callback should run in the browser, when the task mentions
`window.dash_clientside`, or when browser-side state should be updated without a
server round trip.

## Registration patterns

Inline JavaScript is simplest for a small transformation:

```python
from dash import Dash, Input, Output, html, dcc

app = Dash(__name__)
app.layout = html.Div([dcc.Input(id="x"), html.Div(id="out")])

app.clientside_callback(
    "function(value) { return value ? value.toUpperCase() : ''; }",
    Output("out", "children"),
    Input("x", "value"),
)
```

For reusable functions, define a namespace in an asset JavaScript file that the
app serves to the browser:

```javascript
window.dash_clientside = window.dash_clientside || {};
window.dash_clientside.my_namespace = {
  uppercase: function(value) {
    return value ? value.toUpperCase() : '';
  }
};
```

Then reference it from Python:

```python
from dash import ClientsideFunction

app.clientside_callback(
    ClientsideFunction(namespace="my_namespace", function_name="uppercase"),
    Output("out", "children"),
    Input("x", "value"),
)
```

Namespace rules:

- Do not use namespaces starting with `_dashprivate_`.
- Do not use `PreventUpdate` or `no_update` as namespace names.
- Make sure the asset script loads before the callback executes.

## Browser callback context

During clientside callback execution, Dash sets:

```javascript
window.dash_clientside.callback_context
```

It includes trigger and dependency values, similar to Python callback context:

```javascript
const ctx = window.dash_clientside.callback_context;
const triggered = ctx.triggered_id;
```

## Skipping updates

Use these browser-side primitives:

```javascript
function(value) {
  if (value === undefined) {
    throw window.dash_clientside.PreventUpdate;
  }
  if (value === 'keep') {
    return window.dash_clientside.no_update;
  }
  return value;
}
```

For multiple outputs, return an array/object matching the Output grouping and
place `no_update` only where the corresponding Output should stay unchanged.

## Direct prop updates

`window.dash_clientside.set_props` updates component props from browser code:

```javascript
window.dash_clientside.set_props('my-component', { value: 'new' });
window.dash_clientside.set_props({type: 'row', index: 0}, {children: 'updated'});
```

Use it sparingly. For ordinary reactive flows, a normal callback Output is easier
to validate and test. Route WebSocket `set_props` streaming tasks to the server
backend sub-skill because those use `ctx.websocket` and connection lifecycle
rules.

## Common conversion recipe

When converting a server callback to clientside:

1. Keep the same `Output`, `Input`, and `State` declarations.
2. Move only deterministic browser-safe logic. Do not move Python-only libraries,
   filesystem access, credentials, database calls, or server state into JS.
3. Decide whether the JS function returns the same shape as the Python callback.
4. Recreate `PreventUpdate`, `no_update`, or `Patch` behavior explicitly.
5. Test in a browser and check console logs; Python unit checks do not prove the
   asset function exists in the browser namespace.

## Troubleshooting quick checks

| Symptom | Check |
| --- | --- |
| `Cannot read properties of undefined` for namespace/function | Verify `window.dash_clientside.<namespace>.<function>` exists in DevTools and that the JS asset is not ignored by `assets_ignore`. |
| Callback never updates | Confirm the same dependency IDs/properties exist in layout and that the browser console has no JS syntax error. |
| Multi-output error | Return the exact array/object shape expected by the Output grouping. |
| `no_update` ignored | Use `window.dash_clientside.no_update`, not a string named `"no_update"`. |
| Asset not loaded under URL prefix | Use Dash asset handling instead of hardcoded absolute paths. |
