---
name: core-conversion
description: "Convert files, streams, paths, URIs, and HTTP responses to
  Markdown with the MarkItDown Python API and CLI."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Core Conversion

Use this sub-skill when a task needs offline MarkItDown conversion through the Python API or `markitdown` CLI: local files, `Path` objects, binary streams, `file:`, `data:`, `http:` or `https:` URIs, and `requests.Response` objects.

## Start Here

- For Python entry points, result objects, stream hints, URI handling, and exception handling, read [references/api-reference.md](references/api-reference.md).
- For shell usage, stdin conversion, output files, stream hints, plugin listing, and data URI preservation, read [references/cli-reference.md](references/cli-reference.md).
- For built-in converter coverage and optional dependency extras, read [references/formats-and-dependencies.md](references/formats-and-dependencies.md).
- For unsupported formats, missing extras, failing converters, I/O boundaries, stream buffering, audio tool warnings, and large embedded data, read [references/troubleshooting.md](references/troubleshooting.md).
- To smoke-test the installed package safely from any directory, run `python scripts/convert_smoke.py --check-import` or `python scripts/convert_smoke.py` from this sub-skill directory.

## Routing Boundaries

- Use this sub-skill for `MarkItDown`, `StreamInfo`, `DocumentConverterResult`, `DocumentConverter`, `convert`, `convert_local`, `convert_stream`, `convert_uri`, `convert_response`, the `markitdown` CLI, built-in converters, local fixtures, and conversion errors.
- Route Azure Document Intelligence or Azure Content Understanding conversion to `../cloud-integrations/SKILL.md`.
- Route OCR plugin usage to `../ocr-plugin/SKILL.md`.
- Route custom converter or plugin authoring to `../plugin-development/SKILL.md`.
- Route MCP serving to `../mcp-server/SKILL.md`.
- Do not make real LLM, cloud, or external API calls from this sub-skill; document required kwargs only.

## Safe Conversion Pattern

1. Choose the narrowest API: `convert_local` for trusted local paths, `convert_stream` for caller-owned bytes, `convert_uri` only when URI fetching or URI decoding is intended, and `convert_response` when an HTTP client already fetched the response.
2. Add `StreamInfo(extension=..., mimetype=..., charset=...)` when bytes have no reliable filename, content type, or charset.
3. Capture `result.markdown`; use `result.title` when a converter provides a title, and `result.text_content` only for compatibility with older code.
4. Preserve embedded data URIs only when explicitly needed with `keep_data_uris=True` or CLI `--keep-data-uris`.
5. Catch `MissingDependencyException`, `UnsupportedFormatException`, and `FileConversionException` separately so users know whether to install an extra, choose another tool, or inspect converter-specific failures.
