# Metrics Troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `py_metrics_ops` import fails | Installed wheel lacks compiled ops or TensorFlow ABI mismatch | Reinstall a WOD wheel matching the TensorFlow line; avoid mixing package versions. |
| Metrics stay zero or empty | Local metric variables were not initialized or update op not run | Initialize local variables and run the update op before reading value ops. |
| Motion metric assertion error | Non-batch dimensions are dynamic or inconsistent | Set static shapes for groups/top-K/agents/steps and align config step counts. |
| Detection box DOF error | Config box type does not match prediction/ground-truth box dimension | Use 7 for 3D, 5 for oriented 2D, or 4 for axis-aligned 2D. |
| Missing or unexpected breakdown names | Config breakdown generator/difficulty mismatch | Use `config_util_py.get_breakdown_names_from_config` before filtering results. |
| No-label-zone field confusion | Detection wrapper expects `prediction_overlap_nlz` | Supply a boolean tensor for predictions or derive it from preprocessing. |
