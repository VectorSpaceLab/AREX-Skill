# Version and Capability Notes

## Verified Package Facts

- Live inspection verified `ultralytics` package version `8.4.72`.
- Public exports include `YOLO`, `YOLOWorld`, `YOLOE`, `NAS`, `SAM`, `FastSAM`, and `RTDETR`.
- CLI entry points are `yolo` and `ultralytics`.
- CLI modes include `train`, `val`, `predict`, `export`, `track`, and `benchmark`.
- CLI tasks include `detect`, `segment`, `classify`, `pose`, `obb`, and `semantic`.

## Model and Task Notes

- YOLO26 names appear throughout this checkout and may download pretrained weights on first use.
- Semantic segmentation is first-class in this checkout and exposes dense semantic masks rather than per-instance boxes or polygons.
- SAM3-related source and docs are present. Treat SAM3 workflows as version-sensitive and dependent on weight availability, optional dependencies, and documented access constraints.
- `NAS` and `RTDETR` are detection-oriented model families; do not route them to segmentation, pose, OBB, or semantic workflows unless newer evidence proves support.
- `FastSAM` is segmentation-oriented and rejects YAML model construction patterns that ordinary YOLO model families may allow.

## Optional Extras

- Base install covers core Python API/CLI inspection, prediction planning, and config parsing.
- `export-base` supports many ONNX/OpenVINO-style export flows; broader `export` pulls TensorFlow/CoreML-related packages and should be installed only when needed.
- `solutions` adds analytics-app dependencies such as geometry, similarity search, and Streamlit-related packages.
- `logging` adds integrations such as W&B, TensorBoard, and MLflow.
- `dev` adds test/docs/development tools and should be used for repo maintenance, not ordinary inference or training users.

## Side-Effect Notes

- Built-in dataset names can download data. Built-in model names can download weights.
- Training, validation, prediction, tracking, solutions, export, and benchmark can create output directories or files.
- TensorRT, CUDA export, full benchmarks, video analytics, Streamlit, Triton, and similarity search may require GPUs, services, display/media inputs, or optional packages.
- Keep examples in public guidance small and explicit about offline/local-path alternatives.
