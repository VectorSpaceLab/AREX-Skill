# Development And Testing Reference

Use this reference when a user asks how to validate changes in the Dask repository, run targeted tests, or understand configured lint/test behavior. These commands are reference-only; they are not bundled runtime scripts.

## Environment Manager

Dask uses `pixi` for development environments and task execution. Prefer `pixi run ...` commands from the repository root when validating repo changes.

## Common Commands

| Task | Command |
| --- | --- |
| Run default tests | `pixi run test` |
| Run full CI-style suite | `pixi run test-ci` |
| Run linting | `pixi run lint lint` |
| Run doctests | `pixi run doctest` |
| Run one test module | `pixi run test dask/tests/test_config.py` |
| Run one test | `pixi run test dask/tests/test_cli.py::test_config_list` |
| Run slow tests | `pixi run test --runslow` |
| Run array-expression tests | `pixi run --environment py314 test-array-expr` |
| Run arbitrary Python | `pixi run -- python -c 'import dask; print(dask.__version__)'` |

## Relevant Targeted Tests

| Area | Candidate tests |
| --- | --- |
| Config API and schema | `dask/tests/test_config.py` |
| CLI commands and entry points | `dask/tests/test_cli.py` |
| Progress bar | `dask/diagnostics/tests/test_progress.py` |
| Profilers and visualization | `dask/diagnostics/tests/test_profiler.py` |

## Pytest Behavior To Expect

- Tests use strict markers and strict config.
- Warnings are treated as errors with selected ignores.
- Default per-test timeout is long enough for slow platforms; do not shorten casually.
- `xfail_strict = true`, so unexpected passes fail the test run.
- Use markers such as `network`, `slow`, `gpu`, `array_expr`, and `normal_and_array_expr` according to existing patterns.

## Dependency Matrix Notes

Dask supports multiple Python and dependency combinations. The project metadata requires Python 3.10+ and core dependencies such as `click`, `cloudpickle`, `fsspec`, `packaging`, `partd`, `pyyaml`, and `toolz`.

Important optional extras:

| Extra | Adds |
| --- | --- |
| `array` | NumPy support |
| `dataframe` | Array extra, pandas, and pyarrow |
| `distributed` | Distributed scheduler package pinned to the compatible Dask release range |
| `diagnostics` | Bokeh and Jinja2 for diagnostic visualization |
| `complete` | Array, dataframe, distributed, diagnostics, and lz4 |
| `test` | pytest and development validation tooling |

## Linting And Style Signals

- Ruff line length is 120.
- Import sorting is enforced through Ruff rules.
- New source files should use `from __future__ import annotations` following project convention.
- Tests live alongside source in `dask/**/tests/test_*.py`.
- Use existing test helpers and patterns rather than creating new infrastructure for small changes.

## Safe Validation Strategy

1. Start with the narrowest affected test, for example `pixi run test dask/tests/test_config.py::test_get`.
2. Expand to the owning test module.
3. Add related CLI or diagnostics tests if config touches command behavior or callback behavior.
4. Run lint only after code-level changes are stable.
5. Avoid running network, GPU, or distributed cluster tests unless the task explicitly needs them and the environment supports them.
