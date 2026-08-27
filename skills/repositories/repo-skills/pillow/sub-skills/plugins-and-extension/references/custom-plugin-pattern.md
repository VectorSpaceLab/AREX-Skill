# Custom Plugin Pattern

This reference shows the pattern for a small Pillow image plugin. Keep custom plugins importable, explicitly registered, and covered by tests that call both `Image.open()` and `im.load()`.

## Skeleton

```python
from PIL import Image, ImageFile


def _accept(prefix: bytes) -> bool:
    return prefix.startswith(b"MAGIC")


class ExampleImageFile(ImageFile.ImageFile):
    format = "EXAMPLE"
    format_description = "Example raster image"

    def _open(self) -> None:
        header = self.fp.read(16)
        if not header.startswith(b"MAGIC"):
            raise SyntaxError("not an EXAMPLE image")

        width = header[8]
        height = header[9]
        self._mode = "L"
        self._size = (width, height)
        self.tile = [
            ImageFile._Tile("raw", (0, 0) + self.size, 16, (self.mode, 0, 1))
        ]


Image.register_open(ExampleImageFile.format, ExampleImageFile, _accept)
Image.register_extension(ExampleImageFile.format, ".example")
```

## Import Requirement

Pillow no longer imports arbitrary files ending in `ImagePlugin.py` from the Python path. A third-party plugin must be imported before `Image.open()` can dispatch to it.

Good application patterns:

- Import the plugin in package initialization, CLI startup, or an integration bootstrap module.
- Document a one-line import such as `import mypackage.ExampleImagePlugin` before opening files.
- In tests, import the plugin module in the test body or fixture before calling `Image.open()`.

If extension-based dispatch is expected, registration still happens only after import. `Image.register_extension()` maps extensions to formats for saving and extension-triggered plugin import paths; it does not import your custom module by itself unless you also integrate with Pillow's internal plugin import tables, which third-party plugins normally should not modify.

## `_accept` Guidelines

`_accept(prefix)` receives the first 16 bytes from `Image.open()`. It should be:

- Narrow: check a magic value, structured signature, or version field, not a common byte or extension.
- Cheap: avoid seeking, decoding, filesystem access, imports, network calls, or reading more data.
- Safe: return `False` for short or malformed prefixes, or return a warning string only when intentionally using Pillow's warning mechanism.

A broad `_accept` causes wrong plugins to steal files from later plugins. A slow `_accept` affects every `Image.open()` call that reaches that plugin.

## `_open` Responsibilities

`_open()` identifies the file and sets metadata; it should not eagerly decode the whole image unless the format cannot be represented as deferred tiles.

Required for successful identification:

- Set `self._size` to a positive `(width, height)` tuple.
- Set `self._mode` to a valid Pillow mode.
- Raise `SyntaxError`, `EOFError`, `struct.error`, `IndexError`, `KeyError`, or `TypeError` for malformed input that means this plugin should reject the file.

Required for loading pixels:

- Set `self.tile` to a list of `ImageFile._Tile(...)` descriptors.
- Use offsets measured from the start of the file.
- Use decoder args matching the file layout, not just the Pillow output mode.

For multi-frame or container formats, implement only the frame navigation and tile setup required by the format. Avoid global state unless the plugin registry itself is the state being modified.

## Registration Checklist

Use these calls at module import time:

- `Image.register_open(format_id, factory, _accept)` for reading.
- `Image.register_save(format_id, save_handler)` for writing one image.
- `Image.register_save_all(format_id, save_all_handler)` for writing multiple frames.
- `Image.register_extension(format_id, ".ext")` or `Image.register_extensions(format_id, [".a", ".b"])`.
- `Image.register_mime(format_id, "image/example")` when a MIME mapping is useful.
- `Image.register_decoder(name, decoder_class)` or `Image.register_encoder(name, encoder_class)` only for Python codec classes.

Format identifiers are normalized to uppercase by Pillow registration functions, but using one canonical uppercase string in the class and registrations avoids confusion.

## Packaging and Tests

A minimal plugin test should verify all of the following:

```python
import io
from PIL import Image
import mypackage.ExampleImagePlugin

fixture = make_example_bytes()
with Image.open(io.BytesIO(fixture), formats=["EXAMPLE"]) as im:
    assert im.format == "EXAMPLE"
    assert im.size == (2, 2)
    assert im.mode == "L"
    im.load()
```

Also test at least one unrelated file prefix to prove `_accept` rejects it quickly.
