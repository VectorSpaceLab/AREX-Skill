# Reconstruction Configuration Reference

## Purpose

Use this when editing SplaTAM reconstruction, optimization, eval, or visualization configs. Configs are Python files that define `config = dict(...)`.

## Core run fields

| Field | Meaning | Notes |
| --- | --- | --- |
| `workdir` | Output root. | Reconstruction scripts combine this with `run_name`. iPhone capture configs may use it as the dataset directory. |
| `run_name` | Result subdirectory. | Keep unique per run to avoid overwriting. |
| `seed` | Reproducibility seed. | Passed to `seed_everything`. |
| `primary_device` | Torch device string. | Public configs use `cuda:0`. |
| `use_wandb` | Enables W&B logging. | Set `False` unless credentials/network are intended. |

## Dataset fields

Common `data` keys:

- `dataset_name`: direct name such as `nerfcapture`, or implicit via `gradslam_data_cfg`.
- `basedir`: dataset root.
- `gradslam_data_cfg`: YAML with camera intrinsics and dataset name for Replica/TUM/ScanNet-style data.
- `sequence`: scene/sequence name; many loaders use `os.path.basename(sequence)`.
- `desired_image_height`, `desired_image_width`: tracking/mapping resolution.
- `densification_image_height`, `densification_image_width`: iPhone/NeRFCapture or densification resolution when present.
- `start`, `end`, `stride`: selected frame range.
- `num_frames`: `-1` means use dataset length in many configs.
- `eval_stride`, `eval_num_frames`: evaluation subset for post-opt/GT-pose/eval scripts.
- `param_ckpt_path`: source `params.npz` for post-SplaTAM optimization.

Dataset loader names handled by main scripts include `icl`, `replica`, `replicav2`, `azure`/`azurekinect`, `scannet`, `ai2thor`, `record3d`, `realsense`, `tum`, `scannetpp`, and `nerfcapture`.

## SLAM tracking/mapping fields

Top-level scheduling:

- `map_every`: map every nth frame.
- `keyframe_every`: add keyframe cadence.
- `mapping_window_size`: number of keyframes considered in local mapping.
- `report_global_progress_every`: progress/eval reporting cadence.
- `eval_every`: evaluation frame stride at the end of SLAM.
- `scene_radius_depth_ratio`: first-frame max depth divided by this value initializes scene radius.
- `mean_sq_dist_method`: public configs use `projective`; comments mention `knn`, but source paths primarily implement projective behavior.
- `gaussian_distribution`: `isotropic` or `anisotropic`.

`tracking` fields:

- `use_gt_poses`: bypass learned tracking when true.
- `forward_prop`: initialize current pose from prior motion.
- `visualize_tracking_loss`: writes/plots tracking diff images when enabled.
- `num_iters`: optimizer iterations per tracking step.
- `use_sil_for_loss`, `sil_thres`, `use_l1`, `ignore_outlier_depth_loss`, optional depth-loss threshold fields.
- `loss_weights`: typically `im` and `depth`.
- `lrs`: separate learning rates for Gaussian parameters and camera rotation/translation.

`mapping` fields:

- `num_iters`: optimizer iterations per mapping update.
- `add_new_gaussians`: add new Gaussians from depth/silhouette residuals.
- `prune_gaussians` and `pruning_dict`: opacity/radius pruning schedule.
- `use_gaussian_splatting_densification` and `densify_dict`: 3DGS-style densification schedule.
- `lrs`: mapping learning rates; camera pose rates are usually zero in mapping.

## Checkpoint and resume fields

For `scripts/splatam.py`:

- `save_checkpoints=True` enables periodic `params<time_idx>.npz` saves.
- `checkpoint_interval` controls cadence.
- `load_checkpoint=True` loads from `<workdir>/<run_name>/params<checkpoint_time_idx>.npz` and `keyframe_time_indices<checkpoint_time_idx>.npy`.
- `checkpoint_time_idx` selects the checkpoint frame.

Resume requires the original result directory and matching keyframe file. Do not set `load_checkpoint=True` for a new run.

## Post-opt and GT-pose train fields

Post-SplaTAM and GT-pose Gaussian splatting configs use `train` instead of `tracking`/`mapping`:

- `num_iters_mapping`: optimization iterations; public configs can be 15k-30k.
- `sil_thres`, `use_sil_for_loss`, `loss_weights`.
- `lrs_mapping`, `lrs_mapping_means3D_final`, `lr_delay_mult`.
- `use_gaussian_splatting_densification` and `densify_dict`.

For post-SplaTAM, `data.param_ckpt_path` must point to an existing source `params.npz`.

## Visualization fields

`viz` controls Open3D display and rendering:

- `render_mode`: `color`, `depth`, or `centers`.
- `offset_first_viz_cam`, `show_sil`, `visualize_cams`.
- `viz_w`, `viz_h`, `viz_near`, `viz_far`, `view_scale`.
- `viz_fps`, `enter_interactive_post_online`.

For viewer-only configs, `scene_path` can point directly to a `params.npz`; otherwise viewer scripts infer it from `workdir/run_name`.

## Smoke-run edits

When validating a new dataset or environment, make a copy of the config and lower cost:

- `data.num_frames`: 5-20 frames if the dataset supports it.
- `tracking.num_iters`: 5-10.
- `mapping.num_iters`: 5-10.
- Image sizes: use reduced dimensions if memory is tight.
- `use_wandb=False`.

A reduced run is only a plumbing/backend check. It is not benchmark evidence.
