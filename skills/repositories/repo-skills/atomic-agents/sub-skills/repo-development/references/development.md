# Repository Development

## Monorepo layout

- `atomic-agents/` — core package and unit tests.
- `atomic-assembler/` — CLI/TUI package.
- `atomic-examples/` — runnable examples.
- `atomic-forge/` — downloadable tool packages.
- `docs/` and `guides/` — Sphinx documentation and writing guides.

## Baseline development commands

| Task | Command |
| --- | --- |
| Sync the workspace | `uv sync` |
| Sync all workspace packages | `uv sync --all-packages` |
| Format | `uv run black atomic-agents atomic-assembler atomic-examples atomic-forge` |
| Lint | `uv run flake8 --extend-exclude=.venv atomic-agents atomic-assembler atomic-examples atomic-forge` |
| Test core package | `uv run pytest --cov=atomic_agents atomic-agents` |
| Build docs | `cd docs && make html` |

## Packaging and release notes

- The published package is `atomic-agents`.
- The root `pyproject.toml` defines the main package metadata and the `atomic` console entry point.
- The repository also contains `setup.py` for compatibility with packaging workflows that still inspect it.
- `build_and_deploy.ps1` is a maintainer-only release helper; do not treat it as a runtime script.

## When to use this file

Use this file when editing the checkout, choosing a test target, debugging local package layout, or checking the development path before a release or docs change.
