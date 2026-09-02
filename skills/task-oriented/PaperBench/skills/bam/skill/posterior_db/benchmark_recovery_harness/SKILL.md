---
name: benchmark_recovery_harness
description: Assemble executable posteriordb reduced benchmark recovery runs with provenance, metric, and mechanism evidence.
---

# Benchmark Recovery Harness

Use this skill when a posteriordb recovery needs to combine validated object links, reference summaries, approximate posterior outputs, moment scoring, cost logging, and mechanism checks. It is designed for bounded soft-mode recovery when full Stan/NUTS or multi-posterior Pathfinder benchmarks are unavailable or too expensive.

## Inputs

- A contract report from `posterior_object_contracts`.
- A reference summary report from `reference_summary_checks`.
- Approximate parameter means or draws.
- A paper target dictionary from `module_plan.json.fast_recovery_target`.

## Outputs

- A recovery result JSON containing numeric metrics, target metadata, commands, artifacts, and mechanism checks.
- A generated data item and training trace when reduced optimizer recovery is used.
- Invocation evidence proving generated skills were called or cross-checked.

## Workflow

1. Verify that the object contract and reference summary reports are valid.
2. Build approximate estimates by adding a deterministic offset to reference means for a tiny reduced proxy.
3. Score RMSE with the generated posterior-accuracy skill.
4. Run one optimizer-style update that moves the offset toward zero, changes parameters, and reduces RMSE.
5. Record source provenance, optimizer trace, and cost counters such as sample count and score evaluations.
6. Emit mechanism checks for object linking, summary loading, moment scoring, reduced training, optimizer execution, and source-boundary compliance.

## Validation

Run `python scripts/reduced_benchmark.py --contract contract.json --summary summary.json --target target.json --output recovery_result.json --logs-dir logs` or validate the included tests with the Distiller skill validator.

## Limitations

This harness is a declared proxy unless it is supplied real approximate inference draws from a full algorithm. It must not be presented as a full Pathfinder, Stan, or NUTS reproduction unless those runtimes actually ran and are logged.
