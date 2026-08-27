# Results and Metrics

## Result directory shape

When `Results.save_results` is true, `slam.py` creates a timestamped directory
under `Results.save_dir`. The intermediate bucket name is derived from the last
segments of `Dataset.dataset_path`; the run directory contains a copy of the
effective config as `config.yml`.

Common files and directories:

| Output | Created by | Meaning |
| --- | --- | --- |
| `config.yml` | `slam.py` save setup | The merged config used for the run. |
| `plot/trj_<label>.json` | `eval_ate` | Estimated and ground-truth poses for selected keyframes. |
| `plot/stats_<label>.json` | `evaluate_evo` | APE/ATE statistics from evo. |
| `plot/evo_2dplot_<label>.png` | `evaluate_evo` | XY trajectory plot colored by error. |
| `point_cloud/final/point_cloud.ply` | `save_gaussians(..., final=True)` | Final Gaussian map export. |
| `point_cloud/iteration_<n>/point_cloud.ply` | periodic save path | Intermediate Gaussian map export. |
| `psnr/<iteration>/final_result.json` | `eval_rendering` | Rendering metrics summary. |

## Metric definitions used by MonoGS

- ATE/RMSE: `eval_utils.evaluate_evo` aligns estimated and reference
  trajectories through evo and reports translational RMSE. Monocular evaluation
  passes `correct_scale=True`.
- PSNR: image quality from `gaussian_splatting.utils.image_utils.psnr` on masked
  rendered and ground-truth pixels.
- SSIM: image similarity from `gaussian_splatting.utils.loss_utils.ssim`.
- LPIPS: perceptual distance through `torchmetrics.image.lpip.LearnedPerceptualImagePatchSimilarity(net_type="alex")` on CUDA.
- FPS: number of frontend frames divided by CUDA event elapsed time.

## Reading result summaries

Use the bundled summarizer on either `Results.save_dir` or one timestamped run:

```bash
python scripts/summarize_results.py --result-root results
```

The script recursively reports config files, stats JSON files, PSNR summaries,
trajectory JSON files, and point-cloud PLYs. It does not import MonoGS or run any
metric computation.

## What missing files usually mean

- No `plot/stats_*.json`: ATE was not run, the run did not reach a final
  evaluation point, or `save_results`/trajectory conditions were not active.
- No `psnr/*/final_result.json`: `Results.eval_rendering` was false or the
  rendering pass failed.
- No final PLY: the run did not complete, `save_dir` was `None`, or the final
  save path was skipped after a failure.
- No W&B table: W&B was disabled or the evaluation branch failed before logging.
