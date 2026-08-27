---
name: single-image-inference
description: "Safely use or adapt pytorch-semseg test.py for one-image semantic
  segmentation with trained checkpoints, dataset palette decoding, output mask
  creation, and optional DenseCRF."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Single Image Inference

Use this sub-skill when the task is to run, adapt, or debug `test.py` for a single RGB image and an existing trained checkpoint. It covers the inference CLI, checkpoint-name architecture parsing, dataset palette decoding, output image semantics, compatibility patches, and optional DenseCRF post-processing.

Route elsewhere:

- Training commands, checkpoint production, validation metrics, and resume behavior belong to `training-and-evaluation`.
- Dataset filesystem layouts, YAML config authoring, and dataset split preparation belong to `data-and-configs`.
- Model constructor signatures, registry internals, and architecture API details belong to `model-zoo-and-apis`.

## Core operating facts

- The source inference entry point is `test.py`.
- Supported CLI flags are `--model_path`, `--dataset`, `--img_norm` / `--no-img_norm`, `--dcrf` / `--no-dcrf`, `--img_path`, and `--out_path`.
- The architecture id is parsed from the checkpoint basename before the first underscore. A checkpoint named `icnetBN_cityscapes_best_model.pkl` selects `icnetBN`; a name without `_` is unsafe because the script's slicing logic will not recover the intended model id.
- The script constructs the dataset loader with `root=None`, `is_transform=True`, the chosen `img_norm`, and `test_mode=True`, then calls `loader.decode_segmap(pred)` to produce the colorized output mask.
- The saved output is a dataset-palettized RGB segmentation visualization, not a raw class-index mask. Adapt the script before `decode_segmap` if a numeric label image is required.
- For `pspnet`, `icnet`, and `icnetBN`, the input image is resized to odd spatial dimensions before model inference and the prediction is resized back to the original image size with nearest-neighbor interpolation.
- DenseCRF is optional. The source script prints a warning if `pydensecrf` cannot be imported, but a `--dcrf` run still needs the package available and compatible.
- The original image helper calls use legacy `scipy.misc.imread`, `scipy.misc.imresize`, and `scipy.misc.imsave`; modern environments often need a compatibility patch or a legacy SciPy/Pillow environment.

## Safe command construction

Use the bundled dry-run helper before running real inference:

- [scripts/build_inference_command.py](scripts/build_inference_command.py) validates the dataset key, checkpoint basename pattern, image path, output parent, normalization flag, and DenseCRF selection without loading images, checkpoints, datasets, or models.
- It prints a ready-to-run `test.py` command and warnings for unsafe checkpoint names, missing files, optional dependency risk, and PSPNet/ICNet odd-size behavior.

Detailed recipes and adaptation notes are in [references/workflows.md](references/workflows.md). Failure modes and fixes are in [references/troubleshooting.md](references/troubleshooting.md).

## Minimal workflow

1. Confirm you already have a trained pytorch-semseg checkpoint containing a `model_state` entry.
2. Confirm the checkpoint basename begins with a supported architecture id followed by `_`.
3. Choose the matching dataset key so `decode_segmap` uses the intended color palette.
4. Run the bundled command builder from this sub-skill directory, or pass its path from your working directory.
5. Run the printed `test.py` command from a checkout or environment where `test.py` and `ptsemseg` are importable.
6. If the run fails before inference because of SciPy or `pydensecrf`, patch the helpers or disable DenseCRF using the guidance in the references.
