# OCR Plugin Troubleshooting

## OCR Blocks Are Missing

Expected OCR blocks look like:

```text
*[Image OCR]
<extracted text>
[End OCR]*
```

Work through these causes in order:

1. Plugin not installed or not discovered: run `markitdown --list-plugins` or `python scripts/check_ocr_plugin.py --require-entry-point`; the list should include `ocr`.
2. Plugins not enabled: use `MarkItDown(enable_plugins=True, ...)` or CLI `--use-plugins`.
3. Missing OCR service configuration: pass both `llm_client` and `llm_model`; the plugin loads without them but OCR is skipped or standard conversion continues.
4. Unsupported source type: the OCR plugin only enhances PDF, DOCX, PPTX, and XLSX; other formats route to regular MarkItDown converters.
5. No embedded images on the accepted extraction path: the file may contain vector text, unsupported drawing objects, external references, or images stored in a way the converter does not extract.
6. LLM/API warning: the vision request may have failed, returned empty text, lacked vision support, exceeded quota, or used invalid credentials; conversion can still finish without that image's OCR text.

## Plugin Is Not Listed

Symptoms:

- `markitdown --list-plugins` does not show `ocr`.
- `python scripts/check_ocr_plugin.py --require-entry-point` exits non-zero.

Likely causes:

- `markitdown-ocr` is not installed in the active environment.
- The `markitdown` command resolves to a different Python environment than `python`.
- Package metadata is broken or hidden, so the `markitdown.plugin` entry point is unavailable.

Safe checks:

```bash
python -m pip show markitdown-ocr
python -c "import markitdown_ocr; print(markitdown_ocr.__version__)"
python scripts/check_ocr_plugin.py --require-entry-point
```

Repair by installing the plugin into the exact environment that runs MarkItDown.

## Plugin Loads But OCR Is Skipped

If `llm_client` or `llm_model` is missing, registration still succeeds but the converters receive no `LLMVisionOCRService`. In that mode, conversion should proceed without OCR blocks.

Correct Python shape:

```python
md = MarkItDown(
    enable_plugins=True,
    llm_client=client,
    llm_model="gpt-4o",
)
```

A configured client object must already know how to authenticate; do not place real credentials in skill files, logs, or examples.

## LLM API Errors Or Empty OCR Text

The OCR service catches exceptions from the OpenAI-compatible chat completion call and returns an empty OCR result with error metadata. Converters skip empty OCR results, so the most visible symptom is a missing block for one image while surrounding document content remains.

Check:

- The selected model supports vision/image input.
- Credentials, endpoint, API version, quota, and network access are valid in the user's environment.
- The prompt does not ask for output that the model refuses or cannot extract.
- The source image is readable and large enough for OCR.

When assisting a user, distinguish a per-image API warning from a fatal MarkItDown conversion failure. Do not retry with real API calls unless the user authorizes the spend/network call.

## Scanned PDFs Need Full-Page OCR

For PDFs with no extractable text, the PDF converter can render whole pages and send each page image to the OCR service. This only works when an OCR service is configured. Without `llm_client` and `llm_model`, scanned pages may produce little or no text because there is no OCR fallback.

If full-page OCR still fails, likely causes include PDF parsing/rendering errors, very large pages, image quality problems, or a model/client issue.

## Format-Specific Image Extraction Notes

- PDF: image extraction is page-based and positional; scanned PDF fallback renders full pages when text extraction is empty.
- DOCX: images are read from document relationships; OCR placeholders are swapped after Markdown conversion so markers are not escaped.
- PPTX: picture shapes, placeholder images, and grouped images are considered in slide reading order; text boxes and tables still convert separately.
- XLSX: worksheet images are emitted after each sheet table under `### Images in this sheet:`; they are not interleaved into individual rows or cells.

If a user expects OCR in an embedded object that is not a normal image for the format, explain that the regular MarkItDown conversion may still work while OCR blocks are absent.

## Converter Priority Surprises

The OCR converters register at priority `-1.0`, ahead of built-in converters at normal priority. This means accepted PDF, DOCX, PPTX, and XLSX files are tried by the OCR converter first when plugins are enabled.

If output differs from built-in MarkItDown output, verify whether plugins were enabled and whether `markitdown-ocr` is installed. To compare behavior, run a safe local conversion without plugins, then with plugins and a configured client, only after the user approves real API use.

## Real-World Triage Patterns

### Scanned PDF With Graceful Degradation

For a scanned PDF and an OpenAI-compatible vision client, configure `MarkItDown(enable_plugins=True, llm_client=..., llm_model=...)`. If OCR for one page fails, expect conversion to continue and either omit that page's OCR text or include a converter-level page processing message rather than losing all surrounding pages.

### Installed Plugin But No OCR Blocks

Classify the issue before changing code:

- Discovery failure: `ocr` missing from plugin list.
- Enablement failure: plugin installed but `enable_plugins=True` or `--use-plugins` missing.
- Configuration failure: plugin enabled but no `llm_client` or no `llm_model`.
- Format mismatch: file is not PDF, DOCX, PPTX, or XLSX.
- Image-path limitation: accepted file has images stored outside the converter's extraction path.
- API warning: vision client/model/credentials failed for one or more images.
