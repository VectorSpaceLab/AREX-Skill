---
name: model-lifecycle
description: "Guides RoboSat model training, checkpoint resume, ONNX export,
  batch prediction, on-demand serving, U-Net APIs, configs, and CPU/CUDA
  troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Model lifecycle

Use this sub-skill for RoboSat work that sits on the model side of the pipeline.

## Use this route when the user needs to

- train a segmentation model on an existing slippy-map dataset
- resume or fine-tune from a `.pth` checkpoint
- export a trained checkpoint to an ONNX `.pb`
- run batch prediction and write probability tiles
- serve on-demand mask tiles through the Flask tile server
- inspect or reason about `UNet`, losses, metrics, transforms, or dataset wrappers
- debug CPU/CUDA, checkpoint, or config problems

## Do not use this route for

- imagery download, OSM extraction, rasterization, class-weight generation, or tile-layout work
- probability-to-mask conversion, GeoJSON feature extraction, merge/dedupe/compare workflows
- Docker publishing or maintainer release workflows

## Read first

- [references/workflows.md](references/workflows.md) for command templates and validation steps.
- [references/configuration.md](references/configuration.md) for model/dataset TOML fields and checkpoint format.
- [references/api-reference.md](references/api-reference.md) for model classes, losses, metrics, transforms, and buffered tile helpers.
- [references/troubleshooting.md](references/troubleshooting.md) for the common failure modes and recovery paths.

## Bundled checks

- [scripts/unet_cpu_smoke.py](scripts/unet_cpu_smoke.py) proves the installed package can build `UNet(pretrained=False)` and run a tiny CPU forward pass.
- [scripts/check_training_layout.py](scripts/check_training_layout.py) validates the `training/` and `validation/` splits, matching tile ids, and optional batch/drop-last risk.

## Short route map

### Train or resume
1. Check the dataset layout and class-weight assumptions in `configuration.md`.
2. Run `scripts/check_training_layout.py` against the dataset root before launching training.
3. Use `rs train` or `python -m robosat.tools train` with a writable checkpoint directory.
4. Inspect the generated `.pth`, `log`, and `history-*.png` files.

### Export
1. Start from a trained checkpoint with the matching class count.
2. Use `rs export` or `python -m robosat.tools export` to write the ONNX `.pb`.
3. Verify the file exists and can be consumed by downstream ONNX tooling.

### Predict
1. Reuse the matching model and dataset config plus a trained checkpoint.
2. Use `rs predict` or `python -m robosat.tools predict` on a slippy-map tile tree.
3. Check the probability tile directory for `z/x/y.png` outputs.

### Serve
1. Reuse the same checkpoint, model config, and dataset config.
2. Set the map access token and a tile URL template with `{x}`, `{y}`, and `{z}` placeholders.
3. Use `rs serve` or `python -m robosat.tools serve` for quick on-demand mask inspection.

## Cross-route guidance

- If the task is about creating the dataset itself, use the data-preparation route instead.
- If the task is about turning probability masks into GeoJSON or comparing/merging masks, use the feature-postprocessing route instead.
- If a workflow hits a missing dependency or backend issue, read `references/troubleshooting.md` before changing the command.
