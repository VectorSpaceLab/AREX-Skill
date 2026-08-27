# Data and Configuration Troubleshooting

## Install or Import Fails

- Confirm the `ultralytics` package imports and reports a version before diagnosing data errors: `python -c "import ultralytics; print(ultralytics.__version__)"`.
- If `yolo` is not found, use `python -m ultralytics` only if the environment supports it, or reinstall the package so the console scripts `yolo` and `ultralytics` are created.
- Optional converter/export paths may need extra dependencies. Keep data/config linting offline where possible; install optional packages only for the workflow that needs them.

## CLI Syntax Errors

- Use `arg=value`, not `--arg value` and not `arg value`.
- Put the optional task before the mode: `yolo detect train ...`, `yolo segment predict ...`, `yolo obb train ...`.
- If the error says an argument is invalid, check for misspellings and deprecated names. Replace `line_thickness` with `line_width`; replace `boxes` with `show_boxes`; replace `hide_labels`/`hide_conf` with the appropriate `show_labels`/`show_conf` value. Do not use removed keys such as `label_smoothing`, `save_hybrid`, or `crop_fraction`.

## Dataset YAML Errors

- Missing `train` or `val`: add both keys for detection, segment, pose, OBB, and semantic datasets.
- Missing `names` and `nc`: add `names` as either a list or an index-to-name mapping. If using `nc`, ensure it matches the class count.
- `names` length mismatch: remove `nc` or make it equal to the number of class names.
- Bad relative paths: set `path` to the dataset root and make `train`/`val` relative to that root, or use explicit paths. Validate before launching training.
- Empty or missing labels: confirm label files sit under a sibling `labels/` tree that mirrors `images/`, with normalized coordinates and class ids in range.
- Pose labels: ensure each row has `5 + num_keypoints * dims` columns and that `kpt_shape` matches the labels.
- Semantic labels: ensure `masks_dir` points to readable mask files whose dimensions match the images; review any `label_mapping` before training.

## Download and Network Risks

- Dataset YAML `download:` may download archives, run `bash` commands, or execute Python snippets when Ultralytics autodownloads missing data.
- Treat official tiny YAMLs like `coco8.yaml`, `coco8-pose.yaml`, `dota8.yaml`, and `cityscapes8.yaml` as smoke-test candidates; do not assume large public dataset YAMLs are cheap.
- In restricted or offline environments, disable autodownload paths and fail fast with local path checks.

## Backend, Device, and Cost Problems

- Use `device=cpu` for planning/smoke tests when GPU availability is uncertain. Use `device=0` or `device=[0,1]` only after checking CUDA visibility.
- If training stalls or consumes too much memory, reduce `imgsz`, `batch`, and `workers`; set `epochs=1` for smoke tests.
- `amp=True`, `half=True`, `compile=True`, and GPU device choices can expose backend-specific failures. Disable them during initial diagnosis.
- Export with `int8=True` may require calibration data and can trigger extra backend dependencies. Confirm `data=...` and export format requirements before running.

## Side Effects to Surface Before Running

- `train`, `val`, `predict`, `track`, `benchmark`, and `export` can write under `runs/` or the provided `project/name` directory.
- `predict` and `track` may open cameras, URLs, video files, or streams via `source`.
- `cache=True`, `cache=ram`, and `cache=disk` can consume significant memory or storage.
- Converter and split APIs create output directories and may overwrite or increment paths depending on the helper.
