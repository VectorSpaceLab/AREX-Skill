# Simulation-data workflows

## Purpose

This reference describes the simulated ALOHA data path from scripted rollout to replay, visualization, mirroring, compression, and truncation.

## 1) Generate scripted episodes

The repository's simulation pipeline uses two environments:

- `ee_sim_env.make_ee_sim_env(task_name)` for scripted end-effector rollout.
- `sim_env.make_sim_env(task_name)` for replaying the resulting joint trajectory and collecting observations.

The scripted policies generate open-loop waypoints from the first timestep and then interpolate between waypoints until the episode ends.

### Task names

Use the task names from `SIM_TASK_CONFIGS`:

- `sim_transfer_cube_scripted`
- `sim_insertion_scripted`
- `sim_transfer_cube_scripted_mirror`
- `sim_insertion_scripted_mirror`

The actual data generation entry point uses `task_name`, `dataset_dir`, `num_episodes`, and optionally `--onscreen_render`.

### Expected output

A successful rollout writes one HDF5 file per episode and prints whether the episode was successful according to the task reward.

## 2) Replay joint commands

`replay_episodes` loads an `episode_<idx>.hdf5` file, seeds the transfer-cube pose, and steps `sim_env` with the stored action sequence. It then writes a replay MP4.

Use this when you want to check whether a recorded action sequence still executes in the current sim/task configuration.

## 3) Visualize an episode

`visualize_episodes` reads the HDF5 file and writes:

- `<episode>_video.mp4`
- `<episode>_qpos.png`

The video writer concatenates camera views horizontally, so camera order matters for readability.

## 4) Mirror and compress episodes

`postprocess_episodes` is the mirror-and-compress pass used for legacy scripted datasets.

What it does:

- swaps left/right arm and gripper channels,
- horizontally flips image streams,
- optionally preserves `/base_action`,
- JPEG-compresses RGB streams,
- stores `/compress_len` so padded rows can be trimmed before decode.

Use this when you need doubled mirrored data or want compressed episode files for storage reduction.

## 5) Compress or truncate entire directories

- `compress_data` makes a `<dataset_dir>_compressed` directory.
- `truncate_data` makes a `<dataset_dir>_truncated` directory and keeps the first `TRUNCATE_LEN = 2250` timesteps.

These utilities are safe for batch preprocessing because they do not step the simulator.

## 6) Common data assumptions

- Sim episode files use 14-dimensional qpos/action arrays in the order left arm, left gripper, right arm, right gripper.
- Sim camera names are usually `top`, `left_wrist`, `right_wrist`.
- `sim_env` requires `BOX_POSE[0]` to be set before reset for transfer-cube/insertion tasks.
- `ee_sim_env` does not use `BOX_POSE[0]` in the same way; it randomizes object poses during reset.
- Headless rendering normally needs `MUJOCO_GL=egl` on the target host.
