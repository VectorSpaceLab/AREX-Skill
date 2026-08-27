# Data Interfaces Troubleshooting

| Symptom | Likely cause | Action |
| --- | --- | --- |
| Invalid mtype | Wrong concrete container for selected scitype | Run `check_data_format.py` on a small sample and inspect metadata. |
| Panel labels mismatch | `y` length does not equal number of panel instances | Count first-level instance IDs and align labels. |
| MultiIndex rejected | Incorrect levels, unsorted index, duplicates, or missing time level | Rebuild a two-level `(instance, time)` index and sort it. |
| Download loader hangs/fails | Network/cache/remote dataset dependency | Use onboard loader for smoke or ask for controlled cache/network approval. |
| File roundtrip loses labels | Writer class labels not supplied or wrong path/problem name | Use `write_dataframe_to_tsfile` with `class_label` and `class_value_list`. |
| Estimator rejects valid mtype | Estimator requires a different internal mtype | Inspect estimator `X_inner_mtype` and convert to the accepted representation. |
