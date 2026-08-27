# App and Callback Troubleshooting

## When to read

Read this when a Dash app imports successfully but layout, callback, page,
asset, clientside, or Jupyter behavior is wrong.

## Callback errors

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `A nonexistent object was used in an Input/Output/State` | Callback references an ID/property that is absent from the current validation layout. | Fix the ID typo, add the component to a `validation_layout`, or use `suppress_callback_exceptions=True` only for deliberate dynamic pages/layouts. |
| Callback never fires | Input is absent, typoed, not changing, blocked by `prevent_initial_call`, or a dynamic component is not mounted yet. | Print/inspect the layout, verify the dependency IDs/properties, and check whether `prevent_initial_call` is set at callback or app level. |
| Callback fires too often | A value is modeled as `Input` when it should be `State`, or several dependencies are changed together. | Convert non-triggering values to `State`; use `ctx.triggered_id` or `ctx.triggered_prop_ids` to route behavior. |
| Circular dependency detected | A callback's Output feeds itself directly or through another callback. | Split callbacks, move read-only values to `State`, or store intermediate data in `dcc.Store`. |
| Multi-output callback return error | Return shape does not match declared Outputs. | Return a tuple/list/dict matching the Output grouping; use `no_update` only for individual outputs to preserve. |
| Callback exception appears as `Callback error updating ...` | The Python callback raised an exception. | Run with debug enabled to see the traceback, add targeted error handling with `on_error`, and validate callback inputs before doing work. |

## Layout and component failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `Invalid component type` | Layout contains unsupported raw objects, often dicts where components/strings/numbers are expected. | Wrap display data in components such as `html.Pre` or serialize it to text. Component IDs can be dicts, but arbitrary child dicts are not layout nodes. |
| Component does not render | Component library not imported, JS bundle/resource failed, or browser console has an error. | Confirm `from dash import html, dcc, dash_table`; check browser console and resource loading. For generated components, read the component renderer troubleshooting reference. |
| Dropdown/Graph appears not to update | Callback returns the same object reference or mutates a list/dict in place. | Return a new list/dict/figure object; do not mutate and return the same object. |
| DataTable slow with large data | Too much data is sent to browser or client-side filtering is overloaded. | Use pagination, virtualization, or server-side filtering before sending data to the component. |

## Dynamic pages and validation

For multi-page apps, callbacks often reference components that are not present on
the initial page. Prefer this order:

1. Add a `validation_layout` that includes all page layouts or all callback
   target component shapes.
2. Use `suppress_callback_exceptions=True` when page modules are intentionally
   discovered dynamically.
3. Use `allow_optional=True` only for dependencies that are truly optional at
   initial render.
4. Check `dash.page_registry` for the page path/title/layout metadata you expect.

## Asset and URL prefix failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Asset 404 in deployment but works locally | Hardcoded `/assets/...` path ignores `requests_pathname_prefix`. | Use `app.get_asset_url("name.ext")` or prefix-aware Dash helpers. |
| JS/CSS asset ignored | `assets_ignore` or `assets_path_ignore` matches the file. | Adjust ignore patterns or move the asset. |
| Page links break behind a proxy | Link paths are not prefix-aware. | Use `dash.get_relative_path` for internal paths when the app can have a pathname prefix. |
| Hot reload does not update | Debug/hot reload disabled or files outside watched paths. | Enable debug/hot reload and add `extra_hot_reload_paths` for external code. |

## Clientside callback failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| JS namespace/function is undefined | Asset file did not load, namespace typo, or function name mismatch. | In browser DevTools, check `window.dash_clientside.<namespace>`. Fix asset path and namespace. |
| Returning `"no_update"` does not work | Returned a string instead of Dash's JS sentinel. | Return `window.dash_clientside.no_update`. |
| `PreventUpdate` does not work | Did not throw the JS sentinel. | `throw window.dash_clientside.PreventUpdate`. |
| Browser console shows syntax error | Invalid JS in asset or inline callback string. | Fix the JS first; Python callback debugging will not catch this. |

## Jupyter display failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Inline app does not display | Notebook/JupyterLab extension or proxy negotiation failed. | Try `jupyter_mode="external"` to separate app health from inline display, then verify Jupyter extension/proxy setup. |
| App works locally but not through JupyterHub proxy | Path prefix mismatch. | Let Dash infer proxy config when possible; otherwise configure `requests_pathname_prefix` deliberately. |
| Event loop errors | Notebook event loop conflicts. | Dash applies `nest_asyncio` in supported Jupyter paths; if custom async code conflicts, isolate the async logic or use an ASGI backend outside the notebook. |

## Security/CSP failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Browser blocks Dash inline scripts under CSP | CSP does not include Dash script hashes. | Add `app.csp_hashes()` to the CSP middleware's allowed hashes. |
| Links with dangerous protocols become blank | Dash frontend URL sanitizer blocked `javascript:` or similar. | Use safe protocols and avoid embedding executable URLs in components. |
| Meta tags render escaped content | Dash escapes meta content to prevent injection. | Treat escaping as expected; do not disable sanitization to render untrusted HTML. |

## Safe reproduction helpers

- `scripts/smoke_dash_app.py --mode callback --json` verifies imports, a simple
  layout, callback registration, and callback return behavior without a browser.
- `scripts/smoke_pages_app.py --json` verifies page registration and page
  metadata without starting a browser.

If the failure only appears in the browser, switch to a focused `dash_duo` test
from the testing sub-skill and keep full traceback/browser log output.
