# Inference Troubleshooting

This guide focuses on Ultralytics prediction and result-consumption failures. For dataset YAMLs or label-format problems, route to `../data-and-configuration/`; for export/runtime engine problems, route to `../export-and-deployment/`; for tracking IDs and tracker configs, route to `../tracking-and-solutions/`.

## Install and Import Failures

Symptoms:

- `ModuleNotFoundError: No module named 'ultralytics'`
- Import failures for `torch`, `cv2`, `PIL`, `polars`, `onnxruntime`, or display/codec packages
- CLI command `yolo` or `ultralytics` not found

Fixes:

- Verify the installed distribution and version in the active environment: `python -c "import ultralytics; print(ultralytics.__version__)"`.
- Use `python -m pip show ultralytics` to confirm the package is installed in the interpreter that runs the script.
- Use `python -m ultralytics` only if console scripts are unavailable; otherwise prefer `yolo ...` or `ultralytics ...`.
- Install optional packages only for the workflow that needs them: `onnxruntime` for the ONNXRuntime example style, GUI/display packages for `show=True`, and `polars` for dataframe export.

## CLI Argument Shape

Symptoms:

- CLI reports an invalid argument or ignores values.
- A command written as `yolo predict --imgsz 640 --source image.jpg` fails unexpectedly.

Fixes:

- Use Ultralytics `arg=value` syntax: `yolo predict model=weights.pt source=image.jpg imgsz=640 conf=0.25`.
- Keep `MODE` explicit: `predict` is required. `TASK` is optional but must be one of `detect`, `classify`, `obb`, `pose`, `segment`, or `semantic` when supplied.
- Quote URLs, globs, and paths containing spaces so the shell does not split or expand them accidentally.
- Check available defaults with `yolo cfg` and broad CLI help with `yolo help`.

## Bad Source or Config Paths

Symptoms:

- `FileNotFoundError`, no images found, empty batches, or source loader errors.
- Paths in text/CSV source lists work locally but fail in another working directory.
- Screenshot/webcam/stream sources fail on a headless or remote machine.

Fixes:

- Resolve relative paths from the current process working directory, not from a Python file location.
- Prefer `Path(...).exists()` checks before calling `model.predict` for local files, directories, text files, and CSV source lists.
- For text/CSV lists, make each row a valid image/video/directory/URL source and keep headers consistent with the loader expectation.
- For webcams, screenshots, and GUI display, confirm hardware/display availability; use file sources and `save=True` on headless systems.
- For RTSP/RTMP/TCP or YouTube sources, expect network and codec failures; start with a local image or short local video to isolate model issues from media transport issues.

## Memory Growth or Slow Video Processing

Symptoms:

- RAM grows during video, stream, webcam, or large-directory inference.
- Prediction finishes only after reading the entire video.
- Long jobs consume too much disk from frame/image saves.

Fixes:

- Use `stream=True` and iterate results immediately: `for result in model(source, stream=True): ...`.
- Do not call `list(model(..., stream=True))` for long sources.
- Store derived rows, counts, or filenames rather than every `Results` object.
- Use `vid_stride=N` to skip frames when full-frame-rate processing is unnecessary.
- Keep `save=False`, `save_txt=False`, `save_crop=False`, and `save_frames=False` unless persistent output is required.
- For live streams, keep `stream_buffer=False` unless delayed buffered processing is intentional.

## Task-Specific Result Mistakes

Symptoms:

- `AttributeError: 'NoneType' object has no attribute 'xyxy'`
- Classification code tries to crop boxes.
- Semantic segmentation code expects instance masks or polygons.
- OBB code draws axis-aligned boxes instead of rotated geometry.

Fixes:

- Always guard optional fields: `if result.boxes is not None`, `if result.probs is not None`, `if result.semantic_mask is not None`.
- Use `result.probs` for classification and skip `save_crop` or box-dependent code.
- Use `result.semantic_mask.data` for semantic segmentation; do not use `result.masks.xy`.
- Use `result.obb.xyxyxyxy` or `result.obb.xywhr` for OBB geometry; use `result.obb.xyxy` only as an axis-aligned approximation.
- Prefer `result.summary(normalize=True)` when you need a task-aware dictionary output.

## Save, Crop, and Plot Side Effects

Symptoms:

- Output files are missing or saved under unexpected `runs/` directories.
- `save_crop` logs warnings and creates no crops.
- `show=True` hangs or crashes in SSH/headless environments.
- RGB/BGR colors look wrong after plotting.

Fixes:

- Set `project`, `name`, and `exist_ok=True` for predictable output locations.
- Use `result.save(filename="outputs/prediction.jpg")` for direct annotated-image control.
- Use `save_crop` only when box-based crops are supported; it is not for classification, OBB, or semantic segmentation.
- Avoid `show=True` without a GUI. Use `result.plot()` and save/encode the array instead.
- `result.plot()` returns an image array that is commonly handled as BGR for OpenCV; convert with `image[..., ::-1]` before making an RGB PIL image.

## Device and Backend Problems

Symptoms:

- CUDA device unavailable or out of memory.
- Half precision fails on CPU or unsupported backends.
- Torch/OpenCV/ONNXRuntime provider errors.
- First inference call is much slower than later calls.

Fixes:

- Start with `device=cpu`, small `imgsz`, and a single local image to prove the model and source are valid.
- Use an explicit CUDA device only after confirming PyTorch sees it, for example with `python -c "import torch; print(torch.cuda.is_available())"`.
- Disable `half=True` on unsupported devices; use full precision on CPU.
- Expect warmup overhead on the first prediction call; measure steady-state after warmup.
- For exported models or ONNXRuntime-style code, route deployment/backend diagnosis to `../export-and-deployment/`.

## Download and Network Risks

Symptoms:

- Constructing `YOLO("yolo26n.pt")` downloads weights.
- URL image/video prediction fails due to timeout, SSL, DNS, codec, or firewall issues.
- CI jobs become flaky because they rely on external assets.

Fixes:

- Use local weight files in production, tests, and skills verification.
- Use local image/video fixtures for deterministic checks.
- Treat named weights and URL sources as network-dependent unless already cached.
- Keep examples safe by using placeholders and warning about possible downloads.

## Threading and Concurrency

Symptoms:

- Race-like behavior or inconsistent results when one `YOLO` object is shared across threads.
- Throughput is worse than expected with Python threads.

Fixes:

- Prefer one `YOLO` instance per worker thread or process.
- If sharing one model is unavoidable, serialize access with `ultralytics.utils.ThreadingLocked` around the function that calls `model.predict`.
- Consider process-based workers or a task queue for heavier CPU/GPU inference workloads.
- Avoid mutating callbacks or predictor state concurrently across threads.

## Avoiding Unintended Expensive Work

Prediction should not train, validate, export, benchmark, or tune unless explicitly requested. Check that commands use `predict` mode, not `train`, `val`, `export`, or `benchmark`. Avoid `save_frames=True` and broad media directories unless disk and time costs are intentional.
