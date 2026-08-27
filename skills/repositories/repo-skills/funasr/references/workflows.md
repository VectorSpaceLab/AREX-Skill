# FunASR workflows

Use this page to decide which sub-skill to read first. It is intentionally broad and routes specialized details elsewhere.

## Fast start choices

| User goal | First stop | Why |
|---|---|---|
| Transcribe a file, folder, or stream of files | `python-asr-pipelines` | This owns `AutoModel`, the `funasr` CLI, audio decoding, hotwords, timestamps, and subtitle generation. |
| Clean punctuation spacing or run ITN/TN | `text-normalization` | This owns the pure punctuation helper and the optional FunTextProcessing stack. |
| Expose FunASR as an API, websocket service, MCP tool, or runtime package | `serving-and-runtime` | This owns the packaged service CLIs, smoke helpers, and runtime deployment notes. |
| Decide whether Nano / GLM / Qwen3 should use vLLM | `llm-asr-and-vllm` | This owns model-family applicability, dtype, and backend caveats. |
| Build manifests, train, export, or run local inference after export | `training-data-and-export` | This owns manifest conversion, config precedence, export, and package-data checks. |

## Common end-to-end paths

### 1. First local transcription

1. Read `model-overview.md` and choose a starting checkpoint.
2. Read `python-asr-pipelines`.
3. Use `AutoModel` or the `funasr` CLI.
4. Add VAD or punctuation only when the output needs it.

### 2. Subtitle generation

1. Start in `python-asr-pipelines`.
2. Use the bundled subtitle helper.
3. Prefer sentence timestamps when available.
4. Fall back to VAD or duration bounds only when the model does not provide sentence-level segmentation.

### 3. Web/API deployment

1. Decide the runtime surface in `serving-and-runtime`.
2. Use the packaged server CLI or one of the bundled smoke helpers.
3. Check CORS, port binding, and optional dependency availability before exposing the service.
4. If the model family is Nano or GLM, route back to `llm-asr-and-vllm` for backend caveats.

### 4. Model-family acceleration

1. Read `llm-asr-and-vllm` before choosing a GPU/vLLM route.
2. Confirm the checkpoint family first.
3. Use `bf16` by default on modern CUDA hardware.
4. Keep Qwen3-ASR separate from FunASR `AutoModelVLLM`.

### 5. Training or export

1. Read `training-data-and-export`.
2. Validate manifests before launching long jobs.
3. Keep top-level distributed flags and nested `train_conf` precedence in mind.
4. Check local inference and export assumptions before trusting a checkpoint.

### 6. Text cleanup after ASR

1. Read `text-normalization` if the transcript words are already correct but spacing or spoken/written form needs cleanup.
2. Use the pure punctuation helper before reaching for the full Pynini stack.

## Integrated difficult cases to keep in mind

- Transcribe a short WAV, normalize punctuation, and write a subtitle file.
- Choose the right model family, start a local speech API, and confirm the smoke helper can reach it.

## Basic operating pattern

- Prefer the smallest working route first.
- Move to a more specialized sub-skill only when the task really needs its dependency surface.
- Keep the bundled helper scripts inside the generated skill tree.
