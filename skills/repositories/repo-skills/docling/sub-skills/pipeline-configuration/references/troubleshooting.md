# Pipeline Troubleshooting

This guide focuses on standard PDF pipeline configuration failures and ambiguous output quality problems.

## Wrong Option Object Under `format_options`

Symptom: converter construction or conversion fails with validation/type errors, or PDF options appear ignored.

Fix: wrap `PdfPipelineOptions` in `PdfFormatOption`:

```python
converter = DocumentConverter(
    format_options={
        InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
    }
)
```

Do not pass `PdfPipelineOptions()` as the direct value for `InputFormat.PDF`.

## Missing OCR Extras or Binaries

Symptoms:

- Import errors for OCR engines.
- Runtime errors invoking `tesseract`.
- Missing language data.
- Model downloads attempted on first OCR use.

Fixes:

- Install Docling with the optional extras needed for the chosen OCR engine when applicable.
- For Tesseract CLI, install the system `tesseract` binary and requested language data.
- For Tesseract bindings, install compatible Python bindings and Tesseract libraries.
- For EasyOCR/RapidOCR, verify model cache access or prefetch models for offline machines.
- Match language code formats to the engine: EasyOCR commonly uses `en`; Tesseract commonly uses `eng`; macOS Vision uses locale-like codes such as `en-US`.

## `OperationNotAllowed` for Remote Services

Symptom: pipeline fails when a remote API-backed OCR, picture description, or other remote stage is configured.

Fix: explicitly opt in before processing user data remotely:

```python
pipeline_options = PdfPipelineOptions(enable_remote_services=True)
```

Also verify the remote service URL, API key/header configuration, and network access. This gate is independent of model-weight downloads.

## Model Cache and `artifacts_path`

Symptoms:

- First conversion stalls while downloading models.
- Air-gapped conversion fails while trying to reach model hosts.
- Different machines produce inconsistent cache behavior.

Fix:

```sh
docling-tools models download
export DOCLING_ARTIFACTS_PATH=/opt/docling-models
```

Or set the path in code:

```python
pipeline_options = PdfPipelineOptions(artifacts_path="/opt/docling-models")
```

For air-gapped deployments, prefetch on a connected machine, copy the complete model artifact directory, and point `artifacts_path` or `DOCLING_ARTIFACTS_PATH` at the copied directory.

## Table Cell Matching Problems

Symptoms:

- Visually separate table columns are merged in output.
- Text appears in the wrong table cell.
- Complex spans are flattened incorrectly.

Fix sequence:

1. Ensure `do_table_structure=True`.
2. Use `TableFormerMode.ACCURATE`.
3. Compare `do_cell_matching=True` versus `False`.
4. Keep the setting that best matches visual cells for the user's document family.

```python
pipeline_options.table_structure_options.do_cell_matching = False
pipeline_options.table_structure_options.mode = TableFormerMode.ACCURATE
```

## CPU/GPU Thread and Device Choices

Symptoms:

- Conversion is slower than expected.
- GPU is not used.
- Unsupported-device errors occur.
- CPU is oversubscribed in a service.

Fixes:

```python
from docling.datamodel.accelerator_options import AcceleratorDevice, AcceleratorOptions

pipeline_options.accelerator_options = AcceleratorOptions(
    num_threads=4,
    device=AcceleratorDevice.CPU,
)
```

Use `AcceleratorDevice.AUTO` for portability, `CPU` for deterministic low-risk deployments, `CUDA` for NVIDIA GPU setups with compatible ML packages, `MPS` for Apple Silicon, and `XPU` for compatible Intel GPU setups. Environment variables `DOCLING_NUM_THREADS`, `OMP_NUM_THREADS`, and `DOCLING_DEVICE` can override defaults in service deployments.

## Option Validation Failures

Symptoms:

- Pydantic reports unknown fields or invalid enum values.
- Code copied from an older/newer Docling version fails.

Fixes:

- Run `python scripts/inspect_pipeline_options.py --classes PdfPipelineOptions TableStructureOptions RapidOcrOptions AcceleratorOptions`.
- Prefer installed enum constants instead of raw strings.
- Remove fields not shown by the installed option model.
- Avoid broad dynamic attribute probing; use explicit installed model fields.

## Safe Minimal Fallback

When a complex configuration fails, reduce to a minimal known-good PDF setup and re-add options one group at a time:

```python
pipeline_options = PdfPipelineOptions()
pipeline_options.do_ocr = False
pipeline_options.do_table_structure = False
converter = DocumentConverter(
    format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)}
)
```

Then add OCR, table structure, accelerator, artifact path, and remote-service options separately.
