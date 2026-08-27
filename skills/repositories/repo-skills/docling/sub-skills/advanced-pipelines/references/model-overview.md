# Advanced Model Overview

Docling's advanced pipelines combine stage-specific models with inference engines. Prefer preset helpers when available, then validate installed fields with a read-only inspection script before building production code.

## Stage Selection

| Stage | Use when | Typical controls |
| --- | --- | --- |
| VLM convert | Full page PDF conversion should be driven by a vision-language model | `VlmPipeline`, `VlmPipelineOptions`, `VlmConvertOptions.from_preset(...)` |
| Picture description | Existing picture regions need captions or descriptions | `PdfPipelineOptions.do_picture_description`, picture description options |
| Picture classification | Picture regions need figure/chart/diagram/image classes | `PdfPipelineOptions.do_picture_classification` |
| Code enrichment | Code blocks need language/semantic enrichment | `PdfPipelineOptions.do_code_enrichment` |
| Formula enrichment | Formula text/items need LaTeX/math enrichment | `PdfPipelineOptions.do_formula_enrichment` |
| ASR | Audio/video needs transcription into a `DoclingDocument` | `AsrPipeline`, `AsrPipelineOptions`, `asr_model_specs` |
| Standard OCR/tables | Scanned PDFs and table recovery need deterministic local extraction | Route to `pipeline-configuration` |

## VLM Convert Model Families

The public model catalog groups VLM conversion presets by output and runtime support:

- DocTags-oriented models such as Granite Docling and SmolDocling are preferred when structured Docling output is the goal.
- Markdown-oriented models such as Granite Vision, Pixtral, GOT-OCR, Phi-4 multimodal, Qwen, Nanonets OCR2, Gemma, Dolphin, and similar families are useful when direct Markdown output is acceptable.
- Runtime support varies by model: Transformers, MLX, API, vLLM, Ollama, LM Studio, and OpenAI-compatible services are not interchangeable for every preset.
- Large models can require substantial GPU memory or service-side resources; validate with one page before scaling.

Safe selection flow:

1. Start with `VlmConvertOptions.from_preset("granite_docling")` for a stable default.
2. Override the engine only when the target platform is known.
3. Use MLX only for Apple Silicon setups.
4. Use API/vLLM runtimes for throughput-oriented GPU serving after confirming remote-service opt-in.
5. Keep page limits during validation.

## Picture Enrichment Models

Picture enrichment is part of the standard PDF pipeline but belongs here when it uses optional VLM/classifier stages.

```python
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption

pipeline_options = PdfPipelineOptions()
pipeline_options.generate_picture_images = True
pipeline_options.images_scale = 2
pipeline_options.do_picture_classification = True
pipeline_options.do_picture_description = True

converter = DocumentConverter(
    format_options={
        InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
    }
)
```

Known picture-description choices include local VLM presets such as SmolVLM and Granite Vision where supported, custom Hugging Face VLM options, and remote API options. Remote picture description requires `enable_remote_services=True`.

## Code and Formula Enrichment

Code and formula enrichment are disabled by default because they add model work.

```python
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption

pipeline_options = PdfPipelineOptions()
pipeline_options.do_code_enrichment = True
pipeline_options.do_formula_enrichment = True

converter = DocumentConverter(
    format_options={
        InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
    }
)
```

Use these toggles when the source documents contain meaningful code blocks or mathematical formulas and the user accepts extra inference cost. Avoid enabling them globally for generic document ingestion.

## Chart and Figure Decisions

For charts and figures, choose the lightest stage that satisfies the task:

- Need to identify whether a picture is a chart, diagram, logo, signature, or natural image: enable picture classification.
- Need natural-language descriptions of figures: enable picture description and choose local or remote VLM options.
- Need page-level VLM output for text-heavy or layout-heavy pages: use `VlmPipeline` rather than picture-only enrichment.

## ASR Model Decisions

Use `asr_model_specs.WHISPER_TURBO` as the default ASR model spec unless the user asks for a larger model. Docling's ASR path selects the appropriate implementation for the environment when supported, including MLX Whisper on Apple Silicon and native Whisper elsewhere.

```python
from docling.datamodel import asr_model_specs
from docling.datamodel.pipeline_options import AsrPipelineOptions

pipeline_options = AsrPipelineOptions()
pipeline_options.asr_options = asr_model_specs.WHISPER_TURBO
```

Use larger ASR specs only after confirming runtime cost, model availability, and expected accuracy gain.

## Model Artifacts and Offline Use

Most advanced models are downloaded on first use unless already prefetched. For offline deployments:

```sh
docling-tools models download
export DOCLING_ARTIFACTS_PATH=/opt/docling-models
```

Then point pipeline options at the copied artifact directory where supported. Do not put machine-specific local paths into reusable skill content or shared scripts; use user-provided paths or environment variables.

## Version-Safe Introspection

Installed Docling versions can add, rename, or remove presets and options. Use explicit imports and Pydantic fields instead of guessing dynamic attributes. For no-download checks, run:

```sh
python scripts/check_optional_backends.py --as-json
```

For detailed option fields, use the pipeline-configuration inspection helper if present in the generated skill tree.
