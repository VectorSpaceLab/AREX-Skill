# VLM and ASR Workflows

This reference covers Docling's advanced conversion pipelines: full-page VLM conversion for PDFs and ASR transcription for audio/video. These workflows are optional, can be expensive, and often require model downloads or remote services.

## VLM Pipeline Quick Start

Use `VlmPipeline` when the document should be converted page-by-page by a vision-language model instead of the standard layout/OCR/table stack.

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

result = converter.convert("input.pdf", max_num_pages=5)
markdown = result.document.export_to_markdown()
```

Use small `max_num_pages` or `page_range` while validating a setup. VLM inference can be much slower and more memory-heavy than the standard pipeline.

## VLM Presets and Runtime Overrides

The installed Docling package exposes preset helpers through `VlmConvertOptions.from_preset(...)`. Common preset IDs include model families such as `granite_docling`, `smoldocling`, `granite_vision`, `pixtral`, `qwen`, `nanonets_ocr2`, `gemma_12b`, `gemma_27b`, and others depending on version.

```python
import platform

from docling.datamodel.pipeline_options import VlmConvertOptions, VlmPipelineOptions
from docling.datamodel.vlm_engine_options import (
    MlxVlmEngineOptions,
    TransformersVlmEngineOptions,
)

engine_options = (
    MlxVlmEngineOptions()
    if platform.system() == "Darwin" and platform.machine() == "arm64"
    else TransformersVlmEngineOptions()
)

pipeline_options = VlmPipelineOptions(
    vlm_options=VlmConvertOptions.from_preset(
        "granite_docling",
        engine_options=engine_options,
    )
)
```

Choose MLX only on Apple Silicon environments with MLX dependencies installed. Use Transformers for portable local inference when the model supports it.

## Remote Model API Inside VLM Pipeline

Remote VLM runtimes are local-pipeline components, not `docling-serve` service clients. They still require explicit opt-in because document page images/text may be sent to the configured endpoint.

```python
from docling.datamodel.pipeline_options import VlmConvertOptions, VlmPipelineOptions
from docling.datamodel.vlm_engine_options import ApiVlmEngineOptions, VlmEngineType

vlm_options = VlmConvertOptions.from_preset(
    "granite_docling",
    engine_options=ApiVlmEngineOptions(
        engine_type=VlmEngineType.API_LMSTUDIO,
        timeout=90,
        concurrency=4,
    ),
)

pipeline_options = VlmPipelineOptions(
    vlm_options=vlm_options,
    enable_remote_services=True,
)
```

Typical OpenAI-compatible endpoints include LM Studio, Ollama, vLLM, and cloud APIs. Confirm the endpoint, model name, API key/header requirements, concurrency, timeout, and privacy policy before enabling.

## Force-Backend Text VLM Route

For text-heavy pages where the user explicitly wants VLM behavior, force `VlmPipeline` and a VLM preset rather than relying on standard OCR/table options. A useful validation case is a one-page, mostly text PDF with a small figure:

1. Run one page with `VlmPipeline` and `VlmConvertOptions.from_preset("granite_docling")`.
2. Keep `max_num_pages=1` while validating the backend.
3. Compare the output with standard conversion only after the VLM setup is known to work.
4. If using a remote API backend, verify `enable_remote_services=True` and endpoint availability.

Do not use a VLM route just to fix ordinary OCR language or table-structure settings; those belong to the standard pipeline configuration path.

## ASR Pipeline Quick Start

Use `AsrPipeline` for audio and video files. Docling produces a `DoclingDocument` transcript that can be exported like other converted documents.

```python
from pathlib import Path

from docling.datamodel import asr_model_specs
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import AsrPipelineOptions
from docling.document_converter import AudioFormatOption, DocumentConverter
from docling.pipeline.asr_pipeline import AsrPipeline

pipeline_options = AsrPipelineOptions()
pipeline_options.asr_options = asr_model_specs.WHISPER_TURBO

converter = DocumentConverter(
    format_options={
        InputFormat.AUDIO: AudioFormatOption(
            pipeline_cls=AsrPipeline,
            pipeline_options=pipeline_options,
        )
    }
)

result = converter.convert(Path("recording.mp3"))
print(result.document.export_to_markdown())
```

Supported media types include common audio files such as WAV, MP3, M4A, AAC, OGG, and FLAC, plus video containers such as MP4, AVI, and MOV when their audio track can be decoded.

## ASR Preflight

Before converting media:

- Install ASR extras, for example `pip install "docling[asr]"`.
- Ensure `ffmpeg` is on `PATH`; video and many audio formats depend on it.
- Expect model download or cache lookup on first use unless artifacts are already available.
- Use a short fixture or small `max_file_size` when validating user-supplied media.

Run the bundled backend checker first:

```sh
python scripts/check_optional_backends.py --as-json
```

## Exporting Advanced Pipeline Results

Both VLM and ASR return `ConversionResult` with a `DoclingDocument`. Route export decisions to the document-output guidance:

```python
markdown = result.document.export_to_markdown()
data = result.document.export_to_dict()
html = result.document.export_to_html()
```

For subtitles such as SRT/WebVTT, use a dedicated ASR/subtitle tool; Docling's ASR output is paragraph-level transcript Markdown with timestamps in current public guidance.
