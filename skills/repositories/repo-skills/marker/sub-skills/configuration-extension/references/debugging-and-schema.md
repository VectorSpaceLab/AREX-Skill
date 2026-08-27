# Debugging And Schema Reference

Use this reference when a user needs to understand debug artifacts, renderer output models, JSON/chunks structures, or Marker schema ownership.

## Debug Option Expansion

When `debug` is truthy, `ConfigParser.generate_config_dict()` adds:

```python
{
    "debug_pdf_images": True,
    "debug_layout_images": True,
    "debug_json": True,
    "debug_data_folder": output_dir,
}
```

`DebugProcessor` writes under:

```text
<debug_data_folder>/<document-base-name>/
```

Potential files include:

- `pdf_page_<page_id>.png`: PDF image with line/layout overlays.
- `layout_page_<page_id>.png`: synthetic layout image with text and layout boxes.
- `blocks.json`: block/page debug data without embedded images.

The rendered metadata may include `debug_data_path` when debug data is attached to the document.

## Debug Folder Surprises

Common surprises:

- `debug_data_folder` defaults to the conversion output directory when using the common `debug` flag.
- `DebugProcessor` appends the input document base name, so files are nested one level deeper than the output directory.
- Supplying a custom processor list that omits `marker.processors.debug.DebugProcessor` can prevent debug artifacts from being produced even if debug config keys are true.
- A direct config dictionary can set debug keys independently; `debug=True` is only the common parser shortcut.

## Renderer Output Contracts

Built-in output helpers know these models:

| Renderer | Output model | Text helper behavior |
| --- | --- | --- |
| `MarkdownRenderer` | `MarkdownOutput(markdown, images, metadata)` | Saves `.md`, metadata JSON, and extracted images. |
| `HTMLRenderer` | `HTMLOutput(html, images, metadata)` | Saves `.html`, metadata JSON, and extracted images. |
| `JSONRenderer` | `JSONOutput(children, block_type, metadata)` | Serializes JSON excluding metadata for main text file; writes metadata separately. |
| `ChunkRenderer` | `ChunkOutput(blocks, page_info, metadata)` | Serializes flat chunk JSON excluding metadata for main text file; writes metadata separately. |
| `OCRJSONRenderer` | `OCRJSONOutput(...)` | Serializes OCR JSON for OCR-focused flows. |
| `ExtractionRenderer` | `ExtractionOutput(...)` | Used by structured extraction; route details to `../llm-extraction-services/`. |

`marker.output.text_from_rendered(rendered)` raises `ValueError("Invalid output type")` for custom output models it does not recognize. If a custom renderer is needed, plan a matching serializer or use the renderer result directly.

## JSON Tree Shape

JSON output is a tree. Top-level children usually represent pages. Blocks include fields such as:

- `id`: unique path-like block id.
- `block_type`: string form of the Marker block type.
- `html`: HTML for that node, possibly containing `content-ref` placeholders.
- `polygon` and `bbox`: geometry.
- `children`: nested blocks or `null`.
- `section_hierarchy`: section context for child blocks.
- `images`: extracted image data for image-like blocks.

Use `marker.output.json_to_html(block)` when a block’s `html` includes `content-ref` placeholders and full child HTML is needed.

## Chunks Shape

Chunks output flattens top-level blocks from every page and expands child HTML into each chunk. It contains:

- `blocks`: list of flat block records with `id`, `block_type`, `html`, `page`, geometry, optional section hierarchy, and optional images.
- `page_info`: page geometry keyed by page id.
- `metadata`: document metadata.

Use chunks when the user wants RAG-friendly block units. Route command construction to `../conversion-cli-api/`; keep renderer/schema questions here.

## Metadata

Built-in renderers generate metadata with:

- `table_of_contents`: detected TOC entries.
- `page_stats`: per-page text extraction method, block counts, and block metadata.
- `debug_data_path`: included when debug data was attached.

## Schema Ownership

Marker schema includes:

- `BlockTypes`: enum of document, page, text, table, figure, list, equation, form, reference, line/span/char, and group types.
- Block classes under `marker.schema.blocks`.
- Group classes under `marker.schema.groups`.
- Text classes under `marker.schema.text`.
- `Document` under `marker.schema.document`.
- `register_block_class()` and `get_block_class()` in the schema registry.

Use schema/block changes when the representation of a block type itself must change. Use processors for most block cleanup, merging, filtering, relabeling, and metadata enrichment.

## Block And Group Debugging

When output looks wrong:

1. Inspect `metadata.page_stats` for unexpected block counts or extraction methods.
2. Enable debug artifacts and inspect layout/PDF overlays.
3. For JSON output, inspect whether a block is a leaf or group by checking `children`.
4. Use `json_to_html` for a block with nested `content-ref` placeholders.
5. Check whether a custom processor ran before or after the processor that owns the observed block transformation.

## Renderer And Schema Mismatch Checks

- Markdown/HTML renderers expect block `render()` behavior to produce HTML-like content.
- JSON and chunks preserve geometry and block hierarchy more directly.
- Custom schema classes must remain compatible with the renderer’s expectations.
- Disabling image extraction changes image output fields and HTML/markdown image behavior.
- `add_block_ids`, `keep_pageheader_in_output`, and `keep_pagefooter_in_output` are renderer-level config attributes that can affect output without changing processors.
