---
name: diayn_recovery_evaluation_harness
description: Assemble validator-compatible reduced DIAYN recovery experiments that exercise fixed skills, discriminator rewards, and policy updates.
---

# DIAYN Recovery Evaluation Harness

Use this skill to produce an executable reduced recovery for DIAYN when full MuJoCo/SAC training is blocked by runtime or time limits. It should be used only with explicit proxy/reduced labeling and mechanism checks. Do not use it to bypass available full training.

## Inputs

- Attempt directory.
- Generated skills root containing the DIAYN helper skills.
- `module_plan.json` with the recovery target.
- `environment/runtime_handoff.json` describing runtime blockers and allowed sources.

## Outputs

- `recovery/recovery_result.json`.
- `recovery/logs/training_trace.json`.
- `recovery/logs/generated_data_item.json`.
- `recovery/logs/generated_skill_invocations.json`.
- `recovery/source_manifest.json`.

## Workflow

1. Read target metadata and runtime handoff.
2. Import and invoke generated helper scripts for prior scheduling, discriminator reward, and policy update.
3. Build a deterministic three-skill line-world rollout batch.
4. Execute a real parameter update and record before/after losses.
5. Write all recovery artifacts and mechanism checks for the experiment gate.
6. Run the Distiller recovery validator after the harness completes.

## Validation

Run `python scripts/run_diayn_recovery.py --attempt-dir <attempt> --skills-root <generated_root>`. Tests exercise the data-building function and confirm the expected mechanism flags.

## Limitations

The harness is a reduced proxy, not a full benchmark reproduction. It should be accepted only in soft mode when full recovery is blocked and the experiment validator passes.
