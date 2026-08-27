# Troubleshooting

## Runtime bundle issues

### Missing `runtime/` files

If a helper cannot find `runtime/detect.py`, `runtime/test.py`, `runtime/train.py`, or the bundled YAML files, the generated skill tree is incomplete.

Recovery:

- Recreate the bundled runtime mirror before using the skill.
- Do not point the helper scripts at the original checkout to work around a missing bundle.

## Model import and backend issues

### `ModuleNotFoundError: mish_cuda`

`models/common.py` imports `MishCuda` directly. This usually means the CUDA Mish extension is missing from the environment or the environment is not the one you expected.

Recovery:

- Use a CUDA-capable environment for full model checks.
- Reinstall or rebuild the Mish CUDA extension before retrying model import or forward validation.
- If you only need to read the skill or validate CLI help, stay in the lightweight inspection path and do not treat a CPU-only import as a full success signal.

### CUDA is unavailable

Some workflows can still parse arguments on CPU, but the model stack, training, and export paths are designed around CUDA. If a GPU-dependent helper or model forward check fails because CUDA is missing, treat that as an environment limitation rather than a skill bug.

## Data and path issues

### `File Not Found` / `No images found` / `No images or videos found`

These usually mean the dataset YAML, source path, or text file points to the wrong place.

Recovery:

- Resolve paths relative to the repository root unless the workflow explicitly says otherwise.
- Use the dataset inspection helper before training or evaluation.
- Confirm the split file actually lists image paths when the YAML points at a `.txt` file.

### `No labels found`

Training cannot proceed without usable labels unless you are deliberately running a label-free inference path.

Recovery:

- Verify the labels directory mirrors the images directory.
- Check that labels use the expected five-column YOLO format.
- Make sure the label files are not empty because of a naming mismatch.

### Negative or out-of-bounds labels

`LoadImagesAndLabels` asserts that labels are normalized and within bounds.

Recovery:

- Re-export the dataset in YOLO format.
- Check that `x_center`, `y_center`, `width`, and `height` are normalized to `[0, 1]`.
- Confirm that class ids are zero-based.

### `image size <10 pixels`

The loader rejects extremely small images during cache creation.

Recovery:

- Remove corrupt or placeholder files.
- Rebuild the dataset cache after fixing the source files.

## Shape and stride issues

### `--img-size must be multiple of max stride`

The model expects image sizes that are compatible with its maximum stride.

Recovery:

- Let the bundled model smoke helper show you the stride.
- Round the image size up to the nearest valid multiple.
- Use the same logic for training and evaluation to avoid mismatched preprocessing.

## Training-specific runtime issues

### DDP batch size problems

Distributed training expects the batch size to be compatible with the world size.

Recovery:

- Make the total batch size divisible by the number of CUDA devices.
- Check the `local_rank` and `world_size` settings before launching.

### TensorBoard import or TensorFlow crashes

The training script imports `SummaryWriter` at module import time. Some mixed TensorBoard/TensorFlow installations can fail before the run starts.

Recovery:

- Use the CLI helper or a minimal preflight before a long training run.
- Repair the environment rather than assuming the repo is broken.

### Anchor warnings during training

The automatic anchor check can warn that the current anchors fit poorly.

Recovery:

- Inspect the dataset layout and label distribution first.
- Only adjust anchors after the dataset itself is valid.

## Evaluation and export issues

### `pycocotools unable to run`

COCO JSON evaluation is optional and depends on `pycocotools`.

Recovery:

- Install the optional package if you need COCO metrics.
- Otherwise keep to the non-JSON evaluation path.

### ONNX or CoreML export fails

Optional export backends are not always installed.

Recovery:

- Check backend availability with the export helper before starting the conversion.
- If CoreML is unavailable, fall back to TorchScript or ONNX.

## Inference issues

### Webcam or stream input fails

The stream loaders rely on OpenCV capture support and can be sensitive to codec or camera issues.

Recovery:

- Test with a local image folder first.
- Confirm the source string or text file is correct.
- Use the inference planning helper to classify the source before running a long detection job.

### Output directory confusion

The detection workflow deletes or recreates the output folder before saving results.

Recovery:

- Treat the output directory as disposable scratch space.
- Point the run at an empty or expendable location.
- Do not use `--update` unless you are intentionally stripping optimizer state from weights.
