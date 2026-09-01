---
name: proxy_recovery_harness
description: Run a bounded mechanism-faithful RAIL-KD proxy experiment with executable recovery and validation evidence.
---

# Proxy Recovery Harness

Use this skill when full RAIL-KD GLUE transformer distillation is blocked but soft-mode recovery permits a reduced, mechanism-faithful experiment. It must call or import the generated mapping, representation-loss, and combined-objective skills rather than duplicating their contracts silently. Do not use this skill to claim full paper reproduction unless real model, data, and training evidence exists.

## Inputs

- Attempt directory containing `module_plan.json` and `environment/runtime_handoff.json`.
- Generated skills root containing `random_layer_mapping`, `rail_representation_loss`, and `combined_kd_objective`.
- Synthetic experiment configuration: teacher layers, student layers, tokens, dimensions, epochs, seed, learning rate, and RAIL variant.

## Outputs

- `recovery/recovery_result.json` with numeric `loss_reduction_fraction`.
- `recovery/logs/training_trace.json` with `params_before` and `params_after`.
- `recovery/logs/generated_skill_invocations.json` proving generated skill usage.
- `recovery/logs/generated_data_item.json` describing the synthetic hidden-state example.
- Mechanism checks for random mapping, coverage, pooling, normalization, objective composition, and optimizer update.

## Workflow

1. Read the module plan target and runtime handoff.
2. Record that full GLUE distillation is blocked unless the handoff proves otherwise.
3. Build deterministic synthetic teacher/student hidden states.
4. For each epoch, call the mapping skill, compute the RAIL representation loss, combine CE/KD/RAIL losses, and update trainable scalar student parameters.
5. Save a command-produced result with before/after metrics and source-boundary evidence.
6. Run the Distiller recovery experiment validator after the harness completes.

## Validation

Run a smoke experiment:

```bash
python scripts/run_proxy_recovery.py --attempt-dir /path/to/attempt --skills-root /path/to/generated/skills --epochs 6 --seed 11
python -m pytest tests
```

## Limitations

The default experiment is a declared reduced proxy. It validates the RAIL-KD mechanism but does not reproduce GLUE scores, large transformer optimization, or out-of-domain results.
