---
name: rnd_proxy_recovery_harness
description: Run a bounded Random Network Distillation proxy recovery experiment with executable evidence and generated-skill invocation logs.
---

# RND Proxy Recovery Harness

Use this skill when full Atari-scale RND training is blocked by runtime cost but soft-mode recovery permits a reduced, mechanism-faithful proxy. The harness should reproduce the paper's MNIST-style novelty intuition: a predictor distills a deterministic random target, and held-out target-class error decreases when more target examples are included.

## Inputs
- Attempt directory containing `module_plan.json` and generated skills.
- Runtime handoff JSON from environment preparation.
- Generated RND module skill paths.

## Outputs
- `recovery/recovery_result.json` with `novelty_mse_reduction_fraction`.
- `recovery/logs/training_trace.json` with loss and parameter changes.
- `recovery/logs/generated_data_item.json` describing proxy data.
- `recovery/logs/generated_skill_invocations.json` proving module usage.

## Workflow
1. Read the module-plan target and runtime handoff.
2. Create deterministic synthetic vectors for a frequent seen class and an under-sampled target class.
3. Normalize observations via `rnd_observation_normalization`.
4. Train a predictor against a frozen random target via `rnd_bonus_model` in low-target and high-target regimes.
5. Cross-check reward scaling and dual-return contracts with their generated skill scripts.
6. Write recovery artifacts and mechanism checks, marking the result as proxy/reduced.
7. Run the recovery experiment validator after the command completes.

## Validation
Run `python scripts/run_proxy_recovery.py --attempt-dir <attempt_dir> --skills-root <generated_skills_root>`. The command should produce all recovery artifacts and a positive reduction fraction.

## Limitations
This is not full Atari PPO training and must not be reported as full reproduction. It is acceptable only under soft recovery mode after recording the full-runtime blocker.
