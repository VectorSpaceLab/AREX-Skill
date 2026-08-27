---
name: repository-development
description: "Edit RF-DETR source while following project contribution, test,
  style, docs, packaging, model-selection, and CI conventions."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# RF-DETR Repository Development

Use this sub-skill when you are changing RF-DETR source, tests, docs, packaging,
or CI. It is for contributor workflows, not for end-user inference, training, or
export recipes.

## Start Here

1. Read [Contributor guidance](references/contributor-guidance.md) before editing
   source, tests, docs, package metadata, or workflow files.
2. Use [Test selection](references/test-selection.md) to choose focused checks
   during development and full gates before handoff.
3. If a check fails or optional backends are involved, use
   [Troubleshooting](references/troubleshooting.md).
4. To get a dry recommendation from changed paths, run:

```bash
python sub-skills/repository-development/scripts/select_checks.py PATH [PATH ...]
```

The script prints commands only; it does not run tests or modify files.

## Routing

- For Python source, tests, examples, docs snippets, or configs, start with
  [Contributor guidance](references/contributor-guidance.md), then choose checks
  from [Test selection](references/test-selection.md).
- For test helpers, fixtures, parametrization, or markers, read
  [test style](references/contributor-guidance.md#test-style) and the
  [test tree map](references/test-selection.md#test-tree-map).
- For package metadata, extras, lock/dependency behavior, or CI install plans,
  read [optional backend guidance](references/contributor-guidance.md#dependencies-and-optional-backends)
  and [dependency checks](references/test-selection.md#dependency-packaging-docs-and-ci-checks).
- For documentation pages or MkDocs config, read
  [docs/build guidance](references/contributor-guidance.md#docs-builds-and-package-builds)
  and [docs troubleshooting](references/troubleshooting.md#docs-build-failures).
- For pre-commit, ruff, mypy, license headers, docstrings, or formatting, read
  [code quality rules](references/contributor-guidance.md#code-quality-rules) and
  [style troubleshooting](references/troubleshooting.md#pre-commit-and-style-failures).
- For CI-only GPU/XLA/CoreML/ExecuTorch/TensorRT failures, use the
  [CI/backend split](references/test-selection.md#ci-and-backend-split) and
  [backend troubleshooting](references/troubleshooting.md#optional-backend-and-ci-failures).

## Non-Negotiables

- Use TDD: failing test first for bug fixes; comprehensive tests for features.
- Every new or changed function/class needs type hints and a Google-style
  docstring; do not duplicate types inside docstrings.
- Python files need the RF-DETR license header.
- Run `pre-commit run --all-files` before any commit/handoff.
- Default examples/docs/tests to `RFDETRSmall` / `"rfdetr-small"`; do not add new
  `RFDETRBase`, `"rfdetr-base"`, segmentation preview, or detection preview usage.
  Keypoint preview is the only preview variant to use for new material.
- Keep imports direct and module-scope unless there is a clear optional-dependency,
  circular-import, import-behavior-test, or startup-side-effect reason.
- Prefer small visible duplication over a helper that adds indirection without
  reducing cognitive load.
