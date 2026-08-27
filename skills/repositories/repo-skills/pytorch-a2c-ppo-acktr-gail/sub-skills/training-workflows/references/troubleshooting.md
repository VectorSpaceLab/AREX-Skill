# Training Workflow Troubleshooting

## Stale `--tau` flag

**Symptom:** `error: unrecognized arguments: --tau 0.95`.

**Cause:** Historical batch templates use `--tau`, but the current parser exposes `--gae-lambda`.

**Fix:** Replace `--tau 0.95` with `--gae-lambda 0.95`. The bundled command builder emits only `--gae-lambda`.

## Gym / PyBullet compatibility

**Symptom:** importing environment wrappers fails with `registry.env_specs` or other Gym registry errors.

**Cause:** Old `pybullet_envs` releases expect pre-0.26 Gym registry internals, while recent Gym/Gymnasium changed the registry.

**Fix:** Use a compatible Gym version for this code path, or patch the PyBullet environment registration layer. For inspection, Gym 0.23.x kept the registry interface used by `pybullet_envs`.

## Atari dependencies missing

**Symptom:** `gym.make("PongNoFrameskip-v4")` fails, ROMs are missing, or Atari wrappers cannot import.

**Cause:** Atari/ALE extras and ROM setup are optional and are not installed by the base package metadata.

**Fix:** Install Gym Atari/ALE support matching the Gym version and verify with a tiny environment creation before training. Do not treat package import as proof that Atari is ready.

## MuJoCo / DeepMind Control dependencies missing

**Symptom:** `gym.make("Reacher-v2")`, `HalfCheetah-v2`, or `dm.<domain>.<task>` fails.

**Cause:** Simulator runtimes and bindings are optional. DeepMind Control Suite also requires `dmc2gym`.

**Fix:** Install and verify the simulator stack separately. Use `--use-proper-time-limits` for MuJoCo-like control tasks once the environment runs.

## Training appears stuck or takes too long

**Symptom:** no quick completion from a command copied from the README.

**Cause:** The documented commands are real training runs with up to millions of environment steps and multiple subprocesses.

**Fix:** For smoke checks, do not run full training. Use `--help`, the command builder, or a deliberately tiny `--num-env-steps` with a disposable `--log-dir` only after the user asks to execute.

## Checkpoint playback fails

**Symptom:** `enjoy.py` cannot find the checkpoint or fails to unpack the loaded object.

**Cause:** Training saves `[actor_critic, obs_rms]` under `<save-dir>/<algo>/<env-name>.pt`; playback expects `--load-dir` to point at the algorithm subdirectory.

**Fix:** Confirm the saved path and pass the algorithm subdirectory, for example `--load-dir trained_models/ppo`. Keep `obs_rms` with the policy for normalized vector environments.

## Recurrent policy with ACKTR

**Symptom:** assertion error saying recurrent policy is not implemented for ACKTR.

**Cause:** `arguments.py` forbids `--recurrent-policy --algo acktr`.

**Fix:** Use `--algo a2c` or `--algo ppo` for recurrent policies, or implement recurrent ACKTR support before enabling that combination.

## CUDA expectations

**Symptom:** task expects CUDA acceleration but training runs on CPU or import says CUDA is unavailable.

**Cause:** CUDA is optional. The parser sets `args.cuda = not args.no_cuda and torch.cuda.is_available()`; a CPU torch wheel or missing device makes this false.

**Fix:** Install a compatible CUDA torch build and verify `torch.cuda.is_available()` before claiming GPU coverage. Use `--no-cuda` for deterministic CPU debugging.
