# Pipeline troubleshooting

Use this when a PaddleX pipeline run fails before routing to module training or deployment setup.

## Unknown pipeline name or config

Symptoms:

- `Unsupported pipeline` or `pipeline not found`.
- CLI accepts the command but fails before model creation.
- Case-sensitive document pipeline names fail.

Actions:

1. Check exact spelling and case. Examples: `OCR`, `PP-StructureV3`, `PaddleOCR-VL`, `image_classification`, `ts_forecast`.
2. If using YAML, confirm the file exists and is a pipeline config, not a module-training config.
3. Export a fresh built-in config with `paddlex --get_pipeline_config NAME` and compare top-level keys.
4. If the user wants to train or export a single model config, use `../modules/` instead.

## Input parsing failures

Actions:

- Confirm the pipeline supports the input kind: image, document/PDF, CSV, audio, video, directory, dict/list.
- Start with one local file before a directory or URL batch.
- For time-series pipelines, confirm timestamp, target, grouping, and feature columns match the config.
- For ChatOCR/document-understanding, check whether the pipeline expects a document plus a question/schema/config dict rather than a bare file path.

## Save-path surprises

Symptoms:

- Only one output appears for a multi-page document.
- JSON exists but images/HTML/XLSX/Markdown are missing.
- A result save method is absent on one pipeline's result object.

Actions:

1. Use a directory for `save_path` and result save helpers.
2. Call only save helpers supported by the result object; the bundled smoke helper probes common methods and skips unsupported ones.
3. For document pipelines, request the artifact type explicitly: image, JSON, HTML, XLSX, Markdown, or CSV.
4. Avoid hard-coded file names for batches unless the result object documents safe naming.

## Device and backend problems

Symptoms:

- `No module named paddle` or PaddlePaddle import errors.
- GPU requested but Paddle reports no CUDA support.
- HPI/TensorRT/ONNX backend errors after enabling `use_hpip` or `engine`.

Actions:

- Install a PaddlePaddle build matching the requested device before installing/running PaddleX.
- Use `device="cpu"` for a baseline smoke run.
- Use `device="gpu:0"` only when a GPU PaddlePaddle wheel is installed and verified.
- Route HPI, TensorRT, Paddle2ONNX, serving, and GenAI server setup to `../deployment/`.
- Clear HPI/model caches after changing TensorRT dynamic shapes or backend versions.

## Engine/config precedence mistakes

Common mistakes:

- setting `use_hpip=True` and also forcing an incompatible `engine`.
- placing `engine_config` at the wrong nesting level for a multi-submodule pipeline.
- editing YAML defaults and then overriding them unintentionally from CLI/API flags.

Actions:

1. Start from a clean exported YAML.
2. Keep pipeline identity and submodule defaults in YAML.
3. Keep run-specific `device`, `input`, `save_path`, and quick backend overrides in CLI/API arguments.
4. If the task is deployment-oriented, move to `../deployment/`.

## Remote service / credential failures

Pipelines such as `PP-DocTranslation`, `PP-ChatOCRv4-doc`, and PaddleOCR-VL variants may rely on external LLM/GenAI services or a local GenAI server. Do not treat these like ordinary image-classification examples.

Checklist:

- Is an API key or model-server URL required?
- Is `genai_config.server_url` supplied when using a server-backed GenAI client?
- Are the `genai-client` or server plugin dependencies installed?
- Is the target backend (`vllm`, `sglang`, `fastdeploy`, etc.) available on the host?

Use `../deployment/references/deployment-overview.md` for the server/client split.

## Video and codec failures

Video pipelines need a decoder such as `decord` plus platform codecs. If package health checks complain about the decoder or import fails, keep video examples optional and verify image/OCR/time-series pipelines first.
