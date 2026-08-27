---
name: runner-and-backends
description: "Use MimicKit's shared runner, backend config triad, distributed
  device flow, logging/video flags, and backend readiness checks."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# runner-and-backends

Use this sub-skill when a user wants to:

- build or sanity-check a MimicKit train/test command
- choose or validate the engine / environment / agent config triad
- expand an `--arg_file` preset with safe CLI overrides
- reason about `--num_envs`, `--devices`, `--master_port`, `--logger`, `--video`, or `--out_dir`
- check whether a checkout still has the expected runner/layout files without importing simulator backends

Do **not** use this sub-skill for motion conversion, motion plotting, or algorithm-specific reward/loss tuning. Route those to the sibling sub-skills.

Start with these bundled references:

- `references/runner-cli.md`
- `references/backend-compatibility.md`
- `references/troubleshooting.md`

Use `scripts/check_mimickit_layout.py --repo-root <repo-root>` when you need a safe layout/config sanity check that does **not** import Isaac Gym, Isaac Lab, Newton, or Warp.

Use `scripts/run_mimickit.py --repo-root <repo-root> -- <runner flags>` when a recipe needs to launch the target checkout's runner through a bundled helper instead of invoking a source path directly.

## What this sub-skill should extract from a user request

1. Mode: `train` or `test`
2. Preset source: direct CLI flags or `--arg_file`
3. Engine / environment / agent config files
4. Device plan: single device or distributed `--devices` plus `--master_port`
5. Runtime toggles: `--num_envs`, `--visualize`, `--video`, `--logger`, `--out_dir`, `--model_file`

## Verified boundary

Current verification only confirms PyTorch CUDA works and source imports succeed with repo-style `PYTHONPATH`. It does **not** prove that Isaac Gym, Isaac Lab, or Newton are installed in the current environment. Treat simulator-native workflows as external prerequisites and describe them as such.

## Expected answer shape

When answering a user, give:

- the exact runner command shape they should use
- which engine / env / agent files belong together
- which backend prerequisites or data assets are still missing
- which output files to expect in training vs testing
- which troubleshooting branch to follow if the command fails
