# Backend selection, model cache, and downloads

This reference covers installation extras, local/remote model file resolution,
model cache behavior, ModelScope routing, and backend-specific constraints.
During construction, only ONNX Runtime CPU provider behavior was verified.
GPU, TensorRT, remote server inference, downloads, and training/export were not
executed.

## Package and extras facts

The package is `x-anylabeling-cvhub` and requires Python >=3.11. Python 3.12 is
recommended by the project installation guide and was used in the prepared
inspection environment. Use exactly one runtime extra in a given environment:

| Extra | Intended backend | Key dependency shape | Notes |
|---|---|---|---|
| `[cpu]` | CPU ONNX Runtime | `numpy>=2`, `onnx>=1.15`, `onnxruntime>=1.15` | Verified during construction. Works for registry inspection and CPU ONNX Runtime imports. |
| `[gpu]` | CUDA 12.x ONNX Runtime GPU | `onnxruntime-gpu>=1.18.1,<1.27.0` on non-macOS | Optional/unverified here. Requires CUDA/cuDNN compatibility with the selected ONNX Runtime build. |
| `[gpu-cu11]` | CUDA 11.x ONNX Runtime GPU | `numpy<2`, `onnx>=1.15,<1.16.1`, `onnxruntime-gpu>=1.15,<1.19.0` | Optional/unverified. Use when deployment is locked to CUDA 11.x. |
| `[gpu-cu13]` | CUDA 13.x ONNX Runtime GPU | `onnxruntime-gpu>=1.27,<1.28.0` | Optional/unverified. Use when deployment is locked to CUDA 13.x. |

Do not install `onnxruntime` and `onnxruntime-gpu` side-by-side in the same
environment. If a CPU environment must be repurposed for GPU inference, remove
the CPU runtime before installing the matching GPU extra, or create a fresh
environment.

TensorRT is separate from these extras. YOLO-family `engine: trt` needs the
`tensorrt` and `cuda-python` packages plus a compatible NVIDIA driver/CUDA stack
and an engine file built for the same TensorRT major version and GPU
architecture.

## Engine values for YOLO-family configs

The YOLO base adapter reads `engine` from the config:

- `ort` or absent: ONNX Runtime with an `.onnx` file. The adapter requests
  `CPUExecutionProvider` when the preferred device is CPU and
  `CUDAExecutionProvider` when the preferred device is GPU.
- `dnn`: OpenCV DNN with an `.onnx` file. GPU mode asks OpenCV DNN to use CUDA
  backend/target.
- `trt`: TensorRT with an `.engine` file. The TensorRT engine helper strips an
  Ultralytics JSON metadata prefix when present, deserializes the engine, and
  allocates CUDA buffers.

If the engine is absent, treat it as ONNX Runtime. Do not set `engine: trt` for
an ONNX file or set `engine: ort` for a TensorRT engine file.

## Model path resolution

Model adapters call `get_model_abs_path(config, field_name)` for path fields.
The behavior is:

1. If the value is not `http://` or `https://`, it is treated as a local path.
   X-AnyLabeling first checks it as written relative to the current process
   directory, then relative to the config file's folder. Absolute paths also
   work, but runtime skill guidance should prefer portable project-relative
   paths in user configs.
2. If the value is an HTTP(S) URL, X-AnyLabeling downloads it into the model
   cache, validates an existing cached file when possible, and returns the cached
   path.
3. Some adapters support non-file identifiers. For example, Florence2 configs
   may use a model id such as a Hugging Face model identifier; that adapter owns
   the extra loading behavior.

Path-like fields include `model_path`, `encoder_model_path`,
`decoder_model_path`, `det_model_path`, `rec_model_path`, `cls_model_path`,
`pose_model_path`, `tag_model_path`, `model_pf_path`, `embedding_model_path`,
SAM3 sidecar data paths, and OCR dictionary paths.

## Cache and work directory behavior

When a URL-backed model is loaded, X-AnyLabeling stores model files under a data
workspace:

```text
<work-dir>/xanylabeling_data/models/<model-name>/<downloaded-file>
```

The default work directory is the user's home directory. Starting X-AnyLabeling
with `--work-dir <directory>` moves the data workspace under that directory. The
loader also contains migration logic for older `anylabeling_data` directories;
if the workspace is writable and the new `xanylabeling_data` directory does not
already exist, legacy data can be renamed.

For each cached model file:

- Known `.onnx`, `.pth`, and `.pt` files are checked in a subprocess before
  reuse. ONNX uses `onnx.checker.check_model`; Torch formats use `torch.load` on
  CPU.
- Empty or failed known files are treated as corrupt and deleted for
  redownload.
- Unknown file extensions are accepted if the file exists and is non-empty.
- Downloads use a `.part` file, retry failed network reads, and support
  cancellation. Cache path sanitization prevents downloaded files from escaping
  the model cache directory.

## ModelScope versus default download URLs

URL-backed configs normally use the URL stored in the YAML. X-AnyLabeling can
rewrite downloads to ModelScope in this priority order:

1. Environment variable `XANYLABELING_MODEL_HUB=modelscope` forces ModelScope.
   If the variable is set to another non-empty value, the original URL is used.
2. If the variable is unset or empty, user config `model_hub: modelscope` selects
   ModelScope. `model_hub: github` keeps the original URL.
3. If neither is set, Chinese UI language (`zh_CN`) falls back to ModelScope;
   other languages keep the original URL.

When ModelScope is selected, the download URL is rewritten to the CVHub520
ModelScope namespace using the model config `name` prefix and the original
filename. If users report network or regional mirror issues, check the env var,
user config, and UI language before changing YAML.

## Remote server and API-backed behavior

`remote_server` is a normal model type in the registry but inference happens
through HTTP. The client:

- reads server URL from saved remote server settings, then from
  `XANYLABELING_SERVER_URL`, falling back to `http://localhost:8000`;
- sends a `Token` header from saved settings when an API key is configured;
- discovers available models from `/v1/models`;
- sends predictions to `/v1/predict` with the current model id, image data, and
  thresholds/prompt parameters;
- uses `/v1/video/init`, `/v1/video/prompt`, and propagation/reset endpoints for
  supported video prompt workflows.

`grounding_dino_api` uses the `GROUNDING_DINO_API_TOKEN` environment variable or
UI token setter and calls an external Grounding DINO API endpoint. It requires a
non-empty text prompt whose words are separated by dots, for example `cat.dog`.

PaddleOCR document parsing can use official API models or remote service models
advertising a PaddleOCR pipeline capability. This is separate from ordinary
built-in OCR detection-recognition configs and requires valid API/service setup.

## Safe backend choice recipe

1. Start with `[cpu]` if the task is registry inspection, config validation,
   conversion, UI setup, or CPU inference with ONNX models. This was the only
   verified path during construction.
2. Choose `[gpu]`, `[gpu-cu11]`, or `[gpu-cu13]` only when the deployment's CUDA
   version and cuDNN compatibility are known. Use one fresh environment per GPU
   family rather than mixing extras.
3. Use TensorRT only when the user has a `.engine` built for the target GPU and
   TensorRT runtime, plus `tensorrt` and `cuda-python` installed.
4. For remote/API models, test connectivity and tokens separately from local
   package installation. A working local `xanylabeling` install does not prove
   remote server availability.
5. For model downloads, decide whether default URLs or ModelScope are expected,
   then run a small known model load only if downloads are allowed. The bundled
   inspector intentionally avoids model downloads.

## Verified and unverified backends

Verified in construction:

- package metadata for `x-anylabeling-cvhub` 4.0.2;
- import of `anylabeling` in the prepared environment;
- CLI availability in that prepared environment;
- conversion registry count of 19 tasks;
- ONNX Runtime with `CPUExecutionProvider`;
- ModelManager registry count of 204 after config/work-directory initialization.

Not verified in construction:

- CUDA/GPU ONNX Runtime inference;
- TensorRT import, deserialization, or execution;
- actual model downloads from default URLs or ModelScope;
- remote server endpoints and API tokens;
- training/export workflows.
