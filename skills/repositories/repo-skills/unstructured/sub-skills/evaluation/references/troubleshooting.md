# Evaluation Troubleshooting

## Missing Optional Dependencies

Symptoms:

- `ModuleNotFoundError` or `ImportError` for `pandas`, `numpy`, `rapidfuzz`, `bs4`, `lxml`, or table helpers.
- Importing `unstructured.metrics.evaluate` fails because `torch` is unavailable.

Actions:

- For text extraction, element type, and table metrics, install the core package dependencies used by the metrics modules.
- If torch is missing and the task is not object detection, avoid `unstructured.metrics.evaluate` and use direct modules or `scripts/evaluate_elements_pair.py`.
- If the task is object detection, install a torch build appropriate for the user's platform and verify `import torch` before running the object detection calculators.

## Mismatched Filenames

Symptoms:

- Batch calculators skip files.
- Logs mention missing prediction or ground truth files.
- Metrics output has fewer rows than expected.

Actions:

- Keep prediction and gold files paired by matching stems.
- For text extraction, prediction `sample.pdf.json` pairs with gold `sample.pdf.txt`.
- For element type and table structure, prediction `sample.pdf.json` pairs with gold `sample.pdf.json`.
- For object detection, prediction discovery uses `analysis/<document-stem>/layout_dump/object_detection.json`; gold matching uses document filenames such as `sample.pdf.json`.
- Check connector subdirectories: calculators may treat a path component as `connector`, but matching still depends on the relative file name logic.

## Malformed Output JSON

Symptoms:

- `json.JSONDecodeError`.
- Element type frequency fails on `metadata` access.
- Pair helper reports that a JSON file is not an element list.

Actions:

- Confirm the file is a JSON array of element dictionaries, not JSON Lines and not a wrapper object.
- Confirm each element has at least `type`, `text`, and `metadata` keys when the metric needs them.
- If the file was generated from element objects, route to the elements-and-metadata sub-skill and use staging helpers such as `elements_to_json` and `elements_from_json` correctly.
- Keep test fixtures self-contained; do not depend on a source checkout's example fixture paths at runtime.

## Text Extraction Scores Look Wrong

Symptoms:

- `cct-accuracy` is unexpectedly near zero.
- `cct-%missing` is high even though prediction has lots of text.
- Accuracy is low for a much shorter or much longer prediction.

Actions:

- Inspect whether the prediction JSON contains element text in the expected `text` fields.
- Check whether headers, footers, OCR noise, or page separators dominate the prediction.
- Compare clean-concatenated text manually for a small pair before running a full batch.
- Remember that missing-text does not penalize extra duplicated text in the same way edit-distance accuracy does.
- A large prediction/source byte-length mismatch can cause the batch calculator to bypass expensive edit distance and assign a low sentinel accuracy.

## Element Type Mismatch

Symptoms:

- `element-type-accuracy` is low while text extraction scores are acceptable.
- Changes in `Title`, `NarrativeText`, `ListItem`, or `Table` frequency drive regressions.

Actions:

- Compare frequency dictionaries by `(type, category_depth)`, not just total element count.
- Determine whether the mismatch is a true category regression or only a `category_depth` difference.
- Confirm gold outputs were produced with compatible partitioning assumptions and element schemas.

## Table HTML or Cell Schema Mismatch

Symptoms:

- Table metrics are all zero or `nan` unexpectedly.
- Errors mention HTML conversion, missing table data, missing `row_nums`, or missing `column_nums`.
- Tables are detected but row/column alignment metrics are poor.

Actions:

- Choose the correct prediction source: `source_type="html"` for `metadata.text_as_html`, or `source_type="cells"` for `metadata.table_as_cells`.
- For prediction cells, use Deckerd-style dictionaries with `x`, `y`, `w`, `h`, and `content`.
- For Table Transformer cells, convert from `row_nums`, `column_nums`, and `cell text` before comparing with cell-based metrics.
- Verify gold `Table` elements store structured cell content in the `text` field when using the table structure evaluator.
- If `text_as_html` is present but lacks parseable `<table>` markup, use cell data instead or regenerate outputs with table structure enabled.
- Inspect row/column index scores separately from content scores; high content with low index accuracy usually means shifted or spanned cells.

## Object Detection Device or Tensor Issues

Symptoms:

- Importing object detection metrics fails with torch errors.
- Runtime errors mention tensor dtype, device mismatch, shape mismatch, class labels, IoU, or empty predictions.

Actions:

- Verify `torch` imports before importing `unstructured.metrics.evaluate` for object detection.
- Keep all prediction and target tensors on the same device.
- Confirm prediction and ground truth JSON agree on `object_detection_classes`.
- Confirm bounding boxes use the expected coordinate format and numeric arrays can convert to tensors.
- Start with a single small document pair through `ObjectDetectionEvalProcessor.from_json_files(...)` before running batch calculators.
- If the user only needs partition/table evaluation, skip object detection instead of installing or debugging torch.

## Empty or Partial Batch Results

Symptoms:

- Output TSVs exist but contain no rows or only aggregate headers.
- Calculators log failures but continue.

Actions:

- Use `visualize_progress=False` and `display_agg_df=False` in automation, but keep logging visible during debugging.
- Run one pair through the bundled helper or direct processor before broad batch execution.
- Verify the selected file extension, relative path, and gold directory pairing.
- Inspect skipped-file warnings; calculator wrappers omit failed rows rather than aborting the whole batch.
