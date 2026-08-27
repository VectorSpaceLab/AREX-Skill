# Cross-Cutting Troubleshooting

## Gym / PyBullet registry failure

**Symptom:** importing `a2c_ppo_acktr.envs` or modules that indirectly import it fails with an error like `AttributeError: 'dict' object has no attribute 'env_specs'`.

**Cause:** Old `pybullet_envs` registration code expects an older Gym registry object. Recent Gym versions changed that registry.

**Fix:** Use a Gym version compatible with `pybullet_envs` for this repository or patch the registration code. Verify with a package import and a safe model smoke before launching training.

## `h5py` missing for GAIL

**Symptom:** `ModuleNotFoundError: No module named 'h5py'` when using GAIL code or expert conversion.

**Cause:** `requirements.txt` includes `h5py`, but `setup.py` does not declare it.

**Fix:** Install `h5py` explicitly before using `gail-imitation` workflows.

## Gym unmaintained / NumPy warning

**Symptom:** Gym prints a warning about being unmaintained or not supporting NumPy 2.0.

**Cause:** This is a legacy Gym codebase. Some wrappers and simulators still depend on older Gym APIs.

**Fix:** Treat the warning as a compatibility signal. Do not blindly migrate to Gymnasium without auditing wrapper APIs, `env.seed`, monitor wrappers, and simulator packages.

## Optional simulator packages

Atari, MuJoCo, DeepMind Control Suite, and PyBullet workflows need optional packages/assets beyond base import checks. A package import smoke does not prove those environments can be created.

Before running an environment-specific command, verify the simulator stack with a tiny environment creation under the user's requested Gym version and hardware.

## CUDA expectations

CUDA is optional. The code chooses CUDA only when not passed `--no-cuda` and when `torch.cuda.is_available()` is true. A CPU-only package inspection environment can validate commands and model shapes, but it does not verify GPU training throughput or simulator performance.

## Long-running RL commands

README-style commands are real training jobs. They may run for millions of environment steps, create or clean monitor CSVs, and write checkpoints. Do not execute them unless the user has provided compute budget and output locations.

## Source-script self-containment

This skill bundles command builders, smoke checks, and GAIL conversion helpers. If a task needs to run the full training loop, make sure the user is operating a checkout or packaged copy that contains the training entrypoint and dependencies; use the bundled helpers to construct and validate commands before launching the long job.
