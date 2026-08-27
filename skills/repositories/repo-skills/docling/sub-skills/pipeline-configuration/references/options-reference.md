# Pipeline Options Reference

This reference summarizes stable Docling pipeline configuration patterns for the standard PDF pipeline. Validate exact fields against the installed package with `scripts/inspect_pipeline_options.py` when supporting multiple Docling versions.

## Correct Object Nesting

`DocumentConverter(format_options=...)` expects `InputFormat` keys and format option values. For PDF pipeline tuning, put the pipeline object inside `PdfFormatOption`, not directly under `format_options`.

```python
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption

pipeline_options = PdfPipelineOptions(do_ocr=False, do_table_structure=True)
converter = DocumentConverter(
    format_options={
        InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
    }
)
```

Avoid this shape:

```python
# Wrong: format_options values are format options, not bare pipeline options.
DocumentConverter(format_options={InputFormat.PDF: PdfPipelineOptions()})
```

## Standard PDF Pipeline Fields

Common `PdfPipelineOptions` fields used by agents:

- `do_ocr`: enable OCR for scanned/bitmap text. Default is enabled in current standard PDF usage.
- `ocr_options`: an OCR option object such as `EasyOcrOptions`, `RapidOcrOptions`, `TesseractCliOcrOptions`, `TesseractOcrOptions`, `OcrMacOptions`, or automatic OCR options when available.
- `do_table_structure`: enable table structure recognition.
- `table_structure_options`: `TableStructureOptions` or compatible table option object.
- `accelerator_options`: `AcceleratorOptions(num_threads=..., device=...)`.
- `artifacts_path`: local directory containing prefetched Docling model artifacts.
- `enable_remote_services`: explicit opt-in gate for pipeline components that send data to remote services.
- `document_timeout`: per-document timeout used by the PDF pipeline; tests exercise it returning partial success.
- Additional enrichment toggles and model options may exist in the installed version; route heavy enrichment setup to advanced-pipelines.

Use constructor keywords for simple values and assignment for nested tuning:

```python
from docling.datamodel.pipeline_options import PdfPipelineOptions, TableFormerMode

pipeline_options = PdfPipelineOptions(
    do_ocr=True,
    do_table_structure=True,
    document_timeout=300,
)
pipeline_options.ocr_options.lang = ["en", "de"]
pipeline_options.table_structure_options.mode = TableFormerMode.ACCURATE
```

## Threaded Pipeline Options

`ThreadedPdfPipelineOptions` extends PDF options with stage batch sizes useful for GPU/throughput tuning:

```python
from docling.datamodel.pipeline_options import ThreadedPdfPipelineOptions

pipeline_options = ThreadedPdfPipelineOptions(
    ocr_batch_size=64,
    layout_batch_size=64,
    table_batch_size=4,
)
```

Use this only when the installed Docling version exposes the threaded option class and the target workload benefits from batching.

## Accelerator Options

`AcceleratorOptions` supports local inference device and CPU-thread selection:

```python
from docling.datamodel.accelerator_options import AcceleratorDevice, AcceleratorOptions

pipeline_options.accelerator_options = AcceleratorOptions(
    num_threads=8,
    device=AcceleratorDevice.CPU,  # AUTO, CPU, CUDA, MPS, XPU are common choices
)
```

Accepted device values include `auto`, `cpu`, `cuda`, `mps`, `xpu`, and CUDA ordinals such as `cuda:1` where supported. Some OCR engines may ignore specific GPU ordinals.

Environment controls:

```sh
export DOCLING_NUM_THREADS=8
export DOCLING_DEVICE=cpu
# OMP_NUM_THREADS can supply num_threads when DOCLING_NUM_THREADS is unset.
```

## Model Artifacts and Offline Use

Docling downloads models on first use unless models are prefetched. For air-gapped use, prefetch models on a connected machine, copy the model directory, then point Docling at it:

```sh
docling-tools models download
export DOCLING_ARTIFACTS_PATH=/opt/docling-models
```

Programmatic configuration:

```python
from docling.datamodel.pipeline_options import PdfPipelineOptions

pipeline_options = PdfPipelineOptions(artifacts_path="/opt/docling-models")
```

For public skill usage, tell agents to use a user-provided path such as `/opt/docling-models` or an environment variable; do not bake local checkout paths into generated code.

## Conversion Resource Limits

`DocumentConverter.convert` accepts limits independently from pipeline options:

```python
result = converter.convert(
    "input.pdf",
    max_num_pages=100,
    max_file_size=20 * 1024 * 1024,
    page_range=(1, 25),
    raises_on_error=False,
)
```

Use `max_num_pages` and `max_file_size` for guardrails before model work starts. Use `document_timeout` inside `PdfPipelineOptions` for pipeline runtime limits.

## Remote-Service Gate

Docling local pipelines avoid sending user data to remote services by default. If a pipeline option includes a remote service component, explicitly opt in:

```python
pipeline_options = PdfPipelineOptions(enable_remote_services=True)
```

If this is omitted for a remote component, Docling can raise `OperationNotAllowed`. This gate is about sending document data to services; model-weight downloads are controlled separately by the model cache/artifacts setup.

## Validation Checklist

- Use `InputFormat.PDF: PdfFormatOption(pipeline_options=...)` for PDF conversion.
- Keep `pipeline_options` classes from `docling.datamodel.pipeline_options`, not backend options or CLI option objects.
- Prefer enum constants such as `TableFormerMode.ACCURATE` and `AcceleratorDevice.CPU` over unverified strings.
- Run `python scripts/inspect_pipeline_options.py --classes PdfPipelineOptions TableStructureOptions AcceleratorOptions` to confirm installed field names/defaults.
- For multi-document services, instantiate one converter per option profile so Docling can reuse initialized pipelines.
