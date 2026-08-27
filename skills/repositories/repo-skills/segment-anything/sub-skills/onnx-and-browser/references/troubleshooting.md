# ONNX and Browser Troubleshooting

## Missing `onnx` or `onnxruntime`

- Plain export needs PyTorch ONNX export support and the `onnx` package in many environments.
- Export validation and quantization need `onnxruntime`.
- If `--help` works but export fails during tracing or serialization, install optional export dependencies in the active Python environment.
- If `--quantize-out` fails, install `onnxruntime` and rerun from the original unquantized ONNX file.

## Opset Too Old

The export path requires ONNX opset >= 11. Use the default opset unless a target runtime has a specific compatibility requirement:

```bash
python sub-skills/onnx-and-browser/scripts/export_onnx_model.py --opset 17 ...
```

If a runtime rejects a newer opset, lower gradually but do not go below 11.

## Checkpoint and Model Type Mismatch

Symptoms include load-time key shape errors, failed export, or nonsensical masks. Match the checkpoint family to the registry key:

- ViT-H checkpoint: `vit_h` or `default`
- ViT-L checkpoint: `vit_l`
- ViT-B checkpoint: `vit_b`

After changing checkpoint or model type, re-export both the ONNX model and all image embeddings.

## GELU or `erf` Runtime Issues

Some runtimes have slow or unsupported `erf` operations used by exact GELU. Re-export with:

```bash
python sub-skills/onnx-and-browser/scripts/export_onnx_model.py --gelu-approximate ...
```

This changes GELU modules to tanh approximation before ONNX tracing.

## Shape Mismatch in ONNXRuntime

Check the exact feed names and shapes:

- `image_embeddings`: `[1, 256, 64, 64]` for standard SAM checkpoints.
- `point_coords`: `[1, num_points, 2]` and float32.
- `point_labels`: `[1, num_points]` and float32.
- `mask_input`: `[1, 1, 256, 256]` and float32.
- `has_mask_input`: `[1]` and float32.
- `orig_im_size`: `[2]` and float32 `[height, width]`.

For click-only prompts, append a padding point with label `-1`. Coordinate values must be scaled to the SAM resized image coordinate system using `1024 / max(height, width)`.

## Browser Header or SharedArrayBuffer Failure

If the app reports `SharedArrayBuffer` unavailable or ONNXRuntime Web threading errors, configure response headers:

```http
Cross-Origin-Opener-Policy: same-origin
Cross-Origin-Embedder-Policy: credentialless
```

Also ensure model, wasm, image, and embedding assets are served with headers compatible with cross-origin isolation.

## Image, Embedding, and Model Mismatch

A common browser failure is using a valid embedding from the wrong image or checkpoint. The ONNX session can run but masks appear empty, offset, or unrelated. Regenerate the embedding from the exact image and exact SAM checkpoint used to export the ONNX model.

## Extra Metrics Shape Expectations

`--return-extra-metrics` changes the number of outputs from three to five. Browser code that reads `model.outputNames[0]` for masks may still work, but code that destructures all outputs or expects `low_res_masks` as the third output must be updated.
