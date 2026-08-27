---
name: dash
description: "Use when building, debugging, testing, or maintaining Plotly Dash
  applications, callbacks, server backends, component packages, renderer
  internals, and Dash repository workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Dash Repo Skill

Dash is Plotly's Python framework for building reactive web applications with
Python layouts, React component bundles, and server-side or clientside callbacks.
Use this repo skill when a task involves Dash application code, callback routing,
Dash server backends, component wrapper generation, the Dash renderer, or Dash
repo test/build workflows.

## Read first

- Read [references/package-overview.md](references/package-overview.md) for the
  installed package shape, public imports, optional extras, CLIs, and major
  subsystems.
- Read [references/troubleshooting.md](references/troubleshooting.md) for
  cross-cutting install/import, generated component, optional dependency, Node,
  browser, and stale-skill failures.
- Read [references/repo-provenance.md](references/repo-provenance.md) before
  deciding whether this skill matches a current Dash checkout.
- Run [scripts/check_dash_install.py](scripts/check_dash_install.py) when you
  need a safe import/optional-backend/CLI diagnostic before using deeper routes.

## Quick install and smoke check

For ordinary app use:

```bash
python -m pip install dash
python - <<'PY'
import dash
from dash import Dash, html, dcc, Input, Output
print(dash.__version__)
app = Dash(__name__)
app.layout = html.Div([dcc.Input(id="name"), html.Div(id="out")])
@app.callback(Output("out", "children"), Input("name", "value"))
def update(value):
    return value or ""
print(app.layout.to_plotly_json()["type"], len(app.callback_map))
PY
```

Choose extras only when the workflow needs them:

| Need | Install |
| --- | --- |
| Selenium/browser testing fixtures | `python -m pip install "dash[testing]"` |
| Diskcache background callbacks | `python -m pip install "dash[diskcache]"` |
| Celery background callbacks | `python -m pip install "dash[celery]"` plus a broker/result backend |
| FastAPI backend and WebSocket callbacks | `python -m pip install "dash[fastapi]"` |
| Quart backend | `python -m pip install "dash[quart]"` |
| `async def` callbacks on Flask | `python -m pip install "dash[async]"` |
| Component generation helpers | install Dash from a checkout with the development dependencies needed by the component package |

## Route by task

### Build or debug a Dash app

Use [sub-skills/app-callback-workflows/SKILL.md](sub-skills/app-callback-workflows/SKILL.md)
when the task mentions:

- `Dash(...)`, layout trees, `html`, `dcc`, `dash_table`, component IDs, assets,
  URL prefixes, Jupyter display, CSP hashes, or pages.
- `@app.callback`, `@dash.callback`, `Input`, `Output`, `State`, `MATCH`, `ALL`,
  `ALLSMALLER`, `ctx`, `callback_context`, `PreventUpdate`, `no_update`, or
  `Patch`.
- Clientside callbacks or `window.dash_clientside`.

Start with its [callbacks and layouts reference](sub-skills/app-callback-workflows/references/callbacks-and-layouts.md),
then use its smoke scripts for layout/callback/page checks.

### Select backends, async, WebSocket, background callbacks, hooks, or MCP

Use [sub-skills/server-backends-and-async/SKILL.md](sub-skills/server-backends-and-async/SKILL.md)
when the task mentions:

- Flask, FastAPI, Quart, ASGI, backend adapters, custom backends, or route
  handling.
- `async def` callbacks, `dash[async]`, `websocket_callbacks`, `websocket=True`,
  `persistent=True`, `ctx.websocket`, `set_props`, or WebSocket disconnects.
- `background=True`, `DiskcacheManager`, `CeleryManager`, `progress`, `running`,
  `cancel`, or callback caching.
- Dash hooks, WebSocket connection hooks, MCP resources/tools, or
  `configure_mcp_server`.

Run its [backend inspection script](sub-skills/server-backends-and-async/scripts/inspect_backends.py)
for a safe optional-extra report before promising backend coverage.

### Work on custom components, built-in components, resources, or renderer

Use [sub-skills/component-renderer-development/SKILL.md](sub-skills/component-renderer-development/SKILL.md)
when the task mentions:

- `dash-generate-components`, `dash-update-components`, `renderer`, component
  metadata, generated Python wrappers, R/Julia wrapper generation, or built-in
  component packages.
- `Component`, `to_plotly_json`, `_children_props`, `_js_dist`, `_css_dist`,
  `serve_locally`, `external_url`, `dev_package_path`, or resource fingerprints.
- `dash-renderer`, callback queues, `setProps`, `crawlLayout`, `paths`,
  `window.dash_component_api`, SharedWorker/WebSocket client, React versions, or
  JSX runtime problems.

Use its CLI-check scripts before running heavier Node or component builds.

### Choose tests, build/lint commands, or repo-maintenance workflow

Use [sub-skills/testing-and-maintenance/SKILL.md](sub-skills/testing-and-maintenance/SKILL.md)
when the task mentions:

- `pytest`, `dash_duo`, Selenium, ChromeDriver, Percy, renderer tests, component
  tests, `npm run build`, `npm run lint`, Black/flake8/pylint/eslint/prettier,
  or contribution policy.
- A patch to Dash source where you need a focused native test plan.

Follow its rule: never run all integration tests by default. Use focused files
and preserve enough output to see tracebacks and assertion context.

## Important boundaries

- Do not claim FastAPI, Quart, Diskcache, Celery, browser, renderer, or component
  build workflows are available until the relevant extra/tool/service is
  installed and checked.
- Do not use a CPU import check as proof of browser, Node, Celery broker, or
  WebSocket runtime behavior.
- For package-use tasks, prefer public APIs and bundled references/scripts in
  this skill. For repo-maintenance tasks, the testing sub-skill may tell you how
  to run focused commands in a current Dash checkout.
- If the current checkout commit, generated component wrapper state, or package
  version differs from [references/repo-provenance.md](references/repo-provenance.md),
  treat this skill as potentially stale and refresh it before relying on
  maintainer-specific details.
