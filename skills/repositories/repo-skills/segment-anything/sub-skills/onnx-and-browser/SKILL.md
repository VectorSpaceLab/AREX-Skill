---
name: onnx-and-browser
description: "Export Segment Anything's prompt encoder and mask decoder to ONNX,
  quantize it, prepare matching image embeddings, and wire the model into
  ONNXRuntime or browser workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# ONNX and Browser Workflows

Use this sub-skill when the user asks to export SAM to ONNX, quantize a SAM ONNX model, run the mask decoder in ONNXRuntime Web, prepare a `.npy` image embedding for a browser demo, or diagnose ONNX/browser input shape issues.

## Route First

- For prompted Python inference with `SamPredictor.predict`, use `../prompted-segmentation/` unless ONNX export or embeddings are part of the request.
- For full-image automatic mask generation with `SamAutomaticMaskGenerator`, use `../automatic-mask-generation/`.
- For browser workflows, export both a mask decoder ONNX file and image embeddings produced by the same checkpoint/model type/image preprocessing path.

## Fast Paths

- Export ONNX with `python sub-skills/onnx-and-browser/scripts/export_onnx_model.py --checkpoint sam_vit_h_4b8939.pth --model-type vit_h --output sam_onnx.onnx`.
- Quantize for browser size/runtime with `--quantize-out sam_onnx_quantized.onnx`; this requires `onnxruntime` because quantization uses ONNXRuntime tooling.
- Prepare a matching embedding by adapting `scripts/prepare_embedding_template.py`; save the `.npy` beside the browser image asset.
- In browser feeds, use input names `image_embeddings`, `point_coords`, `point_labels`, `mask_input`, `has_mask_input`, and `orig_im_size`.

## References

- `references/onnx-export.md` explains export flags, tensor contracts, dynamic axes, quantization, and embedding compatibility.
- `references/browser-demo.md` explains browser asset layout, ONNXRuntime Web feeds, scaling, and SharedArrayBuffer headers.
- `references/api-reference.md` summarizes `SamOnnxModel`, export-script behavior, input/output names, and expected shapes.
- `references/troubleshooting.md` maps common export/runtime/browser errors to concrete fixes.

## Bundled Scripts

- `scripts/export_onnx_model.py` is an adapted export helper with safe `--help` behavior and clearer optional-dependency errors.
- `scripts/prepare_embedding_template.py` is a template for exporting a `.npy` image embedding from `SamPredictor` for ONNX/browser use.
