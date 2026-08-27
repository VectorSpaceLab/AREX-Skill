---
name: pipeline-configuration
description: "Configure Docling's standard PDF pipeline options, OCR engines,
  table structure recovery, accelerators, model artifacts, remote-service gates,
  and option validation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Pipeline Configuration

Use this sub-skill when a task needs Docling PDF pipeline tuning rather than a simple conversion call.

## Route Here For

- Building `PdfPipelineOptions` or `ThreadedPdfPipelineOptions` for `InputFormat.PDF`.
- Enabling/disabling OCR, choosing OCR engines, setting OCR language lists, or forcing full-page OCR.
- Tuning table structure extraction, especially `do_cell_matching` and `TableFormerMode`.
- Selecting `AcceleratorOptions` device/thread settings for CPU, CUDA, MPS, or XPU.
- Setting `artifacts_path`, `DOCLING_ARTIFACTS_PATH`, or `docling-tools models download` for prefetched model caches.
- Diagnosing pipeline option validation, wrong option object placement, or `OperationNotAllowed` from remote-service components.

## Route Elsewhere

- Basic document conversion, export formats, `DocumentConverter.convert`, or `convert_string`: use the conversion sub-skill.
- CLI flag syntax and supported input/output formats: use the cli-and-formats sub-skill.
- VLM, ASR, picture enrichment, code/formula, chart extraction, or other heavy enrichment workflows: use the advanced-pipelines sub-skill.

## Core Pattern

```python
from docling.datamodel.accelerator_options import AcceleratorDevice, AcceleratorOptions
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions, TableFormerMode
from docling.document_converter import DocumentConverter, PdfFormatOption

pipeline_options = PdfPipelineOptions()
pipeline_options.do_ocr = True
pipeline_options.ocr_options.lang = ["en"]
pipeline_options.do_table_structure = True
pipeline_options.table_structure_options.do_cell_matching = False
pipeline_options.table_structure_options.mode = TableFormerMode.ACCURATE
pipeline_options.accelerator_options = AcceleratorOptions(
    num_threads=4,
    device=AcceleratorDevice.AUTO,
)

converter = DocumentConverter(
    format_options={
        InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
    }
)
result = converter.convert("input.pdf", max_num_pages=100, max_file_size=20 * 1024 * 1024)
```

## References

- `references/options-reference.md` for field names, defaults, and validated snippets.
- `references/ocr-and-tables.md` for OCR engines and table recovery choices.
- `references/troubleshooting.md` for common pipeline failures and fixes.
- `scripts/inspect_pipeline_options.py` to print installed option fields/defaults without opening source files.
