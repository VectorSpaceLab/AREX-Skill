# Image-processing troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Output is saturated or nearly all 1.0 after preprocessing | A float tensor in `[0,255]` was treated as `[0,1]`. | Convert once with `x = x.float() / 255` before Kornia float image APIs. |
| `KORNIA_CHECK` or shape error about dimensions | HWC or BHWC data was passed where CHW/BCHW was expected. | Move channels before the call: `x = x.permute(0,3,1,2)` for BHWC, or `x = x.permute(2,0,1)` for HWC. |
| `write_image` rejects dtype or extension | PNG/JPEG paths do not write float32 tensors; unsupported suffix or dtype. | For PNG/JPEG use `(x.clamp(0,1)*255).to(torch.uint8)`. Use TIFF for float32 output. |
| Image I/O import or runtime error mentions Rust backend | `kornia_rs` is missing or cannot decode the file. | Install base Kornia dependencies and confirm `import kornia_rs`; try a supported png/jpg/tiff file. |
| Morphology kernel device mismatch | Kernel tensor was created on CPU while image is on CUDA. | Create/move the kernel with `kernel = kernel.to(image.device)`. |
| Half precision fails in a filter/enhance path | The selected PyTorch kernel, FFT, or linalg path lacks half/bfloat16 support. | Re-run that operation in float32, or isolate low-precision tests per backend before claiming support. |
| Color conversion gives unexpected colors | BGR input was treated as RGB or alpha was silently ignored elsewhere. | Convert explicitly with `bgr_to_rgb`/`rgba_to_rgb` before other color-space conversions. |
| Canny/Sobel output shape surprises downstream code | Some edge APIs return multiple outputs or channel-preserving maps. | Check the exact API return type and assert shape immediately after the call. |

## Debugging sequence

1. Print `tensor.shape`, `tensor.dtype`, `tensor.device`, `tensor.min()`, and `tensor.max()`.
2. Convert layout/range before retrying; do not patch downstream code around a bad input contract.
3. Run `scripts/processing_smoke.py --device cpu` to check the installed package independently of the failing project data.
4. If CPU passes and CUDA/MPS fails, classify it as backend-specific and retry with float32 on the target device before lowering precision.
