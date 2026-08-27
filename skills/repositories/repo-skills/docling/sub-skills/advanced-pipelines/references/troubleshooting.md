# Advanced Pipeline Troubleshooting

Use this guide for VLM, ASR, enrichment, optional backend, GPU/MLX, remote model API, and offline artifact failures.

## Missing Optional Extras

Symptoms:

- Import errors for `AsrPipeline`, VLM engine options, Transformers, MLX, Whisper, or image/audio libraries.
- CLI or API reports that an optional backend is unavailable.

Fixes:

- Install the relevant Docling extra or backend dependency for the feature.
- For ASR, start with `pip install "docling[asr]"`.
- Run `scripts/check_optional_backends.py --as-json` before attempting model execution.
- Do not treat a successful base `import docling` as proof that VLM, ASR, or GPU extras are installed.

## Model Download or Offline Failures

Symptoms:

- First VLM/ASR/enrichment run appears to hang while resolving artifacts.
- Errors mention Hugging Face, model repositories, cache paths, or missing artifact files.
- Air-gapped machines fail despite code being correct.

Fixes:

```sh
docling-tools models download
export DOCLING_ARTIFACTS_PATH=/opt/docling-models
```

For offline deployments, prefetch on a connected machine, copy the complete artifact directory, then point Docling to it with `DOCLING_ARTIFACTS_PATH` or a pipeline `artifacts_path` field when available. The bundled preflight script does not prove artifacts are present because it intentionally avoids downloads and model loading.

## GPU Unavailable or Not Used

Symptoms:

- `torch.cuda.is_available()` is false.
- VLM conversion falls back to CPU and is unexpectedly slow.
- CUDA device errors occur when loading a model.

Fixes:

- Verify the installed PyTorch build matches the CUDA driver/runtime.
- Use CPU or `AUTO` while debugging option shape.
- Reduce to one page and a smaller preset before testing throughput.
- For high-throughput VLM, consider a separate inference server and API runtime rather than loading a large model inline per process.

## MLX Selected on the Wrong Platform

Symptoms:

- MLX imports fail.
- Runtime errors occur on Linux, Windows, or Intel macOS.

Fix:

Use MLX only on Apple Silicon:

```python
import platform

is_apple_silicon = platform.system() == "Darwin" and platform.machine() == "arm64"
```

Select `MlxVlmEngineOptions` only when this check is true and MLX packages are installed. Use Transformers or an API runtime elsewhere.

## `ffmpeg` Missing for ASR

Symptoms:

- Audio/video conversion fails before transcription.
- Errors mention decoding, unsupported audio stream, or missing `ffmpeg`.

Fixes:

- Install `ffmpeg` with the system package manager.
- Ensure `ffmpeg` is on `PATH` for the Python process.
- Re-run `scripts/check_optional_backends.py` and confirm the `ffmpeg` binary check passes.
- Test with a short audio file before processing large video archives.

## Remote Model API Rejected

Symptoms:

- Errors mention `OperationNotAllowed` or remote services not being enabled.
- API-backed VLM or picture description options are configured but conversion refuses to run.

Fix:

```python
pipeline_options = VlmPipelineOptions(
    vlm_options=vlm_options,
    enable_remote_services=True,
)
```

For picture description under the standard PDF pipeline, set `enable_remote_services=True` on the relevant `PdfPipelineOptions` object. Confirm this with the user because document content may be sent to the endpoint.

## Remote Model API Connection or Authentication Failure

Symptoms:

- HTTP connection refused, timeout, 401/403, 404 model not found, or invalid response schema.

Fixes:

- Confirm the endpoint is a chat-completions-compatible URL.
- Confirm local servers such as LM Studio, Ollama, or vLLM are already running.
- Confirm model names match the serving runtime, not necessarily the Hugging Face repo ID.
- Provide API keys through environment variables or secure config, not hard-coded examples.
- Lower concurrency and raise timeout for slow models.

## Expensive or Skipped Behavior

Symptoms:

- Tests or examples skip VLM/API runs.
- CI marks VLM tests with ML or expensive markers.
- Local execution is very slow or memory-heavy.

Fixes:

- Treat skipped VLM/ASR tests as normal unless the environment explicitly provides models and hardware.
- Use one-page PDFs and short audio fixtures for smoke tests.
- Set `max_num_pages`, `max_file_size`, and small `page_range` values during validation.
- Ask before pulling models, running full-document VLM conversion, or contacting paid APIs.

## Enrichment Does Nothing

Symptoms:

- Output lacks code languages, formula LaTeX, picture classes, or descriptions.

Fixes:

- Confirm the relevant toggle is enabled: `do_code_enrichment`, `do_formula_enrichment`, `do_picture_classification`, or `do_picture_description`.
- For picture enrichment, ensure picture images are generated when the selected option requires them.
- Confirm the source document actually contains matching `CodeItem`, formula-labeled text, or picture regions.
- Confirm optional model artifacts are available.

## Wrong Option Nesting

Symptoms:

- Converter construction fails or pipeline options are ignored.

Fix:

Use format option wrappers:

```python
from docling.datamodel.base_models import InputFormat
from docling.document_converter import AudioFormatOption, PdfFormatOption

format_options = {
    InputFormat.PDF: PdfFormatOption(pipeline_cls=VlmPipeline, pipeline_options=pdf_options),
    InputFormat.AUDIO: AudioFormatOption(pipeline_cls=AsrPipeline, pipeline_options=asr_options),
}
```

Do not pass bare pipeline option objects directly as `format_options` values.

## Safe Fallbacks

- For VLM failures: switch to a one-page local PDF, a known preset, and CPU/Transformers or an already-running approved API endpoint.
- For ASR failures: check `ffmpeg`, ASR imports, and a short MP3 before debugging model accuracy.
- For enrichment failures: enable one enrichment at a time.
- For offline failures: prove artifacts exist before running conversion.
