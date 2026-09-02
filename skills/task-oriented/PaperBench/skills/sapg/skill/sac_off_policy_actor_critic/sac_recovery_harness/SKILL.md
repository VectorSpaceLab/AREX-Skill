---
name: sac_recovery_harness
description: Execute a bounded reduced SAC recovery experiment that combines generated objective, backup, and actor-update skills into validation artifacts.
---

# SAC Recovery Harness

Use this skill when the full SAC MuJoCo training stack is unavailable or too expensive, but soft-mode recovery permits an executable mechanism-faithful proxy. The harness must call or cross-check generated SAC module scripts rather than duplicating every mechanism silently.

## Inputs
- Attempt directory with module plan and runtime handoff.
- Paths to generated SAC skills.
- A deterministic reduced replay batch.

## Outputs
- `recovery/recovery_result.json`.
- `recovery/logs/generated_data_item.json`.
- `recovery/logs/training_trace.json`.
- invocation evidence for generated skills.

## Workflow
1. Load the module plan target and runtime handoff.
2. Construct a small continuous-control replay batch with rewards, done flags, Q estimates, and log probabilities.
3. Invoke the maximum-entropy, soft-Bellman, and actor-update helpers.
4. Apply one reduced optimizer update and record before/after losses and parameters.
5. Mark the run as proxy/reduced and never as full MuJoCo performance.

## Validation
Run the recovery command and then the Distiller recovery experiment validator.

## Limitations
This harness validates mechanism transfer only. It does not reproduce the reported MuJoCo return curves.
