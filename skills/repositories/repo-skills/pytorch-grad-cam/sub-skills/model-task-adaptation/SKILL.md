---
name: model-task-adaptation
description: "Routes pytorch-grad-cam adaptation for ViT, Swin, CLIP, object
  detection, semantic segmentation, embeddings, custom targets, and reshape
  transforms."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Model and Task Adaptation

Use this sub-skill when the model output or intermediate activation is not an
ordinary CNN feature map plus classification logits. It covers transformer token
reshaping, CLIP prompt scoring, HuggingFace/timm optional dependencies, object
detection and segmentation targets, embeddings/similarity outputs, and custom
callables.

## Read first

- [`references/target-and-reshape-reference.md`](references/target-and-reshape-reference.md)
  for target callable and reshape contracts.
- [`references/transformer-and-clip-workflows.md`](references/transformer-and-clip-workflows.md)
  for ViT, SwinT, CLIP, and optional dependency patterns.
- [`references/detection-segmentation-embeddings.md`](references/detection-segmentation-embeddings.md)
  for Faster R-CNN, semantic segmentation, embedding outputs, and DFF routing.
- [`references/troubleshooting.md`](references/troubleshooting.md) for shape,
  dtype, device, and missing optional dependency failures.
- Run [`scripts/validate_reshape_transform.py`](scripts/validate_reshape_transform.py)
  before integrating a new token-to-spatial transform.

## Adaptation contract

1. Identify the tensor or structured output whose scalar should be explained.
2. Write a target callable that reduces that output to one scalar per batch item.
3. Identify the activation shape at the chosen target layer.
4. If it is not already spatial `B x C x H x W`, pass a `reshape_transform`
   that removes non-spatial tokens and transposes to channel-first layout.
5. Verify output shapes and device/dtype behavior with synthetic tensors before
   downloading external models or running expensive examples.

Do not select a final transformer block blindly: if the classifier reads only a
class token, patch gradients at the final block can be zero. Use the nearest
pre-head spatially meaningful layer and validate it.
