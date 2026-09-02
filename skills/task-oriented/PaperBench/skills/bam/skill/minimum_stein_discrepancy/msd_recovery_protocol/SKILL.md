---
name: msd_recovery_protocol
description: Assemble executable soft-mode recovery evidence for Minimum Stein Discrepancy Estimator proxy experiments.
---

# MSD Recovery Protocol

Use this skill when recovering Minimum Stein Discrepancy Estimators under bounded runtime. It coordinates the generated Stein-kernel, diffusion-design, and optimiser skills to produce validation-ready recovery artifacts without reading an original source repository.

## Inputs
- Attempt directory containing `module_plan.json`, module docs, generated skills, and `environment/runtime_handoff.json`.
- Recovery mode and target from the run manifest.
- Paths to generated skills that must be invoked or cross-checked.

## Outputs
- `recovery/experiment_plan.md` describing full and proxy options.
- `recovery/source_manifest.json` listing only allowed sources.
- `recovery/logs/generated_skill_invocations.json` with evidence for every core module.
- `recovery/logs/generated_data_item.json` and `recovery/logs/training_trace.json` for reduced proxy evidence.
- `recovery/recovery_result.json` and `recovery/experiment_validation.json`.

## Workflow
1. Confirm full reproduction blockers and soft-mode permission for a declared proxy.
2. Generate a deterministic Student-t location sample matching the module-plan target.
3. Call or import the generated diffusion-design skill to obtain Student-t diffusion diagnostics.
4. Call or import the Stein-kernel skill to evaluate DKSD losses.
5. Call or import the optimiser skill to minimise the empirical loss.
6. Save all logs and mechanism checks before running the recovery validator.

## Validation
Run the bundled `tests/test_msd_recovery_protocol.py` for source-manifest and mechanism-check helpers. The full recovery harness in the attempt directory should additionally run `validate_recovery_experiment.py`.

## Limitations
This skill accepts a declared reduced/proxy target only in soft mode. It must never label proxy evidence as full reproduction of the paper figures.

## Refinement cycle 3 note
A negative source-boundary check rejected an `original_repo` source; keep this check as a required recovery-protocol regression.
