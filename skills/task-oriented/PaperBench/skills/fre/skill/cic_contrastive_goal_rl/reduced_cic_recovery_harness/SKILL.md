---
name: reduced_cic_recovery_harness
description: Run a bounded soft-mode CIC proxy experiment that invokes generated batching, contrastive loss, and entropy reward skills.
---

# Reduced CIC Recovery Harness

Use this skill when full URLB CIC pretraining is blocked or too expensive and soft-mode recovery allows a declared mechanism-faithful proxy. The harness must invoke the generated CIC module scripts and produce validator-compatible recovery artifacts.

## Inputs

- `attempt_dir`: initialized Paper2Skills attempt directory.
- `skill_root`: directory containing the generated CIC module skills.
- `runtime_handoff`: environment handoff JSON from the prepare-recovery-environment stage.
- Optional seed and batch dimensions for deterministic reduced recovery.

## Outputs

- `recovery/recovery_result.json`.
- `recovery/logs/generated_data_item.json`.
- `recovery/logs/training_trace.json`.
- `recovery/logs/generated_skill_invocations.json`.
- Supporting metrics and mechanism checks.

## Workflow

1. Load the module-plan recovery target and runtime handoff.
2. Import the generated transition batching, CIC loss, and particle entropy scripts from `skill_root`.
3. Build a deterministic transition-skill proxy batch.
4. Compute CIC contrastive loss and kNN entropy rewards.
5. Run one dependency-free optimizer step on tiny linear encoders.
6. Save recovery artifacts with explicit proxy and reduced-training declarations.
7. Record invocation evidence for each core generated skill.

## Validation

Run:

```bash
python scripts/run_reduced_cic_recovery.py --attempt-dir <attempt_dir> --skill-root <skill_root>
python tests/test_reduced_harness.py
```

## Limitations

This harness does not claim full URLB results. It is a soft-mode proxy that validates the CIC mechanism under bounded runtime constraints.
