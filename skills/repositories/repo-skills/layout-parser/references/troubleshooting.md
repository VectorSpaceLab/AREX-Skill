# LayoutParser Troubleshooting

This file covers cross-cutting failures that affect multiple sub-skills.
Backend-specific details are still handled in the nearest sub-skill guide.

## Installation and import problems

### `ModuleNotFoundError` for `layoutparser`

- Install the package into the intended environment with `pip install -e .`
  or `pip install layoutparser`.
- Confirm you are using the target environment Python, not the host or another
  checkout.
- Run `python -m pip check` after install.

### `ModuleNotFoundError: No module named 'pkg_resources'`

This can happen when using `google-cloud-vision==1` with a setuptools build
that no longer exposes `pkg_resources`.

Recovery:

1. Install a setuptools build that still provides `pkg_resources`.
2. Re-run `python -c "import pkg_resources"`.
3. Re-import `GCVAgent`.

In the verified inspection environment, `setuptools==77.0.3` restored
`pkg_resources` while still satisfying the torch wheel that was installed.

### Optional backend classes do not import

`Detectron2LayoutModel`, `PaddleDetectionLayoutModel`, `EfficientDetLayoutModel`,
`TesseractAgent`, and `GCVAgent` are lazy or conditional imports. If the class
is missing, check the corresponding extra or system dependency before assuming
LayoutParser itself is broken.

## Geometry and layout object failures

### `InvalidShapeError`

Occurs when a union/intersection would create an invalid shape, such as unioning
intervals on different axes.

### `NotSupportedShapeError`

Occurs for strict quadrilateral operations that could create polygons. Retry
with `strict=False` only if rectangle approximation is acceptable.

### `ValueError` from `TextBlock.to_interval()`

`TextBlock.to_interval()` requires `axis='x'` or `axis='y'` when the wrapped
block is not already an `Interval`.

### `Layout(...)` rejects a nested `Layout`

Use `Layout([layout])` instead of `Layout(layout)` when wrapping an existing
layout.

## I/O failures

### JSON/CSV round-trip errors

- `load_dict()` expects `block_type` to be present for block dictionaries.
- `load_csv()`/`load_dataframe()` need `block_type` either in the dataframe or
  as an argument.
- Mixed `TextBlock` rows depend on text-related columns being present.
- Quadrilateral CSV rows can fail if the `points` column remains a string
  instead of a parsed Python list. This is especially likely with newer pandas
  string dtypes. Pre-parse non-null `points` values with `ast.literal_eval`, or
  prefer JSON for quadrilateral-heavy round-trips.

### PDF loading surprises

- `load_pdf()` without `load_images=True` only uses PDF text extraction.
- `load_pdf(..., load_images=True)` also needs `pdf2image` and a working
  poppler installation.
- Empty PDFs still return page entries, but those layouts may contain no blocks.

## Visualization failures

### Alpha/width/color length mismatches

`draw_box()` and `draw_text()` expect per-block lists to match the layout
length. If you pass lists, make sure each list has one entry per block.

### Bad alpha values

Box/text alpha values must stay in `[0, 1]`.

### Font or image-mode issues

- PIL images may need conversion to RGB before drawing.
- If text rendering looks wrong, confirm the bundled font exists or pass a
  custom `font_path`.
- If `draw_box(..., show_element_id=True)` or `show_element_type=True` fails
  with `AttributeError: 'FreeTypeFont' object has no attribute 'getsize'`, the
  environment likely has a newer Pillow API than LayoutParser 0.3.4 expects.
  Use a compatible Pillow version, avoid id/type labels, or patch the font-size
  measurement path in a maintained fork.

## OCR failures

### Missing Tesseract binary

`pytesseract` is only the Python wrapper. The live OCR path also needs the
`tesseract` executable on the host.

### Missing Google Cloud Vision credentials

`GCVAgent.with_credential()` expects a valid credentials file path and the
`GOOGLE_APPLICATION_CREDENTIALS` environment variable.

### OCR version drift

Saved OCR responses are safer than live OCR when you need deterministic tests.
Tesseract and GCV outputs can change across engine versions.

## Layout-model failures

### `lp://` config parsing errors

Check the config format and backend name:

- `lp://<backend>/<dataset>/<model>/<config|weight>`
- `lp://<dataset>/<model>/<config|weight>`
- `lp://<dataset>`

The available backend depends on what is installed in the environment.

### Missing backends

- EfficientDet requires `torch`, `torchvision`, and `effdet`.
- Detectron2 requires a separate install path and may not be available on every
  platform.
- PaddleDetection requires `paddlepaddle` and its inference runtime.

### Unexpected device choice

`Detectron2LayoutModel` and `EfficientDetLayoutModel` choose CUDA when the
installed torch build reports CUDA availability. If you want CPU-only
inference, set the device explicitly.

### Model download/cache issues

LayoutParser model paths are resolved through `PathManager`. If a model download
fails or a cached file looks corrupt, clear the cache and retry with a clean
network path.

## What to try first

1. Re-run the bundled root smoke scripts.
2. Check backend availability with `../scripts/inspect_backends.py`.
3. If a failure is backend-specific, jump to the nearest sub-skill guide.
