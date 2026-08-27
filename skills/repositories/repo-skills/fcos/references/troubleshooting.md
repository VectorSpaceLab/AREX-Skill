# FCOS Cross-Cutting Troubleshooting

## When to read

Read this when FCOS installation, import, compiled extension, CUDA, model download, or dependency compatibility blocks a workflow before a sub-skill can proceed.

## Fast triage

1. Run the bundled environment diagnostic:
   ```bash
   python scripts/check_fcos_environment.py --config configs/fcos/fcos_imprv_R_50_FPN_1x.yaml
   ```
2. If `fcos_core.config` works but `fcos_core._C` fails, config/data guidance can continue, but real detector inference and many model/layer tests are not verified.
3. If `fcos.FCOS` fails on modern PyTorch, check for older API drift such as `torch._six.PY3` and moved `_download_url_to_file` helpers before changing FCOS model code.

## Common failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ImportError: cannot import name '_C' from 'fcos_core'` | The C++/CUDA extension was not built or is not on the runtime library path. | Reinstall FCOS from source with a compatible PyTorch/CUDA/compiler stack. Import `torch` before probing `_C`. Do not treat pure config imports as proof of detector inference. |
| `libc10.so: cannot open shared object file` | The extension was built against PyTorch but PyTorch shared libraries are not visible. | Import `torch` first in the same Python process; for manual shell checks, ensure the environment that built the extension is active and PyTorch libraries are discoverable. |
| `torch._six` or `_download_url_to_file` attribute/import errors | FCOS was written for older PyTorch APIs. | Prefer an older supported PyTorch stack for real runs, or patch compatibility deliberately in a maintainer workflow after reading `internals-maintenance`. |
| NumPy ABI warning with old PyTorch/TorchVision | Old PyTorch binary was compiled against NumPy 1.x but NumPy 2.x is installed. | Pin `numpy<2` when using older PyTorch/TorchVision wheels. |
| NVCC/GCC build failures or undefined CUDA symbols | CUDA toolkit, PyTorch CUDA wheel, NVCC, and compiler versions are inconsistent. | Check `nvcc --version`, `gcc --version`, and the PyTorch CUDA version. Align toolkit/compiler versions before rebuilding. |
| Model download hangs or fails | Pretrained weights are fetched from remote URLs. | Download weights explicitly in a user-approved location, pass `MODEL.WEIGHT`, and avoid network in automated verification. |
| Out-of-memory during inference/evaluation | Image size, batch size, model variant, or GPU memory is too large. | Reduce `TEST.IMS_PER_BATCH`, reduce `INPUT.MIN_SIZE_TEST`, use a lighter MobileNet config, or use CPU only for command/config validation. |

## Backend honesty

- CPU config validation is a full substitute for config syntax/schema guidance.
- CPU imports and synthetic prompts are only partial substitutes for real detection; real inference needs the compiled extension, weights, and an image.
- Full benchmark reproduction needs datasets, weights, compiled extension, and suitable GPUs. Do not report AP reproduction from command construction alone.
