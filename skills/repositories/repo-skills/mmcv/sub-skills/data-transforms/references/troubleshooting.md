# MMCV Transform Troubleshooting

Use this guide by matching the failing transform, the missing or malformed key, and the expected dict contract.

## Missing Keys

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `KeyError: 'img_path'` in `LoadImageFromFile` | Sample dict does not include an image path. | Ensure the dataset parser creates `img_path`, or bypass `LoadImageFromFile` and provide `img` directly for synthetic tests. |
| `KeyError: 'img'` in `Resize`, `Pad`, `Normalize`, `RandomFlip`, or `ImageToTensor` | Image transforms ran before loading or key mapping hid the image. | Put `LoadImageFromFile` first, or use `KeyMapper(mapping={'img': '<outer-key>'}, auto_remap=True)` around standard transforms. |
| `KeyError` for `ToTensor(keys=['a.b'])` | A dot-separated nested key is missing. | Check every path segment. `ToTensor` intentionally raises rather than silently creating nested dicts. |
| `Compose(...)` returns `None` | A transform returned `None`, commonly `LoadImageFromFile(ignore_empty=True)` or a filtering transform. | Check the transform that can drop samples. If dropping is not intended, set `ignore_empty=False` and fix the path/decode error. |

## Shape and Order Confusion

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Expected `img_shape == (width, height)` but got `(height, width)` | MMCV constructor sizes use width-height while returned image metadata uses NumPy height-width. | Compare `Resize(scale=(w, h))` against `img_shape == (h, w)`. Compare `Pad(size=(w, h))` against padded array shape, usually `(h, w, c)`. |
| Bboxes scale in the wrong direction | Applied `scale_factor` as `(h_scale, w_scale)`. | Use `scale_factor == (w_scale, h_scale)` and multiply boxes by `[w_scale, h_scale, w_scale, h_scale]`. |
| `keep_ratio=True` produces slightly different width/height factors | Output shape is recomputed from resized array dimensions. | Read `results['scale_factor']` after `Resize`; do not recompute from the nominal requested scale. |
| `pad_shape` has three values while expected two | `Pad` stores `img.shape`, which includes channels for color images. | Compare the first two elements for height/width unless channel count is important. |

## Annotation Failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Empty or wrong `gt_bboxes` | `instances` lacks `bbox` entries or boxes are not `[x1, y1, x2, y2]`. | Validate each instance before `LoadAnnotations`; use `np.float32` arrays shaped `(N, 4)` for custom loaders. |
| Labels missing after loading boxes | `with_label=False` or `bbox_label` absent. | Set `LoadAnnotations(with_label=True)` and ensure each instance has `bbox_label`. |
| Segmentation decode error | `with_seg=True` but `seg_map_path` is absent, invalid, or decoded with an incompatible backend. | Provide `seg_map_path`; prefer `backend_args` for non-local storage; keep label maps as single-channel integer images. |
| Segmentation labels become interpolated | Seg map was resized as a normal image by a custom transform. | Use MMCV transforms that resize `gt_seg_map` with nearest-neighbor behavior or implement nearest interpolation in custom transforms. |
| Keypoints have wrong shape | Input keypoints are flat or omit visibility. | Convert to `(N, K, 3)` with `(x, y, visibility)` before geometry transforms. |

## File IO and Backend Arguments

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Deprecation warning for `file_client_args` | MMCV 2.x prefers `backend_args`. | Replace `file_client_args` with `backend_args` when possible. |
| `ValueError` when constructing loader | Both `file_client_args` and `backend_args` were provided. | Use only one. Prefer `backend_args`. |
| Image decode returns `None` | Bad path, unsupported data, or backend cannot decode bytes. | Confirm the path exists and bytes are image data. Try `imdecode_backend='cv2'` or `'pillow'` depending on installed backends. |

## Wrapper Mapping Mistakes

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Outer key is unchanged after wrapped transforms | Used explicit `remapping` that writes to a different output, or forgot `auto_remap=True`. | For simple rename-in/rename-out, use `mapping={'img': 'outer_img'}, auto_remap=True`. |
| Intermediate keys disappear | `KeyMapper` with explicit `remapping` does not retain unmapped intermediate keys. | Add every required output to `remapping`, or set `remapping=None` when you want no output mapping. |
| `ValueError` with `auto_remap=True` and `remapping` | These options are mutually exclusive. | Choose `auto_remap=True` for inverse mapping, or `auto_remap=False` with explicit `remapping`. |
| Broadcast wrapper raises inconsistent sequence length | `TransformBroadcaster` mapped keys contain lists/tuples of different lengths. | Make every mapped sequence the same length or split into separate broadcaster calls. |
| Broadcast shared randomness is not shared | The random transform generates randomness inline instead of in a `@cache_randomness` method. | Refactor the transform to decorate one random-parameter method, or do not use `share_random_params=True`. |
| `avoid_cache_randomness` error under broadcaster | A transform explicitly declares it cannot be safely cached. | Set `share_random_params=False`, replace the transform, or implement a cacheable variant. |

## Tensor Conversion Problems

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `ModuleNotFoundError: torch` | `ToTensor`, `ImageToTensor`, or `to_tensor` requires PyTorch. | Install/use an environment with PyTorch, or postpone tensor conversion to a downstream library that has torch. |
| `TypeError: type <class 'str'> cannot be converted to tensor` | `to_tensor` intentionally rejects strings. | Keep paths/metadata as strings or encode them explicitly outside MMCV tensor conversion. |
| Image tensor has unexpected channel order | `ImageToTensor` transposes `(H, W, C)` to `(C, H, W)` and expands grayscale to one channel. | Check whether later code expects channel-first tensors; do not apply image-array transforms after tensor conversion. |

## Custom Transform Debugging

- Confirm the module defining the custom class is imported before `TRANSFORMS.build()` sees `dict(type='MyTransform')`.
- Preserve standard key names where possible so existing transforms and wrappers compose cleanly.
- Update `img_shape`, `pad_shape`, `scale`, `scale_factor`, `flip`, and `flip_direction` when your transform changes the related image state.
- Return `None` only when sample dropping is intended; otherwise return the dict.
- For random transforms used inside `TransformBroadcaster(share_random_params=True)`, put each random decision in a method decorated with `@cache_randomness` and call that method at most once per sample.

## Lite vs Full MMCV

`mmcv-lite` imports as `mmcv` and covers these transform APIs. Compiled extension failures such as `ModuleNotFoundError: No module named 'mmcv._ext'` belong to the ops/build surface, not transform pipeline composition, unless a downstream project-specific transform imports compiled ops directly.
