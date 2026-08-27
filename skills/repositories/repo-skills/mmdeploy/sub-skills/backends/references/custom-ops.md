# Custom Ops

## Purpose

Read this when a backend package imports successfully but MMDeploy models still
fail during conversion, graph export, or runtime loading because backend custom
operators were not built or were not found.

This guide covers the backend-specific custom-op expectations for ONNXRuntime,
TensorRT, NCNN, and TorchScript. It also explains how to distinguish package
availability from custom-op availability.

## Core Rule

For these backends, `is_available()` and
`is_available(with_custom_ops=True)` are different checks.

- The plain availability check answers: "Can the backend package or converter
  tool be found?"
- The custom-op check answers: "Can MMDeploy also locate the backend plugin or
  custom-op build products that the selected models need?"

A backend can therefore be "available" while still being unable to run a model
that depends on custom operators.

## Shared Build Pattern

When backend custom ops are needed, the common workflow is:

1. Install the backend package or vendor toolkit.
2. Make the vendor library path and executable path visible through the
   documented environment variables.
3. Build MMDeploy with only the selected backend token.
4. Re-run the environment checker with `--with-custom-ops`.
5. Retry the original conversion or load step only after the checker reports the
   custom-op path as available.

Do not build every backend plugin just because one model needs one backend.

## ONNXRuntime Custom Ops

### What they cover

ONNXRuntime custom ops are used for operators that are not in the stock ORT
operator set, including the MMDeploy ONNXRuntime operator families surfaced by
its backend docs and tests.

Typical examples include:

- `grid_sampler`
- `MMCVModulatedDeformConv2d`
- `NMSRotated`
- `RoIAlignRotated`
- `NMSMatch`

### Build expectations

- ORT Python package is present.
- The ONNXRuntime shared library tree is discoverable through `ONNXRUNTIME_DIR`.
- The library path includes the ORT `lib` directory.
- MMDeploy is built with the ORT backend token.

### Common symptoms

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ONNXRuntime custom ops: NotAvailable` in the checker | ORT package exists, but the plugin library was not built or not found | Rebuild the ORT backend with the ORT library path set, then re-run the checker with `--with-custom-ops`. |
| Runtime load error mentioning an unknown op or custom domain | The exported graph contains a custom operator but ORT cannot load the MMDeploy plugin | Confirm the selected model really needs custom ops, then rebuild and re-check the plugin path. |
| Import error for `onnxconverter-common` during fp16 flow | Optional fp16 helper package is missing | Install the optional fp16 helper only for the fp16 route. |

### When to stop

Stop when the failure is due to a missing ORT SDK tarball, unsupported
platform package, or missing GPU runtime that the current machine cannot supply.

## TensorRT Custom Ops

### What they cover

TensorRT custom ops are used for MMDeploy plugin operators such as:

- `TRTBatchedNMS`
- `grid_sampler`
- `MMCVInstanceNormalization`
- `MMCVModulatedDeformConv2d`
- `MMCVMultiLevelRoiAlign`
- `MMCVRoIAlign`
- `ScatterND`
- `TRTBatchedRotatedNMS`
- `GridPriorsTRT`
- `ScaledDotProductAttentionTRT`
- `GatherTopk`
- `MMCVMultiScaleDeformableAttention`

### Build expectations

- TensorRT vendor tar install is present.
- `TENSORRT_DIR` points to the unpacked tree.
- `CUDNN_DIR` is set when the local build requires it.
- CUDA device support is present for the target use case.
- MMDeploy is built with the TensorRT backend token.
- The model's dynamic-shape profile is consistent with the deployment config.

### Common symptoms

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `Cannot found TensorRT headers` or `Cannot found TensorRT libs` | The toolkit path was not exported or the wrong install tree was used | Re-export `TENSORRT_DIR`, add the library path, then rebuild only the TensorRT backend. |
| `please install TensorRT and build TensorRT custom ops first` | The backend package exists but the plugin was not built or not found | Rebuild the TensorRT custom ops and re-run the checker with `--with-custom-ops`. |
| `profileMinDims.d[i] <= dimensions.d[i]` / shape profile check failed | The input shape is outside the configured min/opt/max profile | Update `backend_config.model_inputs[*].input_shapes.<input>` so the runtime shape sits inside the allowed range. |
| `cublasStatus == CUBLAS_STATUS_SUCCESS` assertion failure | CUDA/cuBLASLt/toolkit mismatch or unsupported driver/toolkit combination | Follow the vendor note for the specific CUDA/TensorRT pairing, or disable the tactic if that is the documented recovery. |

### TensorRT shape/profile guidance

When a user reports a shape-profile error, inspect the deployment config first.
The required fields are:

```python
backend_config = dict(
    model_inputs=[
        dict(
            input_shapes=dict(
                input=dict(
                    min_shape=[...],
                    opt_shape=[...],
                    max_shape=[...])))
    ])
```

Do not propose a build-only fix for a runtime shape-range error.

### When to stop

Stop when the machine has no usable CUDA/TensorRT stack or no compatible NVIDIA
hardware. That is a hardware/toolkit gap, not a config mistake.

## NCNN Custom Ops

### What they cover

NCNN custom ops support the operator subset MMDeploy adds for ncnn conversion,
notably the operators exposed in the ncnn custom-op docs.

### Build expectations

- Python `ncnn` package is installed.
- `mmdeploy_onnx2ncnn` is on `PATH`.
- The backend was built with the NCNN token.
- If custom operators are needed, the NCNN extension and its custom-op files
  are also present.

### Common symptoms

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ncnn support is not available, please make sure: 1) mmdeploy_onnx2ncnn existed in PATH 2) python import ncnn success` | Either the executable is missing or the Python package import failed | Install or expose both pieces, then re-run the environment checker. |
| `ncnn custom ops: NotAvailable` | The base package is present, but the extension or custom-op artifact is missing | Rebuild the NCNN backend with custom ops enabled and confirm the plugin path exists. |
| Exported model runs with wrong layout or Vulkan behavior | The backend config did not match the intended `use_vulkan` / precision settings | Re-check the backend config and the runtime target. |

### When to stop

Stop when the required converter executable is absent because the build tree was
never generated or the current platform cannot host the required NCNN toolchain.

## TorchScript Custom Ops

### What they cover

TorchScript availability usually means `torch` is installed, but MMDeploy models
that rely on custom TorchScript ops need a separate LibTorch build and custom-op
path.

### Build expectations

- PyTorch import works.
- The custom-op build was compiled against a compatible LibTorch release.
- Linux builds use the documented pre-cxx11 ABI / version constraints.
- `Torch_DIR` and the Torch library path are exported when custom ops are built.

### Common symptoms

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `torchscript available` but `torchscript custom ops: NotAvailable` in the checker | The `torch` package is installed, but the custom-op build is missing | Treat this as a build gap, not as a failed Torch import. Rebuild the TorchScript custom-op path. |
| `Caffe2Config.cmake` cannot find cuDNN libraries | The LibTorch build expects CUDA/cuDNN but the prefixes are not visible | Export the cuDNN root or install the matching cuDNN package, then rebuild. |
| ABI-related link or load failures | The local LibTorch ABI does not match the rest of the build | Rebuild with the documented ABI choice and matching dependencies. |

### Key distinction

A bare TorchScript import only proves the Python package is usable. It does not
prove the custom-op path, the C++ build, or the SDK backend path are ready.

## Checking Strategy

Use this progression when diagnosing custom-op issues:

1. `python scripts/check_env.py --backend <name>`
2. `python scripts/check_env.py --backend <name> --with-custom-ops`
3. If the second step fails, inspect the relevant row in
   [Backend matrix](backend-matrix.md) and the backend-specific config fields.
4. Retry only the missing backend build or package install.

If the failure is caused by a missing accelerator, missing vendor SDK, or a
platform that cannot host the backend, stop and report the environment limit
instead of retrying the same build.
