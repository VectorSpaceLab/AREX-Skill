---
name: programmatic-api
description: "Guide Python users who want to call Matching, SuperPoint,
  SuperGlue, and the geometry/plotting utilities directly."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Programmatic API

Use this sub-skill when you want to write Python code against the model classes and helper utilities instead of using the batch CLI or live demo.

## In scope

- `models.Matching(config={})` composition and `forward(data)` behavior.
- `models.SuperPoint` and `models.SuperGlue` configs, weights, and output contracts.
- Direct inference on grayscale float tensors with shape `1x1xHxW`.
- Output tensors, unmatched id `-1`, and confidence interpretation.
- Utility functions for image loading, resizing, pose estimation, pose error, AUC, and plotting.
- CPU/CUDA device choice, `eval()`, and `torch.no_grad()` inference.

## Route elsewhere

- Batch image-pair CLI, pair files, `.npz` dumps, and pose-evaluation tables -> [pair-matching-evaluation](../pair-matching-evaluation/SKILL.md)
- Webcam, IP camera, video, or directory demo and visualization controls -> [live-demo-and-visualization](../live-demo-and-visualization/SKILL.md)
- Training code, retraining, or checkpoint editing -> unavailable in this repo

## Bundled references

- [API reference](references/api-reference.md)
- [Workflow patterns](references/workflows.md)
- [Troubleshooting](references/troubleshooting.md)

## Bundled helpers

- `scripts/inspect_superglue_api.py`
- `scripts/run_matching_api_smoke.py`

## Practical rule of thumb

Keep the model and inputs on the same device, use `model.eval()` plus `torch.no_grad()`, and start with a single image pair unless you have already normalized feature lengths across the batch.

The shipped checkpoints live with the repo, so the helpers do not download anything.

Preserve the repository license terms when reusing the bundled code or checkpoints.
