# Backend Matrix

## Purpose

Read this when selecting an MMDeploy inference backend, deciding what to
install, or interpreting backend-manager availability. It distills the supported
backend matrix, backend setup guides, base backend configs, backend manager
implementations, API package exports, and backend tests into a self-contained
operating checklist.

## Quick Selection By Target

| Target need | Prefer | Notes |
| --- | --- | --- |
| Portable ONNX inference on Linux CPU | ONNXRuntime | Easiest CPU substitute for many models; custom ops are a separate build. |
| NVIDIA CUDA engine with maximum runtime performance | TensorRT | Requires CUDA/TensorRT stack; no CPU substitute for engine execution. |
| Mobile/embedded CPU artifact, Android/aarch64/RISC-V emphasis | NCNN | Produces `.param` and `.bin`; converter tool and Python `ncnn` package must both be discoverable. |
| Intel CPU-oriented OpenVINO IR | OpenVINO | Produces `.xml`/`.bin`; Model Optimizer options can be passed through config. |
| CUDA-oriented PPL.NN deployment | PPLNN | Requires `pyppl` and shape information; CPU substitute is not a proof of the CUDA path. |
| LibTorch/TorchScript artifact | TorchScript | `torch` import proves package availability; C++ custom ops require a separate libtorch build. |
| Rockchip NPU | RKNN | Requires RKNN toolkit and target platform; CPU host conversion does not prove device runtime. |
| Huawei Ascend/CANN | Ascend | Requires Ascend ACL/CANN stack; no meaningful CPU substitute. |
| Apple Core ML | CoreML | Requires macOS/CoreML tooling; custom-op conversion may require libtorch. |
| TVM compilation/runtime | TVM | Requires TVM install and target/tuner settings; CPU LLVM target may be a partial substitute only. |
| VastAI VACC accelerator | VACC | Requires VastAI driver/toolkit plus TVM/VACC Python modules. |
| Qualcomm SNPE | SNPE | Requires SNPE SDK, `onnx2dlc`, and often an external device/service URI. |
| `mmdeploy_runtime` SDK model directory | SDK manager | Availability is about SDK runtime Python package, not model conversion. |

## Backend Detail Table

CPU substitute values mean whether a CPU-only environment can validate the same
backend route: `full` for a real CPU backend, `partial` for import/config/host
conversion only, and `none` for accelerator runtime paths.

| Backend config `type` | CMake backend token | Role and output | Device/platform role | CPU substitute | Required packages, tools, and environment | Manager availability check | Config and operational notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `onnxruntime` | `ort` | ONNXRuntime wrapper over `.onnx`; optional fp16 rewrite keeps ONNX as the backend file. | Linux CPU or GPU package; Windows builds also use ORT. | `full` for CPU ORT; `partial` for GPU ORT. | `onnxruntime` or `onnxruntime-gpu`; optional `onnx` and `onnxconverter-common` for fp16; custom ops need an ONNXRuntime library exposed through `ONNXRUNTIME_DIR` and library path. | `get_backend_manager('onnxruntime').is_available()` checks the `onnxruntime` import; `with_custom_ops=True` checks the bundled custom-op shared library path. | `onnxruntime-fp16` uses `backend_config.precision='fp16'` and `common_config` for float16 conversion controls. |
| `tensorrt` | `trt` | Converts ONNX to TensorRT `.engine`. | NVIDIA CUDA GPUs and Jetson. | `none` for engine execution. | TensorRT 8-style install from vendor tar is the documented path; Python `tensorrt`; CUDA/cuDNN when required; `TENSORRT_DIR`, often `CUDNN_DIR`, and library path. | `get_backend_manager('tensorrt').is_available()` checks the `tensorrt` import; `with_custom_ops=True` also checks the TensorRT plugin path. | Use CUDA device strings. Dynamic models require `backend_config.model_inputs[*].input_shapes.<input>.min_shape/opt_shape/max_shape`. INT8 configs need calibration data. |
| `ncnn` | `ncnn` | Converts ONNX to `.param`/`.bin`; wrapper can use Vulkan when configured. | Linux/macOS/Android/aarch64/RISC-V/mobile CPU-oriented deployments; Vulkan support is platform-dependent. | `full` for CPU NCNN conversion/runtime when tooling is present; `partial` for Vulkan/mobile cross-builds. | Python `ncnn`; `mmdeploy_onnx2ncnn` executable in `PATH`; `ncnn_DIR` for CMake; protobuf may be required for source builds; library path for built NCNN. | `get_backend_manager('ncnn').is_available()` requires Python `ncnn` and `mmdeploy_onnx2ncnn`; `with_custom_ops=True` also requires `ncnn_ext` and the custom-op path. | `backend_config.use_vulkan` defaults to false in base configs. INT8 uses `precision='INT8'` and separate quantization workflow. |
| `openvino` | `openvino` | Converts ONNX to OpenVINO IR `.xml`/`.bin`. | CPU-oriented Linux/Windows deployments and OpenVINO SDK runtime. | `full` for CPU OpenVINO. | `openvino-dev[onnx]` for Python conversion; optional runtime archive for SDK; `InferenceEngine_DIR` for CMake SDK builds. | `get_backend_manager('openvino').is_available()` checks the `openvino` import. | `backend_config.mo_options` can pass Model Optimizer `args` and `flags`. `model_inputs.opt_shapes` can supply input info. |
| `pplnn` | `pplnn` | Converts ONNX for PPL.NN and produces an optimized ONNX plus algorithm JSON. | Linux CUDA-oriented examples. | `partial`; import/config checks do not prove accelerator execution. | `pyppl`; PPL.NN build/install; `pplnn_DIR`/PPLNN path for CMake; CUDA stack for the common MMDeploy route. | `get_backend_manager('pplnn').is_available()` checks Python `pyppl`. | Conversion expects `opt_shape` in model inputs; missing shape produces an assertion. |
| `torchscript` | `torchscript` | Uses TorchScript `.pt` artifacts and LibTorch-backed SDK runtime. | CPU or CUDA depending on Torch/LibTorch build. | `full` for pure Python TorchScript CPU models; `partial` for custom-op SDK builds. | Python `torch`; custom ops require libtorch 1.8.1+ with pre-cxx11 ABI on Linux, `Torch_DIR`, and library path. | `get_backend_manager('torchscript').is_available()` checks `torch`; `with_custom_ops=True` checks the TorchScript custom-op library path. | `torchscript available` and `custom ops available` are separate facts. SDK backend can require a dedicated CMake flag. |
| `rknn` | `rknn` | Converts ONNX to `.rknn`. | Rockchip NPU targets, documented around `rk3588` and `rv1126`. | `none` for device runtime; `partial` for host conversion import. | `rknn-toolkit` or `rknn-toolkit2`; often strict Python/ONNX dependency constraints; target device/toolchain for SDK. | `get_backend_manager('rknn').is_available()` checks the `rknn` import; version chooses toolkit2 if present. | `backend_config.common_config.target_platform`, `optimization_level`, and `quantization_config` control target and quantization. |
| `ascend` | not listed in common CMake token table | Converts ONNX to Ascend `.om` through ACL/CANN tooling. | Huawei Ascend hardware. | `none`. | Ascend ACL/CANN Python/runtime stack; `ASCEND_TOOLKIT_HOME` and vendor library paths. | `get_backend_manager('ascend').is_available()` checks Python `acl`. | Model inputs supply input shapes for Ascend conversion. Stop when ACL/CANN is absent. |
| `coreml` | `coreml` | Converts TorchScript to Core ML package/model. | macOS/Core ML and Apple deployment targets. | `partial`; CPU host checks do not replace target Core ML behavior. | `coremltools`; macOS-compatible PyTorch; libtorch/Torch_DIR when conversion needs custom operators. | `get_backend_manager('coreml').is_available()` checks `coremltools`. | Base config uses `convert_to='mlprogram'`. Input shapes include min/default/max when converting dynamic shapes. |
| `tvm` | `tvm` | Compiles ONNX into TVM runtime artifacts; supports tuners. | TVM targets such as LLVM and target-specific runtimes. | `partial`; LLVM CPU compilation can test part of the flow only. | Python `tvm`; TVM build/runtime; `TVM_DIR`/`TVM_HOME`, Python path, and library path. | `get_backend_manager('tvm').is_available()` checks `tvm`. | Conversion needs `shape`, `dtype`, target/tuner information, and may use calibration data for quantized flows. |
| `vacc` | not in common CMake token table | Converts through VastAI VACC/TVM stack. | VastAI accelerator card/runtime. | `none`. | `vacc` and `tvm` Python modules; VastAI driver; `VASTSTREAM_HOME`, `TVM_HOME`, VACC-related environment variables, library path, and Python path. | `get_backend_manager('vacc').is_available()` checks both `vacc` and `tvm`. | Config includes `common_config.name`, `model_inputs.shape`, and `qconfig` calibration parameters. |
| `snpe` | `snpe` | Converts ONNX to SNPE `.dlc` and can use a client/server runtime route. | Qualcomm SNPE/Android device deployments. | `none` for target acceleration; host conversion only is partial. | SNPE SDK; `onnx2dlc` in SDK `bin`; `SNPE_ROOT`, library path, Python path, and PATH; service URI for device-backed flows. | `get_backend_manager('snpe').is_available()` checks whether `onnx2dlc` is discoverable. `get_version()` is not implemented by this manager. | `--uri` or equivalent URI config is required for service-backed device inference. Unsupported features include GPU_FP16, DSP/AIP quantization, operator internal profiling, and UDO operators. |
| `sdk` | selected by SDK build flags, not conversion token | Checks `mmdeploy_runtime` SDK Python runtime availability. | Depends on the backend(s) built into the SDK. | `depends`. | `mmdeploy_runtime` Python package and SDK libraries built with target devices/backends. | `get_backend_manager('sdk').is_available()` checks the SDK runtime import. | Use this only for readiness. Runtime demos and model directory layout belong to the SDK route. |

## Backend Manager Names And Aliases

Use the left column when calling `get_backend_manager(...)`. Common CMake or
user aliases can be normalized as follows:

| User/CMake alias | Backend manager name |
| --- | --- |
| `ort` | `onnxruntime` |
| `trt` | `tensorrt` |
| `libtorch`, `torch_jit`, `torchjit` | `torchscript` |
| `ppl`, `ppl.nn` | `pplnn` |
| other table entries | same as `backend_config.type` |

## Minimal Readiness Checklist

1. Backend row selected and CPU substitute status understood.
2. Python package import check passes, or the failure is recorded as an optional
   backend absence.
3. Required executable/tool is on `PATH` when the manager depends on one:
   `mmdeploy_onnx2ncnn` for NCNN, `onnx2dlc` for SNPE, Model Optimizer tooling
   for OpenVINO SDK flows, and vendor compilers/toolchains for SDK builds.
4. Required environment variables are set only for the selected backend, not for
   every possible backend.
5. `check_env.py --backend <name>` reports the expected backend version or a
   known `None` for unavailable optional backends.
6. If custom ops are required, `check_env.py --backend <name> --with-custom-ops`
   reports custom ops available for ONNXRuntime, TensorRT, NCNN, or TorchScript.
7. If CPU substitute is `partial` or `none`, do not treat CPU import success as
   verification of target hardware runtime.
