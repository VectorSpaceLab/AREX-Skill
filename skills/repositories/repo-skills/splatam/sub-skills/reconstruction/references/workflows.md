# Reconstruction Workflows

## Purpose

Use this as the operating recipe for offline SplaTAM reconstruction, evaluation, export, and visualization. Commands assume the current working directory is a SplaTAM checkout root.

## Offline RGB-D SLAM

1. Choose a config family:

   | Dataset | Typical config |
   | --- | --- |
   | iPhone / captured NeRFCapture dataset | `configs/iphone/splatam.py` |
   | Replica | `configs/replica/splatam.py` |
   | Replica-V2 | `configs/replica_v2/splatam.py` |
   | TUM RGB-D | `configs/tum/splatam.py` |
   | ScanNet | `configs/scannet/splatam.py` |
   | ScanNet++ | `configs/scannetpp/splatam.py` |

2. Copy the config to a run-specific working file.
3. Edit at least:
   - `workdir` and `run_name`.
   - `data.basedir`, `data.sequence`, frame range, and image sizes.
   - `use_wandb=False` unless W&B is intentionally configured.
   - For quick smoke runs, lower `data.num_frames`, `tracking.num_iters`, and `mapping.num_iters`.
4. Verify environment and data:

   ```bash
   python scripts/check_env.py --require-cuda --require-rasterizer
   ```

5. Run SLAM:

   ```bash
   python scripts/splatam.py <working-config.py>
   ```

Expected signal: the script prints loaded config, dataset loading, tracking/mapping progress, average timing, evaluation progress, and writes `<workdir>/<run_name>/params.npz`.

## Result validation

Before handing a result to export, visualization, or reporting:

```bash
python sub-skills/reconstruction/scripts/check_result_bundle.py \
  --result-dir <workdir>/<run_name> --require-params
```

The helper checks that `params.npz` includes core Gaussian arrays and camera metadata. It does not prove visual quality or trajectory accuracy.

## PLY export

After `params.npz` exists:

```bash
python scripts/export_ply.py <working-config.py>
```

The exporter reads `<workdir>/<run_name>/params.npz` and writes `<workdir>/<run_name>/splat.ply`. It expects these arrays: `means3D`, `log_scales`, `unnorm_rotations`, `rgb_colors`, and `logit_opacities`.

## Visualization

Final reconstruction viewer:

```bash
python viz_scripts/final_recon.py <working-config.py>
```

Online replay viewer:

```bash
python viz_scripts/online_recon.py <working-config.py>
```

Visualization configs either specify `scene_path` directly or infer it from `<workdir>/<run_name>/params.npz`. Open3D needs a usable display; headless sessions should treat viewer failures as GUI blocks rather than reconstruction failures.

Useful `viz` keys:

- `render_mode`: `color`, `depth`, or `centers`.
- `show_sil`: show silhouette instead of RGB.
- `visualize_cams`: show camera frustums and trajectory.
- `enter_interactive_post_online`: stay interactive after online replay.

## Post-SplaTAM optimization

Use this when a SplaTAM `params.npz` checkpoint exists and the user wants longer Gaussian optimization from that reconstruction.

1. Choose or copy a `post_splatam_opt.py` config.
2. Set `data.param_ckpt_path` to the source `params.npz`.
3. Confirm `data.basedir`, `sequence`, image size, and eval stride match the original data.
4. Reduce `train.num_iters_mapping` for smoke checks; public configs can use 15k iterations.
5. Run:

   ```bash
   python scripts/post_splatam_opt.py <post-opt-config.py>
   ```

Expected signal: output under `<workdir>/<run_name>/params.npz` after optimization and eval.

## Gaussian splatting with GT poses

Use this when the dataset has usable ground-truth poses and the task is 3DGS-style optimization without SplaTAM tracking.

1. Choose a `gaussian_splatting.py` config for the dataset family.
2. Confirm the config's data root, sequence, initialization/eval sizes, and train iteration count.
3. Run:

   ```bash
   python scripts/gaussian_splatting.py <gs-config.py>
   ```

This uses `train.lrs_mapping`, densification settings, and dataset poses. It writes a standard result directory with `params.npz`.

## Novel-view and split evaluation

Use `scripts/eval_novel_view.py` when a saved scene should be evaluated on a train split or NVS split. The config must provide:

- `scene_path` pointing to a `params.npz` file.
- `load_checkpoint` handling for result-directory creation.
- `data.use_train_split` to select `eval_train` versus `eval_nvs`.
- `mapping.sil_thres`, `mapping.num_iters`, `mapping.add_new_gaussians`, and `eval_every` for reporting.

Run:

```bash
python scripts/eval_novel_view.py <eval-config.py>
```

## Benchmark wrapper scripts

Shell wrappers under dataset config directories launch large benchmark sweeps. Treat them as reference-only unless the user explicitly wants long multi-scene runs. For ordinary tasks, run one edited Python config first.
