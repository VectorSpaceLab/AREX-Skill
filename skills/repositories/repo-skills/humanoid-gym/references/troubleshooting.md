# Troubleshooting

## Cross-cutting failures

| Symptom | Likely cause | Recovery | Route |
|---|---|---|---|
| `ModuleNotFoundError: No module named 'isaacgym'` | Isaac Gym Preview 4 is missing. | Keep to static guidance or install Isaac Gym manually before native training/evaluation. | training-and-evaluation |
| `python -m pip check` complains about `isaacgym` | Same missing backend dependency. | Do not treat the environment as ready for native Isaac Gym execution. | training-and-evaluation |
| `ImportError: libpython3.8.so.1.0` | Python shared library is not available to the runtime loader. | Align `LD_LIBRARY_PATH` with the active environment or install the matching Python library package. | backend |
| `AttributeError: module 'distutils' has no attribute 'version'` | Known Python/PyTorch/Isaac Gym compatibility issue noted by the README. | Use the repo's documented older PyTorch/CUDA stack if this appears. | backend |
| `GLIBCXX_3.4.20 not found` | `libstdc++` mismatch between Conda and the Isaac Gym build. | Align the C++ runtime or move aside the conflicting Conda `libstdc++*` as described in the README. | backend |
| `ValueError: Task with name ... was not registered` | A task was not registered before CLI use, or the task string is wrong. | Use `humanoid_ppo` for the bundled task or register the new task in `humanoid/envs/__init__.py`. | environment-customization |
| Checkpoint path confusion | `get_load_path` sorts timestamped runs and ignores `exported/`. | Pass `--load_run` and `--checkpoint` explicitly when resuming. | training-and-evaluation |
| `headless` still produces render/video side effects | `play.py` hard-codes `RENDER=True` and camera/video creation. | Edit the source if you need a true no-render evaluation. | training-and-evaluation |
| Policy rollout fails in MuJoCo but validator passes | Display/OpenGL or viewer runtime problem. | Use the sim2sim validator first; then debug viewer/display separately. | sim2sim-deployment |
| Policy shape mismatch | Frame stack, observation size, or action count changed. | Reconcile config changes with the 705/12 policy contract before export. | sim2sim-deployment |

## When to stop

If the missing piece is Isaac Gym Preview 4, a compatible NVIDIA driver/CUDA runtime, or a working viewer/display stack, stop short of claiming native execution success and explain the block clearly.
