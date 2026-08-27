# OCR Plugin Workflows

## What The Plugin Adds

`markitdown-ocr` is a MarkItDown plugin that registers OCR-enhanced converters for PDF, DOCX, PPTX, and XLSX. The converters use an OpenAI-compatible vision client supplied through the same `llm_client` and `llm_model` kwargs used by MarkItDown image descriptions.

The plugin has no bundled LLM client and does not perform OCR unless both a client object and model name are provided. With no client/model, plugin discovery and converter registration can still succeed, and standard conversion should continue without OCR blocks.

## Install And Discover

Install the plugin into the active MarkItDown environment:

```bash
python -m pip install markitdown-ocr
```

Install a compatible client package only when real OCR will be used:

```bash
python -m pip install openai
```

Check discovery without credentials or LLM calls:

```bash
markitdown --list-plugins
python scripts/check_ocr_plugin.py --require-entry-point
```

The expected MarkItDown plugin entry point is:

```text
ocr = markitdown_ocr
```

If `ocr` is not listed, the plugin package is not installed in the environment that runs MarkItDown, or the environment's package metadata is not visible.

## Safe No-Credential Probe

From this sub-skill directory, run:

```bash
python scripts/check_ocr_plugin.py --require-entry-point --format pdf
python scripts/check_ocr_plugin.py --format docx
python scripts/check_ocr_plugin.py --format pptx
python scripts/check_ocr_plugin.py --format xlsx
```

These checks import the package, inspect the `markitdown.plugin` entry point, instantiate the selected converter without an OCR service, and verify that the converter accepts the selected extension. They intentionally do not open documents, call `MarkItDown.convert`, or contact an LLM.

Use `--client-module` only to verify that a client package import is available:

```bash
python scripts/check_ocr_plugin.py --client-module openai --model gpt-4o
```

This still does not instantiate a real client or call an API. The `--model` value is recorded as configuration intent only.

## Python API Usage

Real OCR requires the user to provide an OpenAI-compatible vision client and model:

```python
from markitdown import MarkItDown
from openai import OpenAI

md = MarkItDown(
    enable_plugins=True,
    llm_client=OpenAI(),
    llm_model="gpt-4o",
)
result = md.convert("document_with_images.pdf")
print(result.markdown)
```

For specialized extraction instructions, pass `llm_prompt`:

```python
md = MarkItDown(
    enable_plugins=True,
    llm_client=OpenAI(),
    llm_model="gpt-4o",
    llm_prompt="Extract all visible text and preserve table-like line breaks.",
)
```

Do not invent credentials or run the conversion on behalf of the user unless they explicitly provide a configured client and approve API use.

## CLI Usage

The verified core `markitdown` CLI in this checkout exposes `--use-plugins` and `--list-plugins`, but it does not expose generic `llm_client` or `llm_model` flags. Use CLI commands to verify plugin discovery and plugin enablement:

```bash
markitdown --list-plugins
markitdown document.pdf --use-plugins
```

For real OCR that requires a configured OpenAI-compatible vision client and model, prefer the Python API shown above unless the user is running a newer wrapper that explicitly documents client/model CLI flags. For safe diagnostics, prefer `markitdown --list-plugins` and `scripts/check_ocr_plugin.py`.

## Supported Formats

- PDF: embedded images are OCR'd inline near surrounding page text; scanned PDFs with no extractable text can be rendered as full-page images for OCR; malformed PDFs can fall back to page rendering when possible.
- DOCX: document images are extracted from part relationships; OCR blocks are inserted into the converted Markdown flow after HTML placeholder handling.
- PPTX: picture shapes, image placeholders, and grouped images can be processed in slide reading order; an existing LLM image description may be tried before OCR fallback.
- XLSX: worksheet images are extracted per sheet and listed under `### Images in this sheet:` after the sheet table instead of being interleaved into rows.

Unsupported file types should be handled by the usual MarkItDown converters rather than this plugin.

## Output Blocks

Inserted OCR text uses this block format:

```text
*[Image OCR]
<extracted text>
[End OCR]*
```

If OCR service configuration is missing, the image has no extractable OCR result, or an API call fails, the output may contain no OCR block for that image.

## Converter Priority And Fallback

When plugins are enabled, `markitdown-ocr` registers OCR-enhanced PDF, DOCX, PPTX, and XLSX converters at priority `-1.0`, ahead of built-in converters that normally use priority `0.0`. Lower priority numbers are tried first in MarkItDown, so the OCR converters get the first chance to accept those formats.

Fallback behavior is intentionally conservative:

- No `llm_client` or no `llm_model`: converters register without an OCR service and perform standard or near-standard conversion.
- LLM extraction returns empty text: no OCR block is inserted for that image.
- LLM/API extraction fails inside the OCR service: the service returns an empty OCR result with error metadata; conversion continues.
- A converter cannot extract images from a particular embedded-image path: surrounding document text should still be converted when the underlying format parser succeeds.
