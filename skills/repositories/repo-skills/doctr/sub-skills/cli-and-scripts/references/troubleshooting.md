# CLI and Script Troubleshooting

Use this page when `doctr-cli` or the bundled helpers fail before, during, or after OCR inference.

## Command not found: `doctr-cli`

Symptoms:

```text
doctr-cli: command not found
```

Checks:

1. Confirm the active Python environment has the package installed:
   ```bash
   python -c "import doctr; print(doctr.__version__)"
   ```
2. Confirm the package entry point is visible:
   ```bash
   python -m pip show python-doctr
   python -c "import shutil; print(shutil.which('doctr-cli'))"
   ```
3. If the package imports but the entry point is missing, reinstall the package in the active environment or run the equivalent bundled helper with `python scripts/doctr_quick_ocr.py ...`.

## Import errors

Typical messages include missing packages such as image/PDF/model dependencies, backend import failures, or OpenCV/Pillow errors.

Checks:

```bash
python scripts/doctr_cli_env.py --json
python -c "from doctr.io import DocumentFile; from doctr.models import ocr_predictor; print('ok')"
```

Actions:

- Install the package into the same Python environment that runs the command.
- Make sure the runtime satisfies the package's Python version requirement.
- If optional visualization, HTML, contrib, or deployment features are involved, install the corresponding package extra; plain OCR CLI does not require service/demo extras.
- If imports fail only after GPU-related libraries are loaded, verify that the installed PyTorch build matches the machine backend.

## Missing, unsupported, or corrupt input

`doctr-cli` exits `1` for missing files or unreadable image/PDF content. The batch helper also rejects unsupported suffixes before running inference.

Supported helper suffixes:

```text
.jpeg .jpg .png .tif .tiff .bmp .pdf
```

Actions:

- Use an existing local file, not a URL, for CLI/helper OCR.
- Convert unsupported formats before running OCR.
- For a PDF that fails to load, test a single-page or freshly exported PDF to separate corruption from OCR model issues.
- For images, ensure the file is a valid image and not a text/HTML placeholder saved with an image suffix.

## Output write failures

Common causes:

- `doctr-cli` does not create parent directories.
- The output path points to a directory instead of a file.
- A helper output already exists and `--overwrite` was not supplied.
- The destination filesystem is not writable.

Actions:

```bash
# CLI: create parent first.
mkdir -p out
doctr-cli --input_path scan.pdf --output out/scan.json

# Helper: allow replacement explicitly.
python scripts/doctr_quick_ocr.py scan.pdf --output out/scan.json --overwrite
```

For XML, multi-page helper outputs use page-suffixed files. Check the JSON summary or batch `manifest.json` for the exact written paths.

## Pretrained weight downloads or offline runtime

`doctr-cli` always uses trained weights. The bundled helpers default to no trained weights.

Symptoms:

- connection timeout or SSL/certificate error during model construction;
- cache miss in an offline environment;
- slow first run before any OCR starts.

Actions:

- For a safe import/parser/input smoke check, run a helper with `--no-pretrained`.
- For accurate OCR, use `--pretrained` only when the runtime may access cached or downloadable weights.
- If `--pretrained` fails but `--no-pretrained` succeeds, the package and input path are likely valid; resolve model cache/network access separately.

## Model architecture errors

Symptoms include `KeyError`, `AttributeError`, or factory errors for detection/recognition names.

Actions:

- Use the CLI defaults first: detection `db_resnet50`, recognition `crnn_vgg16_bn`.
- For the batch helper's detection factory, use a detection architecture name exposed by the installed `doctr.models.detection` module, such as `fast_base` when available.
- Do not pass recognition names as detection names or vice versa.
- If a custom model object is required, switch to the Python API workflow rather than the CLI helpers.

## Memory, latency, and backend failures

Actions:

- Reduce `--det_bs` and `--reco_bs` for `doctr-cli` or `doctr_quick_ocr.py`.
- Start with one small page before running a large PDF or directory.
- Avoid `--detect_orientation`, `--detect_language`, and `--straighten_pages` unless needed; they add model work.
- On GPU, verify the installed backend and driver with `python scripts/doctr_cli_env.py --json --probe-gpu-commands`.
- On CPU-only machines, expect slower inference and prefer small `--max-files` batch dry runs first.

## Parser spelling issues

`doctr-cli` uses underscore option names, while the helpers use shell-style hyphen names plus compatibility aliases for model names.

Examples:

```bash
# Installed CLI spelling
doctr-cli --input_path scan.jpg --no-assume_straight_pages --no-preserve_aspect_ratio

# Helper spelling
python scripts/doctr_quick_ocr.py scan.jpg --no-assume-straight-pages --no-preserve-aspect-ratio
```

If a command exits with argparse status `2`, run the same command with `--help` and correct the flag spelling before investigating runtime dependencies.
