---
name: reduced_recovery_harness
description: Run bounded reduced PINN recovery experiments that exercise generated benchmark, objective, diagnostics, and curriculum skills.
---

# Reduced Recovery Harness

Use this skill during soft-mode recovery when full paper-scale PINN sweeps are blocked by time or environment constraints. The harness must still execute real parameter updates over a PDE residual objective and must declare proxy scope.

## Inputs
- Attempt directory containing `module_plan.json`.
- Generated skills root containing benchmark, residual objective, diagnostics, and curriculum skills.
- Recovery output directory.
- Runtime handoff and blocker notes from environment preparation.

## Outputs
- `recovery_result.json` with numeric metrics and mechanism checks.
- `logs/generated_data_item.json` for the constructed periodic convection benchmark.
- `logs/training_trace.json` with `params_before`, `params_after`, and before/after losses.
- `logs/generated_skill_invocations.json` proving generated skills were imported or called.

## Workflow
1. Read the module-plan target instead of hard-coding a different recovery metric.
2. Build a reduced periodic convection benchmark with generated skills.
3. Run vanilla high-coefficient optimization and curriculum staged optimization.
4. Compute relative L2 diagnostics for both runs.
5. Emit validator-compatible recovery artifacts and mechanism checks.

## Validation
Run `python scripts/run_reduced_recovery.py --attempt-dir <attempt> --skills-root <skills> --output-dir <attempt>/recovery` after module skills exist, then run the recovery experiment validator.

## Limitations
This is a declared soft-mode proxy. It is not a full reproduction of the paper's multi-system PyTorch sweeps, and it must not read the original repository during recovery.
