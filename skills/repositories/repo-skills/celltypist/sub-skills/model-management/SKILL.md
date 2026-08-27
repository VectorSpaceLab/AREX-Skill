---
name: model-management
description: "Manage CellTypist built-in model discovery, local cache behavior,
  model pickle inspection, conversion, subsetting, markers, and offline test
  fixtures."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# CellTypist Model Management

Use this sub-skill when a task is about locating, downloading, loading, writing, inspecting, converting, subsetting, or smoke-testing CellTypist models.

## Route Quickly

- Read [model reference](references/model-reference.md) for cache paths, remote downloads, `Model.load`, `Model.write`, prediction labels/probabilities, and marker extraction.
- Read [conversion and subsetting](references/conversion-and-subsetting.md) before changing species, gene identifiers, or retained cell types; these methods mutate the loaded model in place.
- Use [troubleshooting](references/troubleshooting.md) for cache/network surprises, invalid pickle files, missing map files, conversion column mistakes, invalid collapse modes, and subset constraints.
- Run [model_cache_check.py](scripts/model_cache_check.py) to inspect the active `CELLTYPIST_FOLDER` model cache or verify a local model pickle without downloading anything.
- Run [tiny_model_factory.py](scripts/tiny_model_factory.py) to create a tiny offline-compatible CellTypist model pickle for smoke tests and examples.

## Stay In Scope

- Stay here for `celltypist.models`, built-in model inventory/download/cache behavior, `Model` object persistence and metadata, marker extraction, `Model.convert`, and `Model.subset`.
- Route annotation with a selected model to [annotation-workflows](../annotation-workflows/SKILL.md).
- Route training a new real reference model to [training-and-custom-models](../training-and-custom-models/SKILL.md).
- Route result tables, AnnData insertion, UMAPs, dotplots, or interpretation of finished predictions to [visualization-and-results](../visualization-and-results/SKILL.md).

## Offline-First Pattern

For offline work, avoid implicit default-model resolution and pass an explicit local model path containing a forward slash, such as `./local_model.pkl` or `Path("local_model.pkl").resolve().as_posix()`.

```python
from pathlib import Path
from celltypist import models

model_path = Path("local_model.pkl").resolve().as_posix()
model = models.Model.load(model_path)
print(model.cell_types)
print(model.features[:5])
```

If a task may run without network access, inspect cache state first:

```bash
python scripts/model_cache_check.py --verify-model ./local_model.pkl
```
