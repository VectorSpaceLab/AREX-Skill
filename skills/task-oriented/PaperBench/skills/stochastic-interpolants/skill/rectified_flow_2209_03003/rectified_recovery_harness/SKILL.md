---
name: rectified_recovery_harness
description: Compose rectified-flow module skills into an executable reduced recovery experiment with auditable JSON logs.
---

# Rectified Recovery Harness

Use this skill when a Distiller recovery attempt needs a bounded executable experiment for the rectified-flow paper. It coordinates generated skills rather than duplicating their contracts.

## Inputs
- Attempt directory containing `module_plan.json` and `environment/runtime_handoff.json`.
- Generated skill root with interpolation, velocity regression, and ODE/reflow skills.
- Seed, sample count, and Euler step count.

## Outputs
- `recovery/recovery_result.json` with metrics and mechanism checks.
- `recovery/logs/training_trace.json` and `generated_data_item.json`.
- `recovery/logs/generated_skill_invocations.json`.

## Workflow
1. Construct a deterministic synthetic coupling for a low-dimensional transport proxy.
2. Invoke the interpolation skill to build rectified-flow records.
3. Invoke the velocity-regression skill to run optimizer steps.
4. Invoke the ODE/reflow skill to simulate transport and straightness diagnostics.
5. Write source-boundary, command, and mechanism evidence.

## Validation
Run the harness from an attempt directory, then run `validate_recovery_experiment.py`.

## Limitations
This harness declares reduced/proxy recovery and keeps full image-training booleans false unless a real full runtime is supplied and validated separately.

## Stress-Test Invariant
Seed stress tests must preserve positive loss reduction and keep reduced/full runtime booleans separate.
