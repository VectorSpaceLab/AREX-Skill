# Plugin Authoring Reference

## Plugin Package Contract

A MarkItDown plugin is an installed Python package exposing an entry point in the `markitdown.plugin` group. The entry point value must import a module or object that provides a `register_converters(markitdown, **kwargs)` function.

Minimal `pyproject.toml` shape:

```toml
[project]
name = "my-markitdown-plugin"
requires-python = ">=3.10"
dependencies = ["markitdown>=0.1.0a1"]

[project.entry-points."markitdown.plugin"]
my_plugin = "my_markitdown_plugin"
```

The entry point key is what `markitdown --list-plugins` prints. Choose a short, stable name that matches the package or plugin feature. If this group is absent or misspelled, MarkItDown will not discover the plugin even if the converter code imports correctly.

## Plugin Module Contract

The module named by the entry point should export:

```python
from markitdown import MarkItDown

__plugin_interface_version__ = 1


def register_converters(markitdown: MarkItDown, **kwargs):
    markitdown.register_converter(MyConverter(), priority=0.0)
```

`__plugin_interface_version__` is the declared plugin interface version; version `1` is the supported pattern. `register_converters()` is called when plugins are enabled on a `MarkItDown` instance. MarkItDown catches exceptions raised while loading the entry point or registering converters, emits warnings, and skips the failing plugin instead of aborting the whole conversion setup.

## Custom DocumentConverter

A converter subclasses `DocumentConverter` and implements both methods:

```python
from typing import Any, BinaryIO
from markitdown import DocumentConverter, DocumentConverterResult, StreamInfo


class MyConverter(DocumentConverter):
    def accepts(
        self,
        file_stream: BinaryIO,
        stream_info: StreamInfo,
        **kwargs: Any,
    ) -> bool:
        return (stream_info.extension or "").lower() == ".foo"

    def convert(
        self,
        file_stream: BinaryIO,
        stream_info: StreamInfo,
        **kwargs: Any,
    ) -> DocumentConverterResult:
        data = file_stream.read().decode(stream_info.charset or "utf-8")
        return DocumentConverterResult(markdown=data)
```

Use `StreamInfo.extension`, `StreamInfo.mimetype`, `StreamInfo.charset`, `StreamInfo.filename`, `StreamInfo.local_path`, and `StreamInfo.url` for fast acceptance checks. `accepts()` may inspect bytes only when needed, but it must restore the original stream position before returning:

```python
position = file_stream.tell()
try:
    header = file_stream.read(8)
    return header.startswith(b"FOO\x00")
finally:
    file_stream.seek(position)
```

MarkItDown asserts that `accepts()` leaves the stream where it found it. If the position changes, conversion can fail before `convert()` runs or can starve later converters of bytes.

## Registration and Priority

Register converters from `register_converters()`:

```python
from markitdown import PRIORITY_SPECIFIC_FILE_FORMAT, PRIORITY_GENERIC_FILE_FORMAT


def register_converters(markitdown, **kwargs):
    markitdown.register_converter(
        MyFooConverter(),
        priority=PRIORITY_SPECIFIC_FILE_FORMAT,
    )
```

`MarkItDown.register_converter(converter, *, priority=0.0)` stores the converter with a priority. Lower priority values are tried first. The converter list is sorted immediately before conversion using a stable sort. New registrations are inserted ahead of older registrations, so converters with the same priority favor the most recently registered converter.

Use priority intentionally:

- Use a low/specific priority, commonly `0.0`, for clear file formats such as `.foo` or a precise MIME type.
- Use a value below a generic fallback when the plugin should override a broad converter.
- Use a higher value when the plugin should act as a fallback after built-ins.
- Avoid overly broad `accepts()` methods at high precedence because they can intercept unrelated formats.

## Discovery and Runtime Enablement

Discovery and runtime conversion are separate:

```bash
markitdown --list-plugins
markitdown --use-plugins document.foo
```

`--list-plugins` reads installed entry points from the `markitdown.plugin` group and prints each entry point name and import target. It does not prove `register_converters()` succeeds or that a converter accepts a file.

Plugins are disabled by default for conversion. Enable them explicitly:

```python
from markitdown import MarkItDown

md = MarkItDown(enable_plugins=True)
result = md.convert("document.foo")
markdown = result.markdown
```

A plugin can also be enabled on an existing instance with `md.enable_plugins(**kwargs)` if it was not already enabled. Calling it repeatedly warns that plugin converters are already enabled.

## Safe Authoring Workflow

1. Implement the converter and direct converter unit tests first with explicit `StreamInfo` hints.
2. Add `__plugin_interface_version__`, `register_converters()`, and the `markitdown.plugin` entry point.
3. Install the package into the same Python environment as MarkItDown.
4. Run `python scripts/check_plugin_package.py --plugin <entry-point-name> --import-module` to inspect entry point metadata and exported hooks.
5. Run `markitdown --list-plugins` and confirm the entry point appears.
6. Run a plugin-enabled conversion with `--use-plugins` or `MarkItDown(enable_plugins=True)`.
7. If a built-in converter wins, inspect priority, `accepts()` selectivity, stream reset behavior, and whether plugins were actually enabled.
