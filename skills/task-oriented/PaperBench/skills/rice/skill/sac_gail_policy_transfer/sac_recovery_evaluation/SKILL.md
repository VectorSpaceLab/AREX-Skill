---
name: sac_recovery_evaluation
description: Score reduced Soft Actor-Critic recovery traces for mechanism fidelity and source boundary compliance.
---

# SAC Recovery Evaluation

Use this skill after a bounded SAC recovery run has produced a trace. It decides whether the proxy exercised the paper mechanism. Do not use it as a substitute for executing the recovery command.

## Inputs
- Mechanism checks from `recovery_result.json`.
- Training trace with losses and parameters before/after.
- Generated skill invocation records.
- Source-boundary flags.

## Outputs
- `mechanism_pass_rate`.
- Failed check names.
- Boolean `ok` for proxy acceptance evidence.

## Workflow
1. Verify entropy, replay, twin-Q, critic, actor, target, and optimizer checks.
2. Verify losses and parameters changed in the trace.
3. Verify generated skills were invoked.
4. Verify no original repository source was used in recovery.

## Validation
Run `python tests/test_evaluation.py` or validate the full skill tree with the Distiller validator.

## Limitations
This skill validates reduced/proxy evidence only; final acceptance still belongs to the Distiller analysis step.
