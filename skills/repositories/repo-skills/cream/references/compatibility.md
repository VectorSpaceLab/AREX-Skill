# Compatibility and Inspection Notes

## Purpose

Read this when you need to know which runtime features were verified in the inspection environment and which ones remain legacy or optional.

## Verified inspection baseline

- Python 3.11 in an isolated Conda prefix.
- CUDA-capable torch runtime was available during inspection: `torch 2.13.0+cu130` with `torchvision 0.28.0`.
- `torch.cuda.is_available()` returned `True` on an NVIDIA A100-SXM4-40GB host.
- `timm 0.4.12`, `yacs 0.1.8`, `easydict 1.13`, `ftfy`, `regex`, `webdataset`, `huggingface_hub`, `submitit`, `fvcore`, `onnx`, `onnxruntime`, `scikit-image`, `opencv-python`, `pandas`, and `thop` were available in the inspection environment.
- `open_clip_torch 2.0.2` was available during inspection and imported as `open_clip`.

## Legacy / optional compatibility findings

- **AutoFormer, Cream, and CDARTS** use older torch-era imports such as `torch._six`. Live inspection under modern torch required a temporary compatibility shim.
- **CDARTS benchmark201** also expects `apex` and a NAS-Bench-201 API file; the benchmark search path was treated as advanced and optional.
- **MiniViT** and **iRPE** emit a warning when `rpe_ops` is not built. The Python fallback remains usable, but the CUDA extension is an optional accelerator path.
- **EfficientViT downstream** uses MMDetection/MMCV-style dependencies. The classification path is lighter; the downstream path is a separate, heavier stack.

## Practical implications

- Use the bundled scripts and subskill references for the supported workflows.
- Treat old `torch._six`-dependent scripts as legacy workflows whose source code may need a compatibility shim or a historical torch runtime.
- Do not assume every project in the monorepo shares the same dependency stack; the repo intentionally mixes modern and legacy ML code.
