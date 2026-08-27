# Evaluation benchmarks

## Two ways to evaluate

| Path | Input | Needs images? | Primary use |
|---|---|---:|---|
| `benchmark.py` | A checkpoint file | Yes | Run the full cropped-image inference pipeline and report AFLW / AFLW2000 NME. |
| `benchmark_aflw.py` / `benchmark_aflw2000.py` | Reconstructed landmark arrays or param-derived landmarks | No, if you already have predictions | Score predictions against the shipped test-config arrays. |

## Full pipeline: `benchmark.py`

`benchmark.py` loads a checkpoint, builds the requested MobileNet backbone, and runs inference on the cropped test sets under `test.data/`.

Important behaviors:

- It loads the checkpoint onto CUDA and wraps the model in `DataParallel`.
- It normalizes images with the same `ToTensorGjz` / `NormalizeGjz(mean=127.5, std=128)` pipeline used in training.
- It extracts predicted 62-d params and then reconstructs landmarks.
- It scores AFLW2000-3D first and AFLW second.

The shipped wrapper uses a single primary CUDA device. If you need a different device layout, call the lower-level helper with your own device list or adapt the wrapper.

## AFLW metric: `benchmark_aflw.py`

This helper computes normalized mean error on the AFLW cropped set.

Required arrays from `test.configs/`:

- `AFLW_GT_crop_yaws.npy`
- `AFLW_GT_crop_roi_box.npy`
- `AFLW_GT_pts68.npy`
- `AFLW_GT_pts21.npy`

Metric interpretation:

- The predicted 68 points are mapped to 21 points by a fixed index grouping.
- The normalization length is `sqrt((maxx - minx) * (maxy - miny))` from the ground-truth 68-point box.
- Results are split into yaw bins: `|yaw| <= 30`, `30 < |yaw| <= 60`, and `|yaw| > 60`.
- The printed overall value is the average of the three bin means, not a sample-weighted global mean.

## AFLW2000-3D metric: `benchmark_aflw2000.py`

This helper scores the AFLW2000-3D cropped set.

Required arrays from `test.configs/`:

- `AFLW2000-3D.pose.npy` or `AFLW2000-3D-new.pose.npy`
- `AFLW2000-3D.pts68.npy`
- `AFLW2000-3D-Reannotated.pts68.npy`
- `AFLW2000-3D_crop.roi_box.npy`

Metric interpretation:

- The helper supports the original and reannotated landmark sets.
- It uses the cropped ROI box to map the normalized fit back to image space.
- It prints the same yaw-bin split as the AFLW helper.

## Param-only fallback

If you already have predicted 62-d params and do not want to re-run inference, call `benchmark_alfw_params(params)` or `benchmark_aflw2000_params(params)` in `benchmark.py`.

Those helpers reconstruct landmarks from the parameter array and score them against the shipped `test.configs/` arrays, so they still need the metric metadata but not the cropped images themselves.

## Reading the results

- Lower NME is better.
- Compare results only when you used the same AFLW / AFLW2000 variant and the same GT annotation choice.
- If you report AFLW2000-3D, state whether you used the original or reannotated landmarks.
