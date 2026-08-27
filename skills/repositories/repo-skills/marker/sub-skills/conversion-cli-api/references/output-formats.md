# Output formats

Marker can render converted content as Markdown, HTML, JSON, or chunks. OCR-only conversion returns OCR JSON regardless of the requested renderer.

## Markdown

Select with `--output_format markdown` or leave the default.

Markdown output includes:

- Document text with headings and paragraphs.
- Markdown tables.
- LaTeX equations fenced with `$$` where detected.
- Code fenced with triple backticks.
- Footnote superscripts.
- Image links when image extraction is enabled.

Saved files usually include `{basename}.md`, `{basename}_meta.json`, and extracted images in the same output folder. Use `--disable_image_extraction` to suppress image files and image links.

## HTML

Select with `--output_format html`.

HTML output uses:

- `img` tags for extracted images.
- `<math>` tags for equations.
- `pre` tags for code.
- Block IDs when configured through renderer options such as `add_block_ids`.

Saved files usually include `{basename}.html`, `{basename}_meta.json`, and extracted images.

## JSON

Select with `--output_format json`.

JSON output is a tree. Top-level children represent pages, and each page/block can contain child blocks. Common fields include:

| Field | Meaning |
| --- | --- |
| `id` | Stable block path-like identifier such as `/page/0/Text/1`. |
| `block_type` | Type such as `Page`, `SectionHeader`, `Text`, `Table`, `Figure`, `Equation`, or `Code`. |
| `html` | HTML for the block, often with `content-ref` placeholders for children. |
| `polygon` | Four-corner page/block coordinates in clockwise order from top left. |
| `children` | Nested child blocks or null. |
| `section_hierarchy` | Heading context for non-page child blocks. |
| `images` | Base64 image payloads for blocks that carry images. |

Use `marker.output.json_to_html(block)` when a future agent needs to replace a JSON block’s `content-ref` tags with child HTML.

## Chunks

Select with `--output_format chunks`.

Chunks output is JSON designed for retrieval and downstream chunking. It flattens top-level blocks into a list and includes full HTML inside each block, so callers do not need to recursively traverse the JSON tree to reconstruct block content.

Chunk output also includes page-level information such as bounding boxes and polygons.

## OCR JSON

Select `OCRConverter` with `--converter_cls marker.converters.ocr.OCRConverter` or the Python `OCRConverter` class.

OCR JSON includes page, line, equation, and optionally character-level structures. Use `--keep_chars` or `keep_chars=True` to preserve character boxes when available.

## Metadata

All saved outputs include `{basename}_meta.json`. Metadata includes fields such as:

- `table_of_contents` entries with title, heading level, page id, and polygon.
- `page_stats` with page ids and text extraction method details.
- Additional renderer/converter diagnostics depending on configuration.

When debugging conversion quality, compare main output with metadata and, if `--debug` was used, debug images and debug JSON.
