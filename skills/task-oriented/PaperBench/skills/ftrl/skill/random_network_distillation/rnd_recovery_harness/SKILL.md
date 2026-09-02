---
name: rnd_recovery_harness
description: Run a bounded soft-mode recovery experiment that validates core RND mechanism evidence without Atari-scale training.
---

# RND Recovery Harness

Use this skill when full Atari PPO training is blocked but soft-mode recovery allows a declared, mechanism-faithful proxy. Do not claim full paper reproduction from this harness.

## Inputs

- Attempt directory with `module_plan.json` and runtime handoff.
- Generated RND module skill directories.
- Optional synthetic-data configuration.

## Outputs

- Executable recovery result JSON with numeric novelty margin.
- Generated data item and training trace.
- Generated-skill invocation log and source manifest.
- Mechanism checks proving target/predictor distillation, optimizer update, normalization, and dual-return semantics ran.

## Workflow

1. Build frequent and rare synthetic observation clusters.
2. Normalize observations using the generated normalization skill.
3. Train the predictor on frequent observations using the generated RND intrinsic reward skill.
4. Compute held-out frequent and rare errors and novelty margin.
5. Run the dual-return helper to verify reward stream semantics.
6. Save validator-compatible artifacts.

## Validation

Run `python tests/test_recovery_harness.py` from this skill directory. In a Distiller attempt, run the generated `recovery/run_recovery.py` and then the Distiller recovery validator.

## Limitations

This is a reduced proxy and intentionally does not run Atari, PPO rollouts, or a deep convolutional policy.
