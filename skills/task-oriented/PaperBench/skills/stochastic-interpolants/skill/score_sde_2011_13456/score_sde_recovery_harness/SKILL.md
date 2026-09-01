---
name: score_sde_recovery_harness
description: Assemble executable soft-mode recovery artifacts for reduced score-SDE training and mechanism validation.
---

# Score SDE Recovery Harness

Use this skill after the score-SDE schedule, loss, and sampling skills exist and a runtime handoff has established whether full training is feasible. It creates validator-compatible recovery artifacts for a declared reduced/proxy run when full image training is blocked.

## Inputs
- Attempt directory path.
- Runtime handoff JSON.
- Module plan with the declared fast recovery target.
- Generated skill root containing the schedule, loss, and predictor-corrector skills.

## Outputs
- `recovery/recovery_result.json` with target metadata and metrics.
- A training trace at `recovery/logs/training_trace.json` with loss before/after and `params_before`/`params_after`.
- `recovery/logs/generated_data_item.json` and `recovery/logs/generated_skill_invocations.json`.
- Mechanism checks for continuous time sampling, perturbation scores, optimizer execution, and predictor-corrector execution.

## Workflow
1. Read the module plan and runtime handoff before selecting reduced recovery.
2. Build a deterministic synthetic Gaussian-mixture proxy batch.
3. Import and call the generated schedule and loss scripts to compute perturbation targets and run one optimizer step.
4. Import and call the predictor-corrector script as a reverse-dynamics cross-check.
5. Write all recovery artifacts and command metadata from the executable run.
6. Keep full-runtime flags false when deep-learning packages or full datasets are unavailable.

## Validation
Run `python scripts/run_recovery.py --attempt-dir <attempt_dir> --generated-skills-root <root>` and then run the Distiller recovery validator.

## Limitations
This harness is valid only as a soft-mode reduced recovery unless the runtime handoff proves full model training is available and the harness is extended accordingly.
