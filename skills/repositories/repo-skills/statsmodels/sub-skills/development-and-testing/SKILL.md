---
name: development-and-testing
description: "Use statsmodels source-development guidance for Meson/Cython
  editable builds, focused pytest selection, docs and example maintenance,
  public API checks, docstring validation, warnings, and contributor
  troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# Development and testing

Use this sub-skill only when the user is editing, reviewing, testing, documenting, packaging, or maintaining a statsmodels source checkout. For ordinary installed-package usage, route to the statistical-modeling sub-skills instead.

## Workflow

1. Determine changed areas: package source, Cython extension, docs/notebooks/examples, tests, public API, warnings, or build metadata.
2. Ensure the checkout is built/installed in editable mode after source or Cython changes. Source builds require compiler, Meson, Cython, NumPy/SciPy, and package dependencies.
3. Run focused tests first, then broader tests only when risk justifies it. Do not run the entire suite by default for small edits.
4. For docs/examples, validate code snippets and generated examples without mutating release or credential-bound tooling.
5. Treat `archive/` as deprecated legacy code and `sandbox/` as experimental unless a task explicitly targets them.

## Read or run

- Read [references/maintenance.md](references/maintenance.md) for editable install, docs/example scripts, API checks, docstring validation, and excluded release tooling.
- Read [references/testing-reference.md](references/testing-reference.md) for focused pytest commands, markers, changed-path mapping, and CI considerations.
- Read [references/troubleshooting.md](references/troubleshooting.md) for build, Cython, pytest plugin, warning, and docs failures.
- Run [scripts/focused_test_plan.py](scripts/focused_test_plan.py) with changed paths to print recommended pytest targets; it does not run tests by default.

## Boundaries

- Do not bundle or run release-key, deploy, or broad CI scripts from this skill.
- Do not tell a future agent to execute original `tools/` scripts as runtime user workflow; this sub-skill describes when such maintainer tools exist and how to replace them with safe commands or focused checks.
- Use the model sub-skills to understand behavior before editing model code.
