---
name: msfm_synthetic_recovery
description: Run a bounded synthetic MSFM proxy experiment that invokes generated coupling and Joint CFM loss skills.
---

# MSFM Synthetic Recovery

Use this skill when full image-scale MSFM recovery is blocked but soft-mode reduced recovery is allowed. It constructs a fresh synthetic 2D source/target batch, compares uniform CondOT and BatchOT pairings, and executes a real optimizer update under the Joint CFM objective.

Do not use this skill to claim full ImageNet or large-model reproduction.

## Inputs

- Seed, batch size, and optimizer settings.
- Paths to `msfm_batch_coupling/scripts/coupling.py` and `msfm_joint_cfm_loss/scripts/joint_cfm.py`.
- Output directory for recovery logs.

## Outputs

- `generated_data_item.json` with source and target samples.
- `training_trace.json` with loss before/after and `params_before`/`params_after`.
- `recovery_result.json`-compatible metric summary.
- Generated skill invocation evidence.

## Workflow

1. Generate deterministic Gaussian-mixture-like 2D source and target samples from the seed.
2. Call the coupling skill for uniform and BatchOT couplings.
3. Reorder pairs according to BatchOT and call the Joint CFM loss skill.
4. Run one or more real gradient updates on a tiny affine vector field.
5. Save transport-cost reduction, loss change, mechanism checks, and invocation records.

## Validation

Run:

```bash
python scripts/run_synthetic_recovery.py --self-test
python tests/test_synthetic_recovery.py
```

## Limitations

- This is a declared mechanism-faithful proxy, not a full reported paper metric.
- The tiny affine model tests objective execution and optimization evidence only.
