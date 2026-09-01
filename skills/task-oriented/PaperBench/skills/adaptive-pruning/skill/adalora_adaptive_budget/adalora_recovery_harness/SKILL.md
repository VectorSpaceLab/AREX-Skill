---
name: adalora_recovery_harness
description: Run bounded soft-mode AdaLoRA recovery experiments with source-boundary logs, mechanism checks, and validation artifacts.
---

# AdaLoRA Recovery Harness

Use this skill to recover a fast AdaLoRA result when full DeBERTa or BART fine-tuning is blocked by runtime limits. The harness must be explicit that it is a reduced/proxy experiment.

## Inputs

- Attempt directory containing `module_plan.json` and `environment/runtime_handoff.json`.
- Generated skill root with the SVD layer, rank allocator, and scheduler skills.
- Optional deterministic experiment configuration.

## Outputs

- `recovery/logs/generated_data_item.json`.
- `recovery/logs/training_trace.json` with `loss_before`, `loss_after`, `params_before`, and `params_after`.
- `recovery/recovery_result.json` with paper target copied from `module_plan.json`.
- Source manifest and generated-skill invocation log.

## Workflow

1. Read only allowed attempt artifacts and generated skill files; never read the original repository.
2. Build a deterministic tiny linear adaptation problem.
3. Invoke the generated SVD layer, budget scheduler, and rank allocator scripts or importable helpers.
4. Perform an actual parameter update on trainable reduced parameters.
5. Apply rank masking and compute mechanism booleans: SVD update used, optimizer changed parameters, budget respected, high-importance triplet retained, and loss decreased.
6. Mark full-model booleans false when no real DeBERTa/BART training occurred.
7. Run the recovery experiment validator.

## Validation

Run the harness script from an attempt directory, then run `validate_recovery_experiment.py`.

## Limitations

This is not a replacement for full paper reproduction. It is acceptable only in soft mode after full runtime blockers are recorded in `runtime_handoff.json`.
