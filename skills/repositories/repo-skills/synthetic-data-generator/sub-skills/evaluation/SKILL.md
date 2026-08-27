---
name: evaluation
description: "Evaluate SDGX real and synthetic tabular data with JSD,
  mutual-information similarity, and safe metric/benchmark adaptation guidance."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# SDGX Evaluation

Use this sub-skill when the task is about comparing real and synthetic SDGX tables, calculating `JSD`, mutual-information similarity, validating sampled outputs, or adapting benchmark-style checks without running heavyweight benchmark defaults.

Use [../single-table-synthesis/SKILL.md](../single-table-synthesis/SKILL.md) to generate the synthetic data first. Use [../data-preparation/SKILL.md](../data-preparation/SKILL.md) if column metadata or data types are unclear.

## Core metrics

- `sdgx.metrics.column.jsd.JSD.calculate(real_data, synthetic_data, cols, discrete=True)` returns a Jensen-Shannon divergence in `[0, 1]`.
- `sdgx.metrics.pair_column.mi_sim.MISim.calculate(src_col, tar_col, metadata)` returns normalized mutual-information similarity for one pair of columns.

Read [references/metrics-reference.md](references/metrics-reference.md) for signatures, data-type metadata expectations, and caveats.

## Bundled helper

Run [scripts/compute_metrics.py](scripts/compute_metrics.py) to calculate JSD and optional MI similarity from CSV files:

```bash
python sub-skills/evaluation/scripts/compute_metrics.py \
  --real real.csv \
  --synthetic synthetic.csv \
  --jsd-cols workclass \
  --discrete true
```

## Benchmark caution

The source benchmark scripts generate large random datasets and run memory-profiler comparisons against SDV CTGAN. Treat them as evidence of performance intent, not as default validation. For normal repo-skill verification, use small metrics and smoke scripts.

## Troubleshooting

Read [references/troubleshooting.md](references/troubleshooting.md) for invalid columns, KDE cost on continuous JSD, metadata type names for MI, and interpreting metric values.
