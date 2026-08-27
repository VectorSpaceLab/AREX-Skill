# SDK Troubleshooting

Use this reference for SDK runtime inference, SDK model package layout, profiler
analysis, language FFI examples, precompiled package usage, and SNPE service
constraints. For backend toolkit installation or conversion failures, diagnose
the SDK-owned symptom first, then hand off to the backend or conversion route.

## Install And Import Failures

| Symptom | Likely causes | Recovery steps | Stop when |
| --- | --- | --- | --- |
| `ModuleNotFoundError: No module named 'mmdeploy_runtime'` | SDK Python runtime wheel/package is not installed; built SDK Python API is not on `PYTHONPATH`; wrong Python environment. | Install a matching `mmdeploy-runtime` or `mmdeploy-runtime-gpu` package, or use a precompiled SDK package that includes the Python runtime. Re-run `python -c "import mmdeploy_runtime; print(mmdeploy_runtime)"`. | No package exists for the target OS/Python/device and the user is not prepared to build SDK Python bindings. |
| `from mmdeploy.backend.sdk import is_available; is_available()` is `False` | `mmdeploy_runtime` cannot be discovered by the converter package; local build artifacts are absent; package installed without SDK runtime. | First check direct `mmdeploy_runtime` import. If missing, install/build runtime. If direct import works but manager check fails, ensure the same Python process sees both packages. | The runtime is intentionally not installed and the task requires SDK execution. |
| Import fails with missing `.so`, `.dll`, `.pyd`, `libonnxruntime`, `mmdeploy`, or backend libraries | Native library path is incomplete; runtime package and backend library versions do not match; wrong CPU/GPU package; platform ABI mismatch. | Use the package's setup script or add its `lib`/`bin` directory to the process library path. Install the CPU or GPU runtime variant matching the target device and backend. Confirm OS, architecture, Python ABI, CUDA/TensorRT/ONNXRuntime compatibility. | Required proprietary/native libraries are unavailable or cannot legally be installed on the target machine. |
| Task class is absent from `mmdeploy_runtime` | Runtime built without that SDK task/language binding; old package version; wrong package variant. | Inspect available names with `python - <<'PY'\nimport mmdeploy_runtime as rt\nprint([n for n in dir(rt) if not n.startswith('_')])\nPY`. Install or build a runtime package that includes the task. | The package cannot be rebuilt or replaced and the missing task is required. |

## Optional Dependency And Language-Binding Failures

| Symptom | Likely causes | Recovery steps | Stop when |
| --- | --- | --- | --- |
| `cv2.imread(...)` returns `None` or demos report failed image/video load | Wrong input path, unsupported image/video codec, OpenCV missing codec support. | Validate the file exists, use an absolute or working-directory-correct path in the user's shell, check `img is not None`, and install OpenCV with needed codecs. | The input data cannot be read by any available media library. |
| Java demo cannot compile or run | Ant unavailable; Java SDK wrapper classes not built; native libraries not on `java.library.path`; OpenCV Java jar required for pose tracking. | Install Ant, build or use generated Java SDK classes, pass library paths explicitly, and add OpenCV Java only for demos that require it. | Java SDK classes/native libraries are not available and the user cannot build or obtain them. |
| C# demo cannot load runtime DLLs or NuGet package | Local/prebuilt NuGet not installed; runtime DLLs not on system path; backend DLLs missing. | Install the local/prebuilt package, put runtime and backend DLL directories on the system path for the process, and use the backend versions from the package notes. | The package targets a different OS/architecture or required backend DLLs are unavailable. |
| C/C++ demo builds but executable cannot find libraries | SDK built dynamically; loader path lacks MMDeploy/OpenCV/backend libraries; monolithic/static expectations do not match package. | Use the package setup script, set the platform loader path for the current shell, or rebuild/link according to the package's monolithic/dynamic choice. | Required native libraries are missing from the package or cannot be redistributed. |

## Backend And Device Runtime Failures

| Symptom | Likely causes | Recovery steps | Stop when |
| --- | --- | --- | --- |
| Python constructor fails when `device_name='cuda:0'` | SDK Python task constructors expect `device_name='cuda'` and `device_id=0`; converter APIs often use a single device string like `cuda:0`. | Split the device into name and id: `Detector(model_path, 'cuda', 0)`. Use `('cpu', 0)` for CPU. | The target device runtime is absent after the argument format is corrected. |
| Passing `device_id=-1` gives unexpected behavior | SDK wrapper normalizes negative parsed ids to `0`; SDK runtime does not use `-1` as a normal device id. | Pass explicit `0`, `1`, ... for device ids. For CPU, use `device_name='cpu', device_id=0`. | The user needs a device selection behavior not supported by the SDK API. |
| TensorRT model fails on another GPU or machine | TensorRT engines are often tied to TensorRT/CUDA/GPU architecture and shape-profile assumptions. | Use a runtime package matching the engine build stack, or regenerate the SDK model directory on/for the target device and TensorRT version. | No compatible TensorRT/CUDA/GPU stack is available. |
| ONNXRuntime/NCNN/OpenVINO backend file exists but SDK load fails | Backend runtime library is missing; `deploy.json` names files that are absent; backend package variant lacks CPU/GPU support requested by `device_name`. | Validate `deploy.json` artifacts, install the runtime library variant for the backend/device, and rerun a minimal SDK load. | Backend runtime cannot be installed for the target platform. |
| Runtime imports but first inference crashes or returns backend-specific errors | Backend engine incompatible with input shape, precision, device, custom ops, or target libraries. | Confirm the model package files match the target backend and device. Re-run conversion/engine build with the right shape/device profile when needed. | The only fix is backend-specific conversion/toolkit work; hand off to backend/conversion guidance. |

## Model Package And Config/Data Failures

| Symptom | Likely causes | Recovery steps | Stop when |
| --- | --- | --- | --- |
| User passes `end2end.engine` to `Detector` as `model_path` | Confusion between converter backend files and SDK model directories. | Explain that SDK needs the directory containing `deploy.json` and `pipeline.json`; set `model_path` to the conversion `--work-dir`. If only the engine exists, regenerate with `--dump-info`. | The JSON metadata cannot be recovered and conversion cannot be rerun. |
| `deploy.json` or `pipeline.json` is missing | Conversion ran without `--dump-info`; directory was manually copied incompletely. | Regenerate conversion output with SDK metadata enabled or copy the complete SDK model directory. | Only raw backend files remain. |
| `detail.json` is missing | Package is incomplete; some runtime APIs may still fail later because provenance/config diagnostics are unavailable. | Prefer regenerating or copying the complete directory with all three JSON files. | The user needs reliable SDK portability/debugging and cannot regenerate metadata. |
| `deploy.json` names a missing `net`, `weights`, or custom file | Backend artifact or task custom file was not copied with the SDK package; manual rename broke manifest. | Compare every `models[].net`, `models[].weights`, and `customs[]` entry to files in the directory. Restore the file names or rerun conversion. | The required backend/custom files are lost. |
| Wrong task class is used, such as `Detector` on a classification package | The runtime class was chosen from the use case rather than `deploy.json.task`. | Read `deploy.json.task` and use the matching SDK class from [SDK workflows](sdk-workflows.md). | The installed runtime package lacks the required class. |
| OCR recognition fails due to missing dictionary or custom file | Text recognition can require task custom files exported with SDK metadata. | Check `deploy.json.customs` and copy required files into the model directory. Regenerate with `--dump-info` if the file was never emitted. | Required custom files cannot be found or rebuilt. |
| Postprocess output shape or labels look wrong | Model config/checkpoint and SDK metadata do not match the backend artifact; input image color/shape differs from expected pipeline; task postprocess parameters stale. | Treat the SDK directory as one immutable package. Regenerate from matching deploy config, model config, checkpoint, and sample input; validate with a known image. | There is no reliable source config/checkpoint to regenerate a coherent package. |

## CLI/API Misuse

| Symptom | Likely causes | Recovery steps | Stop when |
| --- | --- | --- | --- |
| User passes `backend_files=['end2end.engine']` to an SDK task class | Mixing converter `inference_model` API with SDK runtime API. | Use `backend_files` only with converter-level inference APIs. For SDK runtime, pass `model_path='sdk_model_dir'`. | The task actually requires converter API behavior; route away from SDK runtime. |
| C API result memory leaks or double frees | Result buffers were not released, released with the wrong task family, or handle destroyed before release. | Pair every `*_apply` with the matching `*_release_result`, then destroy the task handle once. Do not mix detector release functions with classifier results. | Process stability is already compromised and needs native debugging/restart. |
| Batch C API returns confusing counts | Caller assumes one flat result count; SDK returns per-input counts and contiguous result buffers. | Iterate by input, advancing the result pointer by each `res_count[i]`, then release once with the batch size. | Result contract cannot be matched to downstream code without changing the application. |
| PoseTracker constructor fails or returns no tracks | Pose tracking requires both detection and pose SDK model directories plus a tracker state; it is not a single pose model call. | Provide separate detection and pose model directories, create state, and call the tracker over frames. | Either required model directory is unavailable. |
| Custom pipeline output keys are missing | Pipeline config input/output names do not match the data dict; nested pipeline star/plus broadcast syntax misunderstood. | Start from a minimal `Model` + task-class call, then add `Pipeline` composition only after each model works separately. | The user needs custom pipeline authoring beyond runtime consumption; hand off to extensibility guidance. |

## Profiler Workflow Failures

| Symptom | Likely causes | Recovery steps | Stop when |
| --- | --- | --- | --- |
| Analyzer reports missing `----` separator | File is not SDK profiler text output; profiler was not destroyed/flushed; wrong file chosen; binary or external profiler data. | Regenerate using SDK profiler context, run several inference iterations, destroy profiler/context, and confirm the file contains graph lines, `----`, and event lines. | The SDK runtime cannot produce a text profile in the user's build. |
| Analyzer reports unknown event address or unbalanced events | Profile file is truncated, interleaved, or from an incompatible SDK profiler version. | Regenerate in a single process, avoid editing the file, and analyze after clean shutdown. | Repeated clean profiles are malformed; collect SDK/runtime version and stop for native investigation. |
| Profile shows backend net dominates | Backend engine is slow, device fallback occurred, shape/profile is inefficient, or host/device copies dominate. | Confirm target device, backend runtime variant, engine shape profile, batch size, and warmup. Route backend-specific optimization outside this SDK route. | Required backend tooling/hardware is absent. |
| Profile shows preprocess/postprocess dominates | Image transforms, result decoding, OCR, NMS, or composite pipeline steps dominate. | Inspect `pipeline.json` tasks and input resolution; consider fused preprocessing only when supported by the model/package. | Fix requires converter/extensibility changes to emitted pipeline metadata. |

## Zip Model Failures

| Symptom | Likely causes | Recovery steps | Stop when |
| --- | --- | --- | --- |
| Directory model works but `.zip` path fails | SDK was built without zip-model support; zip is missing root files; archive layout has an extra nested directory. | Use the directory form, or rebuild/obtain an SDK with zip-model support. Verify zip contents include JSON and backend artifacts at the expected relative layout. | Zip-model support cannot be enabled and distribution must remain zipped/encrypted. |
| Memory-loaded model bytes fail | Encrypted bytes were not decrypted; byte length is wrong; API expects a complete zip model package. | Test with an unencrypted zip file first, then add decryption and pass exact bytes/size. | Security requirements prevent debugging with a known-good unencrypted package. |

## Precompiled Package Failures

| Symptom | Likely causes | Recovery steps | Stop when |
| --- | --- | --- | --- |
| Runtime wheel refuses to install | Python ABI/platform tag mismatch; wheel built for another OS/architecture. | Use a wheel matching Python major/minor, OS, architecture, and CPU/GPU variant; otherwise build from source in a clean environment. | No matching package or build toolchain is available. |
| GPU runtime package installs but cannot load GPU backend | CUDA/cuDNN/TensorRT/ONNXRuntime versions do not match the package; driver too old; GPU unavailable. | Check package release notes and backend library versions; install the matching device stack or use CPU runtime when supported. | Target backend has no CPU substitute and compatible GPU stack is unavailable. |
| Package build scripts fail during SDK/runtime packaging | Missing CMake/compiler/toolchain, backend env vars, Python ABI envs, or proprietary libraries. | Treat as maintainer packaging work. Build in clean envs, set only required backend/device flags, and run package smoke tests. | Required proprietary SDKs, compilers, or target devices are absent. |

## SNPE Service Constraints

The SNPE service code is an edge-service pattern, not a generic SDK runtime path.
It exposes gRPC calls for echo, model initialization, output-name query,
inference, and destroy. It sends model weights and float32 tensors over the
service boundary.

| Symptom | Likely causes | Recovery steps | Stop when |
| --- | --- | --- | --- |
| SNPE service cannot initialize model | Input is not a valid `.dlc` byte payload; SNPE SDK/runtime unavailable; server cannot open container. | Confirm the model is a DLC artifact, start the service in an environment with SNPE libraries, and check Init status/info. | SNPE SDK cannot be installed or licensed on the host/edge device. |
| Requested GPU/DSP runtime silently falls back or reports unavailable | SNPE runtime availability check failed; service falls back to CPU when selected runtime is absent. | Query service logs, confirm CPU/GPU/DSP availability on the device, and choose only available runtimes. | Required GPU/DSP acceleration is unavailable and CPU fallback is unacceptable. |
| Static quantization warning appears on CPU/GPU | Static quantization is designed for DSP/AIP-style runtimes, not CPU/GPU. | Use DSP/AIP-capable runtime when required, or proceed without static quantization on CPU/GPU. | Quantized DSP/AIP behavior is required but hardware/runtime is absent. |
| Inference reports tensor count, name, or size mismatch | Client tensor names/shapes do not match SNPE input tensors; float32 byte buffer length is wrong. | Query output/input expectations, send exact input tensor names and float32 data with matching shape and byte length. | Client cannot produce tensors matching the model contract. |
