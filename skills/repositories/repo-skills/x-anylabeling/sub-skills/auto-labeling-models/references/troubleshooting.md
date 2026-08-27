# Auto-labeling model troubleshooting

Use this symptom-oriented guide after identifying whether the user is loading a
built-in model, an adapted custom YAML, an unadapted model adapter, a remote/API
model, or an optional GPU/TensorRT backend.

## Config does not appear or custom loading says invalid format

Checklist:

1. Parse the YAML with the bundled inspector:

   ```bash
   python sub-skills/auto-labeling-models/scripts/inspect_model_configs.py --custom-config model.yaml
   ```

2. Confirm `type`, `name`, and `display_name` exist.
3. Confirm `type` is one of the supported custom-capable types for config-only
   loading. If it is new, this is an unadapted-model development task, not a
   custom-loader task.
4. Confirm `name` contains only letters, numbers, dots, underscores, and hyphens
   and is not `.` or `..`. Slashes, backslashes, spaces, absolute paths, empty
   strings, and non-ASCII names are rejected.
5. Confirm path-like fields are present for the chosen adapter. Many adapters
   need fields beyond the generic three required custom fields.
6. If boolean-looking class names are important, place them under `classes` or
   `filter_classes`; X-AnyLabeling's loader preserves those list values as
   strings.

Likely fixes:

- Copy the closest built-in config pattern and edit paths/classes/thresholds
  rather than writing a config from scratch.
- Use a unique valid `name`; do not include `_custom_` manually unless you know
  you are matching runtime internals.
- For local files, place weights next to the YAML and use a relative path such as
  `./weights/model.onnx`.

## Unsupported model type

If a config-only custom load reports that the type is unsupported, the selected
`type` is not in the custom-capable model list. Do one of the following:

- Change `type` to an already adapted family whose tensor/output contract matches
  the model.
- If no adapted family fits, follow the unadapted-model development workflow in
  [custom-models.md](custom-models.md): add config, registry entry, UI behavior
  lists, ModelManager branch, and a `Model` subclass with `predict_shapes` and
  `unload`.

Do not solve an unsupported type by changing only `display_name` or `provider`;
those are not dispatch keys.

## Missing model path, download failure, or network block

Symptoms include `Model path not found`, `Could not download model`, or a cached
file being deleted and redownloaded.

Checklist:

1. Decide whether the config should use a local path, a default URL, or
   ModelScope.
2. For a local path, check both path resolution locations: process working
   directory and the config file's folder. Prefer paths relative to the YAML
   file for portability.
3. For a URL, verify the selected source:
   - `XANYLABELING_MODEL_HUB=modelscope` forces ModelScope;
   - another non-empty `XANYLABELING_MODEL_HUB` value keeps the original URL;
   - user config `model_hub: modelscope` selects ModelScope when the env var is
     unset/empty;
   - Chinese UI language may fall back to ModelScope when no explicit source is
     set.
4. If network is blocked, manually download the file from an allowed source and
   change the config to a local path.
5. If a cached file is corrupt, remove the specific cached model file or model
   subdirectory and retry once the network/source is correct.

Do not ask the registry inspector to validate downloads; it is intentionally
non-loading and non-downloading.

## Existing cached model is treated as corrupt

Known `.onnx`, `.pth`, and `.pt` files are validated before reuse. ONNX files are
checked with ONNX's model checker; Torch files are loaded on CPU. Unknown file
extensions are accepted if non-empty.

Fixes:

- Re-copy or redownload the model file; partial downloads are often the cause.
- Confirm the URL filename matches the expected file format.
- If the file is a TensorRT `.engine`, use `engine: trt`; it will not be checked
  by the ONNX/Torch validation path but still must deserialize at TensorRT load
  time.

## ONNX Runtime provider or package conflict

Symptoms include provider-not-found errors, GPU provider silently unavailable,
`DLL load failed`, `libonnxruntime_providers_cuda.so` errors, or inconsistent
NumPy/ONNX versions.

Checklist:

1. Run a small provider check in the target environment:

   ```bash
   python - <<'PY'
   import onnxruntime as ort
   print(ort.__version__)
   print(ort.get_available_providers())
   PY
   ```

2. Confirm only one ONNX Runtime distribution is installed. Remove either
   `onnxruntime` or `onnxruntime-gpu`; do not keep both.
3. Match the package extra to CUDA:
   - CPU: `[cpu]` with `onnxruntime`;
   - CUDA 11.x: `[gpu-cu11]`;
   - CUDA 12.x: `[gpu]`;
   - CUDA 13.x: `[gpu-cu13]`.
4. Confirm CUDA/cuDNN versions match the ONNX Runtime GPU wheel compatibility.
5. If GPU is optional, fall back to a clean `[cpu]` environment and use
   `CPUExecutionProvider`.

Construction verified CPU ONNX Runtime only, so do not claim GPU readiness
without running this check in the user's environment.

## TensorRT ImportError or deserialization failure

Symptoms include `TensorRT execution provider requires the 'tensorrt' and
'cuda-python' packages`, CUDA runtime errors, or `Failed to deserialize TensorRT
engine`.

Checklist:

1. Install TensorRT-specific dependencies only in an environment intended for
   TensorRT:

   ```bash
   pip install tensorrt cuda-python
   ```

2. Confirm NVIDIA driver, CUDA runtime, and TensorRT version are compatible.
3. Confirm the `.engine` file was built for the same GPU architecture and the
   same major TensorRT version. TensorRT engines are not portable across many
   GPU/TensorRT combinations.
4. Use `engine: trt` and a `.engine` `model_path`; use `engine: ort` or no
   `engine` for ONNX files.
5. If the engine has an Ultralytics JSON metadata prefix, X-AnyLabeling's helper
   strips it automatically; do not manually edit the engine file unless you have
   separate evidence it is malformed.

## Remote server does not list models or predictions fail

Checklist:

1. Confirm the model type is `remote_server` and the client is configured with
   the intended server URL. The fallback URL is `http://localhost:8000`.
2. Confirm `XANYLABELING_SERVER_URL` or saved settings are not pointing at the
   wrong server.
3. Confirm the API key/token saved in remote server settings matches the server's
   expected `Token` header.
4. Check `/v1/models` manually with the same URL/token. The UI model dropdown
   cannot show models if discovery fails.
5. For prediction errors, check `/v1/predict` and whether the selected model id
   supports the current task, class filters, prompts, or video mode.
6. For video prompts, confirm the server supports video init/prompt/propagation
   endpoints and that frame paths are accessible to the client for packaging.

A working local package install does not verify any remote server endpoint.

## API token errors

- `grounding_dino_api` needs an API token. Set it in the UI or provide
  `GROUNDING_DINO_API_TOKEN` before launch.
- Grounding DINO API prompts must be non-empty English words separated by dots,
  for example `cat.dog`. Commas, spaces, and arbitrary prose are rejected by the
  adapter.
- PaddleOCR official API document parsing needs its own API key saved in the
  PaddleOCR settings. Remote PaddleOCR models only appear when the remote server
  advertises the expected PaddleOCR pipeline capability.

## ModelManager fails in headless scripts

ModelManager expects X-AnyLabeling config/work-directory initialization. If a
headless script directly instantiates `ModelManager` before config initialization,
it may look for a user config path that is not set.

Use the bundled inspector instead of writing ad-hoc registry code. It creates a
temporary work directory, initializes the config module safely, and never loads
weights. If writing your own script, set a work directory and config file before
creating `ModelManager`.

## Wrong output shape, labels, or thresholds

- Confirm `classes` order matches the model's training/export order.
- For pose, confirm the class-to-keypoint mapping and model keypoint metadata
  agree. Invalid `kpt_shape` metadata is rejected by YOLO pose adapters.
- For segmentation, tune `epsilon_factor`/mask fineness only after proving the
  model outputs valid masks.
- For SAHI models, use `slice_height`, `slice_width`, and overlap ratios that
  match object scale.
- For OCR, confirm detector/recognizer/classifier paths and dictionary fields.
  PPOCR v6 can derive some dictionary and DB parameters from official inference
  metadata, but explicit config values remain useful for portability.

## When to stop and reroute

- Dataset conversion problems belong to `../conversion-cli/SKILL.md`.
- GUI editing, XLABEL schema, review state, or manual correction problems belong
  to `../annotation-ui/SKILL.md`.
- Training/exporting a new model or packaging a modified application belongs to
  `../developer-workflows/SKILL.md`.
