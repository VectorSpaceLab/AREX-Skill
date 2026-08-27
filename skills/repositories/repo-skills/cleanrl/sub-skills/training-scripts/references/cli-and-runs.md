# CLI Flags and Run Behavior

CleanRL training scripts are direct Python entry points. Most current scripts use a dataclass named `Args` with `tyro.cli(Args)`, so field names become kebab-case flags such as `--total-timesteps` and boolean flags support `--flag` / `--no-flag`. The PettingZoo multi-agent Atari script uses argparse and has a few value-style booleans.

## Common Flags

| Flag | Typical meaning | Safe guidance |
| --- | --- | --- |
| `--env-id` | Gym/Gymnasium/Procgen/PettingZoo/EnvPool/IsaacGym environment id | Match the script family; do not use Atari `NoFrameskip-v4` ids with EnvPool `-v5` scripts. |
| `--total-timesteps` | Total interaction budget | Always lower for smoke runs; defaults are often hundreds of thousands to billions. |
| `--seed` | Experiment seed | Keep explicit for reproducible tiny runs. |
| `--cuda` / `--no-cuda` | Whether to use CUDA if available | Use `--no-cuda` for tyro CPU smoke runs; PettingZoo argparse uses `--cuda False`. |
| `--num-envs` | Number of vectorized envs | Reduce for local smoke except EnvPool/PettingZoo candidates that expect a minimum vector count. |
| `--num-steps` | On-policy rollout horizon | Keep `total_timesteps >= num_envs * num_steps` so at least one update can happen. |
| `--num-minibatches` | PPO/Procgen/EnvPool minibatch split | Keep compatible with the small batch size; reduce to `1` or `2` for tiny tests. |
| `--learning-starts` | Replay-buffer warmup before gradient updates | For tiny replay smoke, set below `--total-timesteps`. |
| `--buffer-size` | Replay buffer capacity | For tiny replay smoke, keep at or above `--batch-size` and `--learning-starts`. |
| `--batch-size` | Batch size for updates | Reduce for tiny replay smoke; common native candidates use `4`, `32`, or `128` depending on family. |
| `--track` / `--no-track` | Enable W&B logging | Leave disabled unless the user has logged in and explicitly asks for W&B. |
| `--capture-video` / `--no-capture-video` | Record videos from first env | Leave disabled for headless smoke; enable only after render dependencies work. |
| `--save-model` / `--no-save-model` | Save model to the run directory | Enable only when local artifact output is required; route artifact checks to evaluation-and-sharing. |
| `--upload-model` / `--no-upload-model` | Upload saved model to Hugging Face | Requires save behavior plus credentials/network; route details to evaluation-and-sharing. |

## Tyro vs Argparse Boolean Syntax

Most dataclass/tyro scripts accept this style:

```bash
python cleanrl/ppo.py --total-timesteps 256 --no-cuda --no-track --no-capture-video
```

The PettingZoo script uses argparse value booleans and defines `--capture_video` with an underscore:

```bash
python cleanrl/ppo_pettingzoo_ma_atari.py --total-timesteps 256 --cuda False --track False --capture_video False
```

When unsure, run `python <script> --help` first. Help checks are safer than real runs when optional backends may be absent.

## Run Output Layout

CleanRL scripts build a run name like:

```text
{env_id}__{exp_name}__{seed}__{timestamp}
```

Expected local outputs are:

- TensorBoard event files under `runs/{run_name}` for most scripts using `SummaryWriter`.
- Console prints such as `global_step=...`, `episodic_return=...`, and `SPS: ...` when episodes finish or losses are logged.
- Videos under `videos/{run_name}` when video capture is enabled and rendering/moviepy/imageio dependencies work.
- Model files under `runs/{run_name}/{exp_name}.cleanrl_model` for scripts that implement `--save-model`.
- Optional eval videos or Hugging Face upload side effects only when `--upload-model` is requested; use evaluation-and-sharing for those workflows.

## Conservative Tiny-Run Patterns

Use the bundled command builder instead of hand-writing from memory:

```bash
python sub-skills/training-scripts/scripts/build_tiny_run_command.py classic-ppo
python sub-skills/training-scripts/scripts/build_tiny_run_command.py replay-classic --script cleanrl/c51.py
```

Common tiny patterns:

| Family | Pattern | Why |
| --- | --- | --- |
| Classic PPO | `--num-envs 1 --num-steps 64 --total-timesteps 256 --no-cuda` | Completes several small rollout/update cycles on CPU. |
| Classic DQN/C51/PQN replay | `--learning-starts 10 --total-timesteps 16 --buffer-size 10 --batch-size 4 --no-cuda` | Avoids the common failure where total timesteps end before learning starts. |
| Atari replay | Same replay shape plus Atari-compatible env id only after ROM setup | Verifies training loop shape without long defaults. |
| Continuous PPO/RPO | `--env-id Hopper-v4 --num-envs 1 --num-steps 64 --total-timesteps 128 --no-cuda` | Requires MuJoCo; keeps rollout small. |
| DDPG/TD3 continuous | `--env-id Hopper-v4 --learning-starts 100 --batch-size 32 --total-timesteps 105 --no-cuda` | Mirrors native smoke shape and forces at least a few post-warmup steps. |
| SAC continuous | `--env-id Hopper-v4 --batch-size 128 --total-timesteps 135 --no-cuda` | Native smoke evidence uses a larger batch; MuJoCo required. |
| Procgen PPO/PPG | `--num-envs 1 --num-steps 64 --total-timesteps 256 --num-minibatches 2`; PPG adds `--n-iteration 1` | Reduces default 64-env, 25M-step setup. |
| EnvPool XLA | `--num-envs 8 --num-steps 6 --update-epochs 1 --num-minibatches 1 --total-timesteps 256` | Native smoke shape; still requires EnvPool/JAX. |
| PettingZoo | `--num-steps 32 --num-envs 6 --total-timesteps 256 --cuda False` | Matches multi-agent vectorization expectations. |

## Tracking, Video, Save, and Upload

- `--track` imports and initializes W&B. If the user has not run `wandb login`, expect authentication or offline-mode issues. For normal smoke tests, keep tracking off.
- `--capture-video` wraps the first environment with video recording. It can fail from missing render modes, display/OpenGL problems, `moviepy`, `imageio-ffmpeg`, or unsupported env render behavior. Leave it off until the run works without video.
- `--save-model` is local and useful for artifact/evaluation tasks, but it only exists in selected scripts. Inspect first before adding it.
- `--upload-model` is network/credential dependent and should not be used as part of a local training smoke. If requested, first ensure the script saves a model and route the upload details to evaluation-and-sharing.

## Choosing Help vs Execution

Prefer help-only inspection when:

- The script imports optional systems at module import time, such as EnvPool, JAX, Procgen, PettingZoo, MuJoCo, memory-gym, or IsaacGym.
- The user only needs flags/defaults or algorithm selection.
- The requested family needs GPUs or external simulator licenses.
- The command includes W&B, Hugging Face, cloud, or benchmark sweep behavior.

Run a tiny command only when the required backend is present, the command is bounded, and side-effect flags are disabled.

## Adapting Script Flags Safely

1. Inspect the script with `inspect_cleanrl_script.py`.
2. Identify whether it is on-policy, replay-buffer, or specialized backend.
3. Start from `build_tiny_run_command.py` for the closest family.
4. Change only environment id, seed, and the minimal timestep/batch flags needed for the user's goal.
5. Keep output under local `runs/` and `videos/`; do not assume remote tracking/upload.
6. If the smoke command fails because an optional package is absent, document the missing extra and stop instead of broad-installing all extras.
