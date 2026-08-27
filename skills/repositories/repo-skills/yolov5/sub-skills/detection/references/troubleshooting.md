# Detection Troubleshooting

## Weight and checkpoint issues

### `FileNotFoundError` or download failure for `yolov5s.pt`

Likely causes:

- The checkpoint name was passed without local availability and network access is blocked.
- The user intended a local checkpoint path but passed a release-style name.

Recovery:

- Use an explicit local path when offline.
- Confirm whether the checkpoint is detection (`*.pt`) rather than segmentation/classification.
- Check whether the Hub cache needs a reload only after the user approves network/cache mutation.

### Model/class mismatch

Symptoms:

- Shape mismatch when loading a checkpoint into a custom head.
- Incorrect class count after training from scratch.
- Unexpected classes or names in prediction output.

Recovery:

- Match `--cfg` and checkpoint family to the task.
- Verify `names` length in the dataset YAML.
- Use `DetectionModel(cfg, ch, nc, anchors)` only with compatible configs.

## CLI and data issues

### Wrong source type

Examples:

- Passing a stream URL when a local file was intended.
- Using `screen` without a supported capture environment.
- Passing a directory path that contains unsupported files.

Recovery:

- Start with a local image and `--nosave`.
- Move to video, then directory, then stream sources only after the basic path is valid.
- Keep the source type explicit in the command preview.

### Bad `data` YAML

Symptoms:

- `val.py` or `train.py` cannot find labels/images.
- The wrong number of classes appears.
- A path resolves relative to an unexpected directory.

Recovery:

- Check the dataset layout in `references/datasets-and-weights.md`.
- Use a tiny dataset first, such as COCO128, before scaling to full data.
- Verify the YAML `path`, `train`, `val`, and `names` entries.

## Device and precision issues

- Remove `--half` on CPU or unsupported backends.
- Set `--device cpu` for deterministic inspection and parser checks.
- Prefer a CUDA device for realistic throughput or training.
- Use smaller image sizes or model sizes if memory pressure appears.

## Output and run-directory issues

- Set `--project` and `--name` explicitly to avoid scattering runs.
- Use `--exist-ok` only when intentional overwriting is acceptable.
- Use `--nosave` for dry inference checks.
- Use `--save-txt` or `--save-csv` only when a downstream consumer needs those files.

## PyTorch Hub issues

- `custom()` is the preferred local-checkpoint path.
- `autoshape=True` is convenient but not a substitute for the task-specific API.
- If the Hub cache is stale, forcing reload may redownload weights.
- Segmentation and classification models can be loaded through Hub but may not behave like detection models in AutoShape mode.

## Verification signals to expect

- CLI help prints a full parser usage block.
- `torch.cuda.is_available()` is true on a compatible CUDA environment.
- `models.common` and `models.yolo` import cleanly.
- Detection output contains boxes, confidences, and class ids/names.
