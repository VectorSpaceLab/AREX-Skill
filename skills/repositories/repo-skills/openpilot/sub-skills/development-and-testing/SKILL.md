---
name: development-and-testing
description: "Guides safe openpilot checkout setup, uv/SCons builds,
  native-extension prep, linting, tests, docs, and development validation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# development-and-testing

Use this sub-skill for openpilot setup, dependency sync, submodules, SCons/native build products, targeted tests, linting, docs builds, and CI-style validation. Use it before running broad test suites or when imports fail because the checkout is not fully prepared.

## Read first

- [references/setup-build-test.md](references/setup-build-test.md) for the safe setup/build sequence and environment checks.
- [references/testing-reference.md](references/testing-reference.md) for `tools/test_runner.py`, lint choices, docs builds, and native test selection.
- [references/troubleshooting.md](references/troubleshooting.md) when uv, submodules, git-lfs, SCons, native extensions, lint, or hardware-test selection fails.
- Run [scripts/openpilot_dev_check.py](scripts/openpilot_dev_check.py) against a target checkout for read-only diagnostics.

## Common routes

| User asks | Do |
| --- | --- |
| "Set up openpilot" or "imports fail after install" | Inspect Python version, submodules, uv sync state, and SCons outputs with the checker, then follow setup/build guidance. |
| "Run tests for a change" | Choose focused targets from [testing-reference.md](references/testing-reference.md); avoid hardware/network/GUI tests unless prerequisites are available. |
| "Run lint/CI locally" | Use the lint and test runner sections; explain `--fast`, target narrowing, and tool dependency failures. |
| "Build docs" | Use docs build notes in setup-build-test; do not start a long-running docs server unless requested. |
| "Switch branch/update/start device" | Treat as state-mutating; require explicit user intent and read troubleshooting warnings first. |

## Minimal safe workflow

1. Confirm the task really needs repo setup or tests, not just static source reading.
2. Run the bundled read-only checker:

```bash
python skills/disco/openpilot/sub-skills/development-and-testing/scripts/openpilot_dev_check.py --repo-root /path/to/openpilot
```

3. If submodules are empty, initialize them in the target checkout before retrying package sync.
4. If `msgq.ipc_pyx` or `libparams_c.so` imports fail, build only the needed SCons targets before launching broad tests.
5. Select one or a few test targets; prefer CPU-safe unit tests before route/network/hardware cases.
6. Record skipped optional hardware/network/GUI cases with reasons rather than treating them as failed CPU validation.

## Boundaries

- For `LogReader`, route IDs, qlogs/rlogs, or cache errors, switch to [route-log-analysis](../route-log-analysis/SKILL.md).
- For car interfaces, fingerprints, controls, or process replay, switch to [car-ports-and-controls](../car-ports-and-controls/SKILL.md).
- For msgq/Params/manager/loggerd internals after setup is complete, switch to [core-services-and-runtime](../core-services-and-runtime/SKILL.md).
- For replay/Cabana/PlotJuggler/simulator/joystick/UI, switch to [simulator-and-visual-tools](../simulator-and-visual-tools/SKILL.md).
