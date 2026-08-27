---
name: visualization
description: "Routes LayoutParser box and text rendering workflows on images."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# Visualization

Use this sub-skill when the task is to render LayoutParser blocks, OCR text, or
region ids onto an image.

## What belongs here

- `draw_box`
- `draw_text`
- color maps, alpha handling, box widths, and font settings
- layout overlays for detected regions or OCR text
- vertical text, background text boxes, and combined layout+text views

## What does not belong here

- Shape math or region filtering: use `layout-objects`
- Loading layouts from files: use `layout-io`
- OCR extraction itself: use `ocr`
- Model inference: use `layout-models`

## Read these files

- `references/guide.md` for parameter behavior, image-canvas rules, and troubleshooting notes
- `../layout-objects/SKILL.md` when the task starts with a geometry object
- `../ocr/SKILL.md` when the task starts with OCR output

## Fast path

1. Make sure your layout blocks already have the right coordinates and text.
2. Pick `draw_box()` for region overlays or `draw_text()` for OCR text views.
3. Use a color map if category colors matter.
4. Keep alpha values within range and list lengths aligned with the layout.
5. If the page is tight, switch `arrangement` between left/right and up/down.

## Common user requests

- "Draw boxes on the page"
- "Overlay the OCR text"
- "Show ids and categories"
- "Render the layout next to the page image"
- "Use vertical text"

## Minimal smoke

Use the bundled root smoke script to exercise both box and text rendering on a
synthetic image:

```bash
python ../../scripts/smoke_layoutparser_core.py
```

## Failure clues

- List-length mismatches usually mean per-block styling inputs are the wrong
  length.
- Empty text blocks are skipped by `draw_text()`.
- Font problems usually come from a custom `font_path`; fall back to the
  bundled default first.

## Output discipline

When answering, name the image mode, the layout shape, and the styling inputs
that were used. If a region should be highlighted differently, say whether it
needs a different color map, width, alpha, or text placement.
