# Troubleshooting Core Conversion

## Unsupported, Missing Dependency, or Failed Converter

Use exception type and context to separate the common failure modes:

| Symptom | Meaning | Action |
| --- | --- | --- |
| `UnsupportedFormatException` | No converter accepted the content and stream hints. | Verify the bytes are the expected file, add `StreamInfo` or CLI hints, or choose another tool. |
| `MissingDependencyException` | A converter recognized the format but an optional dependency is missing. | Install the relevant extra, such as `markitdown[pdf]`, `markitdown[docx]`, or `markitdown[all]`. |
| `FileConversionException` | At least one converter accepted the input but conversion failed. | Inspect `exc.attempts` for converter names and nested exception types/messages. |
| CLI exits non-zero before conversion | Invalid arguments or invalid hints. | Check `--mime-type` has one slash and `--charset` is recognized by Python codecs. |

`MissingDependencyException` can be nested inside `FileConversionException` because MarkItDown records converter failures while trying fallbacks.

## Safe I/O Boundaries

MarkItDown reads local files, fetches HTTP(S) URLs, resolves `file:` URIs, decodes `data:` URIs, and buffers streams with the privileges of the current process. For untrusted input:

- Use `convert_stream()` for caller-supplied bytes instead of allowing arbitrary path or URI strings through `convert()`.
- Use `convert_local()` only after the path is validated and intentionally readable.
- Use `convert_response()` when the caller needs custom HTTP authentication, retries, timeout, size limit, or allow-list checks before conversion.
- Avoid passing untrusted strings to `convert()` because URI-like prefixes trigger network, file-URI, or data-URI behavior.
- Do not enable plugins or cloud converters unless the user intentionally opts in.

## Streams and Memory

`convert_stream()` requires a binary stream. Text streams are rejected by `convert()` dispatch. MarkItDown expects seekable streams; non-seekable streams are copied fully into memory before conversion. `convert_response()` also buffers response content before conversion. For large inputs, enforce size limits upstream or write to a controlled temporary file and use `convert_local()`.

## Stdin Needs Hints

CLI stdin has no filename. If conversion fails or guesses poorly, provide explicit hints:

```bash
cat upload | markitdown --extension docx --mime-type application/vnd.openxmlformats-officedocument.wordprocessingml.document > out.md
cat page | markitdown --extension html --mime-type text/html --charset utf-8
```

API equivalent:

```python
info = StreamInfo(extension=".html", mimetype="text/html", charset="utf-8")
result = MarkItDown().convert_stream(stream, stream_info=info)
```

## Data URIs and Output Size

By default, MarkItDown truncates data URIs in generated Markdown. Use `keep_data_uris=True` or CLI `--keep-data-uris` only when the exact embedded data is required. Preserving data URIs can create very large Markdown outputs and may expose embedded binary or sensitive content.

## Audio Tooling Warning

Audio conversion depends on audio libraries and may warn that `ffmpeg` or `avconv` was not found. Install or configure the system audio tool required by the runtime if audio conversion is needed. If only text, HTML, Office, or PDF conversion is needed, the warning may be irrelevant.

## LLM Image Captioning

Image and PPTX converters can receive `llm_client`, `llm_model`, and optional `llm_prompt` through `MarkItDown(...)` or conversion kwargs. This sub-skill should not make real LLM calls. Only pass those kwargs when the user explicitly provides a model client and wants image descriptions.

## ZIP Recursion

ZIP files are converted by recursively applying MarkItDown to archive members. If a ZIP conversion fails:

- Check whether a nested file type needs an optional extra.
- Inspect the `FileConversionException.attempts` chain for the converter that accepted and failed.
- Consider extracting the archive in a controlled location and converting important members individually when you need precise failure isolation.
