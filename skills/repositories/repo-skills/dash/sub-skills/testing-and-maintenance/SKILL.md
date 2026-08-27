---
name: testing-and-maintenance
description: "Use for Dash test selection, browser fixtures, build/lint
  commands, and repository maintenance workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Dash Testing and Maintenance

Use this sub-skill when you need to decide which Dash tests to run, how to use
Dash's browser fixtures, or which build/lint commands are safe for a specific
change.

## Start here

1. Read [references/testing-workflows.md](references/testing-workflows.md) for
   the test tiers and fixture behavior.
2. Read [references/build-lint-and-contribution.md](references/build-lint-and-contribution.md)
   for build, lint, and contribution commands.
3. Read [references/native-test-selection.md](references/native-test-selection.md)
   for focused native test candidates and selection guidance.
4. Read [references/troubleshooting.md](references/troubleshooting.md) when a
   test, browser driver, formatter, or build fails.
5. Run [scripts/list_dash_commands.py](scripts/list_dash_commands.py) or
   [scripts/suggest_dash_tests.py](scripts/suggest_dash_tests.py) when you need a
   fast command/menu summary.

## Main routes

### Choose a focused test plan

Use this route when the task asks which Dash tests to run after a source change.
Prefer the smallest unit/integration/browser set that actually exercises the
changed behavior.

### Work with browser fixtures

Use this route for `dash_duo`, `dash_br`, `dash_thread_server`,
`dash_process_server`, `dash_multi_process_server`, `dashr`, `dashjl`, or the
`Browser` helper methods.

### Run builds, lint, or contribution checks

Use this route for `npm ci`, `npm run build`, `npm run lint`, `npm run
first-build`, component package setup, or repository contribution guidance.

## Route elsewhere

- App and callback debugging: [app callback workflows](../app-callback-workflows/SKILL.md).
- Backend/async/WebSocket/MCP runtime checks: [server backends and async](../server-backends-and-async/SKILL.md).
- Component generator and renderer internals: [component renderer development](../component-renderer-development/SKILL.md).

## Validation checklist

Before declaring a test plan complete:

- The chosen test file or command is focused enough to expose the failure.
- Browser-backed tests are only chosen when Chrome/ChromeDriver or a suitable
  browser runtime is available.
- Integration output retains the traceback and assertion context.
- Build commands are separated from test commands so failures are easy to read.
- If a source checkout has generated component wrappers or renderer bundles,
  confirm whether those artifacts need regeneration before the next test run.
