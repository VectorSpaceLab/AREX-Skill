# Bundled Script Adaptations

This sub-skill bundles safe helpers for common command-line OCR tasks. They are self-contained runtime scripts and do not require a source checkout.

## Why use the helpers instead of `doctr-cli`?

Use `doctr-cli` when you want the exact installed package command and JSON-only output with trained weights. Use these helpers when you need one or more of the following:

- explicit `--pretrained` / `--no-pretrained` control;
- safe offline smoke checks that do not intentionally download model weights;
- `txt` or `xml` output in addition to JSON;
- batch processing over a directory;
- output parent directory creation and clearer user-facing errors;
- a machine-readable manifest/summary for shell automation.

## `scripts/doctr_quick_ocr.py`

Single-document OCR helper adapted from the interactive single-file analysis pattern. It removes blocking visualization and writes files instead.

```bash
python scripts/doctr_quick_ocr.py INPUT.pdf --output result.json --format json
```

Important options:

| Option | Default | Meaning |
|---|---:|---|
| `input_path` | required | One PDF or supported image. |
| `-o`, `--output` | `doctr_ocr.json` | Output file path. Parent directories are created. Existing files require `--overwrite`. |
| `-f`, `--format {json,txt,xml}` | `json` | Result format: exported document JSON, rendered text, or hOCR XML. |
| `--det-arch`, `--detection` | `db_resnet50` | Detection architecture. |
| `--reco-arch`, `--recognition` | `crnn_vgg16_bn` | Recognition architecture. |
| `--pretrained` / `--no-pretrained` | `False` | `--no-pretrained` avoids intentional model-weight and pretrained-backbone downloads; `--pretrained` loads trained OCR weights. |
| `--assume-straight-pages` / `--no-assume-straight-pages` | `True` | Straight-text assumption passed to the OCR predictor. |
| `--straighten-pages` | `False` | Try page straightening before recognition. |
| `--preserve-aspect-ratio` / `--no-preserve-aspect-ratio` | `True` | Preserve page aspect ratio during detection resizing. |
| `--symmetric-pad` | `False` | Use symmetric padding. |
| `--det-bs` | `2` | Detection batch size. |
| `--reco-bs` | `128` | Recognition batch size. |
| `--detect-orientation` | `False` | Add page orientation prediction. |
| `--detect-language` | `False` | Add language prediction. |
| `--overwrite` | `False` | Replace an existing output file. |

Examples:

```bash
# Offline/import smoke: random weights, JSON structure only, no intentional weight download.
python scripts/doctr_quick_ocr.py sample.png --no-pretrained --output smoke.json --overwrite

# Real OCR when trained weights may be loaded or downloaded.
python scripts/doctr_quick_ocr.py invoice.pdf --pretrained --format txt --output invoice.txt

# hOCR XML. Multi-page documents are written as page-suffixed XML files.
python scripts/doctr_quick_ocr.py report.pdf --pretrained --format xml --output report.xml
```

At completion the helper prints a JSON summary to stdout with `ok`, `input`, `outputs`, `format`, and `pretrained` fields.

## `scripts/doctr_batch_ocr.py`

Batch OCR helper adapted from the directory/file detection pattern. It preserves the useful `txt`/`json`/`xml` formats, but replaces the hard-coded `output/` directory with an explicit `--output-dir` and writes a manifest.

```bash
python scripts/doctr_batch_ocr.py INPUT_OR_DIR --output-dir ocr-output --format txt
```

Supported input suffixes are `.jpeg`, `.jpg`, `.png`, `.tif`, `.tiff`, `.bmp`, and `.pdf`.

Important options:

| Option | Default | Meaning |
|---|---:|---|
| `input_path` | required | One supported file or a directory containing supported files. |
| `--output-dir` | `doctr_ocr_output` | Destination directory; created if needed. |
| `-f`, `--format {txt,json,xml}` | `txt` | Write rendered text, exported JSON, or hOCR XML. |
| `--detection` | `fast_base` | Detection model factory name. |
| `--bin-thresh` | `0.3` | Binarization threshold passed to compatible detection factories. |
| `--box-thresh` | `0.1` | Box threshold passed to compatible detection factories. |
| `--recognition` | `crnn_vgg16_bn` | Recognition architecture. |
| `--pretrained` / `--no-pretrained` | `False` | `--no-pretrained` avoids intentional downloads; `--pretrained` loads trained detection/recognition weights. |
| `--recursive` | `False` | Recurse into subdirectories. Output basenames include the relative path to avoid collisions. |
| `--max-files N` | `0` | Limit processed files; `0` means no limit. Useful for safe dry runs over large directories. |
| `--overwrite` | `False` | Replace existing result files. |
| `--stop-on-error` | `False` | Stop at the first file error instead of recording failures and continuing. |

Examples:

```bash
# Safe parser/import smoke over the first two files in a folder.
python scripts/doctr_batch_ocr.py scans --no-pretrained --max-files 2 --output-dir smoke-out

# Real OCR over a directory with JSON exports.
python scripts/doctr_batch_ocr.py scans --pretrained --format json --output-dir json-out

# XML output over nested folders.
python scripts/doctr_batch_ocr.py scans --pretrained --recursive --format xml --output-dir xml-out
```

The batch helper writes `manifest.json` in `--output-dir`. Each manifest item records `input`, `status`, `outputs`, and an `error` field when processing fails. The process exits `0` only when all selected files succeeded.

## `scripts/doctr_cli_env.py`

Safe diagnostic helper adapted from the environment collection pattern. It avoids shell commands by default and reports package/import/backend facts that are relevant to CLI troubleshooting.

```bash
python scripts/doctr_cli_env.py --json
```

Use `--probe-gpu-commands` only when it is acceptable to execute short local commands such as `nvidia-smi -L` and `nvcc --version`; each command is bounded by a timeout.

## Pretrained and network/cache policy

- `--no-pretrained` is the default for bundled helpers and passes `pretrained=False` plus `pretrained_backbone=False` where the predictor supports it. This is intended for safe checks, not accurate OCR.
- `--pretrained` passes `pretrained=True` and allows trained model weights to be loaded from cache or downloaded by the backend if missing.
- If `--pretrained` fails because the runtime is offline or the cache is incomplete, re-run with `--no-pretrained` to separate package/import/input issues from weight acquisition issues.

## Output format semantics

- `json`: serializes `result.export()` with UTF-8 and indentation.
- `txt`: serializes `result.render()`.
- `xml`: serializes every hOCR XML page returned by `result.export_as_xml()`. Multi-page outputs receive `_page1`, `_page2`, ... suffixes.
