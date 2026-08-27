# Testing Workflows

## When to read

Read this for Dash's pytest/Selenium fixtures, test tiers, and output discipline.

## Test tiers

| Tier | Typical files | Use when |
| --- | --- | --- |
| Unit | `tests/unit/*` | You need fast, deterministic Python-only coverage. |
| Backend | `tests/backend_tests/*` | The change touches backend selection or adapter behavior. |
| Async/background/WebSocket | `tests/async_tests/*`, `tests/background_callback/*`, `tests/websocket/*` | The change alters callback runtime mode or manager behavior. |
| Integration/browser | `tests/integration/*` | The behavior depends on the browser, renderer, or asset/page runtime. |
| Component package tests | `components/*/tests/*` | The change affects a built-in component package or generated wrapper behavior. |
| Renderer JS tests | `dash/dash-renderer/tests/*` | The change is in the renderer or callback scheduling logic. |

## Fixtures

Dash's main browser fixture is `dash_duo`, a composite of a server runner and a
browser. Related fixtures include:

- `dash_br` — browser only
- `dash_thread_server` — threaded server only
- `dash_process_server` — process-based server only
- `dash_multi_process_server` — multi-process server only
- `dashr` / `dashjl` — language-specific runner/browser composites
- `diskcache_manager` — background-callback manager fixture

## Browser helper behavior

The browser helper exposes methods such as:

- `find_element`, `find_elements`
- `wait_for_element`, `wait_for_text_to_equal`, `wait_for_contains_text`
- `select_dcc_dropdown`, `clear_input`, `multiple_click`
- `get_logs`, `redux_state_is_loading`, `redux_state_paths`, `redux_state_rqs`

Use browser logs and wait helpers to make assertions stable. A clean console is
usually part of the success criteria for browser-backed app tests.

## Output discipline

When a Dash test fails, keep enough output in a single run to diagnose the issue:

- Do not run a suite so broad that the failure location is hidden.
- Do not trim output so aggressively that the assertion, traceback, or browser
  error is lost.
- Use one file or one test-id pattern when possible.
- Preserve the surrounding context for the first failure instead of searching
  only for `FAILED`.

## Selection rules

- Prefer the smallest unit test that covers the changed API.
- Add or choose one browser integration test only when the behavior truly needs
  the renderer/browser/runtime.
- If a patch touches generated component wrappers, select both a wrapper/import
  smoke and the smallest relevant runtime test.
- For backend runtime changes, choose the backend-specific native test before
  falling back to broad integration coverage.

## Safe native candidates

See [native-test-selection.md](native-test-selection.md) for the specific test
files identified for this skill baseline.
