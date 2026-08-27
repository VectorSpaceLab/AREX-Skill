---
name: model-catalog
description: "Select PINTO_model_zoo models by task family, model
  number/directory/name, format flags, and remarks without reopening source
  evidence."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Model Catalog

Use this sub-skill when the task is to shortlist a model from the bundled catalog, interpret format flags, or map a loose request like `ONNX hand pose` or `132_YOLOX` to a concrete folder.

## Fast route

1. Check the license gate first: do not recommend a model for use, redistribution, or execution until the target folder's license terms are acceptable.
2. Query the bundled helper for a short list:

   ```bash
   python ../../scripts/query_model_catalog.py --category "2D/3D Hand Detection" --format ONNX
   python ../../scripts/query_model_catalog.py --format OV --contains pose
   python ../../scripts/query_model_catalog.py --number 132
   python ../../scripts/query_model_catalog.py --directory 132_YOLOX
   python ../../scripts/query_model_catalog.py --list-formats
   ```

3. Read [references/catalog-selection.md](references/catalog-selection.md) for category, flag, directory, name, and remark semantics.
4. Read [references/troubleshooting.md](references/troubleshooting.md) when a filter returns no match, a folder number is ambiguous, a backend flag does not fit the target runtime, or the remarks imply a resolution/input constraint.
5. Hand off to `../model-acquisition/` for downloads and artifact handling, `../inference-demos/` for running an existing model, or `../conversion-and-deployment/` for format conversion, quantization, or deployment planning.

## Boundary with sibling sub-skills

- Need to find or rank candidates only -> stay here.
- Need download scripts, artifact acquisition, or cookie/network planning -> `../model-acquisition/`.
- Need to run an existing demo/test script or interpret runtime output -> `../inference-demos/`.
- Need to convert, quantize, export, or deploy a model artifact -> `../conversion-and-deployment/`.

## What stays here

- catalog lookup and shortlist generation
- format legend interpretation
- no-network model selection
- resolution/shape hint reading from remarks
- number/directory/name mapping

## Bundled files

- [references/model-catalog.json](../../references/model-catalog.json) — the self-contained catalog data.
- [references/catalog-selection.md](references/catalog-selection.md) — selection rules, filter examples, and flag meanings.
- [references/troubleshooting.md](references/troubleshooting.md) — common failure modes and recovery steps.
- [../../scripts/query_model_catalog.py](../../scripts/query_model_catalog.py) — offline query helper for the bundled catalog.
