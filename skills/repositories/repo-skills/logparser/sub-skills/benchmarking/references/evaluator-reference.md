# Evaluator reference

## Purpose

Use this when you need to score a parsed CSV against ground truth.

## `logparser.utils.evaluator.evaluate`

- Signature: `evaluate(groundtruth, parsedresult)`
- Reads both CSVs with pandas.
- Drops ground-truth rows with missing `EventId` before comparing.
- Prints precision, recall, F1, and parsing accuracy.
- Returns `(f_measure, accuracy)`.

## `logparser.utils.evaluator.get_accuracy`

- Signature: `get_accuracy(series_groundtruth, series_parsedlog, debug=False)`
- Computes pair-based precision/recall/F1 and exact-line accuracy.
- Useful when you already have the two `EventId` series in memory.

## Practical notes

- `evaluate()` expects the two CSVs to align after any invalid rows are removed.
- If a parser writes a different output shape, normalize it before calling the
  evaluator.
- The helper is intentionally simple; it is best used for quick comparisons and
  smoke checks, not for complex statistical analysis.
