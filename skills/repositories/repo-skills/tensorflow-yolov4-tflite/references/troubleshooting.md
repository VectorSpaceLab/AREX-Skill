# Cross-Cutting Troubleshooting

Use this when installation, imports, relative paths, optional backends, or
shared configuration fail before a workflow-specific sub-skill can proceed.

## TensorFlow import fails with protobuf descriptor errors

**Symptom**

```text
TypeError: Descriptors cannot be created directly.
...
Downgrade the protobuf package to 3.20.x or lower.
```

**Likely cause**: TensorFlow 2.3 was installed with a modern protobuf package.

**Recovery**

```bash
python -m pip install "protobuf<3.20"
python -m pip check
python -c "import tensorflow as tf; print(tf.__version__)"
```

If the user cannot change dependencies, set
`PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python` only as a slower diagnostic, not
as the preferred production fix.

## `./data/classes/coco.names` is missing

**Symptom**

```text
FileNotFoundError: [Errno 2] No such file or directory: './data/classes/coco.names'
```

**Likely cause**: A script was launched outside the target checkout root. The
repo's config defaults are relative to the current working directory.

**Recovery**

1. Change to the target checkout root before running the repo's scripts.
2. If running a bundled helper from another directory, pass its `--repo-root`
   argument so it can validate the target checkout.
3. For custom class files, edit the target checkout's `core/config.py` or provide
   an equivalent checkout-relative file layout before training/conversion.

## Old package pins are unavailable

**Symptom**

```text
No matching distribution found for tensorflow==2.3.0rc0
No matching distribution found for opencv-python==4.1.1.26
```

**Likely cause**: Historical wheels are missing for the chosen Python version,
platform, or package index.

**Recovery**

- Use Python 3.8 and try TensorFlow 2.3.0 stable plus OpenCV 4.1.2.30 for CPU
  command planning and basic repo use.
- If exact reproduction is required, use an archival container or environment
  known to carry the old wheels.
- Do not upgrade TensorFlow to a much newer major/minor release without testing
  `save_model.py`, `detect.py`, and conversion output shapes; private API paths
  and TensorRT behavior may change.

## GPUs are visible but TensorFlow reports none usable

**Symptom**

TensorFlow logs a visible NVIDIA GPU and then warnings like:

```text
Could not load dynamic library 'libcudart.so.10.1'
Could not load dynamic library 'libcudnn.so.7'
Skipping registering GPU devices...
```

**Likely cause**: The driver sees the GPU, but the TensorFlow 2.3 runtime cannot
find the CUDA 10.1/cuDNN 7 user-space libraries it was built for.

**Recovery**

- Continue CPU-only conversion/inference planning if the task does not require
  TensorRT or GPU speed.
- For TF-TRT or GPU training, use a TensorFlow 2.3-compatible CUDA/cuDNN/TensorRT
  environment or a container that supplies those libraries.
- Do not treat a modern CUDA toolkit alone as proof of compatibility; verify
  `tf.config.experimental.list_physical_devices("GPU")` inside the selected
  environment.

## TFLite or SavedModel commands fail because inputs are absent

**Symptoms**

- `NotFoundError` or `OSError` for a SavedModel directory.
- `FileNotFoundError` for `.weights`, `.tflite`, image, video, or dataset list.
- Empty or missing output artifact after conversion.

**Recovery**

1. Use the model-conversion command planner to confirm source and target paths.
2. Confirm that Darknet weights were downloaded or supplied by the user before
   running `save_model.py`.
3. Confirm that `save_model.py --framework tflite` was used before TFLite export
   when the user intends a TFLite-friendly SavedModel.
4. For INT8 quantization, confirm that the representative dataset file exists
   and contains image paths that are accessible from the machine running the
   command.

## OpenCV image/video load failures

**Symptoms**

- `cv2.imread` returns `None`, then color conversion crashes.
- `ValueError: No image! Try with another video format` during video detection.
- Output image/video is empty or not written.

**Recovery**

- Validate input file existence and format before launching a long detection run.
- Prefer absolute input/output paths when the task spans directories.
- Use image formats OpenCV can decode, and for video output ensure the requested
  codec is available on the host.
- For headless machines, pass the video detection option that disables OpenCV UI
  windows, and write an output file instead.

## Training or evaluation silently uses the wrong annotations

**Symptom**: Training/evaluation reads `./data/dataset/val2017.txt` even though
the user expected a custom dataset.

**Likely cause**: `core.config.cfg.TRAIN.ANNOT_PATH` and
`cfg.TEST.ANNOT_PATH` are fixed in config unless the target checkout is edited.

**Recovery**

- Use the training-data annotation validator on representative lines.
- Confirm class-file order and class indices before training.
- Edit the target checkout's config values deliberately and record the change in
  the user's experiment notes; avoid patching commands blindly.
