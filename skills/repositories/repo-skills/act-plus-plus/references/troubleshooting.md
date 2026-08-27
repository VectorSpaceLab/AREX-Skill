# Cross-cutting troubleshooting

## When to read

Read this when ACT++ imports, sim rendering, training, VINN, or real-robot branches fail before the problem clearly belongs to a single sub-skill.

## Install and import failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: sim_env`, `constants`, or another top-level module | The repo uses top-level scripts/modules. The checkout root is not on `PYTHONPATH`. | Run from the checkout root, install the checkout in editable mode and add the root to `PYTHONPATH`, or pass the checkout to the bundled checkers with `--repo-root`. |
| `ModuleNotFoundError: util` while importing DETR code | The `detr` subdirectory expects its own editable install / import aliases. | Install the `detr` subdirectory in editable mode or add it to `PYTHONPATH` before importing `detr.main`. |
| `ModuleNotFoundError: robomimic.algo.diffusion_policy` | Public robomimic wheels may not provide the diffusion policy module expected by `policy.py`. | Install a compatible robomimic branch/build that exposes `robomimic.algo.diffusion_policy`; then verify `replace_bn_with_gn` and `ConditionalUnet1D` before training. |
| `ImportError: cannot import name 'ConditionalUnet1D'` from robomimic diffusion policy | The installed robomimic places `ConditionalUnet1D` under another module. | Use a compatible build or add an explicit compatibility alias in your private runtime. Do not claim DiffusionPolicy is ready until `python -c "from robomimic.algo.diffusion_policy import ConditionalUnet1D"` succeeds. |
| `ModuleNotFoundError: aloha_scripts` or `interbotix_xs_modules` | The user is entering real Mobile ALOHA / robot hardware code paths. | Install and configure the external Mobile ALOHA / Interbotix stack, or narrow the task to simulated/offline workflows covered here. |

## Backend failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `torch.cuda.is_available()` is false, or training crashes on `.cuda()` | ACT++, Diffusion, latent training, and VINN scripts call `.cuda()` directly. | Move to a CUDA host or patch the repository code for CPU before claiming CPU support. Do not use CPU import as a substitute. |
| MuJoCo/DM Control warns about missing display or rendering fails | Offscreen GL backend is not configured. | Set `MUJOCO_GL=egl` on EGL-capable machines. If no EGL backend exists, install/enable a supported offscreen renderer before data generation. |
| `AssertionError` in `sim_env.initialize_episode` on `BOX_POSE[0] is not None` | Joint-space sim reset requires object pose to be seeded from outside. | Before `make_sim_env(...).reset()`, set `sim_env.BOX_POSE[0] = utils.sample_box_pose()` for transfer cube or concatenate `utils.sample_insertion_pose()` for insertion. |
| Sim data generation works but training is slow or crashes after first batches | Training loads images, applies transforms, and may use many workers; GPU memory or workers may be insufficient. | Lower `--batch_size`, lower `--chunk_size`, reduce workers in `utils.load_data`, and validate the dataset schema first. |

## CLI and workflow mismatches

- README-era ACT training snippets may show `--num_epochs`; current `imitate_episodes.py` requires `--num_steps`.
- `--eval` loads `policy_last.ckpt`, not `policy_best.ckpt`, in the current code path.
- `--load_pretrain` points to a hard-coded pretrain directory in source. Avoid this flag unless the host has the expected checkpoint or the code is patched.
- `task_name` values beginning with `sim_` are resolved from `SIM_TASK_CONFIGS`; non-sim names import `aloha_scripts.constants.TASK_CONFIGS` from external Mobile ALOHA.
- Diffusion uses action min/max normalization and image augmentation; ACT/CNNMLP use action mean/std normalization.

## Data layout failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `Dataset does not exist` from visualization/replay utilities | The command expects `episode_<idx>.hdf5` or `mirror_episode_<idx>.hdf5` under the dataset directory. | Confirm the episode file name and use `--ismirror` only for mirrored files. |
| Compressed episode images decode incorrectly | Missing or ignored `/compress_len` when padded JPEG rows are decoded. | Inspect `attrs['compress']` and `/compress_len`; trim padded rows before decode when writing new utilities. |
| `assert len(episode_idxs) == episode_idxs[-1] + 1` in VINN caching | Episode indices have holes. | Rename/fill episodes so indices are dense from 0, or adapt the VINN script to use the actual sorted list. |
| Training finds zero HDF5 files | Wrong `dataset_dir` in task config or missing files after mirroring/compression. | Verify the task's dataset directory and that filenames end in `.hdf5` and do not only contain `features`. |

## VINN-specific traps

- `vinn_select_k.py` contains an unconditional `IPython.embed()` call. Use the bundled [VINN select-k helper](../sub-skills/vinn-offline/scripts/select_k.py) for unattended selection.
- `vinn_eval.py` hard-codes `real_robot = True` and imports `aloha_scripts.real_env`; treat it as external robot evidence unless the Mobile ALOHA runtime is configured.
- BYOL checkpoint paths are parsed by filename. The expected pattern is similar to `byol-<task>-DUMMY-seed-<seed>.pt`, and `DUMMY` is replaced by camera name.

## Reference-only or excluded source areas

- Robot alignment and Dynamixel diagnostics are not safe generic workflow routes because they require physical robots, ROS/Interbotix packages, and servo communication.
- `train_actuator_network.py` is experiment-specific: it chooses paths from `os.getlogin()`, assumes `/obs_tracer`, and is not a stable public CLI.
- The inspected `byol_pytorch` entry was an empty gitlink, so this skill does not route users into that submodule.
