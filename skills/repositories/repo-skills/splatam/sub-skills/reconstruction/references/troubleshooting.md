# Reconstruction Troubleshooting

## Purpose

Use this for failures after the Python/CUDA/rasterizer environment is importable. For install/backend import failures, start with the root troubleshooting reference.

## `params.npz` missing after a run

Symptoms:

- Result directory exists but no `params.npz`.
- Export or viewer fails with `FileNotFoundError`.

Likely causes:

- SLAM crashed before final `save_params`.
- Config `workdir`/`run_name` differs from the one used by export/viewer.
- Checkpoint-only files exist because the run was interrupted before final save.

Recovery:

1. Confirm the config used by export/viewer is the same copied `config.py` stored in the result directory.
2. Search for `params*.npz`; if only checkpoint files exist, either resume SLAM with `load_checkpoint=True` or treat the run as incomplete.
3. Run `sub-skills/reconstruction/scripts/check_result_bundle.py --result-dir <workdir>/<run_name>` to identify missing files/keys.

## Result bundle has invalid keys or shapes

Symptoms:

- Export fails with missing `means3D`, `log_scales`, `unnorm_rotations`, `rgb_colors`, or `logit_opacities`.
- Viewer fails when reading camera metadata.

Recovery:

- Validate with the bundled result checker.
- Confirm the file is a SplaTAM `params.npz`, not a partial checkpoint from another Gaussian-splat project.
- If using post-SplaTAM optimization, ensure `data.param_ckpt_path` points to the source SplaTAM output and the output `workdir/run_name` is distinct.

## CUDA out-of-memory or very slow mapping

Likely causes:

- Full-resolution frames or too many frames for current GPU memory.
- High `mapping.num_iters`/`tracking.num_iters` or large `mapping_window_size`.
- Densification enabled with large images and long schedules.

Recovery:

1. Reduce `desired_image_height`/`desired_image_width` and densification resolution.
2. Reduce `num_frames`, `mapping_window_size`, `tracking.num_iters`, and `mapping.num_iters` for diagnosis.
3. Disable optional densification for a smoke run.
4. Do not compare reduced-run metrics to published benchmark results.

## Tracking fails or diverges

Symptoms:

- Repeated poor depth loss.
- Camera trajectory is unstable.
- Reconstruction becomes smeared or empty.

Checks:

- Depth images are valid and scaled correctly (`png_depth_scale` or NeRFCapture `integer_depth_scale`).
- Intrinsics in YAML/config match the resized image dimensions.
- `tracking.use_gt_poses` is set deliberately.
- `forward_prop` and learning rates match the dataset motion speed.
- Frame order and `stride` are correct.

For NeRFCapture data, validate the dataset manifest before blaming tracking.

## Evaluation or novel-view split problems

Symptoms:

- `eval_train`/`eval_nvs` directories are empty.
- Eval script loads the wrong split.
- LPIPS or TorchMetrics import/model-weight issues.

Recovery:

- Set `data.use_train_split` deliberately.
- Confirm `scene_path` points to the intended `params.npz`.
- Disable W&B unless metrics need to be logged remotely.
- Ensure `torchmetrics.image.lpip` imports before running eval. Avoid network-triggered weight downloads unless approved.

## PLY export looks wrong

Symptoms:

- `splat.ply` is produced but appears black, tiny, huge, or misplaced in a viewer.

Checks:

- The exporter converts RGB to spherical-harmonic DC coefficients using the stored `rgb_colors`; color range assumptions matter.
- `log_scales` and `logit_opacities` are exported directly in SplaTAM's expected format.
- If `log_scales` has one column, the exporter tiles it to three scale axes.
- Confirm the source `params.npz` came from the intended result directory and not a reduced smoke run.

## Open3D viewer is blank or crashes

- Use `viz.render_mode='centers'` to inspect raw Gaussian centers.
- Confirm a GUI/display is available.
- Confirm the result contains `intrinsics`, `w2c`, `org_width`, `org_height`, and `gt_w2c_all_frames` when camera visualization is enabled.
- Viewer failure in a headless terminal is not proof that SLAM failed.

## Benchmark wrappers take too long

Dataset shell wrappers run multiple scenes or expensive settings. For debugging, use one copied Python config with a reduced frame count first. Only run wrappers when the user wants a long benchmark sweep and has provided data, GPU time, and logging decisions.
