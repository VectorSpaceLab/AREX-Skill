---
name: pytorch-workflows
description: "Routes Raster Vision PyTorch workflow setup for chip
  classification, semantic segmentation, and object detection, including
  GeoDataConfig/ImageDataConfig choices,
  SolverConfig/model/backbone/external_def selection, model-zoo transfer, and
  example command rendering."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# pytorch-workflows

Use this sub-skill when you need to configure, explain, or reproduce Raster Vision PyTorch task workflows.

## Use this route for

- Picking the right PyTorch backend for chip classification, semantic segmentation, or object detection.
- Choosing between `GeoDataConfig` and `ImageDataConfig`, including `nochip`, `allow_streaming`, multiband imagery, and scene cropping.
- Selecting `SolverConfig`, `Backbone`, `ModelConfig`, `ExternalModuleConfig`, `external_loss_def`, and `init_weights`.
- Working from the bundled examples: `tiny_spacenet`, SpaceNet Rio, SpaceNet Vegas, ISPRS Potsdam, COWC Potsdam, and xView.
- Reading training, prediction, bundle, eval, and dataloader debug outputs.
- Using model-zoo bundles for prediction or transfer learning.

## Do not use this route for

- Generic CLI invocation details, runner semantics, or split handling. Use `pipeline-cli`.
- Lower-level raster, vector, label, and scene API details. Use `data-and-models`.
- AWS, Docker, or remote execution setup. Use `cloud-and-filesystems`.

## Read first

- [Task recipes](references/task-recipes.md)
- [Example catalog](references/example-catalog.md)
- [Model zoo and transfer](references/model-zoo-and-transfer.md)
- [Troubleshooting](references/troubleshooting.md)

## Skill-owned scripts

- `scripts/list_example_commands.py` — print safe `rastervision run` commands for known PyTorch examples; it never executes them and supports `--help`.

## Typical workflow

1. Identify the task family and whether the data is scene-based, chip-based, or bundle-based.
2. Choose `GeoDataConfig` when Raster Vision should read scenes directly; choose `ImageDataConfig` when chips already exist.
3. Pick the backend, backbone, and any external model or loss definitions.
4. Use the example catalog and command printer to generate a safe local or remote run command.
5. Inspect `train/`, `predict/`, `eval/`, and `bundle/` outputs before deciding on tuning or transfer.

## Cross-links

- If the problem is really CLI execution or command parsing, switch to `pipeline-cli`.
- If you need scene, raster, vector, or label mechanics, switch to `data-and-models`.
- If you need Docker or AWS execution setup, switch to `cloud-and-filesystems`.
