# Cross-cutting troubleshooting

## Import emits a network warning

Symptom: importing `albumentations` warns about failing to fetch version info.

Fix: set `NO_ALBUMENTATIONS_UPDATE=1` in offline, CI, or deterministic agent runs. The warning does not mean augmentation APIs failed to import.

## `ModuleNotFoundError: cv2`

Install an OpenCV provider compatible with your environment, usually `opencv-python-headless` on servers. Avoid mixing `opencv-python`, `opencv-contrib-python`, and headless variants unless you intentionally control which package provides `cv2`.

## `ToTensorV2` or `ToTensor3D` is missing

A base install may not expose PyTorch tensor transforms. Install PyTorch support with `pip install "albumentations[pytorch]"` or install compatible `torch`, then import from `albumentations.pytorch`. Route shape and dtype issues to `sub-skills/framework-integration/`.

## Transform constructor rejects old parameters

Albumentations 2.x renamed several parameters. Common examples include `value` -> `fill`, `mask_value` -> `fill_mask`, and old dropout min/max arguments -> tuple range arguments. Route migration work to `sub-skills/transform-catalog/`.

## Unknown keys or shape mismatches

Use `strict=True` and keep `is_check_shapes=True` while developing. Unknown target keys need `additional_targets` or must be removed. Shape mismatch errors usually mean image, mask, masks, volumes, or 3D masks have incompatible spatial dimensions. Route Compose-level issues to `sub-skills/pipeline-composition/` and annotation-format issues to `sub-skills/targets-and-formats/`.

## Bboxes or keypoints disappear

Check the declared format, label alignment, and filtering options. `BboxParams` can filter by visibility, area, width, height, aspect ratio, clipping, and validity; `KeypointParams(remove_invisible=True)` drops off-image keypoints. Route details to `sub-skills/targets-and-formats/`.

## Reproducibility does not match expectations

`Compose(seed=...)` controls the pipeline's own random generators, not all external randomness. Use `ReplayCompose` for exact replay of one draw, or `save_applied_params=True` to inspect sampled transform parameters. Route persistent configs and replay debugging to `sub-skills/serialization-and-reproducibility/`.

## Choosing Albumentations vs AlbumentationsX

Albumentations 2.0.8 remains MIT-licensed but unmaintained. AlbumentationsX is the active successor and has different licensing. Do not recommend migration blindly for permissive or proprietary projects without discussing licensing constraints.
