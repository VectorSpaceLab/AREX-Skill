# Workflows

This sub-skill covers training, resuming, exporting, predicting, and serving RoboSat segmentation models. For field meanings and file layouts, read [configuration.md](configuration.md). For class and tensor shapes, read [api-reference.md](api-reference.md).

## Common prerequisites

- Use the installed `rs` entry point when available; otherwise use `python -m robosat.tools`.
- Keep the model and dataset configs aligned with the same class order.
- Use square tile and image sizes that are divisible by 32.
- Set `model.common.cuda = false` for CPU-only runs, or `true` only when a CUDA build of PyTorch is available.
- If you plan to use `CrossEntropy`, `mIoU`, or `Focal` loss, the dataset config must include class weights.
- Before a longer training run, validate the dataset root with `scripts/check_training_layout.py`.
- For a quick install/import sanity check, run `scripts/unet_cpu_smoke.py`.

## Train a model

```bash
rs train --model MODEL_TOML --dataset DATASET_TOML --workers 4
# or
python -m robosat.tools train --model MODEL_TOML --dataset DATASET_TOML --workers 4
```

What it does:

- builds a `UNet` with a ResNet50 encoder
- reads training and validation tiles from `dataset.common.dataset`
- normalizes RGB inputs, resizes and crops them to `model.common.image_size`
- trains for `opt.epochs` epochs with Adam and the configured loss
- writes checkpoints and metric history plots into `model.common.checkpoint`

Expected outputs:

- `checkpoint-00001-of-00010.pth` style checkpoint files
- `history-00001-of-00010.png` style metric plots
- `log` text lines with hyperparameters and epoch summaries

Validation after the run:

- confirm the checkpoint directory exists and is writable
- confirm each `.pth` file contains `epoch`, `state_dict`, and `optimizer`
- confirm the history PNG count matches the number of completed epochs
- confirm the log shows the expected class label and metrics

Important notes:

- The CLI currently calls `UNet(num_classes)` with the default pretrained encoder path, so first runs may try to download ResNet50 weights unless they are already cached.
- `--resume` is parsed as a boolean; pass `--resume True` when you want to restore optimizer state and epoch count.
- If `opt.loss` is `CrossEntropy`, `mIoU`, or `Focal`, missing `weights.values` will stop training.

## Resume or fine-tune from a checkpoint

```bash
rs train --model MODEL_TOML --dataset DATASET_TOML --checkpoint CHECKPOINT.pth --resume True --workers 4
```

Use this when the checkpoint should restore the previous optimizer state and continue epoch counting.

Use a fresh run instead of resume when you only want to initialize from the checkpoint weights.

Validation after the run:

- confirm the resumed epoch advances from the checkpoint value
- confirm the optimizer state is restored if you requested resume
- confirm the new checkpoint directory does not overwrite the old one unless that is intentional

Important notes:

- If the checkpoint epoch is already at or beyond `opt.epochs`, the CLI exits immediately.
- Because the CLI uses `type=bool`, `--resume False` does not behave like a reliable false flag.

## Export to ONNX

```bash
rs export --dataset DATASET_TOML --checkpoint CHECKPOINT.pth OUTPUT.pb
# or
python -m robosat.tools export --dataset DATASET_TOML --checkpoint CHECKPOINT.pth OUTPUT.pb
```

What it does:

- loads the dataset config only to determine the number of classes
- loads the checkpoint on CPU
- exports a GraphProto `.pb` using a square synthetic input tensor

Validation after the run:

- confirm the output file exists and is non-empty
- confirm downstream ONNX tooling can inspect the file
- confirm the chosen `--image_size` is divisible by 32

Important notes:

- export still instantiates the encoder with the default pretrained path, so an offline environment may need cached ResNet50 weights.
- The export command does not use the model config file.

## Batch prediction to probability tiles

```bash
rs predict --model MODEL_TOML --dataset DATASET_TOML --checkpoint CHECKPOINT.pth --tile_size 512 --overlap 32 INPUT_TILES PROBS_DIR
# or
python -m robosat.tools predict --model MODEL_TOML --dataset DATASET_TOML --checkpoint CHECKPOINT.pth --tile_size 512 --overlap 32 INPUT_TILES PROBS_DIR
```

What it does:

- reads a slippy-map directory of input images
- buffers each tile with neighboring context before prediction
- writes `PROBS_DIR/z/x/y.png` palette PNGs containing quantized foreground probabilities

Validation after the run:

- confirm the output tile count matches the input tile count
- open one output tile and confirm it is a palette PNG with the expected dimensions
- confirm the probability tiles preserve the slippy-map `z/x/y` structure

Important notes:

- The current serializer is binary-only and asserts that the model output has exactly two channels.
- The output is a probability directory, not the final mask or GeoJSON workflow.
- The model constructor may try to download pretrained ResNet50 weights on first run unless the cache is already warm.
- `--tile_size` should match the tile size used by the input slippy-map directory and stay divisible by 32.

## Serve on-demand masks

```bash
MAPBOX_ACCESS_TOKEN=TOKEN \
rs serve --model MODEL_TOML --dataset DATASET_TOML --checkpoint CHECKPOINT.pth --url 'TILE_URL_TEMPLATE' --tile_size 512 --host 127.0.0.1 --port 5000
# or
MAPBOX_ACCESS_TOKEN=TOKEN python -m robosat.tools serve --model MODEL_TOML --dataset DATASET_TOML --checkpoint CHECKPOINT.pth --url 'TILE_URL_TEMPLATE' --tile_size 512 --host 127.0.0.1 --port 5000
```

What it does:

- launches a Flask app that fetches imagery tiles on demand
- runs the current checkpoint per request and returns a mask PNG
- serves a simple map page that needs a map token

Validation after the run:

- request `http://HOST:PORT/18/X/Y.png` for a tile you know exists
- confirm the response is a PNG image
- confirm the browser map page renders with the token set

Important notes:

- The current implementation only serves zoom level 18.
- `MAPBOX_ACCESS_TOKEN` must be set for the map page to render.
- `--url` must contain `{x}`, `{y}`, and `{z}` placeholders.
- The server runs with `threaded=False` and is intended for inspection, not high-throughput serving.

## When to switch routes

- Data acquisition, rasterization, and class weights belong to the data-preparation route.
- Probability-to-mask, merge, dedupe, compare, subset, and GeoJSON tasks belong to the feature-postprocessing route.
