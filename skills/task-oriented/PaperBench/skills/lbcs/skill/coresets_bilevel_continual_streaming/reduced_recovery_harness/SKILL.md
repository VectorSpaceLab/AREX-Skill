---
name: reduced_recovery_harness
description: Run a bounded reduced semi-supervised recovery experiment that invokes generated protocol, influence, and masked optimizer skills and emits validator-compatible evidence.
---

# Reduced Recovery Harness

Use this skill in soft-mode recovery when full CIFAR/SVHN/IMDb training is blocked by runtime constraints but an executable mechanism-faithful experiment is required. The harness must call the generated protocol, influence update, and masked optimizer skills rather than duplicating their contracts silently.

Do not use this skill to claim full benchmark reproduction. It produces reduced/proxy evidence only.

## Inputs
- Attempt directory containing `module_plan.json`.
- Generated skills root with sibling module skills.
- Runtime handoff that records full-runtime blockers and soft-mode fallback permission.
- Optional seed and synthetic split size.

## Outputs
- `recovery/recovery_result.json` with numeric validation-loss delta.
- `recovery/logs/training_trace.json` with loss and parameter changes.
- `recovery/logs/generated_data_item.json` and skill invocation evidence.
- Command logs suitable for `validate_recovery_experiment.py`.

## Workflow
1. Load the module plan target and runtime handoff.
2. Import sibling generated skill scripts for data protocol, influence hypergradients, and masked Adam updates.
3. Construct a deterministic binary SSL problem and run one inner logistic parameter update.
4. Compute influence-style weight hypergradients and masked sparse optimizer updates for selected unlabeled ids.
5. Emit recovery artifacts that distinguish reduced training from full benchmark training.

## Validation
Run the harness, then run `recover-paper/scripts/validate_recovery_experiment.py <attempt_dir>`.

## Limitations
The harness is intentionally lightweight. It validates algorithmic mechanisms and artifact contracts, not final paper-scale test error.
