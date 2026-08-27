---
name: repo-development
description: "Maintain the einops repository safely: focused tests, backend/env
  selection, docs and notebook checks, formatting/type checking, CI matrix
  interpretation, release boundaries, and staleness refresh cues."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# repo-development

Use this sub-skill when the task is about maintaining the `einops` repository rather
than writing package-usage recipes. It covers development commands, backend-aware
test selection, docs/notebook checks, README-to-docs conversion, CI interpretation,
packaging boundaries, and refresh/staleness checks.

For tensor operation patterns, API examples, framework-specific user code, or
named einsum/packing recipes, route to sibling sub-skills such as
`tensor-operations`, `named-einsum-and-packing`, or `framework-integrations`.

## Evidence scope

This guidance was distilled from these source-evidence names: `README.md`
Development section, `pyproject.toml`, `einops/tests/run_tests.py`,
`einops/tests/__init__.py`, `scripts/convert_readme.py`,
`scripts/test_notebooks.py`, `scripts/pytorch_examples_source/converter.py`,
`.github/workflows/run_tests.yml`, `.github/workflows/test_notebooks.yml`,
`.github/workflows/deploy_docs.yml`, `.github/workflows/deploy_to_pypi.yml`, and
`mkdocs.yml`.

Do not depend on machine-local checkout paths or environment-specific details.
Prefer the bundled references and scripts below; if repository development files
or workflows have changed since this skill was produced, perform a repo-skill
refresh before relying on stale commands.

## Quick routing

| Maintainer intent | Use this guidance |
|---|---|
| Run minimal package tests without installing all frameworks | [references/docs-and-tests.md](references/docs-and-tests.md#focused-package-tests) and `scripts/run_selected_einops_tests.py` |
| Interpret `EINOPS_TEST_BACKENDS` or framework names | [references/docs-and-tests.md](references/docs-and-tests.md#backend-selection-semantics) |
| Format, lint, or type-check changes | [references/docs-and-tests.md](references/docs-and-tests.md#format-lint-and-type-checks) |
| Build or serve documentation | [references/docs-and-tests.md](references/docs-and-tests.md#docs-build-and-readme-conversion) |
| Convert README content into docs index safely | `scripts/convert_readme_for_docs.py` |
| Check notebook dependencies or execute selected tutorials | [references/docs-and-tests.md](references/docs-and-tests.md#notebook-checks) and `scripts/notebook_execution_check.py` |
| Understand CI matrix coverage | [references/docs-and-tests.md](references/docs-and-tests.md#ci-matrix-notes) |
| Avoid unsafe deploy/publish steps | [references/docs-and-tests.md](references/docs-and-tests.md#release-and-deploy-boundaries) |
| Diagnose common maintainer failures | [references/maintainer-troubleshooting.md](references/maintainer-troubleshooting.md) |

## Safe command patterns

- Tests are distributed with the package. Use the native runner for broad checks:
  `python -m einops.tests.run_tests numpy`.
- Include `numpy` with backend tests unless intentionally investigating a
  symbolic-only case; the README says every framework is tested against numpy.
- Omit `--pip-install` when dependencies are already installed. That flag uses
  `pip install` in the current environment.
- For a dry-run plan or a focused pytest node, use the bundled wrapper:
  `python scripts/run_selected_einops_tests.py numpy --pytest-target test_ops.py::test_repeat_numpy`.
  Add `--execute` only when ready to run.
- For check-only style validation, prefer CI-like non-mutating commands:
  `ruff check .`, `ruff format . --check`, and `mypy .` in an environment with
  the default development dependencies.
- The Hatch `check` script in `pyproject.toml` is intentionally mutating:
  it runs `ruff format`, `ruff check --fix`, then `mypy`.

## Backend selection rules

- Native runner synonyms: `pytorch` -> `torch`, `tf` -> `tensorflow`, and
  `paddlepaddle` -> `paddle`.
- Exact backend names are comma-joined in `EINOPS_TEST_BACKENDS`, for example
  `EINOPS_TEST_BACKENDS=numpy,torch`.
- Missing `EINOPS_TEST_BACKENDS` is an error for tests that call the package test
  utilities directly. The native runner and bundled wrapper set it for you.
- Optional frameworks can conflict in one environment, especially TensorFlow,
  OneFlow, and Paddle protobuf stacks. Use a smaller backend set or a fresh
  environment instead of repairing a shared environment blindly.

## Docs and notebook safety

- `hatch run docs:build` and `hatch run docs:serve` first convert README content
  into the docs index, so they can mutate generated docs content.
- Use `scripts/convert_readme_for_docs.py --readme README.md --output docs_src/index.md`
  for a dry-run preview; add `--execute` only when the mutation is intended.
- Notebook execution needs notebook tooling plus runtime frameworks. CI installs
  `nbformat`, `nbconvert`, `jupyter`, `pillow`, `pytest`, `numpy`, `tensorflow`,
  and CPU `torch` before running notebook tests.
- Use `scripts/notebook_execution_check.py` to list missing dependencies and, if
  approved, execute named notebooks with `--execute` and a bounded timeout.

## CI and release boundaries

- Test CI runs Python 3.10, 3.11, and 3.13 for the main backend bundle
  `numpy pytorch tensorflow jax mlx.core`, plus `pytensor` on Python 3.10 and
  3.13.
- CI ruff compliance uses a check-only form: `ruff check .` and
  `ruff format . --check`.
- Docs deploy is a GitHub workflow with repository write permission and a
  force deploy command. Treat it as credentialed infrastructure, not a local
  maintainer default.
- PyPI deploy is triggered by a GitHub release and uses `UV_PUBLISH_TOKEN` from
  a secret. Local `uv publish` commands are outside this sub-skill except as a
  boundary warning.
- Safe packaging inspection may run build-only commands in an isolated release
  rehearsal, but never run credentialed publish/deploy steps unless the human
  maintainer explicitly owns the credentials and authorizes that action.

## Refresh and staleness cues

Refresh this sub-skill if any of these maintainer surfaces change: supported
Python version, Hatch envs or scripts, native test runner semantics, backend
synonyms, `EINOPS_TEST_BACKENDS` parsing, notebook execution script, README docs
conversion, mkdocs configuration, CI matrices, or docs/PyPI deploy workflows.

## Bundled files

- [references/docs-and-tests.md](references/docs-and-tests.md): command matrix,
  backend semantics, docs/notebook workflow, CI notes, and deploy boundaries.
- [references/maintainer-troubleshooting.md](references/maintainer-troubleshooting.md):
  failure diagnosis for backends, environments, docs mutation, notebooks, and
  release credentials.
- [scripts/run_selected_einops_tests.py](scripts/run_selected_einops_tests.py):
  safe dry-run wrapper around native package tests with optional focused pytest
  targets.
- [scripts/convert_readme_for_docs.py](scripts/convert_readme_for_docs.py):
  dry-run-first README-to-docs converter adapted from the repository script.
- [scripts/notebook_execution_check.py](scripts/notebook_execution_check.py):
  dependency checker and optional bounded notebook executor.
