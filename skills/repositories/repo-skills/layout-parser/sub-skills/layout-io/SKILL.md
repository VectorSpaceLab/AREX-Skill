---
name: layout-io
description: "Routes LayoutParser JSON, CSV, dataframe, PDF, and
  annotation-loading workflows."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# Layout I/O

Use this sub-skill when the user starts with files, tables, or PDFs and wants a
`Layout` object back.

## What belongs here

- `load_json`, `load_dict`
- `load_csv`, `load_dataframe`
- `load_pdf`
- `page_data`, `block_type`, and serialized textblock fields
- COCO-style conversion patterns that become layout objects before rendering

## What does not belong here

- Shape math and `Layout` transforms: use `layout-objects`
- `draw_box` / `draw_text`: use `visualization`
- OCR engine wrappers and response parsing: use `ocr`
- `lp://` model zoo paths and model inference: use `layout-models`

## Read these files

- `references/guide.md` for file-format rules, PDF behavior, and troubleshooting notes
- `scripts/coco_layout_helpers.py` when you need a reusable COCO-to-Layout conversion helper
- `../layout-objects/SKILL.md` when you need to filter, sort, or transform the loaded layout
- `../visualization/SKILL.md` when you need to show the loaded layout on an image

## Fast path

1. Decide whether the source is JSON, CSV, dataframe, or PDF.
2. Make sure the serialized schema still contains `block_type` and any needed
   textblock metadata.
3. Load the data into a `Layout`.
4. If the task is PDF-specific, inspect page dimensions in `page_data` before
   drawing or cropping.
5. Preserve page order when you export page-level layouts.

## Common user requests

- "Load a LayoutParser JSON file"
- "Convert a CSV of boxes into a layout"
- "Parse a PDF into token boxes"
- "Read layout annotations and visualize them"
- "Turn COCO annotations into LayoutParser blocks"

## Minimal smoke

Use the bundled root smoke script to confirm the I/O layer and the synthetic
round-trips:

```bash
python ../../scripts/smoke_layoutparser_core.py
```

## Failure clues

- Missing `block_type` means the serialized data cannot be routed back to a
  concrete block class.
- Quadrilateral CSV values in a `points` column must parse back to Python lists;
  if they stay as strings, pre-parse or use JSON.
- A PDF page with no tokens is still a valid result.
- `load_pdf(..., load_images=True)` depends on the PDF image renderer stack and
  may need poppler.

## Output discipline

When answering, be explicit about the input format and the fields that must be
preserved. If the user wants a local helper for annotation conversion, keep it
inside the generated skill tree rather than depending on the original notebook.
