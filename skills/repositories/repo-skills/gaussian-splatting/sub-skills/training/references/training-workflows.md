# Training Workflows

## When To Read

Read this when you need a command recipe for training, resuming, low-VRAM operation, or feature combinations such as depth regularization, exposure compensation, antialiasing, or Sparse Adam.

## Baseline Training Flow

1. Validate the scene layout with [../../data-preparation/SKILL.md](../../data-preparation/SKILL.md).
2. Confirm the CUDA backend with [../../setup-and-backends/SKILL.md](../../setup-and-backends/SKILL.md).
3. Choose the optimizer command.
4. Run training.
5. Use [../../rendering-evaluation/SKILL.md](../../rendering-evaluation/SKILL.md) to render and score the resulting model.

Typical command:

```bash
python train.py -s <scene> -m <model-output> --disable_viewer
```

With evaluation split:

```bash
python train.py -s <scene> -m <model-output> --eval --disable_viewer
```

## Depth Regularization

If the scene has depth maps and `depth_params.json` exists:

```bash
python train.py -s <scene> -d <depth-folder> --disable_viewer
```

Behavior notes:

- The depth loss is only active when `viewpoint_cam.depth_reliable` is true.
- For real COLMAP scenes, `sparse/0/depth_params.json` must exist and match the depth folder.
- The README recommends `Depth Anything v2` for producing depth PNGs, then `scripts/make_depth_scale.py` for the scale file.

## Exposure Compensation

For exposure-varying captures, the README suggests the following flag bundle:

```bash
--exposure_lr_init 0.001 --exposure_lr_final 0.0001 --exposure_lr_delay_steps 5000 --exposure_lr_delay_mult 0.001 --train_test_exp
```

Use this only when the changed train/test split is acceptable. The resulting metrics are not directly comparable to runs without the exposure split.

## Antialiasing

Enable the `--antialiasing` pipeline flag to turn on the EWA filter used for anti-aliasing.

This flag affects both training and rendering commands because `PipelineParams` feeds the rasterizer.

## Sparse Adam / Accelerated Rasterizer

Use `--optimizer_type sparse_adam` only after the accelerated rasterizer branch is installed and verified. Otherwise `train.py` exits with a sparse-adam installation error.

If the accelerated branch is unavailable, keep `--optimizer_type default`.

## Low-VRAM and Debugging Recipes

Useful memory-saving or debugging adjustments:

- `--data_device cpu` can reduce VRAM pressure when loading large image tensors.
- `--test_iterations -1` avoids extra evaluation spikes during training.
- Increasing `--densify_grad_threshold` or reducing `--densify_until_iter` lowers point growth.
- `--detect_anomaly` helps diagnose invalid gradient paths.
- `--disable_viewer` removes the network viewer socket from the loop.

Example conservative command:

```bash
python train.py -s <scene> -m <model-output> --iterations 7000 --test_iterations -1 --disable_viewer --data_device cpu
```

## Checkpoint Resume

To resume from a checkpoint saved by `--checkpoint_iterations`:

```bash
python train.py -s <scene> -m <model-output> --start_checkpoint <path-to-chkpnt.pth> --disable_viewer
```

The model directory stores checkpoint files named `chkpnt<N>.pth` alongside the main point-cloud snapshots.

## Common Routing Decisions

- If the user has raw images or COLMAP layout issues, route to data preparation first.
- If the user asks how to read metrics or render outputs, route to rendering/evaluation.
- If the user asks about viewer connection warnings, the `--ip` and `--port` options matter, but viewer build/run questions belong to the viewers sub-skill.
