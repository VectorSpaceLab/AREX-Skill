---
name: elements-and-metadata
description: "Understand and manipulate Unstructured Element classes, metadata,
  coordinates, data-source metadata, staging conversions, and bundled inspection
  helpers. Use when inspecting partition output JSON, preserving table metadata
  or coordinates, or converting element JSON to JSON, NDJSON, Markdown, text, or
  HTML; route raw document partitioning to partitioning and chunk composition to
  chunking."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Elements and Metadata

Use this sub-skill when a task starts from already-partitioned Unstructured elements or element JSON and needs schema inspection, metadata debugging, coordinate reasoning, or format conversion. Do not use it to partition source documents or compose chunks.

## Core Model

- Elements are instances of `unstructured.documents.elements.Element` subclasses such as `Title`, `NarrativeText`, `ListItem`, `Table`, `TableChunk`, `Image`, `Formula`, `CheckBox`, `CompositeElement`, `Header`, `Footer`, and `Text`.
- Serialized element dictionaries generally use `type`, `element_id`, `text`, and `metadata`; `CheckBox` also uses `checked`, while text elements may include `embeddings`.
- `ElementMetadata` is sparse: unset fields are omitted from `to_dict()` and JSON output. Unknown ad-hoc metadata can exist, but known fields should be preferred for portable workflows.
- `CoordinatesMetadata` requires both `points` and `system`; one without the other is invalid. Coordinate dictionaries include `points`, `system`, `layout_width`, and `layout_height`.
- `DataSourceMetadata` lives under `metadata.data_source` and supports source-level fields such as `url`, `version`, `record_locator`, dates, and permissions.

See `references/element-schema.md` for concrete JSON examples and metadata field guidance.

## Staging and Conversion

For in-process conversion, prefer `unstructured.staging.base`:

```python
from unstructured.staging.base import elements_from_json, elements_to_json, elements_to_md

elements = elements_from_json(filename="elements.json")
markdown = elements_to_md(elements, exclude_binary_image_data=True)
json_text = elements_to_json(elements, indent=2)
```

For command-line use, use the bundled helpers:

```bash
python sub-skills/elements-and-metadata/scripts/convert_elements_json.py elements.json --format markdown --output out.md
python sub-skills/elements-and-metadata/scripts/convert_elements_json.py elements.json --format ndjson --output out.ndjson
python sub-skills/elements-and-metadata/scripts/render_elements_html.py elements.json --output rendered.html
```

See `references/staging-formats.md` for JSON, NDJSON, Markdown, text, and HTML behavior.

## Table Fidelity

- Preserve `metadata.text_as_html` whenever table structure matters; Markdown and HTML conversion can use it for richer table output than plain `element.text`.
- Preserve `metadata.table_as_cells`, `table_id`, `chunk_index`, and `num_carried_over_header_rows` when reconstructing or validating split tables.
- Compact table HTML normalizes whitespace and strips cosmetic attributes, while preserving structural `rowspan` and `colspan`.
- When converting or filtering element JSON, check that `Table` and `TableChunk` elements retain both text and structural metadata.

## Coordinates

- `RelativeCoordinateSystem` uses width and height `1`; `PixelSpace` is screen-oriented with origin at the upper-left; `PointSpace` is Cartesian with origin at the lower-left.
- Conversion between coordinate systems may invert the y-axis depending on orientation. Use `element.convert_coordinates_to_new_system(new_system, in_place=False)` to inspect without mutation.
- JSON round-trips should preserve all four coordinate fields. Missing `layout_width` or `layout_height` can prevent rehydrating concrete coordinate systems.

## Debugging Flow

1. Load JSON with `elements_from_json()` or `scripts/convert_elements_json.py --inspect` to catch malformed JSON early.
2. Confirm each element has a supported `type`; unknown text-like types may be dropped by `elements_from_dicts()` if they are not mapped.
3. Inspect `metadata` sparsely: missing keys often mean unset fields, not failed serialization.
4. For coordinates, verify `points` and `system` are both present and that `layout_width`/`layout_height` match the originating page or image.
5. For tables, compare `text`, `metadata.text_as_html`, and `metadata.table_as_cells` before and after conversion.
6. For oversized `orig_elements`, image payloads, or compressed metadata, watch base64/gzip limits and prefer `exclude_binary_image_data=True` when rendering.

See `references/troubleshooting.md` for failure modes and fixes.

## Boundaries

- Raw document partitioning belongs to the `partitioning` sub-skill.
- Chunking, `CompositeElement`, `TableChunk` composition, and chunk metadata consolidation belong to the `chunking` sub-skill unless the task is only inspecting existing chunk JSON.
- Review/test artifacts should not be added to this runtime subtree.
