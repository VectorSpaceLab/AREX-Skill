# Plugin Troubleshooting

## Plugin Does Not Appear in `--list-plugins`

Symptoms:

- `markitdown --list-plugins` says no third-party plugins are installed.
- The plugin module imports manually, but the plugin name is absent from MarkItDown discovery.
- `python scripts/check_plugin_package.py --plugin <name>` reports a missing entry point.

Likely causes and fixes:

- The package is not installed in the same Python environment as the `markitdown` command. Reinstall the plugin into that environment and rerun `markitdown --list-plugins`.
- The entry point group is wrong. It must be exactly `[project.entry-points."markitdown.plugin"]`.
- The entry point key differs from the expected plugin name. Use `python scripts/check_plugin_package.py --list` to see installed keys.
- The entry point value points to a non-importable module. Run the checker with `--import-module` to surface import errors without needing the original source tree.
- Editable installs can be stale after metadata changes. Reinstall the package after changing `pyproject.toml` entry points.

`--list-plugins` only inspects entry-point metadata. A plugin can appear there while still failing to import or register converters at runtime.

## Plugin Appears but Conversion Ignores It

Symptoms:

- `markitdown --list-plugins` prints the plugin entry point.
- Built-in output is returned instead of plugin output.
- A direct converter unit test passes, but `MarkItDown(...).convert()` does not use it.

Check in this order:

1. Ensure plugins are enabled: CLI conversions need `--use-plugins`; Python code needs `MarkItDown(enable_plugins=True)` or `md.enable_plugins()`.
2. Confirm `register_converters(markitdown, **kwargs)` calls `markitdown.register_converter(...)` on the supplied instance.
3. Confirm `accepts()` returns `True` for the actual `StreamInfo` guesses MarkItDown uses. Test extension, MIME type, charset, and filename hints explicitly.
4. Ensure `accepts()` restores the stream position before returning. MarkItDown asserts that `accepts()` must not change `file_stream.tell()`.
5. Review priority. Lower values are tried first. If a built-in accepts and succeeds before the plugin, register the plugin with a lower priority or make the file hints more specific.
6. If the plugin converter accepts but raises during `convert()`, MarkItDown records the failure and may try later converters. Inspect `FileConversionException.attempts` when no fallback succeeds.

## Import or Registration Warning Is Printed

MarkItDown treats plugin failures as warnings and skips the failing plugin:

- Entry point import failure: the plugin fails while `entry_point.load()` runs.
- Registration failure: the module imports, but `register_converters()` raises.

Fix import failures by checking dependency availability and entry point target spelling. Fix registration failures by keeping registration side-effect-light: instantiate converters, read optional kwargs, and avoid opening files, making network calls, or requiring credentials during registration.

If a plugin needs optional runtime configuration, accept it through `**kwargs` and make the converter decide at conversion time. For OCR-specific model kwargs and behavior, route to `../ocr-plugin/SKILL.md`.

## Stream Handling Failures

`accepts(file_stream, stream_info, **kwargs)` is allowed to peek at bytes only if it seeks back before returning. Use a `try/finally` guard:

```python
position = file_stream.tell()
try:
    probe = file_stream.read(64)
    return probe.startswith(b"FOO")
finally:
    file_stream.seek(position)
```

Do not close the stream, wrap it in text mode, or leave it partially read. `convert()` receives the same stream immediately after a positive `accepts()` call and expects to read from the original position. MarkItDown also retries converters against multiple `StreamInfo` guesses and asserts the stream position is stable between attempts.

## Priority and Override Surprises

Converter priority is numeric and lower values run first. MarkItDown sorts registrations before each conversion using a stable sort. Registrations with the same priority preserve their registration order after MarkItDown inserts new converters at the front of its registry.

Use these rules to diagnose overrides:

- If a plugin should beat generic text, HTML, or ZIP fallbacks, give it a priority lower than generic fallbacks and keep `accepts()` precise.
- If a plugin should beat a built-in for the same extension, give it a lower priority than that built-in and verify the plugin is registered after plugins are enabled.
- If a plugin is only a fallback, give it a higher priority than built-ins or make `accepts()` reject files when built-in hints are present.
- Avoid returning `True` from `accepts()` for broad MIME prefixes such as `text/` unless the converter is intentionally generic.

## CLI and Python Sanity Commands

List installed entry points:

```bash
markitdown --list-plugins
python scripts/check_plugin_package.py --list
```

Inspect one plugin and import its target module:

```bash
python scripts/check_plugin_package.py --plugin sample_plugin --import-module
```

Convert with plugins enabled:

```bash
markitdown --use-plugins document.foo
```

Convert from Python with explicit stream hints:

```python
from markitdown import MarkItDown, StreamInfo

md = MarkItDown(enable_plugins=True)
result = md.convert_stream(stream, stream_info=StreamInfo(extension=".foo"))
```

For non-plugin core conversion behavior, route to `../core-conversion/SKILL.md`. For MCP environment-variable behavior, route to `../mcp-server/SKILL.md`.
