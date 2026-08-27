# CLI reference

Marker exposes conversion through installed console scripts. Prefer these script names over direct Python files or checkout-local launchers.

## Install prerequisites

- Base PDF/image conversion: `pip install marker-pdf`.
- Non-PDF documents such as DOCX, PPTX, XLSX, HTML, or EPUB: `pip install "marker-pdf[full]"`.
- Apps and servers need additional packages and belong in `../server-deployment/`.
- LLM-enhanced conversion needs service credentials/configuration and belongs in `../llm-extraction-services/`.

## Single-file conversion

Use `marker_single FPATH` for one document. Marker supports PDFs and images in the base install; with the `full` extra it can also handle document types such as DOCX, PPTX, XLSX, HTML, and EPUB.

```bash
marker_single paper.pdf --output_format markdown --output_dir converted
marker_single paper.pdf --output_format json --page_range "0,5-10" --disable_image_extraction --output_dir converted
marker_single scan.png --force_ocr --output_format html --output_dir converted
```

Common options verified from the installed CLI:

| Option | Use |
| --- | --- |
| `--output_format markdown|json|html|chunks` | Choose saved content format. Invalid values are rejected by Click before conversion. |
| `--output_dir PATH` | Directory where Marker creates one output subfolder per input basename. |
| `--page_range TEXT` | Zero-based pages and ranges such as `0,5-10,20`. The parser turns this into a page list. |
| `--disable_image_extraction` | Save text output without extracted image files or markdown image links. |
| `--disable_multiprocessing` | Force single-worker PDF text extraction via `pdftext_workers=1`. Useful for debugging or constrained systems. |
| `--config_json PATH` | Merge additional configuration from JSON. Useful for flags not convenient on the CLI. |
| `--converter_cls CLASS_PATH` | Use another converter class such as `marker.converters.table.TableConverter` or `marker.converters.ocr.OCRConverter`. |
| `--processors CLASS_PATHS` | Override processor classes. This is an extension topic; route nontrivial changes to `../configuration-extension/`. |
| `--debug` | Save debug images and JSON diagnostics under the configured output location. |

Conversion flags available through generated config options include `--force_ocr`, `--strip_existing_ocr`, and `--redo_inline_math`. Use `--force_ocr` when text is garbled or scanned. `--redo_inline_math` is mainly relevant with LLM enhancement, so route quality tuning around LLMs to `../llm-extraction-services/`.

## Folder conversion

Use `marker IN_FOLDER` to convert files directly inside a folder.

```bash
marker incoming_docs --output_format markdown --output_dir converted
marker incoming_docs --output_format json --page_range "0,5-10" --disable_image_extraction --skip_existing --workers 2 --output_dir converted
marker incoming_docs --max_files 20 --debug_print --max_tasks_per_worker 5 --output_dir converted
```

Batch-specific options:

| Option | Use |
| --- | --- |
| `--workers INTEGER` | Override automatic worker count. Lower this on CPU-only systems or when VRAM is tight. |
| `--skip_existing` | Skip a file if an `.md`, `.html`, or `.json` output already exists for that basename. |
| `--max_files INTEGER` | Convert only the first N files selected from the input folder. |
| `--chunk_idx INTEGER` and `--num_chunks INTEGER` | Split a folder across multiple independent runs. `chunk_idx` is zero-based. |
| `--max_tasks_per_worker INTEGER` | Recycle worker processes after N tasks. Useful for long batches or memory growth. |
| `--debug_print` | Log per-file progress in the batch worker. |

The batch CLI sets multiprocessing start method to `spawn`, disables nested multiprocessing internally, and uses a GPU manager based on chunk index. If `spawn` was already set in the current process, rerun from a fresh shell process.

## Chunked multi-GPU folder conversion

Use `marker_chunk_convert IN_FOLDER OUT_FOLDER` when you intentionally want the packaged shell orchestration for multiple GPUs.

```bash
NUM_DEVICES=4 NUM_WORKERS=15 marker_chunk_convert pdf_in md_out
```

Caveats:

- `NUM_DEVICES` should match available GPUs and is intended for 2 or more devices.
- `NUM_WORKERS` controls parallel processes per GPU; too high can exhaust VRAM or CPU RAM.
- The command delegates to Marker’s installed chunk shell script. Do not adapt checkout-local shell paths into a runtime skill.
- For custom scheduling or heterogeneous machines, prefer explicit `marker IN_FOLDER --chunk_idx N --num_chunks M --workers K` commands launched by the caller’s job runner.

## Table-only conversion

Use `TableConverter` when the user wants table/form/table-of-contents blocks instead of a full document conversion.

```bash
marker_single report.pdf \
  --converter_cls marker.converters.table.TableConverter \
  --output_format markdown \
  --page_range "5" \
  --output_dir table_output

marker_single report.pdf \
  --converter_cls marker.converters.table.TableConverter \
  --force_layout_block Table \
  --output_format json \
  --output_dir table_json
```

`--force_layout_block Table` skips layout detection and treats pages as tables. Use `--output_format json` when cell bounding boxes are needed. LLM-assisted table cleanup is out of scope here; route `--use_llm` to `../llm-extraction-services/`.

## OCR-only conversion

Use `OCRConverter` when the user wants OCR JSON rather than a full Markdown/HTML document rendering.

```bash
marker_single scan.pdf \
  --converter_cls marker.converters.ocr.OCRConverter \
  --page_range "0" \
  --output_dir ocr_output

marker_single scan.pdf \
  --converter_cls marker.converters.ocr.OCRConverter \
  --keep_chars \
  --output_dir ocr_chars
```

`OCRConverter` forces OCR internally and uses Marker’s OCR JSON renderer. `--keep_chars` preserves character-level boxes when available.

## Device and throughput controls

- Marker auto-detects the torch device; set `TORCH_DEVICE=cuda`, `TORCH_DEVICE=mps`, or `TORCH_DEVICE=cpu` when the user needs an explicit backend.
- GPU and MPS runs can trigger model downloads into the user’s cache the first time conversion runs.
- Lower `--workers`, use `--disable_multiprocessing`, or split files when VRAM/RAM is limited.
- README throughput notes estimate several GB of VRAM per worker; do not maximize workers blindly.

## Hard-case command synthesis

JSON for pages 0 and 5-10 from a folder, suppress images, skip existing outputs, and avoid too many GPU workers:

```bash
TORCH_DEVICE=cuda marker input_folder \
  --output_format json \
  --page_range "0,5-10" \
  --disable_image_extraction \
  --skip_existing \
  --workers 2 \
  --max_tasks_per_worker 5 \
  --output_dir converted_json
```

Corrected table-only command after a converter class import error:

```bash
marker_single report.pdf \
  --converter_cls marker.converters.table.TableConverter \
  --force_layout_block Table \
  --output_format json \
  --output_dir table_json
```

Validate class paths with `python -c "from marker.converters.table import TableConverter; print(TableConverter)"` before launching a large conversion.
