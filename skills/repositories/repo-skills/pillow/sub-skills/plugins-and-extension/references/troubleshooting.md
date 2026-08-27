# Plugin Troubleshooting

Use this guide when a custom Pillow plugin does not open, load, or save as expected.

## `Image.open()` Does Not Use the Plugin

Likely causes:

- The plugin module was never imported.
- `Image.register_open()` did not run because registration is inside a function or guarded block.
- The format id in `formats=[...]` does not match the registered id.
- `_accept(prefix)` returns `False` for the fixture.
- Another plugin accepts the file first.

Fixes:

- Add an explicit `import yourpackage.YourImagePlugin` before `Image.open()`.
- Inspect `Image.OPEN` after import and confirm your uppercase format id is present.
- Open with `Image.open(fp, formats=["YOURFORMAT"])` during debugging.
- Unit-test `_accept(valid_prefix)` and `_accept(unrelated_prefix)` directly.

## Extension Is Registered But Opening Still Fails

Extension registration is not enough for a third-party plugin. It maps `.ext` to a format id after the plugin has been imported; it does not make Pillow discover arbitrary external plugin modules.

Fixes:

- Import the module before opening.
- Use `Image.register_extensions("FORMAT", [".ext", ".alt"])` at module import time.
- For saving, confirm `Image.SAVE["FORMAT"]` exists, not just `Image.EXTENSION[".ext"]`.

## `_accept` Is Too Broad or Too Slow

Symptoms:

- Your plugin tries to parse unrelated images.
- Opening common formats gets slower.
- Files fail with misleading plugin-specific errors.

Fixes:

- Check only a distinctive magic signature or structured prefix.
- Do not perform full parsing, imports, filesystem reads, decompression, or network calls in `_accept`.
- Move expensive validation into `_open()` and raise `SyntaxError` for malformed files.

## Missing `_size` or `_mode`

Symptoms:

- `Image.open()` raises `UnidentifiedImageError` or a syntax-style identification failure even though `_accept` matched.
- The plugin object is constructed but Pillow says the image was not identified.

Fixes:

- Set `self._size = (width, height)` to positive integers before `_open()` returns.
- Set `self._mode` to a valid Pillow mode such as `"1"`, `"L"`, `"P"`, `"RGB"`, `"RGBA"`, or another mode supported by the intended decoder.
- Validate parsed dimensions before setting tiles; reject zero or negative sizes.

## Incorrect Tile Tuple

Symptoms:

- `Image.open()` succeeds but `im.load()` fails.
- Pixels are scrambled, flipped, truncated, or wrong color order.
- Errors mention decoder configuration, buffer size, or tile offset.

Fixes:

- Use `ImageFile._Tile(...)`, not an ad-hoc tuple unless you exactly match the four fields.
- Use extents `(0, 0) + self.size` for a single full-image tile.
- Measure `offset` from the beginning of the file, commonly `self.fp.tell()` after header parsing.
- For `raw`, set args to `(raw_mode, stride, orientation)`. Use `orientation=-1` only for bottom-up storage.
- Call `im.load()` in tests; opening alone usually validates only the header path.

## Decoder Errors

Symptoms:

- `OSError: decoder ... not available`.
- `OSError: broken data stream when reading image file`.
- `OSError: image file is truncated`.
- Load fails only on machines with different Pillow builds.

Fixes:

- Confirm the tile's `codec_name` is available for the Pillow build.
- Use `python -m PIL` or `features.check()` for optional support such as `jpg`, `jpg_2000`, `zlib`, `libtiff`, `webp`, or `avif`.
- Verify the tile offset points to encoded pixel data, not the header.
- Verify `args` match the decoder's expected shape and raw mode.
- Keep `ImageFile.LOAD_TRUNCATED_IMAGES` as a last-resort application policy, not a plugin correctness fix.

## Optional C Codec Unavailable

Symptoms:

- A plugin works for raw or simple variants but fails for compressed variants.
- The same file works on one environment and fails on another.

Fixes:

- Check `features.check("jpg")`, `features.check("jpg_2000")`, `features.check("zlib")`, `features.check("libtiff")`, `features.check("webp")`, or `features.check("avif")` as relevant.
- Give a clear error message when a format variant requires unavailable support.
- Consider a pure-Python decoder only for simple formats; performance-sensitive codecs usually need compiled support.

## Save Registration Mistakes

Symptoms:

- `im.save("out.ext")` raises an unknown-extension error.
- `im.save(fp, format="FORMAT")` fails even though open works.

Fixes:

- Register a save handler with `Image.register_save("FORMAT", save_handler)`.
- Register `.ext` with `Image.register_extension("FORMAT", ".ext")` if saving by filename extension.
- For multi-frame saves, also register `Image.register_save_all("FORMAT", save_all_handler)`.
- Keep read and save tile args separate; `ImageFile._save()` uses encoder tile descriptors, not open/load tile descriptors.

## Fast Diagnostic Snippet

```python
import io
from PIL import Image, features
import yourpackage.YourImagePlugin

print("registered open:", "YOURFORMAT" in Image.OPEN)
print("registered extension:", Image.EXTENSION.get(".yourext"))
print("zlib:", features.check("zlib"))

with Image.open(io.BytesIO(make_fixture()), formats=["YOURFORMAT"]) as im:
    print(im.format, im.mode, im.size, im.tile)
    im.load()
```
