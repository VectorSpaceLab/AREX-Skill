# Element Schema Reference

This reference summarizes the element and metadata shapes used by Unstructured staging JSON, distilled from the package element model, coordinate model, staging helpers, and related behavior tests.

## Minimal Element JSON

A typical serialized text element has this shape:

```json
{
  "type": "Title",
  "element_id": "8f2d5f2a2d99406aa5f7c7bb9465c879",
  "text": "Quarterly Report",
  "metadata": {
    "filename": "report.pdf",
    "filetype": "application/pdf",
    "page_number": 1
  }
}
```

Important details:

- `type` maps to an element class through `TYPE_TO_TEXT_ELEMENT_MAP`. Examples include `Title`, `NarrativeText`, `ListItem`, `Table`, `TableChunk`, `Image`, `Formula`, `Header`, `Footer`, `PageBreak`, and `CompositeElement`.
- `element_id` is a string. If no ID exists in memory, accessing `element.id` generates a UUID; `id_to_hash(sequence_number)` can replace it with a deterministic hash.
- `text` exists on all elements, including non-text subclasses, and may be an empty string.
- `metadata` is sparse: unset fields are absent from serialized output.

## CheckBox Element JSON

`CheckBox` is not a text element and stores its state separately:

```json
{
  "type": "CheckBox",
  "element_id": "checkbox-1",
  "text": "",
  "checked": true,
  "metadata": {
    "page_number": 2
  }
}
```

## Coordinates Metadata

Coordinates must include both points and a coordinate system. A dictionary with only one side is invalid when rehydrated.

```json
{
  "type": "NarrativeText",
  "element_id": "para-1",
  "text": "A paragraph on the first page.",
  "metadata": {
    "page_number": 1,
    "coordinates": {
      "points": [[72.0, 720.0], [540.0, 720.0], [540.0, 690.0], [72.0, 690.0]],
      "system": "PointSpace",
      "layout_width": 612.0,
      "layout_height": 792.0
    }
  }
}
```

Coordinate systems:

- `RelativeCoordinateSystem`: width and height are `1`; Cartesian orientation.
- `PixelSpace`: image pixel coordinates; screen orientation with origin at the upper-left.
- `PointSpace`: PDF-style points; Cartesian orientation with origin at the lower-left.
- `CoordinateSystem`: generic finite plane when width and height are supplied.

Conversion rules are orientation-aware. Moving between screen and Cartesian systems can invert y-values.

## Data Source Metadata

Data-source metadata is nested under `metadata.data_source`:

```json
{
  "type": "NarrativeText",
  "element_id": "record-1",
  "text": "Customer note text.",
  "metadata": {
    "data_source": {
      "url": "https://example.invalid/records/123",
      "version": "v4",
      "record_locator": {"collection": "tickets", "id": "123"},
      "date_created": "2024-01-05T12:00:00Z",
      "date_modified": "2024-02-10T12:00:00Z",
      "date_processed": "2024-02-11T09:30:00Z",
      "permissions_data": [{"principal": "analyst", "permission": "read"}]
    }
  }
}
```

Only supported fields are used by `DataSourceMetadata.from_dict()`. Values inside `record_locator` and `permissions_data` must be JSON-serializable.

## Common Metadata Fields

Frequently useful known metadata fields include:

- File/source: `filename`, `file_directory`, `filetype`, `last_modified`, `attached_to_filename`, `url`.
- Layout: `page_number`, `page_name`, `parent_id`, `category_depth`, `coordinates`.
- Language and links: `languages`, `links`, `link_texts`, `link_urls`, `link_start_indexes`.
- Tables: `text_as_html`, `table_as_cells`, `table_extraction_method`, `table_id`, `chunk_index`, `num_carried_over_header_rows`.
- Images: `image_path`, `image_url`, `image_base64`, `image_mime_type`.
- Email: `sent_from`, `sent_to`, `subject`, `cc_recipient`, `bcc_recipient`, `email_message_id`, `signature`.
- Audio: `segment_start_seconds`, `segment_end_seconds`.
- Enrichment/debug: `embeddings`, `enrichment_origins`, `detection_class_prob`.

Debug-only fields such as `detection_origin` are omitted from normal metadata serialization unless debug metadata is enabled.

## Table Element Example

Preserve table metadata when downstream tasks need structure:

```json
{
  "type": "Table",
  "element_id": "table-1",
  "text": "Region Revenue North 10 South 20",
  "metadata": {
    "page_number": 3,
    "text_as_html": "<table><tr><td>Region</td><td>Revenue</td></tr><tr><td>North</td><td>10</td></tr><tr><td>South</td><td>20</td></tr></table>",
    "table_as_cells": [
      {"row_index": 0, "col_index": 0, "content": "Region"},
      {"row_index": 0, "col_index": 1, "content": "Revenue"},
      {"row_index": 1, "col_index": 0, "content": "North"},
      {"row_index": 1, "col_index": 1, "content": "10"}
    ],
    "coordinates": {
      "points": [[50, 100], [550, 100], [550, 220], [50, 220]],
      "system": "PixelSpace",
      "layout_width": 600,
      "layout_height": 800
    }
  }
}
```

`metadata.text_as_html` is compact HTML. The table helper preserves structural `rowspan` and `colspan` but strips cosmetic attributes and normalizes whitespace.

## Programmatic Inspection

```python
from unstructured.staging.base import elements_from_json

elements = elements_from_json(filename="elements.json")
for element in elements:
    print(element.category, element.id, element.text[:80])
    if element.metadata.coordinates:
        print(element.metadata.coordinates.to_dict())
    if element.metadata.text_as_html:
        print(element.metadata.text_as_html)
```

For dictionaries rather than element objects, load with `json.load()` and inspect `item["metadata"]` directly before rehydration. Direct dictionary inspection is useful when unknown element types or malformed metadata may be present.
