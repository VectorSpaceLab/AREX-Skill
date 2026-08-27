---
name: advanced-backends-and-performance
description: "Choose Hummingbird advanced backends and performance options:
  TorchScript, TVM, CUDA, threading, batching, and benchmark boundaries."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Advanced Backends and Performance

Use this sub-skill when a Hummingbird task asks for TorchScript, TVM, CUDA/GPU execution, threading, batching, backend availability checks, or performance/benchmark guidance beyond the default CPU PyTorch path.

Natural triggers include: `torchscript backend`, `torch.jit`, `convert to TVM`, `device='cuda'`, `model.to('cuda')`, GPU acceleration, `n_threads`, `batch_size`, `TVM_MAX_FUSE_DEPTH`, `TVM_PAD_INPUT`, and performance benchmark requests.

## First route the task

- Basic `hummingbird.ml.convert(...)` syntax, CPU PyTorch quick starts, and general prediction parity checks: [core conversion](../core-conversion/SKILL.md).
- ONNX output details, ONNX-ML input models, and save/load/integrity workflows: [ONNX and model I/O](../onnx-and-model-io/SKILL.md).
- LightGBM, XGBoost, Prophet, SparkML, or optional source dependency setup: [optional source models](../optional-source-models/SKILL.md).

## Backend decision checkpoint

1. Prefer `backend="torch"`/`"pytorch"` for the lowest-friction local conversion and CPU validation.
2. Use `backend="torch.jit"` or `"torchscript"` when the user needs a traced TorchScript artifact, TorchServe-style deployment, or a JIT-stabilized runtime. Provide representative `test_input`.
3. Use `backend="onnx"` for ONNX runtime/export concerns, then route detailed model I/O to [ONNX and model I/O](../onnx-and-model-io/SKILL.md). Non-ONNX source models need representative `test_input`.
4. Use `backend="tvm"` only in a prepared TVM-capable environment. Provide representative `test_input`; treat its row count and shape as part of the compiled contract.
5. Use `device="cuda"` or `converted_model.to("cuda")` only after proving the installed PyTorch build exposes CUDA and at least one visible CUDA device.

## Required bundled references and helper

- [Advanced backend choices](references/advanced-backends.md) — backend aliases, `test_input` requirements, CUDA and TVM selection rules.
- [Performance and batching](references/performance-and-batching.md) — `N_THREADS`, `BATCH_SIZE`, `convert_batch`, fixed-shape TVM prediction, and benchmark boundaries.
- [Troubleshooting](references/troubleshooting.md) — common advanced-backend failures and safe recovery steps.
- [Backend probe script](scripts/check_backends.py) — safe import/probe helper for backend aliases, torch CUDA status, and TVM importability.

## Safe operating pattern

Run the bundled probe before promising GPU or TVM support:

```bash
python scripts/check_backends.py --json
```

Only run the optional CUDA tensor smoke when the user explicitly wants a device-level check and the environment should touch CUDA:

```bash
python scripts/check_backends.py --json --cuda-smoke
```

If CUDA or TVM is absent, do not install packages blindly. Report the missing backend and give the user the compatibility decision they must make, especially for CUDA-specific PyTorch wheels and TVM's Python-version constraints.
