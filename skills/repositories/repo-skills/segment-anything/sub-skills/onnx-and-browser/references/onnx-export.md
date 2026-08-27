# ONNX Export

SAM exports only the prompt encoder and mask decoder path, not the image encoder. The ONNX model consumes a precomputed image embedding plus prompt tensors and returns masks. A browser or ONNXRuntime workflow therefore needs two artifacts generated from the same SAM checkpoint/model type: an ONNX mask decoder and one `.npy` image embedding per image.

## Export Command

Use the bundled helper from this sub-skill:

```bash
python sub-skills/onnx-and-browser/scripts/export_onnx_model.py \
  --checkpoint sam_vit_h_4b8939.pth \
  --model-type vit_h \
  --output sam_onnx.onnx
```

Valid model registry keys are `default`, `vit_h`, `vit_l`, and `vit_b`. The checkpoint must match the selected `--model-type`; for example, a ViT-H checkpoint must be exported with `--model-type vit_h` or `default`.

## Export Flags

- `--opset` defaults to `17`; keep it at `11` or higher because the export path requires ONNX opset >= 11.
- `--return-single-mask` exports only the selected best mask instead of all multimask candidates, which can reduce browser postprocessing work.
- `--gelu-approximate` changes `torch.nn.GELU` to tanh approximation before tracing; use it when the target runtime has slow or unsupported `erf` operations.
- `--use-stability-score` replaces predicted IoU scores with stability scores computed on low-resolution masks.
- `--return-extra-metrics` returns five outputs instead of three: masks, scores, stability scores, areas, and low-resolution logits.
- `--quantize-out path.onnx` writes a dynamically quantized copy using ONNXRuntime quantization tools.

## Quantization

Quantization is optional but common for browser delivery:

```bash
python sub-skills/onnx-and-browser/scripts/export_onnx_model.py \
  --checkpoint sam_vit_b_01ec64.pth \
  --model-type vit_b \
  --output sam_vit_b.onnx \
  --quantize-out sam_vit_b_quantized.onnx
```

`--quantize-out` requires `onnxruntime`; the plain ONNX export requires `onnx` and PyTorch ONNX export support. Install optional dependencies such as `onnx` and `onnxruntime` in the environment doing the export.

## Embedding Compatibility Rule

Re-export the image embedding whenever any of these changes:

- checkpoint file
- `model_type`
- input image pixels or orientation
- image preprocessing path used before `SamPredictor.set_image`

A stale embedding can still have the expected shape but produce incorrect masks because the ONNX decoder weights and embedding features no longer correspond.

## Tensor Contract

The exported model input names are:

- `image_embeddings`: float tensor shaped `[1, embed_dim, 64, 64]` for standard SAM image size 1024, where `embed_dim` is typically 256.
- `point_coords`: float tensor shaped `[1, num_points, 2]`, in resized SAM coordinates, with dynamic axis 1 named `num_points`.
- `point_labels`: float tensor shaped `[1, num_points]`, with dynamic axis 1 named `num_points`; labels are prompt labels such as positive point `1`, negative point `0`, box corners `2` and `3`, and padding `-1`.
- `mask_input`: float tensor shaped `[1, 1, 256, 256]`; use zeros for the first prompt round.
- `has_mask_input`: float tensor shaped `[1]`; use `[0]` when `mask_input` is empty and `[1]` when providing previous low-resolution logits.
- `orig_im_size`: float tensor shaped `[2]` as `[height, width]` in original image pixels.

Default output names are `masks`, `iou_predictions`, and `low_res_masks`. With `--return-extra-metrics`, expect `masks`, `iou_predictions`, `stability_scores`, `areas`, and `low_res_masks`.
