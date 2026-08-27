# OCR Plugin API Reference

## Distribution And Entry Point

Installable package:

```text
markitdown-ocr
```

MarkItDown plugin entry point group and name:

```text
[project.entry-points."markitdown.plugin"]
ocr = "markitdown_ocr"
```

The importable package exports:

- `__plugin_interface_version__`
- `register_converters`
- `OCRResult`
- `LLMVisionOCRService`
- `PdfConverterWithOCR`
- `DocxConverterWithOCR`
- `PptxConverterWithOCR`
- `XlsxConverterWithOCR`

## Plugin Registration

Use the plugin through MarkItDown rather than importing and registering it manually in normal applications:

```python
from markitdown import MarkItDown

md = MarkItDown(
    enable_plugins=True,
    llm_client=client,
    llm_model="gpt-4o",
    llm_prompt="Extract all visible text.",  # optional
)
```

The plugin receives the MarkItDown constructor kwargs in `register_converters(markitdown, **kwargs)`. It reads:

- `llm_client`: OpenAI-compatible client object; required for real OCR.
- `llm_model`: model name; required for real OCR.
- `llm_prompt`: optional default prompt for image text extraction.

If both `llm_client` and `llm_model` are present, the plugin creates one `LLMVisionOCRService` and passes it to the OCR-enhanced converters. If either is missing, converters are still registered with `ocr_service=None`.

## `LLMVisionOCRService`

Constructor:

```python
LLMVisionOCRService(client, model, default_prompt=None)
```

Method:

```python
extract_text(image_stream, prompt=None, stream_info=None, **kwargs)
```

Behavior:

- Reads the image stream, detects or defaults the image content type, base64-encodes the image as a data URI, and sends one chat completion request with text plus image content.
- Uses `prompt` when provided, otherwise `default_prompt`, otherwise a built-in prompt that asks for only extracted text while preserving layout and order.
- Returns an `OCRResult` with extracted `text`, `backend_used="llm_vision"`, and optional `error`.
- If the client is `None` or an exception occurs, returns empty `text` and error metadata instead of raising to the converter.
- Seeks the image stream back to the beginning before returning.

The service expects an OpenAI-compatible client shape with `client.chat.completions.create(...)`. This sub-skill does not implement alternate client adapters.

## OCR Result Shape

`OCRResult` contains:

- `text`: extracted text or an empty string.
- `confidence`: currently optional and commonly unset for LLM vision output.
- `backend_used`: expected to be `llm_vision` for the bundled service.
- `error`: exception or configuration message when OCR did not produce text.

## OCR-Enhanced Converters

The plugin registers these converter classes at priority `-1.0`:

| Converter | Format accepted | OCR placement |
| --- | --- | --- |
| `PdfConverterWithOCR` | `.pdf` or PDF MIME types | Inline by page reading order when images are detected; full-page OCR fallback for scanned PDFs with no extracted text. |
| `DocxConverterWithOCR` | `.docx` or DOCX MIME types | Replaces image placeholders with OCR blocks while preserving document flow through HTML-to-Markdown conversion. |
| `PptxConverterWithOCR` | `.pptx` or PPTX MIME types | Adds OCR blocks for picture-like shapes in slide top-to-left order; can prefer existing LLM image descriptions when supplied. |
| `XlsxConverterWithOCR` | `.xlsx` or XLSX MIME types | Appends OCR blocks under `### Images in this sheet:` after each sheet table. |

Each converter constructor accepts:

```python
ConverterClass(ocr_service=None)
```

At conversion time, converters can also read `ocr_service` from conversion kwargs. Prefer plugin-driven registration for user workflows; direct converter instantiation is mainly useful for tests and diagnostics.

## Output Contract

OCR text is inserted as Markdown emphasis blocks:

```text
*[Image OCR]
<extracted text>
[End OCR]*
```

Downstream code should detect OCR by looking for the opening marker `*[Image OCR]` and closing marker `[End OCR]*`. Do not assume every image produces a block.

## Warning And Failure Semantics

The OCR service catches LLM/API exceptions and returns an empty result with error metadata. The converters skip empty OCR results, so conversion continues without that image's text. In user-facing troubleshooting, treat missing OCR blocks as a configuration, discovery, unsupported embedded-image path, or API-warning problem rather than as proof the whole conversion failed.

## Version Facts

Verified package facts for this generated skill:

- `markitdown-ocr` version `0.1.0` imports successfully.
- Entry point discovery reports `ocr = markitdown_ocr`.
- `LLMVisionOCRService.__init__(client, model, default_prompt=None)`.
- `LLMVisionOCRService.extract_text(image_stream, prompt=None, stream_info=None, **kwargs)`.
- OCR converters accept optional `ocr_service` and register ahead of built-ins when the plugin is enabled.
