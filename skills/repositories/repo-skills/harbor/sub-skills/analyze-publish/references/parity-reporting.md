# Parity reporting

Parity reporting turns adapter-level `parity_experiment.json` records into a
flat comparison table. It is a reporting transformation, not a benchmark run,
statistical test, or proof that the compared experiments are equivalent.
Generate locally from a copied results/adapter directory and review the output
before publishing it.

## Accepted record shape

Each record is normally an object in a JSON list and may contain:

- `adapter_name`, `adapter_pr` (a list), `parity_between`;
- `number_of_runs` or `number_of_trials`, `parity_benchmark_size`, `model`,
  `agent`;
- `metrics`, a list of objects with a metric name and two comparison sides.

Recognized value-side keys are `original`, `harbor`, `tb_adapter`,
`original_json`, and `original_llm`. Recognized run-side keys are the matching
`*_runs` or `*_trials` keys. Metadata keys such as `benchmark_name`, `metric`,
standard-error fields, and success-count fields are not treated as comparison
sides. Unexpected schemas should be reported and skipped rather than guessed.

The conventional CSV columns are:

```text
Name, Harbor Status, Harbor Adapter PR, Metric, Parity between,
Source value, Source Std, Source runs, Target value, Target Std, Target runs,
Parity task num, # runs, Model, Agent
```

## Side and value normalization

For each metric, detect the two value-side keys. Prefer `harbor` as target;
when present without `harbor`, prefer `tb_adapter`; otherwise use stable sorted
keys. The other side is source. If only one side is present, leave the missing
side blank and flag the row for review. If `parity_between` is absent, infer
conservatively from keys and notes, for example `harbor adapter x original` or
`harbor adapter x terminal-bench adapter`; never infer a numeric comparison from
this label alone.

Parse a value string such as `10.71 +/- 0.94`, `10.71 ± 0.94`, or `10.71` as:

- **mean**: the initial signed decimal number;
- **standard deviation**: the number following `±` or `+/-`, otherwise blank;
- **runs**: the matching list formatted as comma-separated values.

Preserve the raw record separately when rounding, missing values, or text-like
metrics might matter. A numeric-looking value is not necessarily a compatible
metric: confirm direction (higher/lower is better), task subset, verifier,
agent, model, number of attempts, and aggregation before calling it parity.

For a repeatable local CSV conversion, use the bundled
[`scripts/generate_parity_summary.py`](../scripts/generate_parity_summary.py). It
reads only immediate child directories under `--adapters-dir`, accepts an
explicit `--output`, and has no Harbor checkout, network, or credential
dependency. Treat its output as a draft for the review below; do not use it to
publish or overwrite source experiment files.

## Review checklist

1. Confirm the JSON is a list, every metric is an object, and each compared side
   has the expected value and run fields.
2. Check that source and target labels match the declared `parity_between` text.
3. Compare task count, number of runs, agent/model, metric definition, and
   success-count conventions; do not combine means from unequal subsets.
4. Preserve missing, malformed, or skipped adapters in a gap report rather than
   silently dropping them. Distinguish no file, invalid JSON, empty metrics,
   one-sided metrics, and a completed zero value.
5. Write CSV to an explicit output path outside the runtime skill tree, then
   inspect row counts and representative source/target values. Never overwrite
   source experiment JSON as part of report generation.

A parity summary is ready for sharing only after the owner confirms the source
and target are the intended pair and any model/API or credentialed publication
gate has been approved.
