# Root troubleshooting

Use the sub-skill troubleshooting pages for depth. This root page captures the most common cross-cutting failure modes.

| Symptom | Likely cause | First fix | Where to go next |
| --- | --- | --- | --- |
| `AttributeError` mentioning `Scale` | Modern torchvision removed `transforms.Scale` | Use `scripts/check_imports.py` or `scripts/check_main_help.py`, which apply the temporary alias, or pin a legacy torchvision wheel | `sub-skills/training-and-inference/references/troubleshooting.md` |
| `FileNotFoundError` for `opts.json`, logs, or checkpoints | `result_path` does not exist yet | Create the result directory before launch | `training-and-inference` troubleshooting |
| `assert arch == checkpoint['arch']` | Resume checkpoint does not match the current model family/depth | Resume only from the exact architecture | `training-and-inference` troubleshooting |
| `flow input is supported only when input type is hdf5` | JPEG inputs were paired with flow mode | Use RGB JPEG/HDF5 for the bundled data-prep paths, or prepare flow HDF5 elsewhere | `data-preparation` troubleshooting |
| `ffmpeg` / `ffprobe` failures | FFmpeg is missing or not on PATH | Install FFmpeg and verify both commands are visible | `data-preparation` troubleshooting |
| `evaluate_results.py` rejects the JSON | The JSON came from `--inference_no_average` or the label map is inconsistent | Regenerate averaged results or rebuild the label mapping | `training-and-inference` troubleshooting |
| Checkpoint keys still have `module.` prefixes | The file was saved from `nn.DataParallel` | Strip the prefixes once with `strip_dataparallel.py` | `training-and-inference` troubleshooting |

## Quick recovery order

1. Verify the environment with `scripts/check_imports.py`.
2. Verify the full CLI help with `scripts/check_main_help.py`.
3. If the issue is about data layout or frame conversion, switch to `data-preparation`.
4. If the issue is about checkpoints, result JSONs, or training flags, switch to `training-and-inference`.
