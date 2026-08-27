# Troubleshooting

Use this guide when a RoboSat model-lifecycle command fails, exits early, or produces confusing outputs.

## Device and install issues

### CUDA requested but unavailable

- **Symptom:** `Error: CUDA requested but not available`
- **Likely cause:** `model.common.cuda = true` but the current PyTorch build does not expose CUDA.
- **Recovery:** set `cuda = false` for CPU runs, or use a CUDA-capable PyTorch build and GPU runtime before retrying.

### Old torch wheels or legacy Python mismatch

- **Symptom:** import errors or model startup failures around `torch`, `torchvision`, or `resnet50`.
- **Likely cause:** RoboSat targets the legacy PyTorch 1.1 / torchvision 0.3 wheel family and Python 3.6-era packaging.
- **Recovery:** use the legacy wheel family that matches the project, or run inside the documented CPU / GPU container path if you need a reproducible environment.

### Pretrained download avoidance

- **Symptom:** the first training, export, predict, or serve run tries to reach the network for encoder weights.
- **Likely cause:** the CLI stack constructs `UNet(num_classes)` with the default `pretrained=True` encoder path.
- **Recovery:** allow the cache to warm once, run in a networked environment the first time, or use a helper script that explicitly sets `pretrained=False` when you only need a smoke test.

## Configuration and data issues

### Missing class weights for weighted losses

- **Symptom:** `Error: The loss function used, need dataset weights values`
- **Likely cause:** the selected loss is `CrossEntropy`, `mIoU`, or `Focal`, but `dataset.weights.values` is missing.
- **Recovery:** add a `weights.values` vector with one entry per class, or switch to `Lovasz` if you do not want class weighting.

### Image size not divisible by 32

- **Symptom:** `image resolution has to be divisible by 32 for resnet`
- **Likely cause:** `model.common.image_size` or the prediction tile size does not match the encoder-decoder stride requirements.
- **Recovery:** choose a square size that is divisible by 32 for both training and prediction.

### Empty splits or `drop_last` risk

- **Symptom:** the loader produces no batches, or tiles disappear from tiny debug datasets.
- **Likely cause:** the training or validation split is empty, or `batch_size` is larger than the split while `drop_last=True` discards the final incomplete batch.
- **Recovery:** add real tiles to the split, lower `batch_size`, or validate the layout first with `scripts/check_training_layout.py`.

### Checkpoint epoch already reached

- **Symptom:** `Error: Epoch X set in ... already reached by the checkpoint provided`
- **Likely cause:** the checkpoint epoch is already at or beyond `opt.epochs`.
- **Recovery:** raise `opt.epochs`, start from a fresh configuration, or pick an earlier checkpoint.

### `--resume` boolean confusion

- **Symptom:** `--resume False` still behaves like resume or the optimizer state is unexpectedly restored.
- **Likely cause:** the CLI parses `--resume` with `type=bool`.
- **Recovery:** omit the flag for a fresh fine-tune and pass `--resume True` only when you want to restore the optimizer state.

### DataParallel checkpoint loading mismatch

- **Symptom:** a custom loader cannot read the RoboSat checkpoint state dict.
- **Likely cause:** checkpoints are saved from a `DataParallel` wrapped model, so the keys may be prefixed with `module.`.
- **Recovery:** wrap the model in `DataParallel` before loading, or strip the prefix in your custom loader.

## Prediction and serving issues

### Batch prediction is binary-only

- **Symptom:** prediction fails on a multi-class model during PNG serialization.
- **Likely cause:** the current serializer asserts that the output has exactly two channels.
- **Recovery:** use this route only for binary foreground/background models, or adapt the serializer before trying multi-class probability PNGs.

### Serve token, URL, or port issues

- **Symptom:** the map page does not render, the tile request returns 404, or the server fails to start.
- **Likely cause:** `MAPBOX_ACCESS_TOKEN` is missing, the tile URL template does not contain `{x}`, `{y}`, and `{z}`, the requested port is already in use, or the request is not for zoom level 18.
- **Recovery:** set the token, fix the URL template, choose a free port, and request `/18/x/y.png` tiles for the current implementation.

## Validation reminders

- If a training run fails early, rerun `scripts/unet_cpu_smoke.py` to confirm the installed package can still import and build the model.
- If the dataset looks wrong, rerun `scripts/check_training_layout.py` before spending time on another training attempt.
- If a custom script fails to load a checkpoint, remember that the saved `state_dict` came from `DataParallel`.
