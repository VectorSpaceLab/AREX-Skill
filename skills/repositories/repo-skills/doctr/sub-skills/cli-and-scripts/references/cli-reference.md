# `doctr-cli` Reference

`doctr-cli` is the installed command-line entry point for end-to-end OCR over one image or PDF. It builds an OCR predictor, loads the input with docTR document readers, runs inference, and writes `Document.export()` as JSON.

## Command shape

```bash
doctr-cli --input_path INPUT --output results.json
```

The installed entry point is registered by the package as `doctr-cli`. If the command is unavailable, try the import/backend checks in [troubleshooting.md](troubleshooting.md) before assuming the package is broken.

## Exact options and defaults

```text
usage: doctr-cli [-h] --input_path INPUT_PATH [--det_arch DET_ARCH]
                 [--reco_arch RECO_ARCH]
                 [--assume_straight_pages | --no-assume_straight_pages]
                 [--straighten_pages]
                 [--preserve_aspect_ratio | --no-preserve_aspect_ratio]
                 [--symmetric_pad] [--det_bs DET_BS] [--reco_bs RECO_BS]
                 [--detect_orientation] [--detect_language]
                 [--output OUTPUT]
```

| Option | Default | Meaning |
|---|---:|---|
| `-h`, `--help` | exits | Print parser help and exit with status `0`. |
| `--input_path INPUT_PATH` | required | Path to one input PDF or image. A lower-case `.pdf` suffix is loaded as PDF; every other suffix is passed to the image reader. |
| `--det_arch DET_ARCH` | `db_resnet50` | Detection architecture name or detection model object name accepted by the installed docTR model factory. |
| `--reco_arch RECO_ARCH` | `crnn_vgg16_bn` | Recognition architecture name or recognition model object name accepted by the installed docTR model factory. |
| `--assume_straight_pages` / `--no-assume_straight_pages` | `True` | Whether to assume pages contain only straight text elements. Use `--no-assume_straight_pages` for rotated text elements. |
| `--straighten_pages` | `False` | Estimate page-level skew/orientation and run OCR on a straightened page. |
| `--preserve_aspect_ratio` / `--no-preserve_aspect_ratio` | `True` | Preserve aspect ratio during detection resizing. |
| `--symmetric_pad` | `False` | Use symmetric padding instead of bottom/right padding. |
| `--det_bs DET_BS` | `2` | Detection batch size. |
| `--reco_bs RECO_BS` | `128` | Recognition batch size. |
| `--detect_orientation` | `False` | Add page orientation predictions. |
| `--detect_language` | `False` | Add language predictions. |
| `--output OUTPUT` | `results.json` | JSON output path. Parent directories must already be writable. |

## Pretrained behavior

`doctr-cli` always constructs the OCR predictor with `pretrained=True`. There is no `--pretrained` or `--no-pretrained` CLI flag. In a fresh cache, this can trigger model weight downloads through the installed backend. For offline smoke checks or deliberate random-weight tests, use [scripts/doctr_quick_ocr.py](../scripts/doctr_quick_ocr.py) or [scripts/doctr_batch_ocr.py](../scripts/doctr_batch_ocr.py), both of which default to `--no-pretrained` and require `--pretrained` for trained weights.

## Output JSON

The CLI writes UTF-8 JSON with `indent=4` and `ensure_ascii=False`. The root object is the exported docTR `Document` result and contains a `pages` array. Each page export contains page-level metadata plus nested OCR structures such as blocks, lines, words, confidence values, and geometries. Optional flags may add page orientation or language fields when supported by the installed model stack.

Minimal invocation:

```bash
doctr-cli --input_path document.pdf --output ocr.json
```

With non-default page processing:

```bash
doctr-cli \
  --input_path scan.jpg \
  --output scan-ocr.json \
  --det_arch db_mobilenet_v3_large \
  --reco_arch crnn_vgg16_bn \
  --no-assume_straight_pages \
  --straighten_pages \
  --detect_orientation
```

## Parser behavior

- `doctr-cli --help` exits `0` after printing help.
- Missing `--input_path`, unknown flags, invalid integer/float values, or invalid BooleanOptionalAction spelling are argparse errors and exit with status `2`.
- Boolean optional flags must use the parser spellings with underscores: `--no-assume_straight_pages` and `--no-preserve_aspect_ratio`, not hyphenated forms.

## Runtime error behavior

The command logs messages with the form `LEVEL: message` and exits `1` for common runtime failures:

- missing input file: `File not found: ...`;
- unreadable/corrupt/unsupported image or PDF: `File could not be read as a valid image or PDF: ...`;
- unexpected load failure: `Error occurred while loading the document: ...`;
- missing output parent or impossible output path: `Could not write output file at given path: ...` or `Results could not be saved: ...`.

The CLI does not create output parent directories, does not offer `txt` or `xml` output, and does not batch over directories. Use the bundled helpers for those workflows.
