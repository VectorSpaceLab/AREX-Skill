# Training Script Troubleshooting

Use this guide when a CleanRL training command fails before or during a local smoke run. Prefer diagnosing the selected script family and optional backend over installing every extra.

## Install and Import Failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `Requires-Python` or syntax/runtime mismatch | CleanRL metadata supports Python `>=3.8,<3.11` | Use a supported Python 3.8-3.10 environment. Do not recommend Python 3.11+ for this version. |
| `ModuleNotFoundError: tyro`, `torch`, `gym`, `gymnasium`, or `wandb` | Base package dependencies missing or environment not activated | Install the base CleanRL package/dependencies in the active environment before optional extras. |
| `ModuleNotFoundError: ale_py`, `AutoROM`, `shimmy`, or Atari env missing | Atari extra and/or ROMs are missing | Use the Atari dependency set and complete ROM/license setup before running Atari scripts. |
| `ModuleNotFoundError: jax`, `flax`, `optax`, `chex` | JAX extra missing | Install the JAX dependency set compatible with platform/CUDA; use help-only inspection until installed. |
| `ModuleNotFoundError: envpool` | EnvPool extra missing | Install the EnvPool dependency set before `*_envpool*.py`; EnvPool Atari ids are usually `Breakout-v5` style. |
| `ModuleNotFoundError: mujoco`, `dm_control`, or `h5py` | MuJoCo or DM Control extra missing | Install only the needed continuous-control extra; do not use MuJoCo commands as base smoke tests. |
| `ModuleNotFoundError: procgen` or `gym3` | Procgen extra missing | Use the Procgen dependency set before `ppo_procgen.py` or `ppg_procgen.py`. |
| `ModuleNotFoundError: pettingzoo`, `supersuit`, or `multi_agent_ale_py` | PettingZoo multi-agent extra missing | Use the PettingZoo dependency set; remember the script uses argparse boolean syntax. |
| `ModuleNotFoundError: memory_gym`, `minigrid`, or `einops` | PPO-TrXL nested requirements missing | Prepare the PPO-TrXL dependency set before running memory tasks. |
| IsaacGym import/task errors | IsaacGym simulator stack not installed or not GPU-ready | Treat IsaacGym PPO as a specialized backend; verify simulator install, CUDA, and task assets before execution. |

## Gym, Gymnasium, and NumPy Warnings

- Gym `0.23.1` can emit an upstream warning about NumPy 2 or Gym being unmaintained. A warning during help/import is not by itself a training failure.
- Do not silence warnings by changing algorithm code unless the task is repository maintenance.
- If an environment id fails, check whether the script expects Gym classic control (`CartPole-v1`), Gymnasium MuJoCo (`Hopper-v4`), Atari NoFrameskip (`BreakoutNoFrameskip-v4`), EnvPool Atari (`Breakout-v5`), Procgen (`starpilot`), PettingZoo (`pong_v3`), DM Control (`dm_control/cartpole-balance-v0`), or IsaacGym (`Ant`) naming.

## CUDA and Torch Failures

| Symptom | Recovery |
| --- | --- |
| `torch.cuda.is_available()` is false but the script starts | Use `--no-cuda` for tyro scripts or `--cuda False` for argparse PettingZoo smoke runs. |
| CUDA library, driver, or NCCL mismatch | Use a CPU smoke command first; only debug GPU after torch/CUDA versions and drivers match. |
| `ppo_atari_multigpu.py` fails under plain Python | Launch distributed smoke with `torchrun --standalone --nnodes=1 --nproc_per_node=<n> ...`; do not use it as a default local script. |
| XLA/JAX GPU errors | Try CPU JAX help/import first; match `jaxlib` to CUDA only when GPU acceleration is required. |

## Tiny Run Fails Before Learning

Replay-buffer algorithms can complete the tiny command without training if warmup exceeds the total budget.

- For DQN/C51/Rainbow/QDagger Atari and classic DQN/C51, set `--learning-starts` below `--total-timesteps`, such as `10` and `16`.
- Keep `--buffer-size >= --batch-size`; native tiny candidates often use `--buffer-size 10 --batch-size 4` for Atari replay scripts.
- For DDPG/TD3, native smoke candidates use `--learning-starts 100 --batch-size 32 --total-timesteps 105`.
- For PPO-style scripts, ensure `--total-timesteps` is at least `--num-envs * --num-steps` and reduce `--num-minibatches` if the derived batch is tiny.

## Atari and ROM Issues

- Atari scripts using `NoFrameskip-v4` need Atari dependencies and ROM availability.
- EnvPool Atari scripts use Gymnasium-style ids such as `Breakout-v5`; do not substitute `BreakoutNoFrameskip-v4` into EnvPool scripts.
- ROM license acceptance may be required before a real Atari run can create environments.
- Video capture on Atari can add OpenCV/moviepy/render dependencies; first run without `--capture-video`.

## W&B Tracking Problems

| Symptom | Recovery |
| --- | --- |
| `wandb` asks for login or API key | Disable tracking with `--no-track` for tyro scripts or `--track False` for PettingZoo; only enable after `wandb login` or a deliberate offline setup. |
| Run hangs or fails from network access | Keep tracking off for smoke tests; route benchmark/report workflows to experiment-operations. |
| User wants W&B project/entity tags | Confirm credentials and use `--wandb-project-name` / `--wandb-entity`; do not print secrets. |

## Video Capture Problems

- `--capture-video` can fail from missing `moviepy`, `imageio-ffmpeg`, OpenCV, render mode support, or headless display/OpenGL setup.
- Disable video first and prove training works; then add video capture to one env only.
- PettingZoo uses `--capture_video`, not `--capture-video`.
- Some environments require `render_mode="rgb_array"`; script wrappers usually set this only when video is enabled.

## MuJoCo and DM Control Problems

- MuJoCo commands require the `mujoco` dependency set; DM Control env ids additionally need `dm_control` dependencies.
- Headless rendering can fail even when training works. Disable video and focus on environment creation first.
- If `Hopper-v4` is unavailable, confirm the installed Gymnasium/MuJoCo combination rather than switching algorithms.
- For RPO/PPO continuous, use tiny on-policy flags; for TD3/DDPG/SAC, use replay-friendly learning-start/batch settings.

## EnvPool, Procgen, PettingZoo, PPO-TrXL, and IsaacGym

- EnvPool: Missing `envpool` or wrong env id family is the most common issue. XLA variants also require JAX. Use help checks before execution.
- Procgen: Missing `procgen`/`gym3` or graphics libraries can fail environment creation. Use one env and tiny minibatches for smoke.
- PettingZoo: Use argparse syntax and ensure `--num-envs` is compatible with vectorization; native smoke uses `6`.
- PPO-TrXL: Memory-gym/minigrid/einops dependencies are separate from base CleanRL. Defaults are large memory tasks, not smoke tests.
- IsaacGym: Requires specialized simulator installation and typically GPU/CUDA. Do not promise CPU-only smoke for IsaacGym PPO.

## Save and Upload Issues

- `--save-model` only exists in selected scripts; inspect before adding it.
- A saved model path usually lands under `runs/{run_name}/{exp_name}.cleanrl_model`.
- `--upload-model` requires local save behavior plus Hugging Face credentials and network access; route upload/evaluation details to evaluation-and-sharing.
- If a smoke task only needs to prove training starts, leave both save and upload disabled.

## Diagnostic Order

1. Run `inspect_cleanrl_script.py` on the selected script to confirm flags and defaults without imports.
2. Run `python <script> --help` if the optional backend is expected to be installed.
3. Build a bounded command with `build_tiny_run_command.py`.
4. Disable CUDA, W&B, video, save, and upload unless they are the explicit target.
5. If failure names an optional package or simulator, document the missing extra/backend and stop for user approval before environment mutation.
