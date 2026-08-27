# Installation and Feature Gates

Read this before giving install advice, diagnosing import failures, or deciding which Torch-TensorRT workflows are available in a user's environment.

## Public package identities

| Purpose | Distribution name | Import path | Notes |
| --- | --- | --- | --- |
| Standard Torch-TensorRT | `torch-tensorrt` | `torch_tensorrt` | Uses NVIDIA TensorRT. This is the default package for Linux x86-64 and Windows GPU workflows. |
| TensorRT-RTX variant | `torch-tensorrt-rtx` | `torch_tensorrt` | Experimental variant for TensorRT-RTX. Same import path, distinct wheel/package flavor. |
| TensorRT Python package | `tensorrt` | `tensorrt` | Required for standard TensorRT workflows. NVIDIA may serve large CUDA-versioned libraries from its package index. |
| TensorRT-RTX Python package | `tensorrt_rtx` | `tensorrt` and `tensorrt_rtx` | Required for the RTX variant. The `torch_tensorrt` import still stays the same. |

The installed package flavor is not visible from `import torch_tensorrt` alone. Probe `torch_tensorrt.ENABLED_FEATURES` and the TensorRT package identity before choosing workflows.

## Basic installs

Use commands appropriate for the user's PyTorch/CUDA stack. Do not mix arbitrary stable and nightly wheels without checking version constraints.

```bash
# Stable-style install; choose a CUDA-compatible PyTorch first.
python -m pip install torch torch-tensorrt tensorrt

# Nightly example for CUDA 13.0-style wheels.
python -m pip install --pre torch torch-tensorrt tensorrt \
  --extra-index-url https://download.pytorch.org/whl/nightly/cu130

# TensorRT-RTX variant. The import path is still torch_tensorrt.
python -m pip install torch torch-tensorrt-rtx
```

For a source checkout, prefer the build/maintenance sub-skill before recommending `pip install .`, because build flags change which features exist.

## Minimal verification

From any project directory:

```bash
python - <<'PY'
import torch
import torch_tensorrt
print('torch', torch.__version__)
print('torch_tensorrt', getattr(torch_tensorrt, '__version__', 'unknown'))
print('features', getattr(torch_tensorrt, 'ENABLED_FEATURES', 'missing'))
print('cuda available', torch.cuda.is_available())
if torch.cuda.is_available():
    x = torch.ones(1, device='cuda')
    torch.cuda.synchronize()
    print('cuda smoke', x.item())
PY
```

Or run the bundled probe:

```bash
python scripts/check_torch_tensorrt_env.py
```

## Feature gates to check

`torch_tensorrt.ENABLED_FEATURES` is a named tuple with these fields in this source snapshot:

| Field | What it means | Typical blocker |
| --- | --- | --- |
| `dynamo_frontend` | Dynamo/ExportedProgram compiler path is available. | PyTorch too old or incompatible. |
| `torchscript_frontend` | Legacy TorchScript frontend library is present. | Python-only or no-TorchScript build. |
| `torch_tensorrt_runtime` | C++ Torch-TensorRT runtime library is present. | Python-only build or missing runtime library. |
| `fx_frontend` | Legacy FX frontend is available. | Disabled in TensorRT-RTX builds. |
| `refit` | Refit APIs are exposed. | Version/platform gating. |
| `qdp_plugin` | Quick Deploy Plugin/custom kernel layer is available. | TensorRT plugin package missing, TensorRT 10.14 known plugin issue, or TensorRT-RTX build. |
| `windows_cross_compile` | Windows cross-compile runtime libraries are available. | Missing cross-compile libraries. |
| `tensorrt_rtx` | The TensorRT-RTX variant is active. | Standard TensorRT package installed instead. |
| `trtllm_for_nccl` | TRT-LLM fallback for NCCL collectives is available. | CUDA/TRT-LLM mismatch or missing packages. |
| `native_trt_collectives` | TensorRT native collectives are available. | TensorRT version too old or runtime library absent. |

## Choosing standard TensorRT vs TensorRT-RTX

Use standard TensorRT when the user needs normal production TensorRT engine behavior, FX frontend compatibility, QDP/plugin workflows, C++ runtime/TorchScript packaging, or deployment targets documented for TensorRT engines.

Use TensorRT-RTX only when the user's target is an RTX desktop/laptop/workstation or they explicitly need RTX runtime settings such as `RuntimeSettings(runtime_cache=..., dynamic_shapes_kernel_specialization_strategy=..., cuda_graph_strategy=...)`. TensorRT-RTX is experimental in Torch-TensorRT and has different feature availability.

## Common install and import failures

| Symptom | Likely cause | Action |
| --- | --- | --- |
| `ModuleNotFoundError: torch_tensorrt` | Package not installed in the active Python environment. | Install a matching `torch-tensorrt` or `torch-tensorrt-rtx` wheel, then run the minimal verification. |
| TensorRT wheel download is extremely large or times out | NVIDIA CUDA-versioned TensorRT libraries are served as large wheels. | Use an NGC PyTorch container, a pre-provisioned TensorRT install, a smaller/matching CUDA wheel, or resume the download outside a tight timeout. |
| `torch-tensorrt` requires a different PyTorch version | PyTorch and Torch-TensorRT wheel metadata do not match. | Install matching stable/nightly builds from compatible indexes; do not treat `pip check` failures as harmless for production. |
| `CUDA-capable device(s) is/are busy or unavailable` | GPU visibility, exclusive mode, MIG, scheduler, or another process. | Check `nvidia-smi`, select an idle `CUDA_VISIBLE_DEVICES`, and retry a tiny PyTorch CUDA allocation before compiling. |
| Quantization ops warn about missing `modelopt` | ModelOpt optional dependency is not installed. | Install the documented ModelOpt extra only when the user needs INT8/FP8/FP4 quantization workflows. |
| TorchScript/C++ runtime APIs raise `NotImplementedError` | Python-only or no-TorchScript build. | Reinstall a wheel/build that includes the runtime, or use Python/Dynamo `.ep` workflows instead. |
| QDP/custom kernel APIs raise availability errors | QDP plugin dependencies or standard TensorRT plugin support are missing. | Use the extensibility sub-skill; verify standard TensorRT, plugin packages, CUDA Python/core deps, and TensorRT version. |

## Inspection limitation from skill generation

The generated skill was drafted with a partial backend proof: imports and one tiny TensorRT-RTX Dynamo compile succeeded, but full standard TensorRT, C++ runtime, QDP, distributed, quantization, and serialization execution were not proven. Treat this as a reason to probe the user's current environment, not as a reason to avoid those documented workflows when their prerequisites are actually satisfied.
