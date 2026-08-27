---
name: plugins-and-extension
description: "Extend Pillow with custom image plugins, diagnose plugin
  registration/open dispatch problems, and inspect optional codec/feature
  support for advanced integrations."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Pillow Plugins and Extension

Use this sub-skill when you need to add a custom Pillow image plugin, debug why `Image.open()` is not dispatching to a plugin, understand the boundary between Python plugin code and decoder backends, or inspect optional feature/codec support. For everyday open/save usage and metadata options, use the root skill's formats guidance instead.

## Core Model

Pillow image loading is plugin-driven:

1. A plugin module registers a format with `PIL.Image.register_open(format_id, factory, accept)`.
2. `Image.open(fp, mode="r", formats=None)` reads the first 16 bytes and calls each loaded plugin's `accept(prefix)` function in registry order.
3. When `accept` returns truthy, Pillow constructs the registered `ImageFile.ImageFile` subclass and calls its `_open()` method.
4. `_open()` parses only enough header data to set image metadata and `tile` descriptors; actual pixels are decoded later when `load()`, pixel access, conversion, or saving needs the data.
5. `ImageFile.load()` sorts tile descriptors, creates the requested decoder, seeks to tile offsets, and feeds bytes to the decoder.

Important consequence: a new plugin must be imported before it can participate in dispatch. Pillow does not automatically import arbitrary `*ImagePlugin.py` files from `sys.path`.

## Minimal Plugin Checklist

For a read plugin:

- Create a module named like `XxxImagePlugin.py` or another importable module name used by your package.
- Define a narrow, cheap `_accept(prefix: bytes)` that inspects only the available prefix bytes.
- Subclass `PIL.ImageFile.ImageFile`.
- Set class attributes `format = "FORMAT"` and `format_description = "Human description"`.
- In `_open()`, validate the header, set `self._size = (width, height)`, set `self._mode = "L"`, `"RGB"`, or another valid Pillow mode, and set `self.tile` if the image can be loaded.
- Register with `Image.register_open(format, ImageFileSubclass, _accept)`.
- Register extensions with `Image.register_extension(format, ".ext")` or `Image.register_extensions(format, [".ext", ...])`.
- Import the plugin before calling `Image.open()` unless it is packaged so the application imports it during startup.

Use `scripts/minimal_spam_plugin.py` as a self-contained working example. It registers a trivial raw SPAM format and has `--self-test` to create and open a tiny fixture without relying on repository files.

## Tile Boundary

A tile descriptor tells `ImageFile.load()` how to decode bytes into a rectangular region. Use `ImageFile._Tile(codec_name, extents, offset, args)`:

- `codec_name`: a decoder name such as `"raw"`, `"jpeg"`, `"zip"`, or a registered Python decoder name.
- `extents`: `(left, top, right, bottom)` in image coordinates, usually `(0, 0) + self.size` for one full-image tile.
- `offset`: byte offset from the start of the file to the encoded image data.
- `args`: decoder-specific parameters. For the raw decoder, use `(raw_mode, stride, orientation)`; common simple case is `(self.mode, 0, 1)`.

Python plugins can parse headers and route bytes to existing decoders. They cannot magically add support for a compressed bitstream that Pillow has no decoder for; use an existing decoder, implement a Python `ImageFile.PyDecoder`, or provide/enable a C extension codec when performance or codec availability requires it.

## Feature and CLI Inspection

Use `PIL.features` and `python -m PIL` to diagnose environment-dependent support:

```python
from PIL import features
print(features.check("jpg"))
print(features.check("webp"))
print(features.version("littlecms2"))
print(features.get_supported())
```

- `python -m PIL` prints Pillow build information and supported formats.
- `python -m PIL --report` prints the report without the verbose supported-format listing.
- `features.check(name)` accepts module, codec, or feature names such as `pil`, `freetype2`, `littlecms2`, `webp`, `avif`, `jpg`, `jpg_2000`, `zlib`, `libtiff`, `raqm`, `libjpeg_turbo`, and `xcb`.
- Optional codec absence explains failures for plugins that delegate to compiled decoders, for example JPEG 2000, TIFF, WebP, or AVIF.

## Debugging Flow

1. Confirm the plugin module is imported before `Image.open()`.
2. Check the format id is uppercase-consistent in registrations and class `format`.
3. Check `_accept(prefix)` returns truthy for a valid file and falsey for unrelated files.
4. Open with `formats=["FORMAT"]` to isolate registry-order effects.
5. Confirm `_open()` sets valid `_size`, `_mode`, and `tile` before returning.
6. Confirm tile offset and raw mode match the file layout.
7. Call `im.load()` in tests so decoder errors appear instead of only header-identification success.
8. Use `python -m PIL` or `features.check()` when the plugin depends on optional compiled support.

## References

- `references/custom-plugin-pattern.md` gives the authoring pattern and packaging/import guidance.
- `references/plugin-api-reference.md` summarizes the registry, `ImageFile`, tile, decoder, and features APIs.
- `references/troubleshooting.md` maps common plugin failures to fixes.
- `scripts/minimal_spam_plugin.py` is an executable reference plugin and self-test.
