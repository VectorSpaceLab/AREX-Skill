---
name: advanced-pipelines
description: "Configure Docling VLM, ASR, enrichment, model-catalog, optional
  backend, GPU, MLX, remote-model API, and offline model workflows without
  triggering unsafe downloads by default."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Advanced Pipelines

Use this sub-skill when a task needs Docling's heavy or optional pipelines rather than the standard PDF OCR/table path.

## Route Here For

- Running the `VlmPipeline` for full-page PDF conversion with DocTags or Markdown VLM output.
- Selecting VLM presets, inference engines, MLX, Transformers, vLLM, Ollama, LM Studio, OpenAI-compatible APIs, or runtime overrides.
- Running the `AsrPipeline` for audio/video transcription through `InputFormat.AUDIO`.
- Enabling code, formula, picture classification, picture description, chart, or VLM-backed enrichment stages.
- Choosing model families from the Docling model catalog and planning GPU, CUDA, MPS, MLX, XPU, API, or offline artifact deployments.
- Prefetching or validating model artifacts for air-gapped use, while avoiding conversion-time downloads in preflight checks.

## Route Elsewhere

- Basic conversion, `DocumentConverter.convert`, strings, URLs, streams, or failure handling: use `conversion`.
- CLI syntax, supported format tables, and shell export recipes: use `cli-and-formats`.
- Standard PDF OCR engines, table structure options, accelerators, and `artifacts_path` basics: use `pipeline-configuration`.
- Remote `docling-serve` service clients, service URLs, API keys, and service CLI routing: use `remote-service-client` when available. Remote model APIs embedded inside a local pipeline remain here.
- Markdown, JSON, HTML, DocTags export, serialization, or chunking: use `document-outputs`.

## Safe Defaults

- Do not run VLM, ASR, enrichment, or model-prefetch commands unless the user opted into downloads, expensive inference, and any remote data transfer.
- Use `scripts/check_optional_backends.py` for read-only environment preflight; it checks imports and binaries but does not instantiate models, download weights, contact model APIs, or convert documents.
- For remote model APIs inside `VlmPipeline` or picture description, set `enable_remote_services=True` only after confirming the endpoint and data-sharing policy.
- For ASR, confirm `docling[asr]` and `ffmpeg` before converting audio/video.

## Core Patterns

```python
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import VlmConvertOptions, VlmPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.pipeline.vlm_pipeline import VlmPipeline

vlm_options = VlmConvertOptions.from_preset("granite_docling")
converter = DocumentConverter(
    format_options={
        InputFormat.PDF: PdfFormatOption(
            pipeline_cls=VlmPipeline,
            pipeline_options=VlmPipelineOptions(vlm_options=vlm_options),
        )
    }
)
```

```python
from docling.datamodel import asr_model_specs
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import AsrPipelineOptions
from docling.document_converter import AudioFormatOption, DocumentConverter
from docling.pipeline.asr_pipeline import AsrPipeline

pipeline_options = AsrPipelineOptions(asr_options=asr_model_specs.WHISPER_TURBO)
converter = DocumentConverter(
    format_options={
        InputFormat.AUDIO: AudioFormatOption(
            pipeline_cls=AsrPipeline,
            pipeline_options=pipeline_options,
        )
    }
)
```

## References

- `references/vlm-asr-ocr.md` for VLM conversion, ASR transcription, remote model API, and force-backend decision patterns.
- `references/model-overview.md` for model-stage selection across VLM convert, picture description, code/formula, layout, table, and ASR.
- `references/optional-backends.md` for extras, GPUs, MLX, CUDA, API runtimes, model artifacts, and offline planning.
- `references/troubleshooting.md` for missing extras, model downloads, remote-service gates, GPU/MLX issues, `ffmpeg`, skip behavior, and expensive runs.
- `scripts/check_optional_backends.py` for safe installed-environment checks before running advanced pipelines.
