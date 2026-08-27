# Reconstruction Troubleshooting

Use this guide for fitting, scalar-map, ODF/peak, simulation, and CLI failures.

| Symptom | Likely cause | Recovery | Validate |
| --- | --- | --- | --- |
| Mask shape error during fit or `peaks_from_model` | Mask is not exactly `data.shape[:-1]`. | Recreate/resample the mask through the IO or preprocessing path; convert to boolean; do not include a gradient dimension. | `mask.shape == data.shape[:-1]` and `mask.dtype` is boolean-like. |
| Model fit complains about bvals/bvecs or volume mismatch | `len(bvals)`, `bvecs.shape`, and `data.shape[-1]` disagree; b-vectors may be transposed or not unit length. | Route parsing to `../../io-data/`; rebuild `gradient_table`; use `atol` only for small unit-vector tolerance, not grossly wrong vectors. | `len(gtab.bvals) == data.shape[-1]`; non-b0 vector norms are near 1. |
| `b0_threshold` warning or missing expected b0 volumes | Scanner b0 values are above threshold, or threshold is lower than the smallest b0-like value. | Increase `b0_threshold` to include known b0 volumes and record the choice. | `gtab.b0s_mask.sum()` matches expected b0 count. |
| Zero, negative, NaN, or infinite signals before fitting | Background included, preprocessing introduced invalid values, or log-sensitive models need clipping. | Replace nonfinite values, clip to a small positive `min_signal` when supported, and tighten the mask. | `np.isfinite(data[mask]).all()` and, for log-sensitive models, `data[mask].min() > 0`. |
| FA contains NaNs or values outside `[0, 1]` | Degenerate tensors, invalid signals, background voxels, or numerical noise. | Use `np.nan_to_num`, clip/report FA in `[0, 1]`, and inspect data/mask. | FA inside mask is finite and in range; all-zero FA in expected tissue is investigated. |
| DKI metrics fail or look unstable | Acquisition is too sparse, wrong fit method, invalid signals, or constrained/nonlinear method needs more runtime/solver support. | Use `WLS` or `OLS` for ordinary checks, verify multi-shell sampling, and mark constrained/nonlinear paths `skip-optional` when solvers are absent. | `mk()`, `ak()`, `rk()`, `evals`, and tensor maps are finite in mask. |
| CSD/CSA/QBall/GQI/SFM says more DWI volumes are required | `sh_order_max` requires more SH coefficients than available diffusion volumes. | Lower `sh_order_max` only when scientifically acceptable, use DTI for low-gradient scalar metrics, or request richer acquisition. | `data.shape[-1] >= (sh_order_max + 1) * (sh_order_max + 2) / 2` when SH outputs are required. |
| CSD peaks are empty or implausible | Bad response function, poor mask, too-high peak threshold, insufficient gradients, or bad b0 normalization. | Validate response eigenvalues/ratio, choose a plausible single-fiber ROI or supplied response, lower `relative_peak_threshold` cautiously, and inspect mask coverage. | Response eigenvalues are positive/prolate; `peak_values[mask].max() > 0`; GFA is nonzero in expected regions. |
| `peaks_from_model` import fails | Wrong import path or stale instructions. | Import `peaks_from_model` from `dipy.direction.peaks` or `dipy.direction`; do not use `dipy.reconst.peaks` for this version. | `python -c "from dipy.direction.peaks import peaks_from_model"` succeeds. |
| `peaks_from_model` is slow or hangs with multiprocessing | Multiprocessing overhead or process configuration issue. | For smoke tests and small data, set `parallel=False`; for larger jobs, set `num_processes` explicitly and never use `num_processes=0`. | A small masked subset completes with expected shapes. |
| SH coefficients differ across tools or versions | `sh_basis_type`, `legacy`, or sphere differs. | Record `sh_basis_type`, `legacy`, `sphere`, and `sh_order_max`; rerun with explicit settings when comparing. | Coefficient shapes and peak directions are compared under identical settings. |
| CLI writes unexpected filenames or misses extracted NIfTI maps | Defaults were used, `--out_dir` was omitted, or extraction/metric flags were not set. | Run `dipy_fit_* --help`; set `--out_dir`; specify `--save_metrics` or extraction flags. | Expected files exist in the chosen output directory. |
| MSMT-CSD CLI exits early | `iso < 3`, missing tissue masks/T1, or tissue-classification assumptions are not met. | Keep `iso >= 3`; provide WM/GM/CSF masks or T1 when requested; route mask generation to preprocessing/tracking. | Tissue masks have DWI spatial shape; generated WM/GM/CSF masks are present when expected. |
| MAPMRI errors about timing parameters or scalar meaning | `small_delta`/`big_delta` missing or inappropriate; b-value threshold/regularization not set intentionally. | Supply timing parameters, document `laplacian`/`positivity`, and run on a bounded subset first. | Selected scalar outputs are finite and settings are recorded. |
| Specialized model selected for ordinary tensor data | DSI/GQI/MAPMRI/FORCE/RUMBA/FORECAST does not match acquisition or runtime budget. | Revisit `model-selection.md`; select DTI, DKI, CSA, or CSD as appropriate; mark specialized runs `skip-expensive` unless required. | The selected model's acquisition assumptions are written before fitting. |
| `dipy_fit_rumba` is requested but command is missing | No installed CLI was verified for RUMBA in the inspected command catalog. | Use the Python `RumbaSDModel` API or re-run CLI discovery through `../../cli-workflows/`. | Installed command list contains the requested command before using it. |
| Base install lacks visualization or neural-network dependencies | Optional dependencies such as `fury`, `matplotlib`, `torch`, or `tensorflow` may not be installed. | Avoid rendering/NN examples by default; mark `skip-optional` and ask before installing optional dependencies. | Import checks match the planned optional surface. |

## Difficult Case: Low-Gradient DTI Versus CSD

Use this when a user asks for CSD/ODF peaks from a small DWI dataset.

1. Count total volumes, non-b0 volumes, and unique gradient directions.
2. Compute the SH coefficient requirement for the requested `sh_order_max`.
3. If available DWI volumes are below the SH requirement, choose `TensorModel` for FA/MD/AD/RD and principal directions.
4. If the user still needs crossing-fiber peaks, ask for a richer HARDI/multi-shell acquisition or document an exploratory lower-order fit.
5. Validate that any produced peaks/PAM output has nonzero peak values in mask before handing it to `../../tracking-segmentation/`.

## Difficult Case: Zero Or Negative Signal Before Fitting

Use this when tensor, CSA, DKI, or CSD fitting fails or returns NaNs.

1. Confirm the data is floating point and finite; reject NaN/Inf before model construction.
2. Confirm the mask excludes background and has no diffusion dimension.
3. For tensor/DKI/free-water models, pass a strictly positive `min_signal` when zero or negative values may appear.
4. For CSA/QBall/OPDT and other log/normalization-sensitive models, keep `min_signal=1e-5` or another documented positive value; avoid `assume_normed=True` unless data is already normalized by b0.
5. Run one tiny masked fit and inspect FA/eigenvalues or GFA/peaks before launching a full-image CLI.

## Quick Import/Environment Check

For base reconstruction APIs, the bundled smoke script should pass:

```bash
python ../scripts/dipy_tensor_smoke.py --json
```

If it fails, fix the Dipy installation/import path first; do not debug full reconstruction workflows before the base tensor import and simulation surfaces work.
