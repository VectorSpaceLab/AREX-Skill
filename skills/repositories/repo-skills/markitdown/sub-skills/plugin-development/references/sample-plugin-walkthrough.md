# Sample Plugin Walkthrough

## What the Sample Demonstrates

The sample plugin pattern adds an RTF converter as a third-party MarkItDown plugin. The same structure applies to other custom formats:

- A package installs a `markitdown.plugin` entry point.
- The entry point imports the plugin module.
- The module exports `__plugin_interface_version__ = 1` and `register_converters()`.
- `register_converters()` attaches a `DocumentConverter` instance to the active `MarkItDown` object.
- The converter decides whether it accepts a stream and returns a `DocumentConverterResult` from `convert()`.

## Package Metadata Pattern

The sample entry point is equivalent to:

```toml
[project.entry-points."markitdown.plugin"]
sample_plugin = "markitdown_sample_plugin"
```

`sample_plugin` is the discovery name shown by `markitdown --list-plugins`. `markitdown_sample_plugin` is the importable Python module that exposes the plugin interface.

The sample package depends on MarkItDown and the format-specific parsing library used by its converter. For a new plugin, keep MarkItDown as a runtime dependency and add only the libraries required to parse the custom format.

## Module Export Pattern

The plugin package re-exports its interface from package import time:

```python
from ._plugin import __plugin_interface_version__, register_converters, RtfConverter

__all__ = [
    "__plugin_interface_version__",
    "register_converters",
    "RtfConverter",
]
```

This keeps the entry point target simple: the entry point imports the top-level package and MarkItDown can find `register_converters()` there.

## RTF Converter Pattern

The sample converter accepts RTF by checking `StreamInfo` instead of reading bytes:

```python
ACCEPTED_MIME_TYPE_PREFIXES = ["text/rtf", "application/rtf"]
ACCEPTED_FILE_EXTENSIONS = [".rtf"]


def accepts(file_stream, stream_info, **kwargs):
    mimetype = (stream_info.mimetype or "").lower()
    extension = (stream_info.extension or "").lower()
    return extension in ACCEPTED_FILE_EXTENSIONS or any(
        mimetype.startswith(prefix) for prefix in ACCEPTED_MIME_TYPE_PREFIXES
    )
```

This is a safe default for file formats with reliable extensions or MIME types because it does not move the stream. If a format needs magic-byte detection, save `file_stream.tell()` before reading and restore it before returning.

The sample conversion then decodes bytes with `stream_info.charset` when available, falls back to the system-preferred encoding, and returns `DocumentConverterResult(markdown=...)` after passing the RTF text through a parser. New plugins should make charset handling explicit for text-like formats and should raise a clear converter exception if a required dependency or format parse fails.

## Registration Pattern

The sample registration is intentionally small:

```python
__plugin_interface_version__ = 1


def register_converters(markitdown, **kwargs):
    markitdown.register_converter(RtfConverter())
```

For production plugins, keep registration similarly direct, but pass a priority when override behavior matters:

```python
def register_converters(markitdown, **kwargs):
    markitdown.register_converter(RtfConverter(), priority=0.0)
```

Lower priority values run first. Equal priorities retain stable order after registration, and newly registered converters are inserted before older ones. If a plugin should override a built-in or generic converter, use a lower priority and a precise `accepts()` check.

## Test Pattern

A useful test set mirrors the sample:

1. Direct converter test: open a fixture as bytes, call `RtfConverter().convert(file_stream, StreamInfo(extension=".rtf", mimetype="text/rtf", filename="test.rtf"))`, and assert expected Markdown snippets.
2. Integration test: instantiate `MarkItDown(enable_plugins=True)`, convert the fixture path, and assert the same output snippets.
3. Discovery test: run the checker in this sub-skill or inspect `importlib.metadata.entry_points(group="markitdown.plugin")` for the plugin entry point.

The sample RTF fixture proves both direct converter behavior and MarkItDown plugin loading. For a new `.foo` plugin, keep a tiny fixture that exercises real parser behavior and a negative fixture that should not be accepted.

## Using OCR as a Real Plugin Example

The OCR package is also discovered through the `markitdown.plugin` group, but its behavior is domain-specific: it augments PDF, DOCX, PPTX, and XLSX conversion with model-backed OCR when an `llm_client` and `llm_model` are supplied. For OCR setup, model kwargs, and skip behavior when no model client is provided, route to `../ocr-plugin/SKILL.md` instead of duplicating those details here.
