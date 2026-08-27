# Cross-Cutting Dash Troubleshooting

## When to read

Read this before diving into a sub-skill when the failure could be caused by
installation, optional extras, generated component wrappers, Node/browser tools,
or a stale checkout rather than by one specific API.

## Fast triage

1. Run the import diagnostic:
   ```bash
   python path/to/dash/scripts/check_dash_install.py --json
   ```
2. If imports fail, fix the package install before debugging app logic.
3. If optional backend fields report missing packages, install only the extra
   that matches the workflow (`dash[fastapi]`, `dash[quart]`, `dash[diskcache]`,
   `dash[async]`, or `dash[testing]`).
4. If the task is repo maintenance, check whether generated component wrappers
   exist before assuming Dash itself is broken.
5. If the current checkout differs from [repo-provenance.md](repo-provenance.md),
   refresh this skill or verify source facts against the current code.

## Install and import failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'dash'` | Dash is not installed in the active Python. | Install `dash` or install the checkout editable in the intended environment. Verify with `python -c "import dash; print(dash.__version__)"`. |
| `ImportError: cannot import name ... from dash` | Feature not available in the installed Dash version or stale local module shadowing. | Print `dash.__version__`, inspect `dash.__file__`, and compare to the expected version. Avoid naming your app file `dash.py`. |
| `module 'dash.html' has no attribute 'Div'` in a development checkout | Generated built-in component wrappers under the package are missing or stale. | For maintainer work, generate/update component artifacts with the component workflow. For app use, install a released Dash wheel instead of an incomplete checkout. |
| `app.index()` raises `FileNotFoundError` for `dash/deps/polyfill...` or another Dash JS file | Python imports are working, but package JS/resource files are missing from the development checkout or editable install. | For app use, install a released Dash wheel or rebuild/package the frontend resources. For maintainer work, read the component renderer resource workflow and run focused resource/config tests after regenerating bundles. |
| Old imports such as `import dash_core_components as dcc` fail | Modern Dash uses unified imports. | Use `from dash import dcc, html, dash_table`. |
| `pip check` reports conflicts | Broad extras or unrelated packages changed dependency resolution. | Use a clean environment and install only the needed extras. Do not debug callback logic before dependency health is clean. |

## Optional-extra failures

| Symptom | Need | Recovery |
| --- | --- | --- |
| FastAPI backend import fails | ASGI backend or WebSocket callbacks | Install `dash[fastapi]`, then use the backend inspection script in the server sub-skill. |
| Quart backend import fails | Quart ASGI backend | Install `dash[quart]`. |
| `async def` callback errors under Flask | Flask coroutine callbacks | Install `dash[async]` or move to FastAPI/Quart when the app is already ASGI-oriented. |
| `DiskcacheManager requires extra dependencies` | Local background callbacks | Install `dash[diskcache]`. |
| `CeleryManager requires extra dependencies` or disabled backend error | Distributed background callbacks | Install `dash[celery]`, then configure a Celery broker and result backend. Package install alone is not enough. |
| `dash.testing` fixtures unavailable | Browser integration tests | Install `dash[testing]` and verify browser/driver availability separately. |

## Node and component build failures

Component generation and renderer tasks can require Node/npm in addition to
Python. Use the component sub-skill before running heavy builds.

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `dash-generate-components` not found | Dash is not installed with console scripts in the active environment. | Reinstall Dash in the active environment and verify `dash-generate-components --help`. |
| `dash-update-components` fails while running npm | Node/npm dependencies are missing, package lock state is stale, or a component package build failed. | Run focused component CLI help first, then install Node dependencies only for the relevant package. Preserve full build output. |
| Python formatter command missing during component build | Component build script expects Black in the active environment. | Install the documented dev/CI formatter dependency for maintainer builds. |
| Generated wrappers import but browser shows missing component | JavaScript bundle/resource registration, `namespace`, package data, or asset serving problem. | Read the component renderer resources reference and check `_js_dist`, `dash/deps` package files, `serve_locally`, and browser console errors. |

## Browser and Selenium failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `session not created` mentioning ChromeDriver version | ChromeDriver does not match the installed browser. | Check browser and driver versions; install a matching driver before rerunning a focused integration test. |
| Browser tests hang at app startup | Server failed, port occupied, generated test components missing, or app import error hidden in logs. | Run a focused test with `-xvs` and enough output to see the traceback. Do not tail only a few lines. |
| Percy snapshot warning without failing assertions | `PERCY_TOKEN` is absent or Percy CLI not configured. | Treat visual snapshot as optional unless the task requires Percy. |
| Integration suite is too slow/noisy | Running too broad a selection. | Use one file or one test-id pattern. See the testing sub-skill for focused selection. |

## App-level or workflow-specific failures

- Callback, layout, pages, asset, clientside, CSP, or Jupyter behavior:
  [app troubleshooting](../sub-skills/app-callback-workflows/references/troubleshooting.md).
- Backend, async, background, WebSocket, hooks, or MCP behavior:
  [server troubleshooting](../sub-skills/server-backends-and-async/references/troubleshooting.md).
- Component generation, resources, renderer, React, or JavaScript callback
  pipeline behavior:
  [component troubleshooting](../sub-skills/component-renderer-development/references/troubleshooting.md).
- Test selection, build/lint, browser driver, or contribution behavior:
  [testing troubleshooting](../sub-skills/testing-and-maintenance/references/troubleshooting.md).

## Stop conditions

Stop and ask for a concrete environment or scope decision when:

- A task requires a Celery broker, browser driver, Node build, or ASGI deployment
  target that is not available.
- The user expects validation of a full browser/WebSocket/service workflow but
  only package imports have been checked.
- The current checkout has changed relative to provenance and the task depends
  on exact source behavior.
