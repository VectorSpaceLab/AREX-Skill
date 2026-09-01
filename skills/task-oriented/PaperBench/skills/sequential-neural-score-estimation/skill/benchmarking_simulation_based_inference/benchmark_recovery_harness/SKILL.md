---
name: benchmark_recovery_harness
description: Run an auditable reduced recovery experiment for the SBI benchmark by composing generated task, sampling, and C2ST skills.
---

# Benchmark Recovery Harness

Use this skill after the SBI benchmark module skills have been generated and validated. It writes recovery artifacts that prove the task protocol, posterior sampling, and C2ST metric were exercised without reading the original repository during recovery.

## Inputs
- Attempt directory containing `module_plan.json` and `environment/runtime_handoff.json`.
- Generated skills root containing `sbibm_task_protocol`, `posterior_sampling_baseline`, and `c2st_metric_evaluation`.
- Sample count, seed, and approximation mode.

## Outputs
- `recovery/recovery_result.json`, command-compatible logs, generated data item, training trace, source manifest, and invocation log.

## Workflow
1. Read the module plan target and runtime handoff.
2. Call the task protocol script to construct a Gaussian Linear proxy item.
3. Call the posterior sampling script to draw reference and approximate samples.
4. Call the C2ST metric script to compute the proxy metric.
5. Write mechanism checks proving reduced training/proxy execution, optimizer-like parameter update evidence, and source-boundary compliance.

## Validation
Run the harness, then run `recover-paper/scripts/validate_recovery_experiment.py` on the attempt directory.

## Limitations
This is a soft-mode reduced recovery harness. It must not be presented as a full paper reproduction across all tasks, algorithms, and budgets.

## Refinement Note
A shifted-posterior ablation should raise C2ST above the acceptance threshold; keep matched and shifted modes available for sanity checks.
