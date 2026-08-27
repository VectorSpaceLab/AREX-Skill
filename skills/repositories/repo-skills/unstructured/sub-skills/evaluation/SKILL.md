---
name: evaluation
description: "Evaluate Unstructured partition outputs against gold outputs for
  text extraction, element types, table structure, and optional object detection
  metrics."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Evaluation

Use this sub-skill when a user needs to compare existing Unstructured outputs with gold-standard outputs, interpret metric TSVs, or decide whether optional object-detection evaluation is appropriate.

## Route Here For

- Text extraction accuracy and missing-text checks between partition output JSON/TXT and gold TXT.
- Element type frequency matching, including `metadata.category_depth` effects.
- Table structure evaluation from `Table` elements, `metadata.text_as_html`, or `metadata.table_as_cells`.
- Optional object detection metrics when `torch` and layout dump JSON files are available.
- Safe, local comparison of two element JSON files before running broader metric batches.

## Boundaries

- To create or regenerate partition outputs, route to the partitioning sub-skill first.
- To serialize, deserialize, or validate element JSON schemas, route to the elements-and-metadata sub-skill first.
- Do not promise that a partition smoke test passed unless the user has run one in their own environment.
- Treat object detection evaluation as optional because importing `unstructured.metrics.evaluate` can pull the torch-backed object detection module.

## Quick Workflow

1. Confirm that prediction and gold files are already generated and are paired by matching base filenames.
2. Choose the metric family: text extraction, element type, table structure, table alignment/format conversion, or optional object detection.
3. Validate file shape before batch evaluation: element JSON should be a list of element dictionaries; table JSON should include `Table` elements with table metadata or Deckerd-style cell data.
4. For one pair of element JSON files, use [`scripts/evaluate_elements_pair.py`](scripts/evaluate_elements_pair.py) for a dependency-light summary.
5. For batch metrics, use the package calculators documented in [`references/metrics-reference.md`](references/metrics-reference.md).
6. When a metric fails unexpectedly, check [`references/troubleshooting.md`](references/troubleshooting.md) before changing the partitioning pipeline.

## Pair Comparison Helper

```bash
python sub-skills/evaluation/scripts/evaluate_elements_pair.py \
  --prediction predicted.json \
  --gold gold.json \
  --table-source auto
```

The helper reports element count differences, text accuracy, missing text, element-type frequency match, and table structure metrics when compatible table data exists. It intentionally avoids importing `unstructured.metrics.evaluate` so ordinary text/element/table checks do not require torch.

## Batch Calculator Pattern

For package-level TSV outputs, instantiate the metric calculator, pass prediction and gold directories, and write to an output directory outside the runtime skill tree:

```python
from unstructured.metrics.evaluate import TextExtractionMetricsCalculator

TextExtractionMetricsCalculator("predictions", "gold", document_type="json").calculate(
    export_dir="metrics",
    visualize_progress=False,
    display_agg_df=False,
)
```

Use the detailed calculator table and output filenames in [`references/metrics-reference.md`](references/metrics-reference.md).
