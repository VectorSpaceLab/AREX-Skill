# Troubleshooting

Use the symptom → cause → recovery table below when custom data or prediction fails.

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Loader fails on the date column | The CSV does not have a literal `date` column, or the values are not parseable timestamps. | Rename the column to `date` and normalize the timestamps into a parseable format before retrying. |
| Loader fails around `--cols` or the target | `--cols` does not contain the target exactly once, or the target name does not match the CSV. | Add the target to `--cols` once, spell it exactly, or omit `--cols` and let the loader infer the covariates. |
| Validation or test length is zero | The split is too short for the chosen `seq_len` and `pred_len`. | Shorten the windows or add more rows so each split still has at least one usable window after the `seq_len` overlap. |
| Frequency error from the time-feature helper | `--freq` or the preserved detail frequency does not map to a supported cadence. | Use a supported cadence, keep `--embed` aligned with the intended time-feature path, and verify the cadence with the smoke helper first. |
| Model shape mismatch at build time | `enc_in`, `dec_in`, or `c_out` do not match the selected feature mode and channel count. | Recompute the channel count from the reordered custom CSV and set the model sizes accordingly. |
| Output looks wrongly scaled after inversion | `StandardScaler.inverse_transform` is being asked to invert a width that does not match the scaler fit width. | Use the correct `S` / `M` / `MS` mode, keep `c_out` aligned, or disable `--inverse` if you want scaled values. |
| `--cols` raises a remove error | The target was not included in `--cols`. | Add the target to `--cols` once, because the loader removes it before appending it back as the final column. |
| No `real_prediction.npy` appears | Prediction mode did not run, or the file was searched in the wrong directory. | Confirm `--do_predict`, then look under `results/<setting>/real_prediction.npy`. Remember that `pred.npy` and `true.npy` come from test mode, not prediction mode. |
| Future timestamps look shifted | The detailed cadence used for prediction does not match the CSV cadence. | Recheck the prediction cadence string and rerun the shared smoke helper before the full job. |

## Fast recovery order

1. Check the CSV schema.
2. Check `--cols` and `--target`.
3. Check the split length.
4. Check `--freq` and `--embed` together.
5. Check `enc_in`, `dec_in`, and `c_out`.
6. Check whether you are looking for test outputs or prediction outputs.
