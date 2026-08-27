# Build, Lint, and Contribution Commands

## When to read

Read this for Dash's build, lint, formatter, and contribution conventions.

## Python environment and install

Common package install for a Dash checkout:

```bash
python -m pip install -e ".[testing]"
```

Choose extras only when needed:

- `dash[testing]` for Selenium/browser fixtures.
- `dash[diskcache]` for background callback manager tests.
- `dash[fastapi]` or `dash[quart]` for backend coverage.
- `dash[async]` for Flask async callbacks.

## Build commands

| Command | Purpose | Notes |
| --- | --- | --- |
| `npm ci` | Install repository JavaScript dependencies from lockfiles | Run before any package build. |
| `npm run build` | Build the repo's JS/component artifacts | Can be heavy; use when component or renderer assets changed. |
| `npm run first-build` | Initial Windows-oriented build sequence | Used in the repo docs for first-time builds. |
| `npm run setup-tests.py` | Prepare test components used by browser/component tests | Needed for some integration suites. |
| `dash-update-components "dash-core-components"` | Refresh one component package | Use when a change is limited to a single package. |
| `dash-update-components "all"` | Refresh all built-in component packages | Heavier; use only when multiple packages changed. |

## Lint commands

| Command | Purpose |
| --- | --- |
| `npm run lint` | Run repo-level lint orchestration. |
| `npm run private::lint.black` | Black check for Python files. |
| `npm run private::lint.flake8` | Flake8 for Python files. |
| `npm run private::lint.pylint-dash` | Pylint for `dash/` and `setup.py`. |
| `npm run private::lint.renderer` | Renderer lint. |

## Contribution conventions

- Follow GitHub flow: branch, focused commits, review, merge.
- Keep commits logical when a change spans code, docs, and generated artifacts.
- Use the repo's test pyramid guidance: unit tests first, browser tests only when
  they are necessary, and renderer/component tests when the changed code owns
  them.
- Keep formatter and linter failures visible before rerunning the command.

## Troubleshooting advice

- If a test/helper command says a generated package or formatter is missing,
  install the package in the active environment before debugging the source.
- If a build command fails because a formatter is absent, do not assume the build
  itself is broken; install the prerequisite and rerun.
- If a browser test fails, verify Chrome/ChromeDriver versions before expanding
  to a larger suite.
