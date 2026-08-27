# Training Troubleshooting

## `Trying to use sparse adam but it is not installed`

Cause: `--optimizer_type sparse_adam` was requested without the accelerated rasterizer that exposes `SparseGaussianAdam`.

Fix:

- Use `--optimizer_type default`, or
- Install the accelerated rasterizer branch and rerun backend checks.

## `Could not recognize scene type!`

The scene root did not contain a COLMAP `sparse/` directory or a Blender `transforms_train.json` file.

Fix:

- Validate the layout with the data-preparation sub-skill before training.
- Confirm that `--source_path` points at the scene root, not a nested image folder.

## Blender Synthetic Training Crashes in Pillow

If training on a Blender/NeRF synthetic scene fails early with a `PIL.Image.fromarray` `TypeError` mentioning `Cannot handle this data type: (1, 1, 3), |i1`, the issue is in the synthetic-scene image conversion path rather than the optimizer loop.

Recovery:

- Use a Pillow version compatible with the repo's synthetic-scene loader path.
- Recreate or rebuild the environment after adjusting Pillow if the error appeared after a package upgrade.
- If the user can switch to COLMAP data, route them through the COLMAP preparation path instead of the Blender loader.

## CUDA Out-of-Memory / GPU Spikes

Likely causes:

- The scene uses too many points or too high a resolution.
- Evaluation iterations cause extra memory spikes.
- The viewer and training are competing for the same GPU memory.

Recovery:

- Add `--disable_viewer`.
- Set `--test_iterations -1` for a short smoke run.
- Use `--data_device cpu` for source image loading when the GPU is memory constrained.
- Reduce `--densify_until_iter` or increase `--densify_grad_threshold`.
- Shorten the run with fewer iterations until the scene loads successfully.

## `Config file not found at .../cfg_args`

This usually appears in `render.py`, but the training side matters because `cfg_args` is created when training writes the model directory.

Fix: make sure training actually created the model directory and that the later render step points at the correct model root.

## Viewer Connection Problems During Training

Symptoms:

- Training appears to hang when the viewer is enabled.
- The viewer cannot connect to `127.0.0.1:6009` or a custom port.
- The optimizer is running in a headless environment.

Fix:

- Add `--disable_viewer` for headless runs.
- If the viewer should connect, make sure the same `--ip` and `--port` are used by both sides and that the port is reachable.

## Debug Mode Is Slow

`--detect_anomaly` and rasterizer debug mode slow training substantially. Use them only for targeted troubleshooting.

## Unexpected Output Folder

If `-m` is omitted, `train.py` writes to a randomized directory under `./output/`. Use an explicit `--model_path` when you need a stable location for later rendering.
