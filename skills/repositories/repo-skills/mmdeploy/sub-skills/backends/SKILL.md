---
name: backends
description: "Select, install, check, and troubleshoot MMDeploy inference
  backends, custom ops, and backend manager availability."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# MMDeploy Backends Router

Use this sub-skill when a task is about choosing an MMDeploy backend, installing
backend packages or vendor toolkits, checking `BackendManager` availability,
building backend custom ops, or recovering from backend-specific failures.

Do not use this sub-skill to orchestrate full model conversion, SDK demo usage,
or regression benchmarking. For those workflows, keep this sub-skill responsible
only for backend readiness and failure diagnosis, then route the actual
conversion, SDK runtime, or validation flow to the owning route.

## Read These First

- [Backend matrix](references/backend-matrix.md) — backend role, device/platform
  fit, CPU substitute status, required packages, tools, environment variables, and
  backend manager checks.
- [Custom ops](references/custom-ops.md) — ONNXRuntime, TensorRT, NCNN, and
  TorchScript custom-op build expectations and symptoms.
- [Troubleshooting](references/troubleshooting.md) — symptom-driven recovery for
  missing packages, missing converter tools, TensorRT profiles, OpenVINO
  `libpython`, TorchScript ABI/cuDNN, vendor toolkits, SDK runtime, config, and
  API misuse.
- [Backend environment checker](scripts/check_env.py) — safe read-only helper
  adapted from MMDeploy's environment checker.

## Route The User Request

1. **Identify the target artifact and device.**
   - ONNX inference on CPU/GPU: ONNXRuntime.
   - TensorRT engine on NVIDIA CUDA/Jetson: TensorRT.
   - `.param`/`.bin` mobile or embedded CPU artifacts: NCNN.
   - OpenVINO IR (`.xml`/`.bin`) on Intel CPU-oriented deployments: OpenVINO.
   - PPL.NN artifacts, usually CUDA-oriented in MMDeploy examples: PPLNN.
   - TorchScript `.pt` artifacts or LibTorch SDK backend: TorchScript.
   - Vendor accelerator artifacts: RKNN, Ascend, CoreML, TVM, VACC, or SNPE.
   - `mmdeploy_runtime` model directories and wrappers: SDK backend manager.
2. **Check backend availability before trying conversion.** Run the bundled
   checker from this sub-skill:

   ```bash
   python scripts/check_env.py --backend tensorrt --with-custom-ops
   python scripts/check_env.py --backend onnxruntime --backend ncnn --json
   ```

   When the package is installed but custom ops are missing, read
   [Custom ops](references/custom-ops.md) before rebuilding anything.
3. **Inspect the deployment config shape.** The relevant key is always
   `backend_config.type`; backend-specific details live under
   `backend_config.common_config`, `backend_config.model_inputs`,
   quantization fields, or Model Optimizer options. TensorRT dynamic profiles
   must include coherent `min_shape`, `opt_shape`, and `max_shape` values for
   every runtime input name.
4. **Install only the backend stack required by the selected target.** Do not
   install all optional backends. Prefer Python package/import checks first,
   then vendor toolkit and CMake/build checks only when SDK runtime or custom
   ops are required.
5. **Stop instead of guessing** when a proprietary toolkit, hardware device,
   driver, cross-compiler, service URI, or SDK runtime is absent and no CPU
   substitute is available.

## Backend Manager Checks

Use manager checks when diagnosing availability or conditional API exports:

```python
from mmdeploy.backend.base import get_backend_manager

manager = get_backend_manager('tensorrt')
print(manager is not None)
print(manager.is_available())
print(manager.is_available(with_custom_ops=True))
print(manager.get_version())
```

Important interpretation rules:

- `is_available()` usually means the Python package or required converter tool
  can be found; it does **not** prove custom ops, SDK runtime, or accelerator
  hardware work.
- `is_available(with_custom_ops=True)` is stricter for ONNXRuntime,
  TensorRT, NCNN, and TorchScript. It can be `False` even when the backend
  package itself is available.
- Backend API modules may export converter functions conditionally. If a backend
  package is unavailable, imports such as `from mmdeploy.apis.tensorrt import
  onnx2tensorrt` may be absent even though `is_available` itself can still be
  imported.
- SNPE manager availability is based on the `onnx2dlc` tool path; version
  reporting is not implemented by its manager.

## Setup Sequence

1. Read the row for the target backend in [Backend matrix](references/backend-matrix.md).
2. Install the Python package(s) and make vendor libraries discoverable through
   the documented environment variables.
3. Run `python scripts/check_env.py --backend <name>`.
4. If the selected model/codebase needs custom ops, run
   `python scripts/check_env.py --backend <name> --with-custom-ops` and use
   [Custom ops](references/custom-ops.md) to build the backend plugin only for
   that backend.
5. Re-run the checker. Continue only when the required manager and custom-op
   state match the target workflow, or record the backend as unavailable with a
   clear stop reason.

## Boundaries And Handoffs

- Backend conversion should be called through the package API or the generated
  conversion route, not through standalone backend converter scripts bundled
  here. This sub-skill intentionally provides no standalone `onnx2*` converter
  wrappers.
- Runtime SDK demos, package layout, and `mmdeploy_runtime` model execution are
  owned by the SDK route. This sub-skill only checks SDK backend-manager
  availability and explains missing runtime symptoms.
- Validation, profiling, and regression matrix execution are owned by the
  validation route. This sub-skill only explains backend readiness failures that
  block those tasks.
