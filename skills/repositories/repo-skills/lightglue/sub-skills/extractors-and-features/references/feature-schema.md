# Feature dictionary schema

LightGlue matchers consume two feature dictionaries, one per image. Extractor classes produce these dictionaries through `.extract(image, **preprocess)`, and precomputed features must mimic the same structure.

## Coordinate and batch conventions

- Keypoints use pixel coordinates in `(x, y)` order.
- `image_size` uses `(width, height)` order, not `(height, width)`.
- `.extract()` returns a batch dimension even for one image: tensors are shaped with `B=1`.
- The shared extractor helper accepts `(C,H,W)` or `(1,C,H,W)` input and normalizes keypoints back to the original image size after optional resizing.
- Use floating point tensors on the same device for `keypoints`, `descriptors`, and the optional SIFT/DoGHardNet fields.

## Extractor output keys

| Key | Shape | Required for matching? | Produced by | Meaning |
|---|---:|---|---|---|
| `keypoints` | `[B, N, 2]` | yes | all extractors | Pixel-space `(x, y)` keypoint coordinates. |
| `descriptors` | `[B, N, D]` | yes | all extractors | Local descriptors. `D` must match the selected matcher preset. |
| `image_size` | `[B, 2]` | strongly recommended | `.extract()` for all extractors | Original `(width, height)` before extractor resizing; used to normalize keypoints. |
| `keypoint_scores` | `[B, N]` | no for LightGlue | SuperPoint, DISK, ALIKED, OpenCV SIFT, older pycolmap SIFT | Detector confidence/response. Newer pycolmap SIFT may omit it. |
| `scales` | `[B, N]` | yes for SIFT and DoGHardNet presets | SIFT, DoGHardNet | Keypoint scale/size used by pretrained SIFT-family matchers. |
| `oris` | `[B, N]` | yes for SIFT and DoGHardNet presets | SIFT, DoGHardNet | Keypoint orientation in radians. |

## Descriptor dimensions and preset requirements

| Matcher preset | Expected descriptor dim | Extra required keys | Compatible extractor output |
|---|---:|---|---|
| `LightGlue(features="superpoint")` | 256 | none beyond `keypoints`, `descriptors`, `image_size` | `SuperPoint` |
| `LightGlue(features="disk")` | 128 | none beyond `keypoints`, `descriptors`, `image_size` | `DISK` |
| `LightGlue(features="aliked")` | 128 | none beyond `keypoints`, `descriptors`, `image_size` | 128-D `ALIKED` variants such as `aliked-n16`, `aliked-n16rot`, `aliked-n32` |
| `LightGlue(features="raco-aliked")` | 128 | none beyond `keypoints`, `descriptors`, `image_size` | Compatible precomputed 128-D RACO-ALIKED-style features |
| `LightGlue(features="sift")` | 128 | `scales`, `oris` | `SIFT` or faithful SIFT-like precomputed features |
| `LightGlue(features="doghardnet")` | 128 | `scales`, `oris` | `DoGHardNet` or faithful DoG+HardNet precomputed features |
| `LightGlue(features=None, input_dim=D, descriptor_dim=...)` | caller-selected `D` | only if `add_scale_ori=True` is set | Custom/precomputed features with a compatible trained matcher setup |

The matcher checks descriptor dimensions with assertions. A common failure is using `LightGlue(features="superpoint")` with 128-D descriptors or using `LightGlue(features="aliked")` with `ALIKED(model_name="aliked-t16")`, which emits 64-D descriptors.

## Minimal matcher input

```python
data = {
    "image0": {
        "keypoints": keypoints0,      # [B, M, 2]
        "descriptors": descriptors0,  # [B, M, D]
        "image_size": image_size0,    # [B, 2] = width,height
    },
    "image1": {
        "keypoints": keypoints1,      # [B, N, 2]
        "descriptors": descriptors1,  # [B, N, D]
        "image_size": image_size1,    # [B, 2] = width,height
    },
}
```

For SIFT-family presets, add:

```python
data["image0"].update({"scales": scales0, "oris": orientations0})  # [B, M]
data["image1"].update({"scales": scales1, "oris": orientations1})  # [B, N]
```

## Precomputed descriptor guidance

When the user supplies precomputed features:

1. Add a batch dimension: `[N,2] -> [1,N,2]`, `[N,D] -> [1,N,D]`, `[N] -> [1,N]`.
2. Ensure descriptors are ordered as `[B,N,D]`, not `[B,D,N]`.
3. Put all tensors on the same device and use floating dtypes for coordinates/descriptors.
4. Provide `image_size=[width,height]` as a float or tensor convertible to the keypoint device.
5. Choose the matcher preset by descriptor family, not just descriptor dimension.
6. For SIFT-like or DoGHardNet-like descriptors, include `scales` and `oris`; otherwise the pretrained `sift`/`doghardnet` matchers cannot build their positional encoding.

If the user has only SIFT-like `keypoints` and 128-D descriptors but lacks `scales`/`oris`, do one of the following:

- recompute features with `SIFT(...).extract(image)` or `DoGHardNet(...).extract(image)` so the missing fields are present;
- recover scale/orientation from the original detector that produced the descriptors; or
- avoid the pretrained SIFT-family presets and use a custom `features=None` matcher configuration only when appropriate trained weights/configuration are available.

Do not fill `scales` with ones and `oris` with zeros as a silent default for pretrained SIFT-family matching unless the user explicitly accepts the accuracy risk; those fields are part of the learned matcher input.

## SIFT and DoGHardNet `scales`/`oris`

- `SIFT` extracts `scales` from detector keypoint size and `oris` from detector angle converted to radians.
- `DoGHardNet` inherits SIFT detections, then uses `keypoints`, `scales`, and `oris` to form local affine frames for HardNet descriptors.
- The pretrained SIFT and DoGHardNet LightGlue presets set `add_scale_ori=True`; matcher code concatenates normalized `(x,y)` with `scales` and `oris` before positional encoding.
- Shape must be `[B,N]`. Using `[N,1]`, `[B,N,1]`, or degrees instead of radians is a schema bug unless deliberately converted.

## Validation checklist

Before matching, check:

- `keypoints.shape[:2] == descriptors.shape[:2]` for each image.
- `descriptors.shape[-1]` matches the selected preset input dimension.
- `image_size.shape == (B,2)` and order is `(width,height)`.
- SIFT-family presets have `scales.shape == oris.shape == keypoints.shape[:2]`.
- No tensor remains on a different device from the matcher input tensors.
- For batch matching, every key in a single feature dictionary has the same batch size. Single-image matching with `B=1` is simplest and matches `.extract()` behavior.

Use `scripts/inspect_feature_schema.py --image path/to/image --extractor sift` for an offline-safe schema example on a real image.
