# TimeMixer Universal Task Troubleshooting

Use this guide when the imputation, anomaly-detection, or classification branch runs but produces NaNs, warnings, or shape errors.

## Quick checks

1. Confirm the task/data pair is valid: imputation with generic loaders, anomaly detection with PSM/MSL/SMAP/SMD/SWAT, classification with UEA.
2. For imputation and anomaly detection, keep `c_out == enc_in` so the reconstruction can be reshaped back to the input channel count.
3. For classification on multivariate UEA data, use `channel_independence=0`.
4. Remember that `mask_rate` is a fraction, while `anomaly_ratio` is a percentage.
5. If you see a warning rather than a crash, check whether it is a known source warning such as softmax or sklearn zero-division behavior.

## Symptom-to-fix map

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Imputation loss becomes NaN | A batch has no observed values after masking, or `batch_x[batch_x != 0].mean()` is computed on an empty set. | Lower `mask_rate`, verify the input series contains observed values, and avoid batches that are entirely zero. |
| Imputation silently treats real zeros as missing | The source replaces every zero in `batch_x` before masking. | Use a dataset where zero is a valid missing marker, or preprocess the data so real zeros are not semantically important. |
| Reconstruction output shape is wrong | `c_out` does not match the channel count expected by the reconstruction branch. | Set `c_out` equal to `enc_in` for imputation and anomaly detection. |
| Anomaly detector flags almost everything or nothing | `anomaly_ratio` is too large or too small for the chosen threshold percentile. | Adjust `anomaly_ratio`; remember that `25` means 25%, while `0.25` means 0.25%. |
| `precision_recall_fscore_support` emits zero-division or undefined metric warnings | The threshold produced only one predicted class, or the labels are highly imbalanced. | Tune `anomaly_ratio`, inspect the ground-truth label balance, and treat the warning as a thresholding issue rather than a loader failure. |
| `torch.nn.functional.softmax` warns about `dim` | Classification uses `softmax(preds)` without an explicit `dim` argument. | Treat it as a source warning; if you patch the code, use `dim=1`. |
| Classification crashes on multivariate UEA input | The default `channel_independence=1` builds a one-channel embedding, but the classification branch does not reshape multivariate inputs the way forecasting does. | Set `channel_independence=0` for multi-feature UEA, or use a one-feature input tensor. |
| Classification accuracy is poor because sequences were truncated | `seq_len` did not match the padded length used by the collate function. | Set `seq_len` to the dataset's max sequence length so the collate function and model agree. |
| `No .ts files found` or `No files found using ...` | The UEA root directory does not contain the expected `.ts` split files. | Point `root_path` at the directory containing the UEA split files and keep the `TRAIN`/`TEST` naming convention. |
| `load_from_tsfile_to_dataframe` import or parse failure | `sktime` is missing or the installed version is incompatible with the current Python version. | Install a compatible `sktime`; the repo note for Python 3.8 points to `0.29.1`. |
| Anomaly detection fails on a known dataset | The dataset key does not match the anomaly loader branch. | Use one of `PSM`, `MSL`, `SMAP`, `SMD`, or `SWAT`; the anomaly branch does not use the generic forecasting loaders. |

## Task-specific notes

### Imputation

- `mask_rate` should stay in `(0, 1)`.
- The loss is only evaluated on masked positions.
- `features='MS'` keeps only the last channel for scoring, so check that the final channel is the one you intend to evaluate.

### Anomaly detection

- `anomaly_ratio` is a percentile percentage, not a fraction.
- The detector uses training energies plus test energies to compute the threshold.
- The final `adjustment` step expands contiguous anomaly hits, so the printed metrics are post-adjustment metrics.

### Classification

- The loader expects `.ts` files, not CSV or NPY files.
- The padding mask is a 2D tensor with `1` for valid timesteps and `0` for padding.
- The source uses the test split for both validation and testing, so do not expect an independent validation file in this branch.
