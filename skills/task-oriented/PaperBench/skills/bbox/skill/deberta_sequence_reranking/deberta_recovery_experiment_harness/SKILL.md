---
name: deberta_recovery_experiment_harness
description: Orchestrate a source boundary clean DeBERTa reduced recovery harness that records executable evidence and mechanism checks.
---

# DeBERTa Recovery Experiment Harness

Use this skill after the DeBERTa module skills and environment handoff exist. It helps a recovery script copy the module-plan target, record allowed sources, log generated skill invocations, and decide whether a soft-mode reduced proxy is valid. Do not use it to justify a proxy when hard recovery mode is active.

## Inputs

- Attempt directory.
- Generated skills root.
- `module_plan.json`.
- `environment/runtime_handoff.json`.
- Recovery mode from `run_manifest.json`.

## Outputs

- Source manifest structure.
- Target consistency checks.
- Invocation-log entries for generated skills.
- Validator-friendly mechanism-check fields.

## Workflow

1. Read the module-plan target and keep it as authoritative.
2. Read the runtime handoff and require blockers before selecting reduced recovery.
3. Build a source manifest that excludes the original repository.
4. Record one invocation entry for each generated skill that is imported, called, cross-checked, or marked not applicable.
5. Mark full model booleans false when the model stack is unavailable.

## Validation

The bundled tests verify target copying, source manifest construction, and reduced-recovery eligibility under soft mode with runtime blockers.

## Limitations

This skill is a harness helper. The actual experiment command must still run a recovery script that produces metrics, training traces, and Distiller recovery-gate evidence.
