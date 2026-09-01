---
name: autovp_tuning_benchmark
description: Select AutoVP candidate configurations and record benchmark-style accuracy targets for recovery runs.
---
# AutoVP Tuning Benchmark
Use this skill when comparing AutoVP candidate configurations or writing benchmark result metadata. It should not claim full Table 2 reproduction for a reduced proxy.

## Inputs
Candidate configurations, early validation metrics, dataset name, metric name, and paper target.

## Outputs
Selected configuration and benchmark summary with proxy/full status.

## Workflow
Normalize records, sort by metric with deterministic tie-breaking, choose the best candidate, and emit dataset/metric/target metadata. Preserve module-plan target values exactly.

## Validation
Run included candidate-selection test.
