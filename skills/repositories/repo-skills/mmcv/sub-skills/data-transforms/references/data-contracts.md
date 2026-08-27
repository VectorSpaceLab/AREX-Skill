# MMCV Transform Data Contracts

MMCV transforms pass a mutable Python `dict` through a pipeline. Each transform reads named keys, may update existing keys, and may add metadata. Future agents should debug by comparing the incoming dict to the contract of the next transform.

## Common Keys

| Key | Typical type and shape | Producer | Consumer and notes |
| --- | --- | --- | --- |
| `img_path` | `str` path or URI understood by MMEngine file IO | Dataset/sample parser | Required by `LoadImageFromFile`. |
| `img` | `np.ndarray`, usually `(H, W, C)` or `(H, W)` | `LoadImageFromFile`, dataset, or custom loader | Required by most processing transforms. Updated in place by resize, crop, pad, normalize, flip, grayscale, and tensor conversion. |
| `ori_shape` | tuple `(height, width)` | `LoadImageFromFile` | Original decoded image shape before later transforms. Do not compare to width-height constructor arguments directly. |
| `img_shape` | tuple `(height, width)` after processing | `LoadImageFromFile`, `Resize`, crop, `Pad` | Current image shape metadata. Used by geometry transforms for clipping and flipping. |
| `pad_shape` | padded image shape, commonly `(height, width, channels)` or `(height, width)` | `Pad` | Shape after padding. It may include channels because it is derived from `img.shape`. |
| `scale` | target scale tuple `(width, height)` or sampled scalar/tuple | `Resize`, `RandomResize`, `RandomChoiceResize`, `MultiScaleFlipAug` | Used by resize internals and stored for downstream metadata. Constructor and `scale` values follow width-height conventions. |
| `scale_factor` | tuple `(w_scale, h_scale)` | `Resize` and random resize variants | Used to update boxes and keypoints. For `keep_ratio=True`, width and height factors can differ slightly because they are recomputed from output shape. |
| `keep_ratio` | `bool` | Resize transforms | Records whether aspect ratio-preserving resizing was used. |
| `flip` | `bool` | `RandomFlip`, `MultiScaleFlipAug` | Indicates whether a flip was applied. Some packers expect it as metadata. |
| `flip_direction` | `str` or `None` | `RandomFlip`, `MultiScaleFlipAug` | One of `horizontal`, `vertical`, `diagonal`, or `None`. |
| `img_norm_cfg` | `dict(mean, std, to_rgb)` | `Normalize` | Records normalization settings. |

## Annotation Keys

| Key | Typical type and shape | Producer | Consumer and notes |
| --- | --- | --- | --- |
| `instances` | list of dicts with `bbox`, `bbox_label`, optional `keypoints` | Dataset/sample parser | Required by `LoadAnnotations` when bbox, label, or keypoint loading is enabled. |
| `seg_map_path` | `str` path or URI | Dataset/sample parser | Required by `LoadAnnotations(with_seg=True)`. |
| `gt_bboxes` | `np.float32` array `(N, 4)` in `x1, y1, x2, y2` order | `LoadAnnotations` or custom loader | Optional input to `Resize`, `RandomResize`, `RandomChoiceResize`, `RandomFlip`, `CenterCrop`, and sometimes `Pad`. X coordinates scale/clip against width; Y coordinates scale/clip against height. |
| `gt_bboxes_labels` | `np.int64` array `(N,)` | `LoadAnnotations(with_label=True)` | Class labels paired with `gt_bboxes`; many generic MMCV transforms preserve it but do not interpret it. |
| `gt_seg_map` | `np.uint8` or label array `(H, W)` | `LoadAnnotations(with_seg=True)` or custom loader | Resized with nearest-neighbor semantics, padded with `pad_val['seg']`, and flipped with optional label swapping. Must remain aligned with `img`. |
| `gt_keypoints` | `np.float32` array `(N, K, 3)` with `(x, y, visibility)` | `LoadAnnotations(with_keypoints=True)` or custom loader | Resized by multiplying `(x, y)` by `(w_scale, h_scale)` and flipped against image width/height while preserving visibility metadata. |

## Shape and Order Rules

- Constructor sizes and transform config scales such as `Resize(scale=(640, 480))`, `RandomResize(scale=(...))`, `RandomChoiceResize(scales=[...])`, and `Pad(size=(640, 480))` use width-height order where MMCV image helpers expect `(w, h)`.
- Returned image metadata such as `ori_shape`, `img_shape`, and `pad_shape` comes from NumPy image arrays and therefore uses height-width order, often `(h, w)` or `(h, w, c)`.
- `scale_factor` is `(w_scale, h_scale)`, not `(h_scale, w_scale)`.
- Bounding boxes are `[x1, y1, x2, y2]`; x fields use width and y fields use height.
- Keypoints use `(x, y, visibility)`; only x/y coordinates are scaled or flipped.
- Segmentation maps follow image height-width layout but usually lack a channel dimension.

## Required-Key Sequencing

A robust image pipeline usually starts with:

1. A dataset/sample parser that creates at least `img_path` and, if annotations are needed, `instances` and/or `seg_map_path`.
2. `LoadImageFromFile` to create `img`, `img_shape`, and `ori_shape`.
3. `LoadAnnotations` when boxes, labels, segmentation, or keypoints are needed.
4. Processing transforms such as resize, flip, crop, pad, normalize.
5. Formatting transforms such as `ToTensor` or `ImageToTensor`, or a downstream project-specific packer.

Do not place `Resize`, `Pad`, `Normalize`, `RandomFlip`, `ImageToTensor`, or custom image transforms before `img` exists. Do not place annotation-processing transforms before annotation keys exist.

## Loading Contracts

- `LoadImageFromFile` reads `img_path`; missing `img_path` raises `KeyError` before any file IO.
- `LoadImageFromFile(ignore_empty=False)` raises for bad paths or failed decoding. With `ignore_empty=True`, it returns `None`; `Compose` then stops and returns `None`.
- `LoadAnnotations(with_bbox=True)` expects `instances` to be iterable dicts. Each bbox instance should have `bbox`; labels require `bbox_label`; keypoints require `keypoints`.
- `LoadAnnotations(with_seg=True)` expects `seg_map_path` and decodes the segmentation image through MMEngine file IO plus `mmcv.imfrombytes`.
- Prefer `backend_args` over deprecated `file_client_args`. Setting both is invalid.

## Tensor Conversion Assumptions

- `to_tensor`, `ToTensor`, and `ImageToTensor` require PyTorch to be importable.
- `ToTensor(keys)` preserves the semantic shape of numpy arrays and converts nested dot keys like `instances.bbox`; it raises `KeyError` if any path segment is missing.
- `ImageToTensor(keys)` assumes image layout `(H, W, C)`, transposes to `(C, H, W)`, and adds a channel dimension for 2D arrays.
- Do not normalize or resize after `ImageToTensor` unless the later transform explicitly accepts torch tensors; MMCV image processing transforms generally expect NumPy arrays.

## Wrapper Contracts

- `KeyMapper(mapping={'img': 'gt_img'}, auto_remap=True, transforms=[...])` lets inner transforms read/write standard key `img` while preserving the outer key `gt_img`.
- `KeyMapper(..., allow_nonexist_keys=False)` does not fail immediately for every missing key because mapping uses `dict.get`, but downstream transforms can fail when required inner keys are absent. Set `allow_nonexist_keys=True` only when missing keys are deliberate and wrapped transforms tolerate their absence.
- `KeyMapper(..., remapping=...)` with `auto_remap=False` drops unmapped intermediate outputs during output mapping; include every output you need in `remapping`.
- `TransformBroadcaster` scatters mapped lists or tuples; all mapped sequences must have equal length and at least one target.
- `TransformBroadcaster(share_random_params=True)` only shares random decisions for methods decorated with `@cache_randomness`. A transform that generates randomness inline in `transform()` must either be rewritten to expose cacheable methods or marked with `@avoid_cache_randomness` to prevent misuse.
