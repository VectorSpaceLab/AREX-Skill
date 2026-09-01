---
name: vpt_mechanism_faithful_recovery
description: Run a bounded soft-mode Visual Prompt Tuning proxy that proves prompt insertion, frozen training, and evaluation mechanisms.
---

# VPT Mechanism-Faithful Recovery

Use this skill when full VPT training with real VTAB/FGVC data and pretrained ViT checkpoints is blocked, but soft-mode recovery permits a declared reduced proxy. Do not use it to claim full paper reproduction unless real benchmark data and pretrained backbones are actually used.

## Inputs

- Runtime handoff with package, model, dataset, and environment mutation status.
- Generated VPT skills for prompt insertion, frozen prompt training, and evaluation protocol.
- `module_plan.json.fast_recovery_target` identifying the full target and proxy allowance.
- A tiny real or synthetic classification dataset.

## Outputs

- Executable recovery command logs and `recovery_result.json`.
- `training_trace.json` containing loss before/after, `params_before`, `params_after`, and frozen-backbone checks.
- `generated_skill_invocations.json` proving generated skills were imported or called.
- Mechanism checks covering prompt insertion, deep prompt support, trainability mask, optimizer step, frozen backbone, and numeric metric.

## Workflow

1. Read the runtime handoff and record full-runtime blockers.
2. Declare reduced proxy recovery if real data/checkpoints are unavailable and soft mode allows it.
3. Build a tiny deterministic classification task that can be learned through prompt/head parameters.
4. Call the prompt insertion skill to build prompted token sequences.
5. Call the frozen training skill to create trainable groups and freeze checks.
6. Execute at least one optimizer step that changes prompt/head parameters while leaving the frozen backbone fixed.
7. Call the evaluation skill to compute accuracy and parameter-efficiency metadata.
8. Save all recovery artifacts and run the Distiller recovery validator.

## Validation

Run `python tests/test_recovery_contract.py`, or use the Distiller validator with `--run-tests`.

## Limitations

This reduced harness is mechanism-faithful but not a substitute for paper-scale VTAB or FGVC accuracy. It must be labeled `is_proxy: true` unless a real full benchmark is run.
