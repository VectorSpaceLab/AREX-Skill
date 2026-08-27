# Training troubleshooting

## Quick triage order

1. Reproduce with a bounded module command and explicit CPU device:
   ```bash
   python -m rl_zoo3.train --algo ppo --env CartPole-v1 \
     --n-timesteps 100 --log-folder ./runs/triage --device cpu --seed 0 \
     --eval-freq -1 --save-freq -1
   ```
2. If the module command works but `rl_zoo3 train ...` fails before parsing train flags, use the console-entry guidance below.
3. If the failure is environment-specific, verify Gymnasium registration and optional environment packages before changing RL hyperparameters.
4. If the failure is continuation-specific, validate the zip path and replay-buffer/normalization files next to it.

## Failure matrix

| Symptom | Likely cause | Action |
| --- | --- | --- |
| `ENV_ID not found in gym registry, you maybe meant ...?` | Typo, Gymnasium version suffix mismatch, missing optional env package, or custom env registration module was not imported. | Check the env id spelling and version suffix. For custom envs, add `--gym-packages your_registration_module`. For optional env families, install the package that registers the env. Use `python -m rl_zoo3.train` after package installation to avoid console-router issues while debugging. |
| Closest match is unrelated or says no close match | The desired environment is not registered at all in this Python process. | Confirm that importing the intended package registers the id: `python -c "import gymnasium as gym; import your_registration_module; print('MyEnv-v0' in gym.envs.registry)"`. If false, fix the package's registration code or `--env` id. |
| Import error for Atari, MuJoCo, Box2D, PyBullet, highway, Minigrid, robotics, or other env families | RL Zoo core install does not include every simulator stack or dataset/ROM requirement. | Install only the optional environment package needed for the chosen env. For smoke tests, switch to `CartPole-v1` or `Pendulum-v1`. For custom package details, route to `../../custom-components/SKILL.md`. |
| Assertion: trained agent must be a valid `.zip` path | `--trained-agent` path does not exist, is a directory, or does not end in `.zip`. | Locate the actual final model zip under `log_folder/algo/env_id_runid/env_id.zip`, or route to `../../evaluation-and-artifacts/SKILL.md` for artifact inspection. Do not pass the run folder itself. |
| Continue training loads model but not replay history | `replay_buffer.pkl` is missing next to the zip, algorithm does not support replay buffers, or previous run omitted `--save-replay-buffer`. | For off-policy algorithms, rerun/save with `--save-replay-buffer`. Put `replay_buffer.pkl` in the same folder as the zip passed to `--trained-agent`. Use `--expect-replay-buffer` in the command builder to catch missing buffers before launch. |
| Replay-buffer continuation fails on algorithm capability | On-policy algorithms such as PPO/A2C/TRPO/ARS do not use replay buffers; some model classes may not expose `load_replay_buffer`. | Only expect replay-buffer persistence for off-policy replay-buffer algorithms such as DQN, QRDQN, DDPG, SAC, TD3, TQC, and CrossQ. Remove buffer assumptions for on-policy algorithms. |
| Unexpected evaluation/checkpoint frequency | RL Zoo divides positive `--eval-freq` and `--save-freq` by configured `n_envs`. | Compute `max(requested_freq // n_envs, 1)`. If using `--hyperparams n_envs:8`, a requested `--eval-freq 10000` becomes callback frequency `1250`. Increase requested frequency or reduce `n_envs` if callbacks are too frequent. |
| `rl_zoo3 train ...` fails on plotting imports or plotting dependencies | The console entry point imports the CLI router, which imports plot modules even for train/enjoy subcommands. Base installs may not include plotting extras. | Use `python -m rl_zoo3.train ...` for training. If console form is required, install compatible plotting extras as described by `../../../references/install-and-environment.md`. |
| CUDA/device error or no accelerator is visible | `--device cuda` was requested without a compatible PyTorch/CUDA runtime, or the host has no accessible GPU. | Use `--device cpu` for portable runs. Use `--device auto` only if fallback behavior is acceptable. Verify accelerator availability separately before long CUDA training. |
| Run unexpectedly takes a long time | Config default `n_timesteps` can be large; simulator envs and multiple envs can be expensive. | Always smoke-test with `--n-timesteps 100` or `1000`. Set `--save-freq` and `--eval-freq` for resumability. Use `--device cpu` and simple envs for logic checks. Do not launch hard-coded multi-seed or cluster-style ablation loops unless explicitly requested. |
| Output directory collision or mixed artifacts | Multiple commands write under the same `--log-folder` and env id. | Add `--uuid` for concurrent launches or give each run a separate `--log-folder`. Check the emitted `Log path:` line to know the exact run folder. |
| `--env-kwargs`, `--eval-env-kwargs`, or `--hyperparams` parse incorrectly | Tokens use `key:python_expression` and are evaluated by RL Zoo after shell parsing. Strings and dictionaries require careful shell quoting. | Quote each token as one shell argument. For string values, pass nested quotes such as `name:"'value'"`. For complex config grammar, route to `../../config-hyperparams/SKILL.md`. |
| `--vec-env subproc` fails but `dummy` works | Subprocess vectorization requires picklable env constructors and importable registration/wrapper modules in worker processes. | Retry with `--vec-env dummy`. Ensure `--gym-packages` modules are importable from worker processes. Move non-picklable closures out of env construction. |
| `--track` fails with missing `wandb` or authentication/service errors | W&B is optional and can require package install, credentials, and network access. | Remove `--track` for local training, or route to `../../integrations-hub-tracking/SKILL.md` before enabling service tracking. |
| Progress bar output corrupts logs | `--progress` emits rich/tqdm terminal control output. | Omit `--progress` for plain text logs, CI, or non-interactive capture. |
| Hyperparameters not found for `algo-env` | Selected config lacks an env-specific entry, and no `default` fallback applies. | Choose an env/algo pair represented in the config, pass a custom `--conf-file` with the env id or `default` entry, or route to `../../config-hyperparams/SKILL.md`. |

## Environment registration diagnostic

For a missing env id, run this from the target Python environment, replacing package/env names:

```bash
python - <<'PY'
import gymnasium as gym
# import your_registration_module  # uncomment for custom env packages
needle = "CartPole-v1"
print(needle, needle in gym.envs.registry)
print([env_id for env_id in gym.envs.registry if needle.split('-')[0] in env_id][:20])
PY
```

If the env appears only after importing a module, include that module with `--gym-packages` in the RL Zoo training command.

## Continuation diagnostic

Check the exact files before a resume command:

```bash
python - <<'PY'
from pathlib import Path
zip_path = Path("./runs/sac-buffer/sac/Pendulum-v1_1/Pendulum-v1.zip")
print("zip exists:", zip_path.is_file(), zip_path)
print("replay buffer exists:", (zip_path.parent / "replay_buffer.pkl").is_file())
print("vecnormalize exists:", (zip_path.parent / "Pendulum-v1" / "vecnormalize.pkl").is_file())
PY
```

Only the zip is required for generic continuation. The replay buffer is optional and algorithm-dependent; normalization stats are used when present.

## Safer command construction

Use the bundled builder before expensive runs:

```bash
python ../scripts/train_command_builder.py --algo sac --env Pendulum-v1 \
  --n-timesteps 1000 --log-folder ./runs/sac-buffer \
  --save-replay-buffer --hyperparams buffer_size:1000 \
  --env-kwargs g:8.0 --eval-env-kwargs g:5.0 \
  --eval-freq 500 --save-freq 500 --seed 7 --device cpu
```

The builder does not validate Gymnasium registration or train a model; it catches command-shape problems such as missing timesteps, invalid algorithms, unsafe continuation paths, malformed `key:value` tokens, and frequency/n-env surprises.
