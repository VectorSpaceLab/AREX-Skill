---
name: vae_recovery_evaluation
description: Convert VAE/AEVB proxy training traces into auditable recovery_result.json artifacts with target matching and mechanism checks.
---

# VAE Recovery Evaluation

Use this skill after a VAE training trace has been produced. It checks that the recovery target matches the module plan and that the trace proves the core paper mechanism ran.

## Inputs
- `module_plan.json` with `fast_recovery_target`.
- Training trace JSON from `aevb_vae_core`.
- Runtime handoff path.
- Command and artifact paths.

## Outputs
- Recovery result JSON with numeric `loss_delta`, proxy declaration, paper target metadata, commands, artifacts, and mechanism checks.

## Workflow
1. Preserve target metadata from `module_plan.json`.
2. Read before/after total loss and compute or verify `loss_delta`.
3. Require encoder, reparameterization, decoder, reconstruction loss, KL, and optimizer checks; fail closed if any core mechanism check is missing or false.
4. Mark the result as proxy when the plan target is proxy.
5. Record limitations and source-boundary notes.

## Validation
Run:

```bash
python scripts/build_recovery_result.py --module-plan module_plan.json --trace recovery/logs/training_trace.json --output recovery/recovery_result.json
python tests/test_recovery_evaluation.py
```

## Limitations
This skill evaluates recovery evidence; it does not train a VAE by itself and cannot make a reduced proxy equivalent to full dataset training.
