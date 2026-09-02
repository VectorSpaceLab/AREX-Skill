---
name: fid_activation_statistics
description: Compute FID-style activation mean/covariance summaries for generated or real feature matrices.
---

# Fid Activation Statistics

Use this skill when a recovery or implementation needs the `fid_statistics` module from the TTUR/FID paper without rereading the original repository. Do not use it to claim full GAN reproduction unless real image features, dataset statistics, and training evidence are available.

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
Run `python tests/test_fid_activation_statistics.py` from this skill directory.

## Limitations
This skill is self-contained and does not require the original TTUR repository. It does not download Inception models or train full GANs.
