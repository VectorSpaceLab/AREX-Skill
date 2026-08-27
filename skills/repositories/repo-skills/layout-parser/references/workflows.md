# LayoutParser Workflow Notes

These are the cross-cutting workflows that stitch multiple sub-skills together.
Use them as a bridge when a task spans geometry, I/O, visualization, OCR, and
layout models.

## 1) Deep document layout parsing

Typical flow:

1. Load an image with OpenCV or PIL.
2. Use `AutoLayoutModel` or a backend model to detect layout blocks.
3. Filter and sort the output with `Layout`, `Interval`, and `filter_by()`.
4. Crop blocks and run OCR with `TesseractAgent` or `GCVAgent`.
5. Render the result with `draw_box()` or `draw_text()`.

Use this when the user wants an end-to-end document image pipeline, especially
for papers, reports, or page-region parsing.

## 2) OCR table parsing

Typical flow:

1. Run OCR on a scanned table or text-heavy page.
2. Inspect the returned `Layout` or response object.
3. Split the OCR output into rows/regions with intervals and `filter_by()`.
4. Use `generalized_connected_component_analysis_1d()` or custom row grouping
   to merge fragments.
5. Export the result to a dataframe or CSV.

Use this when the user wants structured data from OCR, not just raw text.

## 3) COCO-style layout annotation loading

Typical flow:

1. Read COCO annotations from a local JSON file.
2. Convert each box into `TextBlock(Rectangle(...))` objects.
3. Visualize the converted layout with `draw_box()`.
4. Optionally merge with model predictions or export to a dataframe.

This pattern is useful for the notebook that loads PubLayNet-style layouts.
The bundled `../sub-skills/layout-io/scripts/coco_layout_helpers.py` module packages the same recipe for reuse.

## 4) Model customization with external annotations

The repository also contains a Label Studio demo that downloads external
annotation assets and auxiliary paper images. Treat that workflow as
reference-only unless the user explicitly wants a networked setup.

## When to switch sub-skills

- Geometry, shape ops, or layout grouping: `layout-objects`
- JSON/CSV/PDF loading or layout export: `layout-io`
- Box/text rendering: `visualization`
- `lp://` detection model wrappers and backend selection: `layout-models`
- OCR wrappers and saved-response parsing: `ocr`
