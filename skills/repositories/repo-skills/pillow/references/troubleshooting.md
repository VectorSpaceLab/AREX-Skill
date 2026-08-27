# Pillow Troubleshooting

## Import or Installation Fails

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'PIL'` | Pillow is not installed in the Python that runs the script | Run `python -m pip install pillow` for that Python and re-check `python -c "from PIL import Image"` |
| Source build reports missing `jpeg` | JPEG headers/libraries are absent | Install libjpeg/libjpeg-turbo development package or use a prebuilt wheel |
| Source build reports missing `zlib` | zlib headers/libraries are absent | Install zlib development package or use a prebuilt wheel |
| A format works on one machine but not another | Optional codec library differs by build | Run `python -m PIL` or `format_capability_report.py`; add fallbacks or install required codec support |
| `python -m pip check` reports conflicts | Mixed package environment or incompatible dependency versions | Reinstall Pillow in a clean environment or repair the conflicting packages |

## Opening and File Lifecycle

- `Image.open()` reads headers immediately but defers pixel data. Keep the file open until `load()`, `copy()`, or all frame access is complete.
- Use `with Image.open(path) as im:` and call `im.copy()` for images that must outlive the context manager.
- `UnidentifiedImageError` usually means unsupported/corrupt input or a stream positioned at the wrong byte offset.
- For `BytesIO`, seek to the beginning before opening: `buffer.seek(0)`.

## Large or Untrusted Images

Pillow protects against decompression bombs. Very large images can emit `DecompressionBombWarning` or raise `DecompressionBombError` depending on configured limits.

```python
from PIL import Image
Image.MAX_IMAGE_PIXELS = None  # only for trusted inputs after risk review
```

For untrusted inputs, keep the guard enabled and reject unexpectedly large dimensions before processing.

## Format and Metadata Surprises

- Input format is detected from content; output format is inferred from filename extension unless `format=` is passed.
- JPEG cannot save alpha. Convert `RGBA` to `RGB` after flattening against an explicit background.
- Transforming images often drops `format`, file pointer, and some `info` values. Save metadata explicitly.
- Multi-frame sources require `ImageSequence.Iterator` and `save_all=True` when writing animations or multi-page files.
- EPS/PDF and some advanced formats may require external tools or optional libraries.

## Geometry, Modes, and Alpha

- Boxes are `(left, upper, right, lower)` and right/lower are exclusive.
- `paste()` boxes must match the source region size unless using the two-coordinate form.
- Use `RGBA` for alpha-preserving pipelines and `alpha_composite()` when both layers are RGBA.
- Use `NEAREST` for masks/pixel art, `BICUBIC` for balanced resizing, and `LANCZOS` for high-quality downscaling.

## Text and Fonts

- `ImageFont.truetype()` needs a valid font file path or file-like object; missing fonts raise `OSError`.
- Complex layout features (`direction`, OpenType `features`, `language`) need libraqm support.
- `textlength()` measures advance; `textbbox()` measures visible bounds. Use the right one for layout validation.
- Embedded color glyph rendering needs `embedded_color=True` and a compatible image mode.

## Custom Plugins

- Import the plugin module before calling `Image.open()`.
- `_accept(prefix)` should be fast and specific.
- `_open()` must set `_size`, `_mode`, and a valid `tile` list for readable image data.
- Register openings and extensions with `Image.register_open()` and `Image.register_extensions()`.
