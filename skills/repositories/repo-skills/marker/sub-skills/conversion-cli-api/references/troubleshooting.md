# Troubleshooting conversion

## Install or import failure

Symptoms:

- `marker_single: command not found`.
- `ModuleNotFoundError: No module named 'marker'`.
- Python can import `marker` but console scripts are unavailable.

Fixes:

- Install the package with `pip install marker-pdf`.
- For DOCX, PPTX, XLSX, HTML, or EPUB inputs, install `pip install "marker-pdf[full]"`.
- Confirm the active Python environment owns the console scripts: `python -m pip show marker-pdf` and `python -c "import marker; print(marker.__name__)"`.
- Use `python scripts/marker_cli_smoke.py` from this sub-skill to check installed CLI help without running conversion.

## Model download or cache surprise

Symptoms:

- First conversion stalls while fetching model weights.
- Offline machines fail at model initialization.
- CI hangs when a helper accidentally calls `create_model_dict()`.

Fixes:

- Treat real conversion as a model-loading operation, not a smoke test.
- Keep `create_model_dict()` inside guarded runtime code.
- Pre-warm the user’s model cache in an approved environment before large jobs.
- Use help-only checks for validation when conversion is not explicitly requested.

## Torch device, VRAM, or worker failure

Symptoms:

- CUDA out-of-memory.
- MPS fallback warnings or unsupported operations.
- CPU conversion is slow or oversubscribed.
- Batch conversion fails after spawning many workers.

Fixes:

- Force a backend only when needed: `TORCH_DEVICE=cuda`, `TORCH_DEVICE=mps`, or `TORCH_DEVICE=cpu`.
- Lower `marker --workers`; start with `1` or `2` on constrained GPUs.
- Use `--disable_multiprocessing` for debugging or single-process runs.
- Split long PDFs or use folder chunking rather than excessive workers.
- Remember that Marker can use several GB of VRAM per worker.

## Invalid output format

Symptoms:

- CLI rejects `--output_format pdf` or another unsupported value.
- Python `ConfigParser.get_renderer()` raises `ValueError("Invalid output format")`.

Fixes:

- Use one of `markdown`, `json`, `html`, or `chunks`.
- For OCR-only JSON, select `OCRConverter`; do not invent an `ocr` output format.

## Invalid page range

Symptoms:

- Conversion fails while parsing `--page_range`.
- Output has unexpected pages.

Fixes:

- Use zero-based page indices.
- Use comma-separated numbers and inclusive ranges, for example `0,5-10,20`.
- Quote the value in shells: `--page_range "0,5-10"`.
- Test a tiny range before launching a large batch.

## Missing optional document dependencies

Symptoms:

- PDF conversion works but DOCX, PPTX, XLSX, HTML, or EPUB fails.
- Provider selection or import errors mention optional libraries.

Fixes:

- Install the full extra: `pip install "marker-pdf[full]"`.
- Re-run conversion in the same environment that received the extra.
- If the file is actually a PDF or image, verify the extension and file type are correct.

## Wrong converter class path

Symptoms:

- `Error loading converter` in logs.
- `ModuleNotFoundError` or `AttributeError` from `--converter_cls`.
- User typed a class name like `TableConverter` without its full module path.

Fixes:

- Use full import paths:
  - `marker.converters.pdf.PdfConverter`
  - `marker.converters.table.TableConverter`
  - `marker.converters.ocr.OCRConverter`
- Validate before conversion: `python -c "from marker.converters.table import TableConverter; print(TableConverter)"`.
- For custom converters, route to `../configuration-extension/`.

Correct table-only command:

```bash
marker_single report.pdf \
  --converter_cls marker.converters.table.TableConverter \
  --force_layout_block Table \
  --output_format json \
  --output_dir table_json
```

## Bad input path or folder

Symptoms:

- Single-file CLI cannot find the input.
- Folder CLI converts zero files.
- Batch conversion ignores nested documents.

Fixes:

- `marker_single` expects one file path.
- `marker` reads files directly inside `IN_FOLDER`; it does not recursively crawl nested directories.
- Validate paths before starting expensive conversion.
- For folder jobs, use `--max_files 1` first to validate behavior.

## Output directory assumptions

Symptoms:

- User expects files directly in `--output_dir` but sees basename subfolders.
- `save_output` fails in Python because the target directory does not exist.
- `--skip_existing` does not skip because outputs are in a different folder.

Fixes:

- CLI output goes under `output_dir/{input_basename}/`.
- `save_output(rendered, output_dir, fname_base)` writes directly into the provided `output_dir`; create it first.
- `--skip_existing` checks for `.md`, `.html`, or `.json` in the CLI-computed basename folder.

## Chunk conversion GPU topology

Symptoms:

- `marker_chunk_convert` underuses GPUs or exhausts memory.
- Environment variables do not match available devices.
- A single machine has mixed GPU sizes.

Fixes:

- Set `NUM_DEVICES` to available GPU count and `NUM_WORKERS` conservatively.
- Prefer explicit `marker --chunk_idx N --num_chunks M --workers K` commands for custom schedulers.
- Keep chunk indexes zero-based and below `num_chunks`.
- Avoid chunk conversion on CPU-only machines unless the caller has a specific reason.

## Debug artifacts

Symptoms:

- Debug run creates many images or JSON files.
- User cannot tell where debug files went.

Fixes:

- `--debug` enables debug PDF images, layout images, debug JSON, and a debug data folder based on the configured output directory.
- Use a dedicated `--output_dir` for debug runs.
- Remove debug artifacts before sharing outputs if they contain document content.
