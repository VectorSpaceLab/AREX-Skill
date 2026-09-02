---
name: offline_recovery_harness
description: Execute a bounded D4RL-style offline recovery proxy with fixed-dataset training and normalized-score evidence.
---

# Offline Recovery Harness

Use this skill when full D4RL packages or datasets are unavailable but soft-mode recovery permits a declared mechanism-faithful proxy. The harness should still perform executable work: validate a fixed transition dataset, run a parameter update from that dataset, compute normalized scores, and save mechanism evidence.

## Inputs

- `module_plan.json` containing the fast recovery target.
- `environment/runtime_handoff.json` describing package blockers and allowed sources.
- Generated skill root containing dataset validation, score normalization, and taxonomy skills.
- An output recovery directory.

## Outputs

- `recovery_result.json` with numeric metrics and target metadata.
- `logs/generated_data_item.json` with transition content and provenance.
- `logs/training_trace.json` with `loss_before`, `loss_after`, `params_before`, and `params_after`.
- Invocation logs proving generated skills were used.

## Workflow

1. Read the module plan target and runtime handoff.
2. Build a tiny fixed offline chain dataset with explicit synthetic-proxy provenance.
3. Validate the dataset through `offline_dataset_protocol`.
4. Classify proxy metadata through `benchmark_property_taxonomy`.
5. Fit a one-parameter linear Q approximation with a deterministic gradient update.
6. Compute raw and normalized return through `d4rl_score_normalization`.
7. Save mechanism checks: no online collection, fixed dataset consumed, reduced training executed, optimizer step changed parameters, full D4RL packages unavailable, and normalized scoring used.
8. Keep full-runtime flags false when the runtime handoff reports missing packages.

## Validation

Run the harness script used by the recovery attempt, then run Distiller's `validate_recovery_experiment.py` on the attempt directory.

## Limitations

This harness is a reduced proxy, not a full D4RL benchmark run. It should be accepted only in soft mode after full recovery is blocked and the experiment gate passes.
