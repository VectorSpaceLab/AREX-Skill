---
name: optimization-building-blocks
description: "Routes advanced keras-vis customization requests that combine
  custom losses, regularizers, Optimizer control, input or gradient modifiers,
  backprop modifiers, and callbacks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---
# optimization-building-blocks

Use this sub-skill for low-level optimization pieces that sit underneath the higher-level activation and saliency flows.

## Route away first
- For high-level activation maximization requests, use [activation-maximization](../activation-maximization/SKILL.md).
- For saliency maps or Grad-CAM, use [saliency-and-cam](../saliency-and-cam/SKILL.md).
- For image loading, drawing, stitching, and display helpers, use [image-utilities](../image-utilities/SKILL.md).

## Stay here for
- Writing custom `Loss.build_loss()` implementations.
- Combining weighted loss tuples with `Optimizer`.
- Choosing `wrt_tensor`, `grad_modifier`, `input_modifiers`, and callbacks.
- Using `ActivationMaximization`, `TotalVariation`, `LPNorm`, `Jitter`, `Print`, `GifGenerator`, and gradient/backprop modifiers directly.
- Debugging TensorFlow guided/rectified backprop overrides, graph mode, and optional callback dependencies.

## Reference map
- API signatures and constraints: [references/api-reference.md](references/api-reference.md)
- Practical workflow and composition rules: [references/customization-guide.md](references/customization-guide.md)
- Known failures and fixes: [references/troubleshooting.md](references/troubleshooting.md)
- Best-effort deterministic smoke check: [scripts/optimizer_smoke.py](scripts/optimizer_smoke.py)

## Guardrails
- `Optimizer.minimize()` uses a fixed RMSProp-style loop with internal loss weighting; it only updates the input tensor itself.
- When `wrt_tensor` is not the input tensor, treat the loop as a gradient probe and read `grads` / `wrt_value`.
- `verbose=True` already adds the bundled `Print` callback.
- TensorFlow backprop modifiers require graph mode and do not support advanced activations here.
- `GifGenerator` needs both `imageio` and Pillow at runtime.
