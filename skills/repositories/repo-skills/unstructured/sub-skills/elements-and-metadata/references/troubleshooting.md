# Elements and Metadata Troubleshooting

Use this guide when element JSON fails to load, metadata appears missing, or converted output loses structure.

## Malformed Element JSON

Symptoms:

- `json.JSONDecodeError` while loading a file.
- Top-level JSON is an object instead of an array.
- Elements are missing expected keys such as `type`, `text`, or `metadata`.

Checks:

```bash
python sub-skills/elements-and-metadata/scripts/convert_elements_json.py elements.json --inspect
```

Fixes:

- Ensure the top-level payload is a JSON array of element objects.
- Use UTF-8 unless the caller explicitly provides another encoding.
- Inspect raw dictionaries before calling `elements_from_json()` when the file may contain unknown element types.
- Add an empty object for missing `metadata` only if the downstream path requires that key; Unstructured can construct empty `ElementMetadata` when `metadata` is absent or null in many paths.

## Unknown Element Type

Symptoms:

- Rehydrated element count is smaller than the input dictionary count.
- Output silently omits records with custom `type` values.

Cause:

`elements_from_dicts()` only creates text elements for types known to `TYPE_TO_TEXT_ELEMENT_MAP`, plus `CheckBox`. Unknown types are not converted.

Fixes:

- Preserve the raw dictionaries if custom element types must not be dropped.
- Map custom text-like records to a supported type such as `NarrativeText`, `Title`, `ListItem`, `Table`, or `Text` before rehydration.
- Use `--inspect` to report input types before conversion.

## Missing Metadata Fields

Symptoms:

- Expected metadata keys are absent in JSON.
- DataFrame or CSV output has empty columns.

Cause:

`ElementMetadata.to_dict()` is sparse and omits unset values, empty lists, empty dicts, and debug-only fields.

Fixes:

- Treat absent metadata as unset rather than failed serialization.
- Check `element.metadata.fields` for populated fields and `element.metadata.known_fields` for populated known fields.
- Do not expect `detection_origin` in normal JSON output; it is debug metadata.

## Coordinate Inconsistency

Symptoms:

- `ValueError: Coordinates points should not exist without coordinates system and vice versa.`
- Rehydrated coordinates have `system=None`.
- Boxes appear vertically flipped after conversion.

Checks:

- Each `metadata.coordinates` object should contain `points`, `system`, `layout_width`, and `layout_height`.
- `system` should be `RelativeCoordinateSystem`, `PixelSpace`, `PointSpace`, or `CoordinateSystem`.
- Concrete coordinate systems need layout dimensions to rehydrate.

Fixes:

- Restore missing `layout_width` and `layout_height` from the source page/image when available.
- Preserve point order from the source. Do not sort points unless the caller explicitly asks for bounding boxes.
- Account for orientation: `PixelSpace` has a top-left origin; `PointSpace` has a bottom-left origin.
- Use non-mutating conversion first: `element.convert_coordinates_to_new_system(new_system, in_place=False)`.

## Table Structure Lost

Symptoms:

- Markdown/text output contains flattened table text only.
- HTML no longer contains row/column structure.
- Split table chunks cannot be stitched or audited.

Checks:

- Confirm `type` is `Table` or `TableChunk`.
- Confirm `metadata.text_as_html` is present for HTML structure.
- Confirm `metadata.table_as_cells`, `table_id`, `chunk_index`, and `num_carried_over_header_rows` are preserved when chunked table reconstruction matters.

Fixes:

- Prefer JSON or HTML output over text when table fidelity matters.
- Do not strip `metadata` during filtering.
- Use `--format markdown` or `--format html`; both can preserve `text_as_html` better than plain text.
- Validate `rowspan` and `colspan` after any HTML normalization.

## Base64, Gzip, and Payload Size

Symptoms:

- Compressed `orig_elements` fails to decompress.
- Conversion produces very large Markdown or HTML files.
- Image-heavy element JSON is slow to load or write.

Causes:

- `metadata.orig_elements` may contain base64-encoded compressed element JSON.
- `image_base64` can dominate output size.
- Decompression has a maximum size guard.

Fixes:

- Use `--exclude-binary-image-data` for Markdown and HTML conversion when embedded images are not required.
- Do not expand compressed metadata from untrusted sources unless required.
- If decompression exceeds the configured limit, ask whether the workflow really needs `orig_elements` or image payloads.

## Output Encoding

Symptoms:

- Unicode characters are corrupted.
- Formula symbols or table text look wrong after writing files.

Fixes:

- Use UTF-8 by default.
- Pass `--encoding` in bundled scripts when the caller requires another encoding.
- For formulas, decide whether Markdown should normalize Unicode math symbols or emit plain text.

## Safe Debugging Pattern

```python
import json
from unstructured.staging.base import elements_from_dicts

with open("elements.json", encoding="utf-8") as file:
    payload = json.load(file)

assert isinstance(payload, list)
print({item.get("type") for item in payload if isinstance(item, dict)})

# Rehydrate only after raw schema checks.
elements = elements_from_dicts(payload)
print(len(payload), "input records ->", len(elements), "rehydrated elements")
```
