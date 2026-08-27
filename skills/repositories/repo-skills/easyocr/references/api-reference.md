# EasyOCR API Reference

This reference covers the public EasyOCR runtime surface that future agents use
most often.

## Package surface

- `easyocr.__version__`
- `easyocr.Reader`
- Console entry point: `easyocr`

## `Reader`

Constructor signature:

```python
Reader(
    lang_list,
    gpu=True,
    model_storage_directory=None,
    user_network_directory=None,
    detect_network='craft',
    recog_network='standard',
    download_enabled=True,
    detector=True,
    recognizer=True,
    verbose=True,
    quantize=True,
    cudnn_benchmark=False,
)
```

Key behaviors:

- `lang_list` is a list of language codes.
- `gpu=True` auto-selects CUDA, then MPS, then CPU.
- `gpu=False` forces CPU.
- Any other `gpu` value is used as the device string directly.
- `model_storage_directory` and `user_network_directory` override the cache
  locations.
- `download_enabled=False` turns missing model files into immediate failures
  instead of downloads.
- `detect_network` currently routes through `craft` or `dbnet18`.
- `recog_network='standard'` means built-in language selection.

## Main methods

### `readtext`

```python
readtext(
    image,
    decoder='greedy',
    beamWidth=5,
    batch_size=1,
    workers=0,
    allowlist=None,
    blocklist=None,
    detail=1,
    rotation_info=None,
    paragraph=False,
    min_size=20,
    contrast_ths=0.1,
    adjust_contrast=0.5,
    filter_ths=0.003,
    text_threshold=0.7,
    low_text=0.4,
    link_threshold=0.4,
    canvas_size=2560,
    mag_ratio=1.0,
    slope_ths=0.1,
    ycenter_ths=0.5,
    height_ths=0.5,
    width_ths=0.5,
    y_ths=0.5,
    x_ths=1.0,
    add_margin=0.1,
    threshold=0.2,
    bbox_min_score=0.2,
    bbox_min_size=3,
    max_candidates=0,
    output_format='standard',
)
```

Accepted image inputs: file path, NumPy array, bytes, or a raw image URL.

Return shapes:

- `detail=0` -> list of strings.
- `detail=1`, `output_format='standard'` -> list of `(box, text, confidence)`.
- `output_format='dict'` -> list of dictionaries with `boxes`, `text`, and
  `confident` keys.
- `output_format='json'` -> JSON strings.
- `output_format='free_merge'` is an API-only advanced output path.

### `readtext_batched`

Batched version of `readtext` for same-sized images. It returns one OCR result
list per input image.

### `detect`

Returns the detection boxes and free-form text regions. It is the right call
when you want boxes first and recognition later.

### `recognize`

Runs recognition against already detected boxes or a full crop. If you call it
with both box lists omitted, it treats the full image as one region.

### `readtextlang`

A legacy helper that tries to match recognized characters against files in a
local `characters/` directory. Treat it as fragile and prefer `readtext`
with your own filtering unless you specifically need that legacy behavior.

## CLI entry point

The installed CLI is `easyocr`. See `references/cli-reference.md` for the
flag groups and parser caveats.

## Related references

- `references/cli-reference.md` for CLI flags and quirks.
- `references/configuration.md` for cache paths, backend selection, and
  language/model rules.
- `references/troubleshooting.md` for CLI quirks and runtime caveats.
- `sub-skills/inference/references/workflows.md` for end-to-end usage examples.
