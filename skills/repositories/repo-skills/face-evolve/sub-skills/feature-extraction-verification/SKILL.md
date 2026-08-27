---
name: feature-extraction-verification
description: "Extract face.evoLVe embeddings from trained PyTorch checkpoints
  and evaluate LFW-style verification metrics."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# feature-extraction-verification

Use this sub-skill when you need to:

- extract embeddings from a trained face.evoLVe PyTorch checkpoint,
- run the torchvision/ImageFolder batch path or the OpenCV single-image path,
- compare v1 and v2 preprocessing, with or without horizontal-flip TTA,
- compute ROC, threshold accuracy, or VAL-style verification metrics from embeddings,
- debug checkpoint, backbone, shape, or pair-layout mismatches.

Do not use this sub-skill to train a model, create checkpoints, download data, or align raw faces first. Route those requests to the other face-evolve sub-skills instead.

## Read / run

- `references/feature-and-verification-workflows.md` — read this first for the end-to-end extraction and verification flow, preprocessing choices, TTA, and `perform_val` semantics.
- `references/api-reference.md` — read this when you need exact function signatures, tensor or array shapes, or metric return values.
- `references/troubleshooting.md` — read this when loading checkpoints, matching backbones, validating pair counts, or locating bcolz-style validation data.
- `scripts/extract_features.py` — run this to produce `.npy` embeddings from a trained checkpoint using either an `ImageFolder` root or a single image file.
- `scripts/evaluate_pairs.py` — run this to score embeddings against an `issame` array and export ROC / accuracy / VAL metrics as JSON.

## Routing boundaries

- Checkpoint creation, backbone training, head/loss selection, and optimizer setup belong to `pytorch-training`.
- Image acquisition, dataset layout, and identity-folder preparation belong to `data-preparation`.
- Alignment or MTCNN crop before feature extraction belongs to `face-alignment`.
- PaddlePaddle extraction or verification requests belong to `paddle-workflows`.

## What this sub-skill guarantees

- Distilled preprocessing for `extract_feature_v1.py` and `extract_feature_v2.py`.
- Explicit horizontal-flip TTA behavior and `l2_norm` normalization.
- Compatibility checks for 512-d face embeddings from IR / IR-SE / ResNet backbones.
- Pairwise verification metrics that expect embeddings in `[img1, img2, img3, img4, ...]` order.
- Safe wrappers that do not depend on the original checkout path at runtime.
