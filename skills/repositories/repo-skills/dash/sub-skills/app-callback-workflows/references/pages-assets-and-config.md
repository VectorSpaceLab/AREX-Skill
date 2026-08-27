# Pages, Assets, Configuration, Jupyter, and Security

## When to read

Read this when a task involves multi-page Dash apps, URL path prefixes, assets,
external resources, dev tools, Jupyter display, or CSP/security configuration.

## Multi-page apps

Dash pages use `register_page`, `page_registry`, and `page_container`:

```python
# app.py
from dash import Dash, html, dcc, page_container

app = Dash(__name__, use_pages=True)
app.layout = html.Div([
    dcc.Link("Home", href="/"),
    dcc.Link("Report", href="/report/2026"),
    page_container,
])
```

```python
# pages/report.py
from dash import html, register_page

register_page(__name__, path_template="/report/<year>", title="Report")

def layout(year=None, **query):
    return html.Div([html.H1(f"Report {year}"), html.Pre(str(query))])
```

Key facts:

- `register_page(module, path=..., path_template=..., layout=..., title=...,
  description=..., image=..., redirect_from=..., **kwargs)` records pages in
  `dash.page_registry`.
- `path_template` variables are passed as keyword arguments to layout functions.
- Query-string values are also passed to layout functions when routing.
- `page_container` contains internal `dcc.Location`, content, store, and dummy
  div components used by the page routing callback.
- Files in a pages folder starting with `_` or `.` are skipped during automatic
  discovery.
- Home page `/` sorts first by default; other pages sort by `order` then name.

Validation guidance:

- When `suppress_callback_exceptions=False`, make sure callbacks for page-local
  components are covered by the page validation layout or a loaded page layout.
- If a page has no `layout` variable/function and none is supplied to
  `register_page`, Dash raises a layout exception when importing pages.
- For dynamic route variables, include `**kwargs` in layout functions if the
  page should tolerate extra routing inputs.

## Assets

Dash scans the app's assets folder at startup:

- `.css` files are added as stylesheets.
- `.js` files are added as scripts.
- `favicon.ico` is used as the favicon when present.
- Other files are served when requested.

Constructor options:

```python
app = Dash(
    __name__,
    assets_folder="assets",
    assets_url_path="assets",
    assets_ignore=".*ignored.*",
    assets_path_ignore=["ignored-subdir"],
    assets_external_path=None,
    include_assets_files=True,
)
```

Use `app.get_asset_url("file.png")` instead of hardcoding `/assets/file.png` so
URL prefixes and hosted deployments work correctly.

## URL prefixes

Dash has three related prefix knobs:

| Option | Purpose |
| --- | --- |
| `url_base_pathname` | Base for both app routes and AJAX routes when the same prefix applies. |
| `requests_pathname_prefix` | Prefix used by frontend requests to Dash endpoints. Important behind proxies or Dash Enterprise-style app prefixes. |
| `routes_pathname_prefix` | Prefix where the server registers Dash routes. |

Use `dash.get_relative_path(path)` and `dash.strip_relative_path(path)` when
app code must be prefix-aware. Do not concatenate strings with deployment
prefixes by hand unless the deployment contract demands it.

## External scripts and stylesheets

Use constructor fields instead of old `append_script` patterns:

```python
app = Dash(
    __name__,
    external_scripts=[{"src": "https://cdn.example/mod.js", "type": "module"}],
    external_stylesheets=["https://cdn.example/theme.css"],
    serve_locally=True,
)
```

`serve_locally=True` serves Dash/component resources from the installed package.
`serve_locally=False` uses external URLs declared by resources when available.

## Dev tools

`app.run(debug=True)` enables dev tools. For finer control:

```python
app.enable_dev_tools(
    dev_tools_ui=True,
    dev_tools_props_check=True,
    dev_tools_serve_dev_bundles=True,
    dev_tools_hot_reload=True,
    dev_tools_prune_errors=True,
)
```

Useful environment variables include `DASH_DEBUG`, `DASH_UI`,
`DASH_PROPS_CHECK`, `DASH_HOT_RELOAD`, `DASH_PRUNE_ERRORS`, `HOST`, and `PORT`.

## Jupyter display

Dash apps can display inside notebooks and JupyterLab:

```python
app.run(jupyter_mode="inline", jupyter_width="100%", jupyter_height=650)
```

Modes:

| Mode | Behavior |
| --- | --- |
| `inline` | Display an iframe in the cell. |
| `external` | Print a URL for the user to open. |
| `jupyterlab` | Open a JupyterLab tab when the extension is active. |
| `tab` | Open a browser tab. |

JupyterHub/proxy deployments need correct `requests_pathname_prefix` negotiation.
If notebook communication fails, verify the Jupyter extension/proxy layer before
rewriting app callbacks.

## CSP and security

Dash includes security helpers and frontend URL sanitization:

- `app.csp_hashes()` returns hashes for inline scripts so CSP middleware can
  allow Dash's inline renderer/bootstrap scripts.
- Dangerous URL protocols such as `javascript:` and `vbscript:` are sanitized in
  protected component attributes.
- Meta tag content is escaped.
- Keep `suppress_callback_exceptions=False` unless the app deliberately has
  dynamic layouts; validation catches many ID mistakes.

Example CSP shape:

```python
hashes = app.csp_hashes()
# Pass hashes to your framework's CSP middleware, for example Flask-Talisman.
```

## Smoke check

Run:

```bash
python path/to/app-callback-workflows/scripts/smoke_pages_app.py --json
```

The script exercises `register_page`, a tiny `Dash(..., use_pages=True)` app,
and page registry metadata without starting a browser.
