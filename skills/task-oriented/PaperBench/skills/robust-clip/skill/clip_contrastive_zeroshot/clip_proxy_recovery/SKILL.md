---
name: clip_proxy_recovery
description: Run a bounded soft-mode CLIP proxy recovery that logs contrastive training and zero-shot evaluation evidence.
---

# CLIP Proxy Recovery

Use this skill when full web-scale CLIP pretraining is blocked but soft-mode recovery permits a declared proxy. Do not use it as proof of full CLIP performance.

## Inputs
- Distiller attempt directory with `module_plan.json` and generated skills.
- Runtime handoff documenting package/model blockers.
- Tiny paired feature fixture or generated proxy data item.

## Outputs
- `recovery_result.json` with numeric proxy metrics.
- `generated_data_item.json`, `training_trace.json`, experiment command log, and generated-skill invocation log.
- Mechanism checks for pair construction, contrastive loss, optimizer update, prompt classification, and source boundary.

## Workflow
1. Read the module-plan target and runtime handoff.
2. Create or validate a tiny paired image-text feature dataset.
3. Run a real optimizer update on trainable scalar parameters using symmetric contrastive loss.
4. Classify held-out image vectors with prompt-derived class vectors.
5. Write auditable logs and mark the recovery as proxy/reduced.

## Validation
Run the recovery harness and then `validate_recovery_experiment.py` on the attempt directory.

## Limitations
This skill validates the mechanism, not the paper's full ImageNet-scale accuracy.
