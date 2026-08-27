# Plugin API Reference

This is a compact reference for Pillow plugin-extension work.

## Registry APIs

Import from `PIL import Image`.

- `Image.register_open(id, factory, accept=None)`: registers an image file factory for opening. `id` is uppercased; `factory` is usually an `ImageFile.ImageFile` subclass; `accept(prefix)` receives the first 16 bytes and returns truthy to try the factory.
- `Image.register_save(id, driver)`: registers a save function for single-image output.
- `Image.register_save_all(id, driver)`: registers a save function for multi-frame output.
- `Image.register_extension(id, extension)`: maps one lowercase extension, such as `.spam`, to a format id.
- `Image.register_extensions(id, extensions)`: maps multiple extensions.
- `Image.register_mime(id, mimetype)`: maps a format id to a MIME type.
- `Image.registered_extensions()`: initializes plugins and returns the extension-to-format mapping.
- `Image.register_decoder(name, decoder_class)`: registers a Python decoder class.
- `Image.register_encoder(name, encoder_class)`: registers a Python encoder class.

`Image.open(fp, mode="r", formats=None)` accepts a `formats` list/tuple. Use `formats=["YOURFORMAT"]` to isolate plugin debugging and avoid unrelated plugins in registry order.

## `ImageFile.ImageFile` Contract

A readable plugin normally subclasses `PIL.ImageFile.ImageFile`.

Important attributes and methods:

- `format`: uppercase format id, for example `"SPAM"`.
- `format_description`: human-readable description.
- `_open(self)`: parse header, validate file type, set `_size`, `_mode`, and usually `tile`.
- `self.fp`: binary file object positioned at the start when the factory is constructed.
- `self._size`: internal size tuple used by `im.size`.
- `self._mode`: internal mode string used by `im.mode`.
- `self.tile`: list of `ImageFile._Tile` descriptors used by `load()`.
- `load_seek()` / `load_read()`: optional methods for formats whose data is not simply read by seeking and reading from `self.fp`.
- `load_prepare()` / `load_end()`: optional hooks around decoder execution.

If `_open()` returns without a valid mode or positive size, Pillow treats the file as not identified by that driver.

## Tile Descriptors

Use `ImageFile._Tile(codec_name, extents, offset=0, args=None)`.

Equivalent conceptual tuple:

```python
(codec_name, (left, top, right, bottom), offset, args)
```

For a full-image raw grayscale file with 128 bytes of header:

```python
self.tile = [ImageFile._Tile("raw", (0, 0) + self.size, 128, ("L", 0, 1))]
```

Raw decoder args:

- `raw_mode`: byte layout in the file, often the same as `self.mode`.
- `stride`: bytes between rows; `0` means packed.
- `orientation`: `1` for top-to-bottom rows, `-1` for bottom-to-top rows.

A tile list can contain multiple tiles for formats that store channels, layers, strips, or blocks separately. Tile regions must match the decoder and output image geometry.

## Python Plugin vs Decoder Backend

A plugin module can:

- Recognize a file format.
- Parse headers and metadata.
- Expose frame navigation for container formats.
- Route compressed or raw bytes to existing decoders through tiles.
- Implement a Python `ImageFile.PyDecoder` for simple custom compression.
- Register save handlers and Python encoders.

A plugin module alone cannot decode arbitrary compressed data unless it implements or delegates to a decoder. If the format requires JPEG, JPEG 2000, TIFF, WebP, AVIF, zlib, or another compiled codec, verify that the relevant Pillow feature is installed.

## Feature APIs

Import from `from PIL import features`.

- `features.check(name)`: returns support for a module, codec, or feature. Unknown names warn and return `False`.
- `features.version(name)`: returns a version string or `None`.
- `features.get_supported()`: returns supported modules, codecs, and features.
- `features.check_module(name)`, `check_codec(name)`, `check_feature(name)`: stricter category-specific checks that raise `ValueError` for unknown names.
- `features.pilinfo(out=None, supported_formats=True)`: prints the same style of information used by `python -m PIL`.

Common names:

- Modules: `pil`, `tkinter`, `freetype2`, `littlecms2`, `webp`, `avif`.
- Codecs: `jpg`, `jpg_2000`, `zlib`, `libtiff`.
- Features: `raqm`, `fribidi`, `harfbuzz`, `libjpeg_turbo`, `mozjpeg`, `zlib_ng`, `libimagequant`, `xcb`.

`python -m PIL` calls `features.pilinfo()`. `python -m PIL --report` suppresses the supported-format listing for a shorter environment report.

## Existing Plugin Patterns

Useful built-in patterns to emulate conceptually:

- PPM-style raw raster: simple header parsing plus a `raw` tile.
- PNG-style compressed raster: header/chunk parsing plus a `zip` decoder tile.
- JPEG-style delegated compressed format: validate marker, set metadata, route to a compiled decoder tile.
- DDS-style mixed implementation: parse a complex header, use different tile decoders depending on pixel format, and handle optional decoder limitations.

When adapting patterns, copy the architecture, not source-specific constants or private internals you do not need.
