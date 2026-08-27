---
name: model-enrichment
description: "Guide fastdup workflows for embeddings, feature-vector search,
  captions, OCR, and zero-shot visual enrichment."
metadata:
  disco-role: operating
disable-model-invocation: true
license: NOASSERTION
---

# model-enrichment

Use this sub-skill when the task is about model-assisted visual analysis rather than plain duplicate cleanup.

## Use when

The request mentions any of the following:

- TIMM or ONNX embeddings
- precomputed feature vectors
- image search or vector search
- captions, VQA, or age labeling
- zero-shot classification, detection, or segmentation
- OCR or text-aware enrichment
- `init_search`, `search`, `vector_search`, `caption`, or `enrich`

## Typical workflow

1. Decide whether the task is a pure feature-vector path or a model-backed path.
2. For feature-vector work, save or load the binary features first.
3. For model-backed work, confirm the optional dependency set before running anything expensive.
4. Keep the input small until the model helper is proven in the current environment.
5. Export or visualize the results only after the model output columns look correct.

## What to read

- `../../references/api-reference.md` for `init_search`, `search`, `vector_search`, and the gallery APIs
- `../../references/data-formats.md` for binary feature layout and search-related output files
- `../../references/workflows.md` for the model-enrichment workflow family
- `../../references/tensorboard-projector.md` when TensorBoard projector output is requested
- `../../references/troubleshooting.md` for optional dependency and model-download failures
- `references/troubleshooting.md` in this sub-skill for model-specific caveats

## Bundled scripts

- `../../scripts/run_feature_vector_smoke.py` — verify the binary feature round-trip used by search workflows
- `../../scripts/run_search_smoke.py` — exercise `init_search`, `search`, and `vector_search` on a tiny synthetic fixture
- `../../scripts/export_tensorboard_projector_smoke.py` — optional projector smoke when TensorFlow is already installed

## Common decisions

- Use `save_binary_feature`/`load_binary_feature` when the vector matrix already exists.
- Use `init_search` + `search` for image search over a prepared index.
- Use `vector_search` when the query is itself a vector.
- Keep `d` aligned with the actual feature width; mismatches will fail.
- Treat captions, OCR, and zero-shot helpers as optional extras that may require additional packages or downloaded weights.
- Treat TensorBoard projector output as an optional workflow that only applies when TensorFlow is installed.

## Known limitation

Model-heavy helpers are optional. If the environment does not have the relevant extra installed, stay on the binary-feature, search, or documented-reference path instead of claiming a model-backed run succeeded.
