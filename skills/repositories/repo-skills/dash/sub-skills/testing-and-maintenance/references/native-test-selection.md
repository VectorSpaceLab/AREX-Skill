# Native Test Selection

## When to read

Read this when you want a focused Dash test file or command for a code change.

## Safe CPU-native candidates for this baseline

The repository's `tests/unit/test_configs.py` and `tests/unit/test_resources.py`
use the `mocker` fixture. Install `pytest-mock` alongside pytest when selecting
those files; without it, collection/setup reports a missing fixture rather than
an implementation failure.

| Candidate | Why it matters | Typical command |
| --- | --- | --- |
| `tests/unit/test_callback_unit.py` | Callback decorator API and public signature surface | `python -m pytest tests/unit/test_callback_unit.py -q` |
| `tests/unit/test_layout.py` | Layout traversal and component lookup utilities | `python -m pytest tests/unit/test_layout.py -q` |
| `tests/unit/test_configs.py` | Config/environment merging and prefix behavior; `app.index()` cases also prove packaged JS resources exist | `python -m pytest tests/unit/test_configs.py -q` |
| `tests/unit/test_resources.py` | Resource registration and local/CDN logic | `python -m pytest tests/unit/test_resources.py -q` |
| `tests/backend_tests/test_preconfig_backends.py` | Backend selection and import behavior | `python -m pytest tests/backend_tests/test_preconfig_backends.py -q` |

## Optional browser-backed candidates

These are useful when the change truly depends on the browser or renderer:

- `tests/integration/callbacks/test_basic_callback.py`
- `tests/integration/multi_page/test_pages_layout.py`
- `tests/integration/clientside/test_clientside.py`
- `tests/integration/security/test_xss.py`
- `tests/integration/dash_assets/test_dash_assets.py`

Use them only when Chrome/ChromeDriver and the `dash[testing]` extra are ready.

## Candidate-to-workflow mapping

- App callbacks/layouts/pages/assets: `tests/unit/test_callback_unit.py`,
  `tests/unit/test_layout.py`, `tests/unit/test_configs.py`, plus one focused
  browser integration test when the issue is browser-visible.
- Renderer/resource changes: `tests/unit/test_resources.py`, plus renderer JS
  tests when the change touches `dash/dash-renderer/src`.
- Backend/runtime changes: `tests/backend_tests/test_preconfig_backends.py`,
  plus the smallest backend-specific async/background/WebSocket test file.
- Repository-maintenance or generated-wrapper changes: unit import smoke plus the
  narrowest component package or renderer test that exercises the generated
  artifact.

## Selection heuristic

Choose the smallest file that exercises the changed behavior, then add one more
layer only when the first layer cannot prove the bug fix or regression.
