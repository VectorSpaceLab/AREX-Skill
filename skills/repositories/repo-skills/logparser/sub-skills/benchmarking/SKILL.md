---
name: benchmarking
description: "Guides Logparser benchmark runs, dataset evaluation, and
  accuracy/F1 comparison workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Benchmarking

Use this sub-skill for any workflow that compares parser output against ground
truth or runs a Loghub-style benchmark harness.

## Include here

- Evaluating `*_structured.csv` against ground truth.
- Interpreting `F1_measure`, `Accuracy`, parsing accuracy, grouping accuracy,
  and template accuracy.
- Adapting the parser-specific `benchmark.py` files.
- Reasoning about `data/loghub_2k/` and `data/loghub_2k_corrected/` layouts.

## Exclude from here

- Choosing or tuning a parser for a raw log file; use `../parsing/SKILL.md`.
- Import shims, compilers, APIs, and other special parser issues; use
  `../specialized-parsers/SKILL.md`.

## Read these references

- `references/benchmark-workflows.md` for the benchmark flow and dataset notes.
- `references/evaluator-reference.md` for the metric helper and output meaning.
- `references/troubleshooting.md` for result-path, dataset, and metric issues.

## Run this script

- `scripts/evaluate_csvs.py` — quick metric helper for a ground-truth / parsed
  CSV pair.

## When to route here

Choose this sub-skill when the request says things like:

- "benchmark Drain"
- "compare parsers"
- "compute F1/accuracy"
- "evaluate the structured CSV"
- "run the Loghub benchmark"
- "inspect the benchmark output"

## Working notes

- The benchmark flow usually reuses the same parser configuration as the parsing
  flow, so read the parsing sub-skill if you need to adjust the parser first.
- The benchmark scripts sometimes assume a dataset directory layout; confirm the
  input paths before running a large job.
