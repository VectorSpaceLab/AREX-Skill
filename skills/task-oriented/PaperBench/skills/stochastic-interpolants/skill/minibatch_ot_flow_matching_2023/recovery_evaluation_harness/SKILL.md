---
name: recovery_evaluation_harness
description: Run bounded executable OT-CFM proxy recoveries with command logs, mechanism checks, and validator-compatible artifacts.
---

# Recovery Evaluation Harness

Use this skill when recovering this paper under bounded runtime constraints. It is responsible for producing executable evidence, not for hand-writing final metrics. Do not use it to claim full CIFAR or single-cell reproduction unless the corresponding real runtime and data actually ran.

## Inputs
- Attempt directory containing `module_plan.json` and generated skills.
- Runtime handoff describing available Python packages, GPU state, and allowed recovery sources.
- Generated CFM objective and minibatch OT coupling skills.

## Outputs
- `recovery/recovery_result.json` with numeric metrics and target metadata copied from the module plan.
- `recovery/logs/training_trace.json` with `loss_before`, `loss_after`, `params_before`, and `params_after`.
- `recovery/logs/generated_data_item.json`, generated-skill invocation log, source manifest, and command log.

## Workflow
1. Select the strongest feasible target from the runtime handoff. Under soft mode, declare a reduced proxy only after full training is blocked.
2. Build deterministic source and target minibatches.
3. Invoke the generated minibatch OT skill to compute a coupling and the CFM objective skill to construct velocity targets.
4. Run a real optimizer update on a tiny trainable linear vector-field parameter.
5. Save validator-compatible artifacts and mechanism checks.
6. Run the recovery experiment validator and refine any missing evidence.

## Validation
Run the recovery script on a temporary attempt directory, then run the Distiller recovery validator. The skill itself can be validated with `python tests/test_recovery_metrics.py`.

## Limitations
The bundled harness is a reduced/proxy experiment. It validates the CFM/OT mechanism but does not reproduce full-scale neural ODE image generation or single-cell benchmarks.
