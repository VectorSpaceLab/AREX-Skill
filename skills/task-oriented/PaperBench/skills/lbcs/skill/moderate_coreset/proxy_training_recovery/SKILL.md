---
name: proxy_training_recovery
description: Run a bounded Moderate-DS proxy recovery harness with generated skill invocations and optimizer evidence.
---

# Proxy Training Recovery Harness

Use this skill when full image-dataset retraining is blocked but soft-mode recovery permits a declared mechanism-faithful proxy. The harness must import or call the scoring, median-selection, and ablation skills, produce executable logs, and write validator-compatible recovery artifacts.

## Inputs
- Attempt directory containing `module_plan.json` and `environment/runtime_handoff.json`.
- Generated skills root containing the Moderate-DS module skills.
- Optional synthetic dataset parameters for stress tests.

## Outputs
- `recovery/recovery_result.json` with numeric metrics and mechanism checks.
- `recovery/logs/generated_data_item.json` describing the proxy data.
- `recovery/logs/training_trace.json` showing loss before and after a real optimizer update.
- `recovery/logs/generated_skill_invocations.json` proving all core skills were exercised.

## Workflow
1. Create a deterministic class-cluster representation dataset with central, moderate, and far points.
2. Import the generated scoring, median-selection, and ablation scripts from the generated skills root.
3. Select the moderate coreset and compare it against extreme policies.
4. Run a simple trainable linear proxy update on the selected coreset and log parameter changes.
5. Write recovery artifacts and source boundaries before invoking validation.

## Validation
Run `python scripts/run_proxy_recovery.py --attempt-dir <attempt_dir> --skills-root <skills_root>`. Then run the Distiller recovery validator on the attempt directory.

## Limitations
This is not a full CIFAR-100/ImageNet reproduction. It is a soft-mode proxy that validates the mechanism under bounded runtime constraints.
