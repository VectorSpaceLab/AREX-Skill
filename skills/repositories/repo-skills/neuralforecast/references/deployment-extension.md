# Deployment and Extension

## Purpose

Read this when the task is about persistence, loading saved models, extending
NeuralForecast with a new model, or using optional export/logging workflows.

## Core deployment path

- `NeuralForecast.save(path, overwrite=False, save_dataset=True)` writes a fitted
  model bundle.
- `NeuralForecast.load(path, verbose=False, **kwargs)` restores that bundle.
- Use `overwrite=True` only when you are intentionally replacing an existing
  save directory.

## Safe round-trip mindset

1. Fit a tiny model.
2. Save it to a temporary directory.
3. Load it back.
4. Re-run `predict()` and compare shapes or a small sample.

This is the fastest way to prove the model bundle is portable.

## Optional export and logging surfaces

- ONNX export is documented in the notebooks, but it requires optional packages
  such as `onnx`, `onnxruntime`, and `onnxscript`.
- MLflow logging is documented in the notebooks, but it requires `mlflow` and a
  usable tracking setup.
- These workflows are reference-guidance unless the user explicitly wants the
  optional stack.

## Extending the package

If the user wants to add or modify a model:

- Read `CONTRIBUTING.md` for the repo's maintainer workflow.
- Inspect the model family docs and tests before editing.
- Keep new public behavior aligned with the constructor patterns in
  `model-overview.md` and `api-reference.md`.
- Use a small save/load or training smoke to prove the new model can be
  instantiated and serialized.

## Docs and maintainer notes

- `Makefile` and `docs/to_mdx.py` support docs regeneration.
- `scripts/cli.py` and `scripts/filter_licenses.py` are maintainer-only helper
  scripts, not user-facing runtime helpers.

## Read next

- `workflows.md` for the save/load round-trip and quickstart.
- `troubleshooting.md` for serialization, optional-dependency, and docs issues.
