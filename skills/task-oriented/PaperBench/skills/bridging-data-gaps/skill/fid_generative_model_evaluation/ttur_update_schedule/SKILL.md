---
name: ttur_update_schedule
description: Run deterministic two-time-scale update traces for GAN-style min-max proxy dynamics.
---

# Ttur Update Schedule

Use this skill when a recovery or implementation needs the `ttur_schedule` module from the TTUR/FID paper without rereading the original repository. Do not use it to claim full GAN reproduction unless real image features, dataset statistics, and training evidence are available.

## Inputs
- Numeric arrays or JSON files matching the module contract.
- For recovery orchestration, a module-plan target and runtime handoff.

## Outputs
- Deterministic JSON-compatible statistics, distances, traces, or recovery checks.
- Diagnostics sufficient to audit reduced/proxy recovery.

## Workflow
1. Validate input shapes and finite numeric values.
2. Execute the module-specific deterministic script in `scripts/`.
3. Preserve diagnostics and command evidence when used in recovery.
4. Treat synthetic activations or toy dynamics as proxy evidence only.

## Validation
Run `python tests/test_ttur_update_schedule.py` from this skill directory.

## Limitations
This skill is self-contained and does not require the original TTUR repository. It does not download Inception models or train full GANs.

## Refinement Note
Include an equal-rate ablation when possible; it should set `separate_rates` false so TTUR evidence cannot be satisfied by a single shared learning rate.
