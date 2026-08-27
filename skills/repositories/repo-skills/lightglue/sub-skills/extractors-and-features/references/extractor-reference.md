# Extractor reference

This reference summarizes the LightGlue-supported extractor classes and the feature-specific matcher pairings they produce. Use it to choose an extractor and to decide whether first-use downloads, optional backends, or extra feature keys are expected.

## Feature families and defaults

| Extractor class | Family | Descriptor dim | Default feature limit | Default preprocessing | First-use downloads / optional dependencies | Notes |
|---|---:|---:|---|---|---|---|
| `SuperPoint` | learned detector+descriptor | 256 | `max_num_keypoints=None` | `Extractor.extract(..., resize=1024)` | Downloads SuperPoint weights with `torch.hub.load_state_dict_from_url` on construction if not cached. | Converts RGB input to grayscale internally. `max_num_keypoints` must be positive or `None`. |
| `DISK` | learned detector+descriptor | 128 | `max_num_keypoints=None` | `resize=1024` | Uses `kornia.feature.DISK.from_pretrained(weights="depth")`; Kornia may download/cache pretrained weights. | Converts grayscale input to RGB internally. `detection_threshold=0.0`, `nms_window_size=5`, `pad_if_not_divisible=True`. |
| `ALIKED` | learned detector+descriptor | 128 for `aliked-n16`, `aliked-n16rot`, `aliked-n32`; 64 for `aliked-t16` | `max_num_keypoints=-1` | `resize=1024` | Downloads selected ALIKED checkpoint with `torch.hub.load_state_dict_from_url` on construction if not cached. | Default `model_name="aliked-n16"`, `detection_threshold=0.2`, `nms_radius=2`. Top-k semantics depend on `detection_threshold`; see below. |
| `SIFT` | Difference-of-Gaussians detector + SIFT/RootSIFT descriptor | 128 | `max_num_keypoints=4096` | `resize=1024` | Default `backend="opencv"` has no model weights. Optional `pycolmap`, `pycolmap_cpu`, and `pycolmap_cuda` require a separate `pycolmap` installation and compatible hardware for CUDA. | Converts RGB input to grayscale. Default `rootsift=True`, `nms_radius=0`, `detection_threshold=0.0066667`, `edge_threshold=10`, `num_octaves=4`. Emits `scales` and `oris`. |
| `DoGHardNet` | SIFT/DoG keypoints + HardNet descriptors | 128 | inherits `SIFT` default | inherits `SIFT` default | Uses the SIFT backend for detections and constructs a pretrained Kornia `HardNet`; Kornia may download/cache weights. | Emits SIFT-style `scales` and `oris`. Use with `LightGlue(features="doghardnet")`, not the SIFT matcher. |

## Matcher pairing table

| Feature dictionary source | Recommended matcher | Required descriptor dim | `LightGlue` adds scale/orientation? | Weight behavior |
|---|---|---:|---|---|
| `SuperPoint(...).extract(image)` | `LightGlue(features="superpoint")` | 256 | no | Matcher weights may download on construction. |
| `DISK(...).extract(image)` | `LightGlue(features="disk")` | 128 | no | Matcher weights may download on construction. |
| `ALIKED(model_name="aliked-n16"/` `"aliked-n16rot"/` `"aliked-n32").extract(image)` | `LightGlue(features="aliked")` | 128 | no | Matcher weights may download on construction. |
| Compatible 128-D RACO-ALIKED-style precomputed features | `LightGlue(features="raco-aliked")` | 128 | no | Matcher weights may download on construction; no dedicated extractor class is exported. |
| `SIFT(...).extract(image)` | `LightGlue(features="sift")` | 128 | yes; needs `scales` and `oris` | Matcher weights may download on construction. |
| `DoGHardNet(...).extract(image)` | `LightGlue(features="doghardnet")` | 128 | yes; needs `scales` and `oris` | Matcher weights may download on construction. |
| Custom/precomputed descriptors without a compatible preset | `LightGlue(features=None, input_dim=D, descriptor_dim=...)` | caller-selected | only if `add_scale_ori=True` is set manually | Does not download feature-specific pretrained matcher weights; meaningful matching requires an appropriate trained configuration or separately loaded weights. |

Do not mix a pretrained matcher preset with descriptors from a different family unless the descriptor dimension and training distribution are intentionally compatible. A dimension match alone does not guarantee meaningful correspondences.

## `Extractor.extract` and `ImagePreprocessor`

All bundled extractor classes inherit the shared `Extractor.extract` helper:

- Accepts a torch image tensor shaped `(C,H,W)` or `(1,C,H,W)`, normalized to floating point values in `[0,1]`.
- Adds a batch dimension for unbatched input and asserts a single-image batch.
- Stores the original image size as `(width, height)` in `image_size`.
- Runs `ImagePreprocessor`, whose defaults are `resize=None`, `side="long"`, `interpolation="bilinear"`, `align_corners=None`, and `antialias=True`.
- Each extractor overrides preprocessing with `resize=1024`; pass `resize=None` to disable this automatic resizing.
- Rescales output keypoints back to the original image coordinates with the same corner convention used by the implementation.

## ALIKED variant and keypoint-limit semantics

ALIKED has four model variants:

| `model_name` | Descriptor dim | Typical use with pretrained LightGlue |
|---|---:|---|
| `aliked-t16` | 64 | Not compatible with `LightGlue(features="aliked")`, which expects 128-D descriptors. Use only with a matching custom configuration/weights. |
| `aliked-n16` | 128 | Default and compatible with `LightGlue(features="aliked")`. |
| `aliked-n16rot` | 128 | Compatible descriptor dimension; choose when the model variant is desired and weights can be downloaded/cached. |
| `aliked-n32` | 128 | Compatible descriptor dimension; larger local descriptor head setting. |

ALIKED does not interpret `max_num_keypoints` exactly like SuperPoint or SIFT:

- With `detection_threshold > 0` (default `0.2`), ALIKED runs threshold mode. `max_num_keypoints > 0` caps the threshold-mode output; `-1` allows up to the internal safety limit.
- With `detection_threshold <= 0` and `max_num_keypoints > 0`, ALIKED switches to fixed top-k mode.
- With `detection_threshold <= 0` and `max_num_keypoints <= 0`, it falls back to a mean-score threshold and the internal safety limit.

For a request like “exactly top 1024 ALIKED features”, use `ALIKED(max_num_keypoints=1024, detection_threshold=-1)` and a 128-D variant if pairing with `LightGlue(features="aliked")`.

## SIFT backend notes

`SIFT` accepts `backend` in `{ "opencv", "pycolmap", "pycolmap_cpu", "pycolmap_cuda" }`.

- `opencv` is the default, CPU-safe path and should be the first choice for offline schema validation.
- `pycolmap` selects device automatically when available; `pycolmap_cpu` and `pycolmap_cuda` force the backend.
- Older CPU pycolmap SIFT behavior is known to be buggy; upgrade pycolmap or use a verified CUDA-capable build if you rely on pycolmap output.
- OpenCV SIFT returns detector responses as `keypoint_scores`; newer pycolmap SIFT may not expose scores, so do not make matcher code depend on that key.
