---
name: tecoa_recovery_harness
description: Run an executable reduced TeCoA recovery experiment with generated skill invocations and mechanism checks.
---

# TeCoA Recovery Harness

Use this skill during soft-mode recovery when full CLIP/ImageNet adversarial training is blocked or too expensive, but a mechanism-faithful reduced experiment is required. The harness connects the generated prompt, contrastive objective, and adversarial attack skills, then performs a real trainable adapter update on adversarial features.

Do not use this skill to claim full paper reproduction unless the runtime handoff documents that real CLIP, data, and training were used. In the standard reduced path, mark `is_proxy: true` and explain the full-runtime blockers.

## Inputs

- `attempt_dir`: current Distiller attempt directory.
- `skills_root`: generated skill root containing the TeCoA module skills.
- `runtime_handoff`: JSON handoff from environment preparation.
- `module_plan`: target metadata with the fast recovery target.

## Outputs

- `recovery/logs/training_trace.json` with `params_before`, `params_after`, losses, margins, and parameter-change evidence.
- `recovery/logs/generated_skill_invocations.json` proving each core generated skill was called or cross-checked.
- `recovery/recovery_result.json` containing metrics and mechanism checks.
- `recovery/source_manifest.json` listing allowed recovery sources and excluding the original repository.

## Workflow

1. Read the module plan target and runtime handoff.
2. Construct a deterministic four-class synthetic embedding batch and prompts.
3. Invoke the prompt protocol skill to create CLIP-style prompt metadata.
4. Invoke the contrastive objective skill for baseline and adversarial scoring.
5. Invoke the adversarial feature attack skill to generate bounded adversarial features.
6. Train a tiny diagonal image adapter for multiple finite-difference SGD steps on TeCoA loss.
7. Save numeric evidence that the optimizer changed parameters and improved adversarial alignment.
8. Write recovery artifacts and run the Distiller recovery experiment validator.

## Validation

Run `tests/test_recovery_proxy.py` for an isolated harness smoke test, then run `python recovery/run_recovery.py` from the attempt directory during actual recovery.

## Limitations

The default harness is a reduced proxy. It validates the TeCoA mechanism, not ImageNet-scale robust accuracy. It uses only standard-library Python to avoid mutating shared environments.
