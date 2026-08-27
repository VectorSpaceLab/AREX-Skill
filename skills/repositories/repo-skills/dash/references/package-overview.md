# Dash Package Overview

## When to read

Read this when you need the package layout, public imports, extras, command-line
entry points, and the main subsystem map before choosing a focused sub-skill.

## What Dash provides

Dash exposes a Python API that declares a component tree and connects component
properties with callbacks. At runtime, the server serves the initial layout,
callback dependency metadata, component bundles, assets, and callback endpoints;
the dash-renderer frontend hydrates the layout and schedules callback work.

Verified public imports include:

```python
import dash
from dash import (
    Dash,
    html,
    dcc,
    dash_table,
    Input,
    Output,
    State,
    MATCH,
    ALL,
    ALLSMALLER,
    callback,
    clientside_callback,
    callback_context,
    ctx,
    no_update,
    NoUpdate,
    Patch,
    register_page,
    page_container,
    DiskcacheManager,
    CeleryManager,
)
```

The inspected package version for this skill baseline is `4.4.1`.

## Major subsystems

| Subsystem | What it owns | Route |
| --- | --- | --- |
| App object and routes | `Dash`, layout serving, assets, dev tools, callbacks, pages, Jupyter, CSP hashes | [app callback workflows](../sub-skills/app-callback-workflows/SKILL.md) |
| Callback API | `@callback`, `@app.callback`, `Input`, `Output`, `State`, grouped inputs/outputs, background/websocket flags | [app callback workflows](../sub-skills/app-callback-workflows/SKILL.md), then [server backends](../sub-skills/server-backends-and-async/SKILL.md) for runtime modes |
| Server backends | Flask default WSGI, FastAPI/Quart ASGI, backend adapters, WebSocket endpoints | [server backends and async](../sub-skills/server-backends-and-async/SKILL.md) |
| Background callbacks | `DiskcacheManager`, `CeleryManager`, result/progress/cache plumbing | [server backends and async](../sub-skills/server-backends-and-async/SKILL.md) |
| MCP and hooks | Dash MCP route, MCP-decorated functions, resource/tool exposure, setup/layout/route/error/callback/websocket hooks | [server backends and async](../sub-skills/server-backends-and-async/SKILL.md) |
| Component model | `Component`, generated `html`/`dcc`/`dash_table` wrappers, `to_plotly_json`, `_children_props` | [component renderer development](../sub-skills/component-renderer-development/SKILL.md) |
| Resource system | `_js_dist`, `_css_dist`, local/CDN resource selection, dynamic/dev bundles, fingerprinted component assets | [component renderer development](../sub-skills/component-renderer-development/SKILL.md) |
| Renderer | React/Redux hydration, paths, callback queues, clientside callbacks, WebSocket SharedWorker client | [component renderer development](../sub-skills/component-renderer-development/SKILL.md) |
| Testing | pytest plugin, `dash_duo`, browser helpers, app runners, focused native test selection | [testing and maintenance](../sub-skills/testing-and-maintenance/SKILL.md) |

## Installation variants

Base install requirements include Flask/Werkzeug, Plotly, requests, retrying,
nest-asyncio, setuptools, janus, pydantic, typing extensions, importlib metadata,
and comm support.

Optional extras are intentionally split:

| Extra | Main use | Notes |
| --- | --- | --- |
| `dash[testing]` | Dash pytest/Selenium fixtures | Requires a browser/driver for browser tests. Browser availability is separate from Python package install. |
| `dash[diskcache]` | Local background callback manager | Installs diskcache, multiprocess, and psutil. Does not require an external service. |
| `dash[celery]` | Distributed background callback manager | Requires a configured Celery app with broker and result backend. Installation alone is not an end-to-end proof. |
| `dash[fastapi]` | FastAPI ASGI backend and WebSocket callbacks | Installs FastAPI and uvicorn. WebSocket runtime also depends on browser SharedWorker support. |
| `dash[quart]` | Quart ASGI backend | Installs Quart/Hypercorn dependencies. |
| `dash[async]` | `async def` callbacks on Flask | FastAPI/Quart are natively async; Flask needs the async extra for coroutine callbacks. |
| `dash[dev]` | Development helpers such as component generation dependencies | Component package builds also require Node/npm package dependencies. |

Avoid installing broad extras such as CI, cloud, ag-grid, compress, or Celery
unless the task actually needs them.

## Console entry points

| Command | Purpose | Safe first check |
| --- | --- | --- |
| `dash-generate-components` | Generate Python/R/Julia component wrappers from React component metadata | `dash-generate-components --help` |
| `dash-update-components` | Rebuild/copy Dash's built-in component package artifacts into the main package | `dash-update-components --help`; full command can run npm install/build |
| `renderer` | Build-process helper for dash-renderer assets | `renderer --help`; full build requires renderer Node dependencies |
| `plotly` | Plotly CLI entry point exposed by Dash package metadata | Use only when the task explicitly involves that CLI surface |

## Minimal object and callback shape

```python
from dash import Dash, html, dcc, Input, Output

app = Dash(__name__)
app.layout = html.Div([
    dcc.Input(id="name", value="Dash"),
    html.Div(id="greeting"),
])

@app.callback(Output("greeting", "children"), Input("name", "value"))
def greet(value):
    return f"Hello {value or 'Dash'}"
```

A component serializes to a JSON-like dict with a component `type`, a JavaScript
`namespace`, and `props`. The renderer uses those fields to resolve React
components from `window[namespace][type]`.

## Verification notes

For a fresh environment, use the root diagnostic script:

```bash
python path/to/dash/scripts/check_dash_install.py --json
```

Then route to the relevant sub-skill. If `html.Div` or `dcc.Graph` cannot be
imported in a development checkout, generated component wrappers may be missing;
see [component troubleshooting](../sub-skills/component-renderer-development/references/troubleshooting.md).
