# Metrics Reference

## Evidence Base

This guidance is distilled from the package metrics modules, metrics behavior tests, sample evaluation fixtures, and package metadata. Installed package inspection verified imports for core metrics modules; object detection evaluation was intentionally not exercised because it pulls torch.

## Dependencies and Import Boundaries

- Core metric modules use `numpy`, `pandas`, `rapidfuzz`, `beautifulsoup4`, and table helpers from the Unstructured package.
- `unstructured.metrics.evaluate` imports `ObjectDetectionEvalProcessor`, which imports `torch`; avoid importing it in minimal environments unless object detection metrics are needed or torch is installed.
- The bundled `scripts/evaluate_elements_pair.py` imports direct text, element-type, and table helpers rather than `unstructured.metrics.evaluate` to keep ordinary comparisons lightweight.
- Table HTML conversion can depend on HTML parsing and table conversion helpers; malformed HTML may score as a table failure rather than a parser success.

## Text Extraction Metrics

Use text extraction metrics when the prediction is Unstructured output JSON or clean-concatenated text, and the gold output is `.txt`.

Relevant APIs:

- `unstructured.metrics.text_extraction.calculate_accuracy(output, source, weights=(2, 1, 1))` returns a 0-1 similarity score based on Levenshtein edit distance.
- `unstructured.metrics.text_extraction.calculate_percent_missing_text(output, source)` returns the fraction of gold words missing from prediction.
- `unstructured.metrics.evaluate.TextExtractionMetricsCalculator(predictions_dir, gold_dir, group_by=None, weights=(1, 1, 1), document_type="json")` batches files.

Batch expectations:

- Prediction filenames should be `.json` or `.txt` according to `document_type`.
- Gold filenames should match prediction stems and resolve to `.txt`.
- JSON prediction text is converted to clean-concatenated text before comparison.
- Per-document TSV: `all-docs-cct.tsv`.
- Aggregate TSV: `aggregate-scores-cct.tsv`.
- Metrics: `cct-accuracy`, `cct-%missing`, plus `filename`, `doctype`, and `connector` metadata.

Interpretation:

- High `cct-accuracy` means the full text is close after quote/whitespace normalization used by the metric.
- High `cct-%missing` means important gold words are absent even if the prediction has extra text.
- A very large prediction/source length mismatch can force text accuracy to a low sentinel value in the batch calculator.

## Element Type Metrics

Use element type metrics when the concern is whether partitioning emitted the right element categories and depths, not exact text.

Relevant APIs:

- `unstructured.metrics.element_type.get_element_type_frequency(elements_json_text)` returns counts keyed by `(type, category_depth)`.
- `unstructured.metrics.element_type.calculate_element_type_percent_match(output_frequency, source_frequency, category_depth_weight=0.5)` returns a 0-1 match score.
- `unstructured.metrics.evaluate.ElementTypeMetricsCalculator(predictions_dir, gold_dir, group_by=None)` batches JSON files.

Batch expectations:

- Prediction and gold files are element JSON arrays.
- Each element should have a `type` field and a `metadata` object; `metadata.category_depth` may be `null`.
- Gold filenames should match prediction stems and resolve to `.json`.
- Per-document TSV: `all-docs-element-type-frequency.tsv`.
- Aggregate TSV: `aggregate-scores-element-type.tsv`.
- Metric: `element-type-accuracy`.

Interpretation:

- Exact `(type, category_depth)` matches count fully.
- Correct type with different depth counts partially using `category_depth_weight`.
- Empty prediction or empty gold frequency returns `0.0`, so inspect malformed or empty JSON before treating the score as model behavior.

## Table Structure Metrics

Use table structure metrics when evaluating `Table` detection, table text alignment, cell row/column alignment, or HTML/cell conversion quality.

Relevant APIs:

- `unstructured.metrics.table.table_eval.TableEvalProcessor.from_json_files(prediction_file, ground_truth_file, cutoff=None, source_type="html")` compares one prediction/gold pair.
- `TableEvalProcessor(...).process_file()` returns `TableEvaluation` with table detection and cell alignment metrics.
- `unstructured.metrics.evaluate.TableStructureMetricsCalculator(predictions_dir, gold_dir, cutoff=None, weighted_average=True, include_false_positives=True)` batches JSON files.
- `unstructured.metrics.table.table_formats.SimpleTableCell.from_table_transformer_cell(cell)` converts Table Transformer cells with `row_nums`, `column_nums`, and `cell text` into simple cell dictionaries.

Input shape:

- Prediction JSON is an element list with `Table` elements.
- Prediction table data can be read from `metadata.text_as_html` with `source_type="html"` or `metadata.table_as_cells` with `source_type="cells"`.
- Gold table data is expected as `Table` elements whose `text` field contains Deckerd-style cells with `x`, `y`, `w`, `h`, and `content`.
- HTML must contain parseable `<table>` markup; non-table text in `text_as_html` is not enough.

Batch outputs:

- Per-document TSV: `all-docs-table-structure-accuracy.tsv`.
- Aggregate TSV: `aggregate-table-structure-accuracy.tsv`.
- Metrics include `total_tables`, `total_predicted_tables`, `table_level_acc`, `table_detection_recall`, `table_detection_precision`, `table_detection_f1`, `composite_structure_acc`, `element_col_level_index_acc`, `element_row_level_index_acc`, `element_col_level_content_acc`, and `element_row_level_content_acc`.

Interpretation:

- `table_detection_recall`, `table_detection_precision`, and `table_detection_f1` describe whether tables were found and matched.
- `table_level_acc` compares matched table text as a sequence-level ratio.
- Element row/column index metrics diagnose shifted cells even when table text is present.
- Element row/column content metrics diagnose ordering or content extraction issues.
- False positive tables can affect weighted aggregate behavior when `include_false_positives=True`.

## Object Detection Metrics

Use object detection metrics only when the user has layout dump predictions and object detection gold files, plus a working torch installation.

Relevant APIs:

- `unstructured.metrics.object_detection.ObjectDetectionEvalProcessor.from_json_files(prediction_file_path, ground_truth_file_path)` compares one pair.
- `unstructured.metrics.evaluate.ObjectDetectionAggregatedMetricsCalculator(predictions_dir, ground_truths_dir)` batches class-aggregated metrics.
- `unstructured.metrics.evaluate.ObjectDetectionPerClassMetricsCalculator(predictions_dir, ground_truths_dir)` batches per-class metrics.

Input shape:

- Predictions are discovered under `analysis/*/layout_dump/object_detection.json` relative to the predictions directory.
- Ground truth JSON files keep the original document extension plus `.json`, such as `document.pdf.json`.
- Ground truth and prediction JSON must agree on `object_detection_classes`.
- Bounding boxes and class tensors must have shapes compatible with torch tensor conversion and IoU computation.

Batch outputs:

- Aggregated per-document TSV: `all-docs-object-detection-metrics.tsv`.
- Aggregated summary TSV: `aggregate-object-detection-metrics.tsv`.
- Per-class per-document TSV: `all-docs-object-detection-metrics-per-class.tsv`.
- Per-class summary TSV: `aggregate-object-detection-metrics-per-class.tsv`.
- Metrics include `f1_score`, `precision`, `recall`, and `m_ap`.

Decision rule:

- If the user only asks about partition text, element categories, or tables, do not force torch setup.
- If the user has document layout detection dumps and wants detection quality, verify torch import, device choice, class labels, and tensor shapes before running the object detection calculators.

## Grouping and Filtering

`unstructured.metrics.evaluate.get_mean_grouping(group_by, data_input, export_dir, eval_name, ...)` can aggregate by `doctype`, `connector`, or all rows for text extraction, element type, or object detection metrics.

`unstructured.metrics.evaluate.filter_metrics(data_input, filter_list, filter_by="filename", ...)` filters TSV/CSV/DataFrame results to a selected filename list. The filter list can be a Python list or `.csv`, `.tsv`, or `.txt` file.

## Choosing the Right Metric

- Use text extraction metrics for OCR/text completeness and edit-distance similarity.
- Use element type metrics for category distribution regressions after changing partition strategy or model settings.
- Use table structure metrics for table identification, cell alignment, and HTML/cell schema regressions.
- Use object detection metrics only for layout dump quality and detection classes, not for general partition quality.
