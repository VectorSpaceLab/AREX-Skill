# Benchmark workflows

## Purpose

Use this reference when you want to compare parser output with ground truth or
adapt a parser-specific benchmark script.

## Standard benchmark shape

Most benchmark scripts in this repository follow the same pattern:

1. Choose a dataset from `data/loghub_2k/` or `data/loghub_2k_corrected/`.
2. Instantiate the parser with the dataset's `log_format` and `rex` rules.
3. Parse the dataset's log file.
4. Compare the resulting structured CSV against the dataset ground truth.
5. Record the metric pair or table.

## Metrics you will see

- `Precision`
- `Recall`
- `F1_measure`
- `Parsing_Accuracy`
- `Accuracy`
- `Grouping Accuracy`
- `Parsing Accuracy`
- `Template Accuracy`

Different parsers and benchmark scripts print different subsets of these
metrics, so always check the parser-specific benchmark notes before comparing
numbers.

## Ground-truth layout

The benchmark corpora store the parsed ground truth next to the raw logs. The
usual pattern is:

- `RAW_LOG.log`
- `RAW_LOG.log_structured.csv`

The parser output should line up row-for-row with the ground truth after any
invalid IDs are removed.

## Example with the bundled helper

```bash
python scripts/evaluate_csvs.py \
  --groundtruth data/loghub_2k/HDFS/HDFS_2k.log_structured.csv \
  --parsed path/to/output/HDFS_2k.log_structured.csv
```

## Large benchmark scripts

The parser-specific `benchmark.py` files usually sweep a whole list of datasets.
Use them when you need the full published table, but prefer the bundled helper
for a fast smoke or when you only want to check one file pair.
