# Installation and Feature Checks

Pillow is installed from the `pillow` distribution and imported as `PIL`.

## Normal Install

For typical users, prefer a wheel install:

```bash
python -m pip install --upgrade pillow
```

Then verify:

```bash
python - <<'PY'
from PIL import Image, features
print(Image.__version__)
print("JPEG", features.check("jpg"))
print("PNG/zlib", features.check("zlib"))
PY
```

## Source Build Dependencies

Pillow can build from source, but zlib and JPEG support are required by default. Other optional features depend on external libraries. Install only the features your workflow needs.

| Feature | Feature check | Typical library |
| --- | --- | --- |
| JPEG | `features.check("jpg")` | libjpeg or libjpeg-turbo |
| PNG compression | `features.check("zlib")` | zlib |
| TIFF | `features.check("libtiff")` | libtiff |
| FreeType fonts | `features.check("freetype2")` | FreeType |
| Color management | `features.check("littlecms2")` | LittleCMS2 |
| WebP | `features.check("webp")` | libwebp |
| JPEG 2000 | `features.check("jpg_2000")` | OpenJPEG |
| AVIF | `features.check("avif")` | libavif plus AV1 codecs |
| Complex text layout | `features.check_feature("raqm")` or `features.check("raqm")` | libraqm, HarfBuzz, FriBiDi |

If a source build fails with missing `jpeg` or `zlib`, install the corresponding development headers/libraries for the active build environment and rebuild Pillow.

## Built-in Reports

Pillow exposes an installed-feature report:

```bash
python -m PIL
python -m PIL --report
```

The bundled [`../scripts/pillow_smoke_check.py`](../scripts/pillow_smoke_check.py) performs a smaller in-memory smoke test. The [`../sub-skills/formats-and-metadata/scripts/format_capability_report.py`](../sub-skills/formats-and-metadata/scripts/format_capability_report.py) script produces a focused feature/format report and can emit JSON.

## Optional Extras

Pillow's package metadata may expose optional groups for docs, tests, Arrow integration, XMP parsing, and legacy file helpers. Do not install broad extras unless the user specifically needs those workflows.

For ordinary image processing, start with base Pillow and add only the external libraries or Python packages required by the target formats or metadata surfaces.

## Environment Expectations

- Python support follows the package metadata for the installed Pillow version.
- Wheel builds usually include common codecs, but source builds depend on local libraries.
- Linux, macOS, Windows, and platform-specific package managers use different library names.
- GPU hardware is irrelevant for normal Pillow use; Pillow's core operations are CPU image processing.
