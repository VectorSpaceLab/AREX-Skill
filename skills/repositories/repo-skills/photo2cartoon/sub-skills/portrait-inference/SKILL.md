---
name: portrait-inference
description: "Run, adapt, and troubleshoot Photo2Cartoon portrait inference
  across PyTorch weights, ONNX weights, and Cog-like predictor surfaces."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Portrait Inference

Use this sub-skill when you need to work with the model-side half of Photo2Cartoon:

- validate or run the portrait checkpoints
- choose between PyTorch and ONNX inference
- understand the Cog-style prediction surface
- debug asset placement, device/provider selection, and output validation

Do not use this sub-skill for face detection, crop expansion, alignment, or segmentation math. Those details belong to the preprocessing sub-skill. Do not use it for training or checkpoint generation; that belongs to the data-and-training sub-skill. Do not use it for architecture internals; that belongs to the model-internals sub-skill.

## Quick route

1. Check the asset set with [`scripts/check_photo2cartoon_assets.py`](scripts/check_photo2cartoon_assets.py).
2. Run the PyTorch recipe with [`scripts/pytorch_inference_recipe.py`](scripts/pytorch_inference_recipe.py).
3. Run the ONNX recipe with [`scripts/onnx_inference_recipe.py`](scripts/onnx_inference_recipe.py).
4. Read [`references/cog-and-api-reference.md`](references/cog-and-api-reference.md) when adapting the Cog predictor surface.
5. Read [`references/troubleshooting.md`](references/troubleshooting.md) when inference fails.

## Contract

- Required external assets: `photo2cartoon_weights.pt`, `photo2cartoon_weights.onnx`, `seg_model_384.pb`.
- Input assumption: this sub-skill consumes the face crop produced upstream, not the raw face-crop algorithm itself.
- The model-side tensor is a resized `256 x 256` face patch with alpha mask compositing.
- PyTorch normalization: `face = (face * mask + (1 - mask) * 255) / 127.5 - 1`.
- Postprocess: rescale back to `uint8`, composite against white, then save the RGB image.
- ONNX names: input `input`, output `output`.
- Cog surface: `Predictor.predict(photo: Path)` returns an output path or `None` when no face is detected.

## Validation

- Run the asset checker before attempting a real inference.
- Confirm the saved image exists, can be decoded, and has nonzero width and height.
- Treat no-face errors as upstream input issues, not model failures.
- Treat provider, device, and load failures as configuration issues before touching model internals.

## References

- [Inference workflows](references/inference-workflows.md)
- [Cog and API reference](references/cog-and-api-reference.md)
- [Troubleshooting](references/troubleshooting.md)

## Notes

- Scripts are safe by default: no downloads, no training, and no destructive writes.
- Pass explicit checkout paths and asset paths when validating a repository checkout.
- Keep preprocessing details in the preprocessing sub-skill and keep architecture internals in the model-internals sub-skill.
