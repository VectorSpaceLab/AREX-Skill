# Troubleshooting

## Purpose

Use this reference when a backend task fails during installation, import,
backend readiness checks, custom-op checks, or backend-specific build/runtime
setup.

The recovery advice below is written for MMDeploy backend selection and backend
manager work only. It does not cover end-to-end model conversion orchestration,
SDK demo execution, or benchmark reporting.

## Fast Triage Order

1. Identify the backend name and target artifact.
2. Run `python scripts/check_env.py --backend <name>`.
3. If the backend is present but the model still fails, rerun with
   `--with-custom-ops` when the route uses custom ops.
4. Match the failure to one of the tables below.
5. Stop when the gap is a missing vendor toolkit, missing hardware, or a missing
   external service that cannot be satisfied on the current machine.

## Cross-Cutting Install And Import Failures

| Symptom | Likely cause | Recovery | When to stop |
| --- | --- | --- | --- |
| `ModuleNotFoundError` / `ImportError` for a backend package | The backend Python package was never installed, or the wrong environment is active | Install the single backend package required by the selected route, then rerun the environment checker. | Stop if the package is proprietary, unavailable for the current platform, or requires hardware you do not have. |
| `check_env.py` prints `None` for the backend version | The backend manager cannot find the package/tool it checks for | Verify the backend row in `backend-matrix.md`, then install the missing package or expose its toolkit path. | Stop if the missing piece is a vendor-only SDK that cannot be installed locally. |
| Conditional import fails for `from mmdeploy.apis.<backend> import ...` | The API module only exports the converter when the backend is available | Fix the backend readiness problem first; do not treat the missing export as a separate code bug. | Stop if the backend package itself is unavailable on this machine. |
| `check_env.py` succeeds for one backend but fails for another | The backends were checked independently and only one dependency stack is present | Install only the backend needed for the current task; do not broaden the environment unless the user asked for multiple backends. | Stop if the additional backend is outside the confirmed task scope. |

## Optional Dependency And Custom-Op Failures

| Symptom | Likely cause | Recovery | When to stop |
| --- | --- | --- | --- |
| `... custom ops: NotAvailable` | The backend package is installed, but the plugin or custom-op build is missing | Read [Custom ops](custom-ops.md), rebuild only the needed backend plugin, and rerun `--with-custom-ops`. | Stop if the backend requires a vendor SDK or hardware that is absent. |
| `onnxconverter-common` import error during ONNXRuntime fp16 flow | Optional float16 helper package is missing | Install the optional helper only for the fp16 route. | Stop if the route does not actually require fp16 conversion. |
| TorchScript import works but custom ops are unavailable | `torch` is installed, but the LibTorch custom-op build was not created | Treat this as a build gap, not a Torch import failure. Rebuild the TorchScript custom-op path. | Stop if the task only needs pure TorchScript and not custom ops. |
| NCNN conversion requires `mmdeploy_onnx2ncnn` but the tool is absent | The backend runtime package exists but the converter executable was not built or not on `PATH` | Expose the tool on `PATH` or rebuild the NCNN backend and custom-op artifacts. | Stop if the current machine cannot host the NCNN build toolchain. |

## Backend-Specific Failures

### TensorRT

| Symptom | Likely cause | Recovery | When to stop |
| --- | --- | --- | --- |
| `Cannot found TensorRT headers` / `Cannot found TensorRT libs` | The TensorRT toolkit path was not exported, or the install tree is incomplete | Re-check `TENSORRT_DIR`, the library path, and the CMake backend token, then rebuild only the TensorRT backend. | Stop if there is no compatible TensorRT install for the current CUDA/driver stack. |
| `please install TensorRT and build TensorRT custom ops first` | The backend package exists, but the plugin was not built or was not found | Rebuild custom ops and rerun the checker with `--with-custom-ops`. | Stop if the selected model genuinely requires GPU execution and the machine has no compatible NVIDIA GPU. |
| `profileMinDims... <= dimensions...` or a profile-range assertion | The runtime input shape falls outside the configured min/opt/max profile | Update `backend_config.model_inputs[*].input_shapes.<input>` so the actual input lies within the profile bounds. | Stop only after the config has been corrected and the failure persists. |
| `cublasStatus == CUBLAS_STATUS_SUCCESS` assertion | CUDA/cuBLASLt/TensorRT version mismatch or a known vendor-toolkit issue | Use the vendor-recommended CUDA/TensorRT pairing or disable the problematic tactic if that is the documented fix. | Stop if the local toolkit/driver pair cannot satisfy the required TensorRT version. |
| `--device cpu` used with TensorRT flow | CLI/API misuse: TensorRT requires CUDA device semantics | Switch the deployment route to a CUDA device and keep the shape profile consistent. | Stop if the user only has CPU hardware and no TensorRT-capable GPU. |

### OpenVINO

| Symptom | Likely cause | Recovery | When to stop |
| --- | --- | --- | --- |
| `ImportError: libpython3.7m.so.1.0: cannot open shared object file` | OpenVINO runtime expects a matching libpython library that is missing from the system | Install the matching `libpython` package for the runtime version or point the runtime at a compatible Python library path. | Stop if the requested OpenVINO runtime version cannot match the current Python/toolchain constraints. |
| OpenVINO conversion fails after package import succeeds | Model Optimizer runtime or `InferenceEngine_DIR` was not exposed | Reinstall or expose the OpenVINO runtime tree and rerun the check. | Stop if the OpenVINO runtime package is unavailable for the current platform. |
| `backend_config.mo_options` ignored | CLI/API misuse: the config fields were not placed under the backend config | Move Model Optimizer options into `backend_config.mo_options.args` and `backend_config.mo_options.flags`. | Stop only after the config is corrected and the option is still ignored. |

### TorchScript

| Symptom | Likely cause | Recovery | When to stop |
| --- | --- | --- | --- |
| cuDNN not found during LibTorch build | The custom-op build expects CUDA/cuDNN prefixes that are not visible | Export the cuDNN root or install the matching cuDNN package, then rebuild. | Stop if the build is intentionally CPU-only and the task does not need custom ops. |
| ABI or linker failures around LibTorch | The LibTorch ABI does not match the rest of the build | Rebuild with the documented pre-cxx11 ABI or matching ABI choice. | Stop if the repository must target a platform where the documented ABI pairing is unavailable. |
| `torchscript available` but `torchscript custom ops: NotAvailable` | Package vs custom-op build confusion | Treat the Python package as installed but the custom-op build as missing. Rebuild the custom-op path. | Stop only if the task does not require custom ops. |

### NCNN

| Symptom | Likely cause | Recovery | When to stop |
| --- | --- | --- | --- |
| `mmdeploy_onnx2ncnn existed in PATH` missing from the checker message | The converter executable is not on `PATH` | Expose the executable or rebuild the NCNN tooling and rerun the checker. | Stop if the current platform cannot host the NCNN converter build. |
| `ncnn custom ops: NotAvailable` | The extension or custom-op artifact was not built | Rebuild the NCNN backend with custom ops and confirm the shared library is discoverable. | Stop if the task does not require the custom-op operators. |
| Vulkan or layout behavior differs from expectation | The backend config did not match the intended runtime target | Review `backend_config.use_vulkan` and the target platform assumptions before rebuilding. | Stop if the target device does not support the requested backend mode. |

### PPLNN

| Symptom | Likely cause | Recovery | When to stop |
| --- | --- | --- | --- |
| Missing `opt_shape` assertion | The deployment config did not provide the shape information PPLNN expects | Add `opt_shape` to the model-input entry and retry. | Stop if the user asked for a route that does not include shape information. |
| `pyppl` import failure | The Python package is not installed | Install `pyppl` and rerun the checker. | Stop if the available package set cannot support the selected PPLNN release. |

### RKNN

| Symptom | Likely cause | Recovery | When to stop |
| --- | --- | --- | --- |
| Unsupported `target_platform` or quantization error | The config still uses the default or wrong Rockchip target settings | Set `backend_config.common_config.target_platform` explicitly and align quantization settings with the target. | Stop if the required Rockchip target board or toolkit is unavailable. |
| `rknn` imports but no device runtime is possible | Hardware or vendor toolkit missing | Confirm the Rockchip toolkit and target device availability before retrying. | Stop if no compatible Rockchip device or toolkit exists. |

### Ascend

| Symptom | Likely cause | Recovery | When to stop |
| --- | --- | --- | --- |
| `acl` import failure | Ascend runtime or ACL stack is missing | Install or expose the Ascend toolkit, then rerun the checker. | Stop if no Ascend hardware/toolkit is available. |
| `.om` conversion fails after import | The device/toolkit stack is incomplete or the input shape is wrong | Recheck the toolkit environment and model-input shape settings. | Stop if the model requires a device not present on this machine. |

### CoreML

| Symptom | Likely cause | Recovery | When to stop |
| --- | --- | --- | --- |
| `coremltools` import failure | CoreML conversion package is missing | Install the CoreML Python tooling and retry. | Stop if the machine is not a compatible macOS target. |
| Custom-op conversion fails for detection models | LibTorch was not compiled with the expected custom operators | Rebuild the LibTorch/custom-op path and retry the conversion. | Stop if the task does not need the detection custom-op path. |

### TVM

| Symptom | Likely cause | Recovery | When to stop |
| --- | --- | --- | --- |
| `tvm` import failure | TVM is not installed | Install or expose the TVM package and required runtime paths. | Stop if the selected target requires a TVM build that the current system cannot host. |
| Missing `TVM_DIR`, library path, or Python path | The TVM runtime/build tree was not exported | Set the documented TVM environment variables and retry. | Stop if the runtime is vendor-managed and cannot be installed locally. |
| `shape`/`dtype`/tuner argument mismatch | CLI/API misuse of the TVM conversion route | Recheck the target, shape dictionary, dtype dictionary, and tuner settings. | Stop after the call site has been corrected and the error persists. |

### VACC

| Symptom | Likely cause | Recovery | When to stop |
| --- | --- | --- | --- |
| `vacc` or `tvm` import failure | The paired VACC/TVM stack is missing | Install the required Python packages and expose the VastAI paths. | Stop if the VACC toolchain or hardware is unavailable. |
| Device or driver checks fail | No compatible VACC card or driver is present | Verify the driver, card, and environment variables before retrying. | Stop if the hardware is absent or inaccessible. |

### SNPE

| Symptom | Likely cause | Recovery | When to stop |
| --- | --- | --- | --- |
| `onnx2dlc` cannot be found | SNPE toolkit path is not exposed | Set `SNPE_ROOT`, update `PATH`, `LD_LIBRARY_PATH`, and `PYTHONPATH`, then retry. | Stop if the SNPE SDK is not available for the host platform. |
| Missing `--uri` or service connection failure | The SNPE client/server flow was not configured with a valid device URI | Provide the service URI and confirm the remote service is listening. | Stop if the remote device or service cannot be reached. |
| Attempting unsupported GPU_FP16 or DSP/AIP flow | The requested feature is outside the supported SNPE subset | Narrow the request to a supported SNPE path. | Stop if the required unsupported mode is mandatory for the user. |

## SDK Runtime Absence

| Symptom | Likely cause | Recovery | When to stop |
| --- | --- | --- | --- |
| `mmdeploy_runtime` import failure | The SDK runtime package was not built or installed | Build or install the SDK runtime for the selected backend stack, then rerun the backend-manager check. | Stop if the task only needs conversion and not SDK runtime execution. |
| SDK manager is unavailable but the base backend is present | The SDK backend is a separate build output from the converter/runtime package | Build the SDK route separately; do not use the converter package as proof of SDK availability. | Stop if the current task does not involve SDK runtime. |

## Config And API Misuse Patterns

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `backend_config.type` does not match the intended backend | A config copied from another backend was reused without normalization | Rewrite the backend config to the correct `type` and backend-specific fields. |
| INT8 or quantized backend flow complains about missing calibration data, calibration file, or dataset | Backend quantization settings were enabled without representative data or a generated calibration artifact | Use the conversion/calibration route to create the calibration file, pass a calibration dataset config when required, or switch to a non-INT8 backend config. |
| TensorRT, RKNN, or VACC quantization settings conflict with the model input shape | Quantization/data settings and `model_inputs` were copied from an incompatible config | Align calibration data, batch shape, and backend-specific `model_inputs` before retrying. |
| Conversion API called with a CPU device for a CUDA-only backend | CLI/API misuse | Use the device required by the backend row in `backend-matrix.md`. |
| Backend-specific import is missing from `mmdeploy.apis.<backend>` | The module only exports the function when the backend is available | Fix the backend install/build first, then retry the import. |
| `check_env.py` says the backend is available, but runtime still fails | The checker proves package presence, not a complete model-specific path | Re-check custom ops, shapes, vendor toolkits, and target hardware. |

## Workflow-Specific Failures

These are failures owned by this sub-skill because they block backend setup or
backend selection:

- package present but custom ops absent
- backend package importable but required converter executable missing
- `check_env.py` cannot classify a backend because the tool path is missing
- SDK runtime absent even though the converter backend is present
- CPU import success mistakenly treated as proof of accelerator readiness

For each of those cases, the recovery step is always the same: inspect the
backend row in [Backend matrix](backend-matrix.md), check the custom-op section
if relevant, and stop if the remaining gap is a missing vendor toolchain or
hardware device rather than a software configuration problem.
