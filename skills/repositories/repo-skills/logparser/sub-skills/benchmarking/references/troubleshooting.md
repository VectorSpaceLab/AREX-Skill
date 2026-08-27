# Benchmark troubleshooting

## Purpose

Use this when a benchmark run starts but the metrics or input files are wrong.

## Ground-truth path issues

**Symptoms**
- `evaluate()` raises a file-not-found error.
- The benchmark script cannot locate `*_structured.csv` ground truth.

**Likely causes**
- The benchmark dataset path does not match the repository layout.
- The output directory for the parser run is different from the benchmark's
  expected location.

**Recovery**
- Read `data/README.md` and the benchmark workflow reference.
- Confirm the raw log and the ground-truth CSV live next to each other.
- Make sure the parser output is the file that `evaluate()` expects.

## Metric confusion

**Symptoms**
- The benchmark prints several metric names and the numbers are hard to compare.

**Likely causes**
- Different benchmark scripts compute different metrics.
- Some scripts are pair-based while others are line-accuracy based.

**Recovery**
- Use the evaluator reference to identify which metrics are returned.
- Compare like-for-like metrics only.

## Expensive full-table runs

**Symptoms**
- The benchmark takes a long time or creates many output files.

**Likely causes**
- The parser-specific benchmark sweeps all Loghub datasets.

**Recovery**
- Start with `scripts/evaluate_csvs.py` on one parsed CSV pair.
- Only run the full benchmark once the parser configuration is stable.
