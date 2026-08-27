---
name: repo-development
description: "Maintain segmentation_models_pytorch source, docs, and focused
  tests safely inside an SMP checkout."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Repo Development

Use this sub-skill when the task is to edit this repository rather than simply use the installed package: add or change a decoder/model architecture, encoder, loss, metric, docs table, tests, pytest marker selection, Makefile workflow, or contributor-facing docs.

Do not use this sub-skill for ordinary training/inference examples, release publishing, private Hugging Face credentials, or broad benchmark/model generation. For usage-level questions, route to the appropriate sibling runtime sub-skill instead of changing repository files.

## Start Here

1. Identify the changed surface from the request and touched paths: decoder/model, encoder, loss/metric, base module, docs, or tests.
2. Read [references/maintainer-guide.md](references/maintainer-guide.md) for source ownership, metadata, Make targets, docs table generation, and safe maintainer boundaries.
3. Use [references/test-selection.md](references/test-selection.md) to choose the smallest useful `pytest`, `ruff`, and docs commands before considering broad `make test` or marker-heavy runs.
4. Run `python sub-skills/repo-development/scripts/list_changed_test_focus.py <changed-path>...` from the generated skill root, or copy the script path from this sub-skill, to get JSON command suggestions from explicit changed files.
5. If a command fails or looks unexpectedly slow/networked, check [references/troubleshooting.md](references/troubleshooting.md) before widening scope.

## Editing Checklist

- Keep package code under `segmentation_models_pytorch/` and tests under `tests/`; update docs in `docs/*.rst` and generated tables only when the changed surface requires it.
- Preserve public API exports in `segmentation_models_pytorch/__init__.py`, decoder package `__init__.py` files, `segmentation_models_pytorch/encoders/__init__.py`, `losses/__init__.py`, and `metrics/__init__.py` when adding new public objects.
- Prefer focused tests first: one decoder test file for a decoder change, one encoder test file for an encoder change, `tests/test_losses.py` for losses, `tests/test_preprocessing.py` for preprocessing metadata, and base tests for shared modules.
- Treat `logits_match`, `compile`, `torch_export`, and `torch_script` as opt-in markers; they can be slow, version-gated, or network/cache-sensitive.
- Use `make fixup` or `ruff check --fix` plus `ruff format` for repository style; the configured Ruff settings live in `pyproject.toml`.
- Do not run or recommend `misc/generate_test_models.py` unless the user explicitly asks for maintainer-only Hugging Face model fixture regeneration.
