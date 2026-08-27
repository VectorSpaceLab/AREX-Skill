# Troubleshooting

Native Isaac Gym training/play verification remains `BLOCKED_REQUIRED_BACKEND` until Isaac Gym Preview 4 is present and importable.

| Symptom | Likely cause | What to do | Scope |
|---|---|---|---|
| `ModuleNotFoundError: No module named 'isaacgym'` | Isaac Gym Preview 4 is not installed. | Install Isaac Gym manually, then retry native `train.py`/`play.py`. Do not treat CPU-only imports as proof of runtime readiness. | Blocks native training/play. |
| `python -m pip check` says `humanoid 1.0.0 requires isaacgym` | Same missing backend dependency. | Keep the skill in static/command-building mode until Isaac Gym is available. | Blocks native training/play. |
| `ImportError: libpython3.8.so.1.0: cannot open shared object file` | Python shared library not on the dynamic loader path. | Point `LD_LIBRARY_PATH` at the active environment's `lib` directory or install the matching `libpython3.8` package. | Backend/environment. |
| `AttributeError: module 'distutils' has no attribute 'version'` | Older Isaac Gym / Python stack mismatch noted in the README. | Use the README workaround: PyTorch 1.12.0 with the matching `cudatoolkit=11.3` stack if that compatibility issue appears. | Backend/environment. |
| `GLIBCXX_3.4.20 not found` | Conda's `libstdc++` conflicts with the system/Isaac Gym build. | Move the Conda-provided `libstdc++*` aside from the active environment's `lib` directory or align the C++ runtime stack. | Backend/environment. |
| CUDA works in PyTorch but train/play still fail | PyTorch/CUDA/driver mismatch or no Isaac Gym backend. | Use the repo's CUDA-era stack (`torch 1.13.1+cu117`) and a compatible NVIDIA driver, then re-check Isaac Gym import. | Backend/environment. |
| W&B login prompt, network stall, or account error | `OnPolicyRunner.learn` calls `wandb.init(...)` when logging is enabled. | Expect login/network side effects in training runs; preconfigure W&B or patch out logging if the run path must stay offline. | Training workflow side effect. |
| Wrong checkpoint is loaded | `get_load_path` chose the newest dated run/model, not the one you intended. | Supply `--load_run` and `--checkpoint` explicitly. Remember that `exported/` is ignored during run selection. | Checkpoint selection. |
| Custom run folder is skipped or sorted oddly | `get_load_path` expects timestamped run names and falls back to lexicographic sorting on parse failures. | Keep generated `MonDD_HH-MM-SS_<run_name>` directories or choose the load path explicitly. | Checkpoint selection. |
| `ValueError: Task with name ... was not registered` | The task was not registered before the entry point ran, or the task name is wrong. | Use `--task=humanoid_ppo` for the bundled task, or register the new task in `humanoid/envs/__init__.py`. | Task registry. |
| `headless` still writes video or opens a camera path | `play.py` hard-codes `RENDER=True` and creates a video writer. | Edit the source if you need a truly no-render run. The builder can only record intent. | Play workflow side effect. |
| Commands do not follow your controller intent | `play.py` hard-codes `FIX_COMMAND=True` and overwrites the command vector each step. | Edit the source if you need free command inputs during evaluation. | Play workflow side effect. |
| `sim_device` and `rl_device` disagree or GPU placement looks wrong | The README expects matching device choices; CUDA_VISIBLE_DEVICES is not the control knob here. | Use aligned settings such as `--sim_device=cpu --rl_device=cpu` or matching CUDA ordinals. | Launch configuration. |
| Large `--num_envs` causes OOM or sluggish smoke runs | 4096-env defaults are too large for smoke or limited VRAM. | Use a tiny smoke value like 1, 8, or 16 and cap `--max_iterations` to 1 for command validation. | Training smoke. |
| `play.py` cannot find a checkpoint | `load_run`/`checkpoint` do not match the actual logs layout. | Inspect `logs/<experiment_name>/<date_time>_<run_name>/model_<iteration>.pt` and remember that exported policies live in `exported/policies/`. | Checkpoint selection. |

## Minimum safe response when blocked

If Isaac Gym is unavailable:
1. Build the requested training or play command.
2. Explain the checkpoint selection logic if relevant.
3. State clearly that native Isaac Gym execution remains blocked.
4. Do not claim a successful training or evaluation run.
