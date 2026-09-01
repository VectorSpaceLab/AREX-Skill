---
name: movement_recovery_harness
description: Run a bounded mechanism-faithful recovery experiment for movement pruning without reading the original source repository.
---

# Mechanism-Faithful Movement Pruning Recovery Harness

Use this skill after the movement-pruning module skills have been generated and validated. It creates a deterministic reduced recovery when full BERT fine-tuning is blocked by runtime constraints. Do not import or inspect the original paper repository during recovery.

## Inputs
- Attempt directory containing `module_plan.json` and `environment/runtime_handoff.json`.
- Generated skill root containing `score_masking`, `movement_scores`, and `soft_regularization`.
- Seed, sample count, keep ratio, and learning rates.

## Outputs
The harness writes `recovery_result.json`, `training_trace.json`, `generated_data_item.json`, command evidence, and generated skill invocation evidence.

## Workflow
1. Construct a transfer-style proxy with stale high-magnitude pretrained weights and low-magnitude adaptive weights.
2. Run a real logistic-loss gradient step on trainable parameters.
3. Call the movement score update skill, score masking skill, and soft regularization skill.
4. Compare movement top-v masks to magnitude masks for adaptive-feature retention.
5. Record numeric metrics and mechanism checks, then run the recovery experiment validator.

## Validation
Run the harness from the attempt directory with `python recovery/run_recovery.py`. A successful run decreases loss, changes parameters, records all required logs, and passes the Distiller recovery gate.

## Limitations
The default experiment is a reduced proxy, not a full BERT/MNLI/SQuAD reproduction. It is acceptable only in soft recovery mode after full runtime blockers are recorded.
