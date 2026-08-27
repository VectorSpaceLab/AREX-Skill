# MarkItDown API Reference

## Imports

```python
from markitdown import (
    MarkItDown,
    StreamInfo,
    DocumentConverterResult,
    DocumentConverter,
    MissingDependencyException,
    UnsupportedFormatException,
    FileConversionException,
)
```

`MarkItDown` is the main conversion facade. Built-in converters are enabled by default; third-party plugin converters are disabled unless `enable_plugins=True` or `enable_plugins()` is called.

## Constructor

```python
md = MarkItDown(enable_builtins=None, enable_plugins=None, **kwargs)
```

Useful built-in kwargs:

- `requests_session`: custom `requests.Session`; otherwise MarkItDown creates one and sets an `Accept` header preferring Markdown, HTML, then plain text.
- `llm_client`, `llm_model`, `llm_prompt`: passed to image-related converters that can caption images; do not supply these unless the caller explicitly wants model-backed image descriptions.
- `style_map`: passed to DOCX conversion for Mammoth style mapping.
- `exiftool_path`: explicit exiftool binary path for metadata extraction; otherwise MarkItDown checks `EXIFTOOL_PATH` and common system locations.
- `docintel_endpoint` and Content Understanding kwargs are cloud conversion options; route those workflows to `../cloud-integrations/SKILL.md`.

## Core Methods

| Method | Use When | Input Behavior |
| --- | --- | --- |
| `convert(source, *, stream_info=None, **kwargs)` | General dispatch for known-safe inputs | Dispatches strings starting with `http:`, `https:`, `file:`, or `data:` to `convert_uri`; other strings and `Path` objects to `convert_local`; `requests.Response` to `convert_response`; binary streams to `convert_stream`. |
| `convert_local(path, *, stream_info=None, **kwargs)` | Trusted local filesystem path | Opens the path as bytes and seeds `StreamInfo(local_path, filename, extension)` from the path. |
| `convert_stream(stream, *, stream_info=None, **kwargs)` | Caller already has bytes | Accepts binary file-like objects. Non-seekable streams are copied into an in-memory `BytesIO` buffer before conversion. |
| `convert_uri(uri, *, stream_info=None, mock_url=None, **kwargs)` | URI decoding or fetching is intended | Supports `file:`, `data:`, `http:`, and `https:`. Unsupported schemes raise `ValueError`. |
| `convert_response(response, *, stream_info=None, **kwargs)` | Caller already fetched HTTP content | Reads `Content-Type`, `Content-Disposition`, and response URL hints, then buffers response content before conversion. |

Legacy kwargs `file_extension` and `url` still work on specific methods, but prefer `stream_info=StreamInfo(...)`. For `convert(source_as_str, url=...)` with URI-like strings, `url` is remapped internally to `mock_url`.

## StreamInfo

```python
StreamInfo(
    mimetype=None,
    extension=None,
    charset=None,
    filename=None,
    local_path=None,
    url=None,
)
```

`StreamInfo` fields are hints; all are optional. Use them when content arrives from stdin, a queue, memory, an API, or an HTTP response with weak headers.

- `extension`: include the leading dot in API code, such as `.html`, `.pdf`, or `.csv`.
- `mimetype`: use standard MIME strings, such as `text/html` or `application/pdf`.
- `charset`: useful for text-like streams, such as `utf-8`.
- `filename`, `local_path`, and `url`: can help converters that use names or URLs for special handling.
- `copy_and_update(...)`: returns a new `StreamInfo`, merging non-`None` fields from another `StreamInfo` and keyword overrides.

Example for bytes with no filename:

```python
import io
from markitdown import MarkItDown, StreamInfo

payload = b"<html><body><h1>Report</h1></body></html>"
result = MarkItDown().convert_stream(
    io.BytesIO(payload),
    stream_info=StreamInfo(extension=".html", mimetype="text/html", charset="utf-8"),
)
markdown = result.markdown
```

## Results

`DocumentConverterResult(markdown, *, title=None)` exposes:

- `markdown`: converted Markdown text.
- `title`: optional title when a converter can infer one.
- `text_content`: compatibility alias for `markdown`; assigning to it updates `markdown`.
- `str(result)`: returns `result.markdown`.

MarkItDown normalizes output line endings, strips trailing whitespace per line, and collapses runs of three or more blank lines to two blank lines before returning a result.

## URI Behavior

- `file:` URIs are converted as local files. Empty host and `localhost` are accepted; other netlocs raise `ValueError`.
- `data:` URIs are parsed into bytes. MIME type and `charset` attributes seed `StreamInfo`; explicit `stream_info` can override or supplement them.
- `http:` and `https:` URIs are fetched with the configured `requests_session`, `raise_for_status()` is called, then the response is converted.
- Prefer `convert_response()` when the caller needs custom authentication, retries, timeouts, or response size checks before conversion.

## Converter Selection

MarkItDown builds stream-info guesses from caller hints, file extensions, MIME types, Magika content detection, and text charset detection. It then tries registered converters by priority. A converter's `accepts(file_stream, stream_info, **kwargs)` must leave the stream position unchanged; `convert(file_stream, stream_info, **kwargs)` returns a `DocumentConverterResult`.

If a converter accepts but fails, MarkItDown records the failed attempt and tries later converters. If none succeeds and at least one accepted converter failed, it raises `FileConversionException`; if no converter attempted conversion, it raises `UnsupportedFormatException`.

## Exceptions

```python
try:
    result = MarkItDown().convert_stream(stream, stream_info=info)
except MissingDependencyException as exc:
    # install the relevant extra, such as markitdown[pdf] or markitdown[docx]
    raise
except UnsupportedFormatException as exc:
    # no converter accepted the content/hints
    raise
except FileConversionException as exc:
    # converter accepted the input but conversion failed
    for attempt in exc.attempts or []:
        converter_name = type(attempt.converter).__name__
```

`MissingDependencyException` is used by built-in converters when a recognized format needs an optional dependency that is not installed. In the full conversion loop this may surface as a `FileConversionException` if the accepting converter fails and no fallback succeeds, so inspect `FileConversionException.attempts` for nested missing-dependency causes.
