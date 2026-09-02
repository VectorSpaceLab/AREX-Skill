---
name: datamodel_recovery_evaluation
description: Run a bounded synthetic proxy recovery that validates linear datamodel prediction and counterfactual mechanisms with executable evidence.
---

# Datamodel Recovery Evaluation

Use this skill to recover the paper's core mechanism when full deep-network retraining on many subsets is infeasible. The recovery is valid only as a declared soft-mode proxy.

## Inputs

- Attempt directory containing `module_plan.json` and `environment/runtime_handoff.json`.
- Generated skill root containing `alpha_subset_protocol`, `linear_datamodel_fit`, and `counterfactual_effect_scoring`.
- Experiment parameters: `d`, `alpha`, train/test subset counts, seed, and noise scale.

## Outputs

- `recovery/recovery_result.json`.
- `recovery/logs/training_trace.json`.
- `recovery/logs/generated_data_item.json`.
- `recovery/logs/generated_skill_invocations.json`.

## Workflow

1. Read the module-plan fast recovery target.
2. Import and call the generated subset protocol skill.
3. Create hidden training-example effects and synthetic subset outcomes.
4. Import and call the linear datamodel fitting skill.
5. Import and call the counterfactual scoring skill.
6. Write mechanism checks proving subset sampling, fitting, held-out evaluation, optimizer-style parameter update, and counterfactual scoring ran.
7. Save recovery artifacts for the Distiller experiment validator.

## Validation

Run:

```bash
python scripts/run_proxy_recovery.py --attempt-dir ATTEMPT --skills-root SKILLS
python tests/test_recovery_harness.py
```

## Limitations

This is not a full reproduction of CIFAR-10 or FMoW deep-network results. It validates the datamodeling mechanism under an executable synthetic proxy because full training is blocked by runtime cost and missing original data/model pipeline.
