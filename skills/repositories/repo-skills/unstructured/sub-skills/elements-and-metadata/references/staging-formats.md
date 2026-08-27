# Staging Formats Reference

This reference covers conversion of already-partitioned Unstructured elements. It distills the package staging helpers, HTML table utilities, and the bundled conversion scripts.

## Loading Elements

Use `elements_from_json(filename=...)` or `elements_from_json(text=...)`; exactly one input source is required.

```python
from unstructured.staging.base import elements_from_json

elements = elements_from_json(filename="elements.json", encoding="utf-8")
```

`elements_from_json()` loads a JSON array of element dictionaries and rehydrates known element types. If you need to diagnose unknown element types, inspect the raw dictionaries first because unsupported types may not produce element objects through `elements_from_dicts()`.

## JSON

`elements_to_json(elements, filename=None, indent=4, encoding="utf-8")` serializes element objects to a JSON array string and optionally writes it.

Behavior to know:

- Metadata is sparse; unset metadata fields are absent.
- Coordinate precision is adjusted before serialization: `PixelSpace` coordinates are rounded to 1 decimal place and other coordinate systems to 2 decimal places.
- `metadata.orig_elements`, when present, is serialized as base64-encoded compressed JSON.

CLI helper:

```bash
python sub-skills/elements-and-metadata/scripts/convert_elements_json.py elements.json --format json --indent 2 --output normalized.json
```

## NDJSON

`elements_to_ndjson(elements, filename=None, encoding="utf-8")` serializes one element dictionary per line. This is useful for streaming and line-oriented review.

CLI helper:

```bash
python sub-skills/elements-and-metadata/scripts/convert_elements_json.py elements.json --format ndjson --output elements.ndjson
```

## Text

`elements_to_text(elements)` returns clean concatenated text, one non-empty element text per line. It drops metadata and structure.

CLI helper:

```bash
python sub-skills/elements-and-metadata/scripts/convert_elements_json.py elements.json --format text --output elements.txt
```

Use text only when layout, table structure, links, coordinates, image payloads, and IDs are not needed.

## Markdown

`elements_to_md(elements, exclude_binary_image_data=False, normalize_formula=True, formula_markdown_style="auto")` converts elements to Markdown.

Notable behavior:

- `Title` becomes a level-1 Markdown heading.
- `Table` with `metadata.text_as_html` emits the HTML table fragment.
- `Image` can emit data URI Markdown when `image_base64` is present and binary data is not excluded.
- `Formula` may be wrapped in display math depending on `formula_markdown_style` and safety checks.

CLI helper:

```bash
python sub-skills/elements-and-metadata/scripts/convert_elements_json.py elements.json --format markdown --exclude-binary-image-data --output elements.md
```

Prefer `--exclude-binary-image-data` when output size or data leakage is a concern.

## HTML

There are two common HTML paths:

1. `create_file_from_elements(..., output_format="html")` or `unstructured.partition.html.convert.elements_to_html()` for general element-to-HTML conversion.
2. Ontology rendering for elements compatible with HTML parser v2 workflows.

Bundled helpers:

```bash
python sub-skills/elements-and-metadata/scripts/convert_elements_json.py elements.json --format html --output elements.html
python sub-skills/elements-and-metadata/scripts/render_elements_html.py elements.json --output rendered.html
```

`convert_elements_json.py --format html` is the general renderer. `render_elements_html.py` adapts the repository's rendered-HTML utility and uses `unstructured.partition.html.transformations.unstructured_elements_to_ontology`; use it when the task specifically asks for rendered HTML reconstruction from element JSON.

## HTML Table Handling

`unstructured.common.html_table.HtmlTable` compacts tables by:

- selecting the first `<table>` fragment;
- preserving header-row knowledge internally;
- stripping cosmetic attributes;
- preserving structural `colspan` and `rowspan`;
- normalizing whitespace;
- converting `<th>` to `<td>` for compact uniform output.

`htmlify_matrix_of_cell_texts(matrix)` creates compact table HTML from rows of cell strings, escaping special characters and using `<br/>` for line breaks.

## Base64 Gzip Metadata

`elements_to_base64_gzipped_json()` and `elements_from_base64_gzipped_json()` support compressed element lists, especially `metadata.orig_elements` in chunk outputs.

Guardrails:

- Decompression is capped by `MAX_DECOMPRESSED_SIZE` in staging code.
- Incomplete or corrupt compressed payloads raise errors.
- Do not expand untrusted compressed payloads unless the caller expects the size and provenance.

## Choosing a Format

- Use JSON for round-trips that must preserve IDs, metadata, coordinates, and table fields.
- Use NDJSON for line-oriented processing where each element is independent.
- Use Markdown for human-readable text with simple tables, images, titles, and formulas.
- Use text for plain search/index debug output only.
- Use HTML when preserving table markup or reconstructing document-like output matters.
