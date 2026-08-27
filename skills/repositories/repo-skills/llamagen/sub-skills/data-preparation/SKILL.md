---
name: data-preparation
description: "Router for ImageNet code extraction, T5 feature extraction, and
  OpenImages manifest generation."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# Data Preparation

Use this sub-skill for released preprocessing workflows that precompute caches and manifests for LlamaGen training.

## Owns
- ImageNet discrete-code extraction for c2i training.
- T5 feature extraction for t2i training.
- OpenImages path-manifest generation.
- Cache layout and sanity checks for the precomputed `.npy` trees and `image_paths.json`.

## Routes out
- Tokenizer training, finetuning, reconstruction, and code/image decode checks -> `tokenizers`.
- Class-conditional training, sampling, serving, and evaluation -> `class-conditional`.
- Text-conditional training, sampling, and evaluation -> `text-conditional`.
- Checkpoint publishing or remote mutation -> excluded.

## Best entry points
- `scripts/extract_codes_c2i.sh`
- `scripts/extract_flan_t5_feat_laion_coco_stage1.sh`
- `scripts/extract_flan_t5_feat_stage2.sh`
- `scripts/extract_flan_t5_feat_trunc_stage2.sh`
- `scripts/build_openimage_index.py`

## Read before answering
- `references/workflows.md`
- `references/cli-reference.md`
- `references/dataset-layout.md`
- `references/troubleshooting.md`

## Fast routing rules
- If the request asks for tokenizer reconstruction, tokenizer training, or code/image round trips, route to `tokenizers`.
- If the request asks for c2i or t2i model training, sampling, serving, or evaluation, route to `class-conditional` or `text-conditional`.
- If the request asks for model publishing, remote uploads, or other side effects, treat it as out of scope.
- Keep the focus on deterministic preprocessing, cache layout, and manifest generation.
