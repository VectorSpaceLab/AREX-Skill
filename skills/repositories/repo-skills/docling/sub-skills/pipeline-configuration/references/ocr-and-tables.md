# OCR and Table Configuration

Use this reference when a PDF conversion needs better scanned-text recovery, table structure output, or hardware-aware OCR choices.

## OCR Toggle

For digital PDFs with reliable embedded text, disable OCR to reduce cost and avoid OCR noise:

```python
pipeline_options = PdfPipelineOptions()
pipeline_options.do_ocr = False
```

For scanned PDFs or bitmap-heavy pages, enable OCR and choose an engine deliberately:

```python
pipeline_options = PdfPipelineOptions()
pipeline_options.do_ocr = True
pipeline_options.ocr_options.lang = ["en"]
pipeline_options.ocr_options.force_full_page_ocr = True
```

`force_full_page_ocr=True` is useful when embedded text is missing or unreliable across full pages. `bitmap_area_threshold` controls how much bitmap coverage triggers OCR processing.

## OCR Engines

Common OCR option classes:

- `EasyOcrOptions`: PyTorch/EasyOCR engine; language codes such as `en`, `fr`, `de`; `use_gpu` can force or disable GPU when supported.
- `RapidOcrOptions`: RapidOCR engine; `backend` can be `onnxruntime`, `openvino`, `paddle`, or `torch`; current common language defaults emphasize Chinese/English.
- `TesseractCliOcrOptions`: uses the `tesseract` command-line binary; language codes such as `eng`, `fra`, `deu`.
- `TesseractOcrOptions`: uses Python Tesseract bindings; requires the binding and system Tesseract data.
- `OcrMacOptions`: macOS Vision framework; locale-like language codes such as `en-US`.
- `KserveV2OcrOptions`: remote OCR through a KServe v2-compatible endpoint; requires `enable_remote_services=True`.

Examples:

```python
from docling.datamodel.pipeline_options import EasyOcrOptions, RapidOcrOptions

pipeline_options.ocr_options = EasyOcrOptions(lang=["en", "de"], use_gpu=False)
pipeline_options.ocr_options = RapidOcrOptions(lang=["english"], backend="torch")
```

For Tesseract CLI:

```python
from docling.datamodel.pipeline_options import TesseractCliOcrOptions

pipeline_options.ocr_options = TesseractCliOcrOptions(
    lang=["eng"],
    tesseract_cmd="tesseract",
)
```

## Table Structure Toggle

Enable table structure extraction when tables matter:

```python
from docling.datamodel.pipeline_options import TableFormerMode, TableStructureOptions

pipeline_options.do_table_structure = True
pipeline_options.table_structure_options = TableStructureOptions(
    do_cell_matching=True,
    mode=TableFormerMode.ACCURATE,
)
```

Disable it when speed matters and tables are irrelevant:

```python
pipeline_options.do_table_structure = False
```

## Cell Matching Strategy

`do_cell_matching=True` maps table structure predictions back to PDF text cells. This is usually the best default for digital PDFs because it preserves backend text.

`do_cell_matching=False` lets the table model's predicted text cells drive output. Use it when a PDF has visually separated columns but extracted PDF cells merge multiple columns into one cell.

Merged-column recovery pattern:

```python
pipeline_options.do_table_structure = True
pipeline_options.table_structure_options.do_cell_matching = False
pipeline_options.table_structure_options.mode = TableFormerMode.ACCURATE
```

If the user reports merged columns, repeated header problems, or cells assigned to the wrong column, compare output with both `do_cell_matching=True` and `False`. Keep `TableFormerMode.ACCURATE` for difficult tables unless latency is the primary requirement.

## Speed vs Accuracy

`TableFormerMode.ACCURATE` prioritizes table quality and is preferred for production or complex tables. `TableFormerMode.FAST` trades accuracy for speed and can be acceptable for simple high-volume documents.

```python
pipeline_options.table_structure_options.mode = TableFormerMode.FAST
```

## OCR and GPU Notes

- `AcceleratorOptions(device=AcceleratorDevice.CUDA)` can accelerate Docling model stages when compatible packages and hardware are present.
- OCR GPU behavior depends on the OCR engine; RapidOCR with `backend="torch"` is a known GPU-oriented choice in current public guidance.
- EasyOCR can use GPU but may not honor specific `cuda:N` selection in all setups.
- Tesseract CLI and Tesseract bindings depend on system binaries/language data, not GPU acceleration.

## Practical Debug Matrix

- Digital PDF, bad OCR artifacts: set `do_ocr=False`.
- Scanned PDF, missing text: set `do_ocr=True`, consider `force_full_page_ocr=True`, verify OCR extras/binaries.
- Wrong language output: set explicit engine-specific `lang` values; do not mix EasyOCR two-letter codes with Tesseract three-letter codes.
- Merged table columns: set `do_cell_matching=False` and `TableFormerMode.ACCURATE`.
- Slow conversion: disable unused OCR/table stages, reduce page range, select CPU/GPU explicitly, and tune thread count.
