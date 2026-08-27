---
name: models-and-inference
description: "Route xTuring model selection, loading, saving, generation, and
  backend-specific inference choices."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# models-and-inference

Use this sub-skill when the user needs to pick a supported model key, load a saved checkpoint, tune generation settings, save a model, or choose between base, LoRA, INT8, and K-bit variants.

## Use this for
- `BaseModel.create("<key>")` for supported registry-backed families.
- `BaseModel.load(path)` for saved xTuring checkpoints and bundled `x/...` hub entries.
- `BaseModel.load(path, model_name="<key>")` for a plain Hugging Face checkpoint directory without `xturing.json`.
- `GenericModel` and the other `Generic*` wrappers for arbitrary local or hub checkpoints.
- `model.generate(...)`, `model.save(...)`, and `model.generation_config()`.

## Route elsewhere for
- dataset schemas, dataset conversion, or self-instruct generation -> `data-prep-and-generation`
- fine-tuning, DPO, or trainer configuration -> `training-and-alignment`
- CLI chat, API server, or playground UI -> `cli-api-ui`
- perplexity or adapter-style evaluation -> `evaluation`

## Read first
1. `references/model-catalog.md`
2. `references/inference-workflows.md`
3. `references/troubleshooting.md`
4. `scripts/inspect_xturing_install.py`

## Known gap
- `StableDiffusion` is registered but placeholder-only; instantiating it raises `NotImplementedError`, so do not route users there as a usable inference target.

This sub-skill is self-contained; do not depend on the original source checkout for model-selection or inference guidance.
