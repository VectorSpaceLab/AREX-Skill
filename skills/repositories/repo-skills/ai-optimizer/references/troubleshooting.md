# Cross-Cutting Troubleshooting

## When to read

Read this before installing dependencies, running generated command recipes, or interpreting failures that cross AI-Optimizer algorithm families.

## First checks

1. Confirm the target checkout has the folder family you plan to use. Empty submodule placeholders were present in the provenance snapshot.
2. Use the nearest bundled command builder or dataset validator before running training.
3. Choose a fresh environment per algorithm family when dependencies conflict.
4. Avoid `pip install -r` across all requirements files; each folder targets a different era of the Python ML stack.

## Common symptoms

| Symptom | Likely cause | Recovery |
|---|---|---|
| `ModuleNotFoundError` for `tensorflow`, `tensorflow_probability`, `ray`, `gym`, `mujoco_py`, `dm_control`, `d4rl`, `tensorboardX`, or `torch` | Algorithm-specific dependency stack not installed. | Route to the owning sub-skill and install only that family's documented dependencies in an isolated environment. |
| TensorFlow 1.x/2.1/2.2 installation fails on a modern Python | Old TensorFlow GPU pins do not support current Python versions. | Use an older compatible Python/runtime for that algorithm, or keep the workflow as a documented command recipe until a compatible environment is available. |
| MuJoCo or `mujoco_py` import/license errors | MBPO/BMPO/offline D4RL tasks need MuJoCo runtime and sometimes old license paths. | Verify MuJoCo version, license/runtime, compiler, Gym/D4RL compatibility, and GPU before training. Do not treat static command generation as MuJoCo verification. |
| `dm_control` rendering or EGL errors | Dreamer/PlaNet visual-control tasks require a rendering stack. | Probe headless rendering, EGL/OSMesa, GPU visibility, and dm_control before long runs. |
| `CUDA_VISIBLE_DEVICES` typo in copied recipes | Some upstream READMEs spell it `CUDA_VISIABLE_DEVICES`. | Use the standard `CUDA_VISIBLE_DEVICES` spelling when selecting GPUs. |
| Command starts a long run or writes logs unexpectedly | Original training scripts are experiment launchers, not dry-run CLIs. | Use bundled helpers first; inspect generated command; run only after confirming output directories, resources, and duration. |
| A command path from a helper does not exist | Target checkout layout differs from the provenance snapshot or submodule state changed. | Run `scripts/check_ai_optimizer_static.py --source-root <target-checkout>` and refresh the skill if paths changed. |
| Offline dataset arrays fail later in training | Shape, terminal, timeout, or dtype problems were not validated. | Run `sub-skills/offline-rl/scripts/validate_mdp_dataset_npz.py` on a local `.npz` before MDPDataset conversion. |
| MARL scenario is rejected or silently ignored | Meeting environments do not use scenario names; MAGYM/MPE do. | Use `sub-skills/multi-agent-rl/scripts/build_easy_marl_command.py` to validate env/agent/scenario compatibility. |

## Heavy verification boundary

This skill can help build commands and validate static inputs. It does not prove:

- benchmark reproduction,
- complete training loops,
- CUDA performance,
- MuJoCo/DMControl/D4RL/Waymo/SMAC/MPE runtime success,
- dataset availability,
- GPU memory adequacy.

Those checks must be run in a task-specific environment after the user approves the compute, data, and licensing requirements.
