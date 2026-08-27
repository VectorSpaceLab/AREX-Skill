# MMCV Transform API Reference

This reference summarizes the transform classes exposed by MMCV 2.2.0 through `mmcv.transforms`. The config entry point is the MMEngine `TRANSFORMS` registry imported from `mmcv.transforms.builder`.

## Base and Registry

| API | Signature | Use |
| --- | --- | --- |
| `BaseTransform` | subclass implements `transform(self, results)` | Base class whose `__call__` forwards to `transform`. Return a dict to continue a pipeline or `None` to stop `Compose`. |
| `TRANSFORMS` | MMEngine registry | Builds config dictionaries such as `dict(type='Resize', scale=(640, 480))`. Custom transforms must be importable and registered with `@TRANSFORMS.register_module()`. |
| `Compose` | `Compose(transforms)` | Sequentially applies callable transforms or config dictionaries. If any transform returns `None`, the composed pipeline returns `None`. |

## Loading

| API | Signature | Reads | Writes and behavior |
| --- | --- | --- | --- |
| `LoadImageFromFile` | `LoadImageFromFile(to_float32=False, color_type='color', imdecode_backend='cv2', file_client_args=None, ignore_empty=False, backend_args=None)` | `img_path` | Loads image bytes with `mmengine.fileio`, decodes with `mmcv.imfrombytes`, writes `img`, `img_shape`, and `ori_shape`. `to_float32=True` casts the image array. `ignore_empty=True` returns `None` on load/decode failures instead of raising. Do not set both deprecated `file_client_args` and `backend_args`. |
| `LoadAnnotations` | `LoadAnnotations(with_bbox=True, with_label=True, with_seg=False, with_keypoints=False, imdecode_backend='cv2', file_client_args=None, backend_args=None)` | `instances` for boxes/labels/keypoints; `seg_map_path` when `with_seg=True` | Writes `gt_bboxes` as `np.float32` shape `(N, 4)`, `gt_bboxes_labels` as `np.int64` shape `(N,)`, `gt_seg_map` as decoded `np.uint8` image, and `gt_keypoints` as `np.float32` shape `(N, K, 3)`. Empty instances become zero-row arrays. |

## Processing and Augmentation

| API | Signature | Primary effects |
| --- | --- | --- |
| `Resize` | `Resize(scale=None, scale_factor=None, keep_ratio=False, clip_object_border=True, backend='cv2', interpolation='bilinear')` | Requires either `scale` or `scale_factor`. Updates `img`, `img_shape`, optional `gt_bboxes`, `gt_seg_map`, `gt_keypoints`, and writes `scale`, `scale_factor`, `keep_ratio`. With `scale`, width-height order is used for the requested target; `img_shape` is height-width. |
| `RandomResize` | `RandomResize(scale, ratio_range=None, resize_type='Resize', **resize_kwargs)` | Samples a target scale, builds the configured resize transform, and then applies the same `Resize` contract. Random scale sampling is decorated with `cache_randomness`. |
| `RandomChoiceResize` | `RandomChoiceResize(scales, resize_type='Resize', **resize_kwargs)` | Uniformly selects one candidate scale, applies the configured resize transform, and adds `scale_idx`. Selection is decorated with `cache_randomness`. |
| `Pad` | `Pad(size=None, size_divisor=None, pad_to_square=False, pad_val={'img': 0, 'seg': 255}, padding_mode='constant')` | Pads `img` and optional `gt_seg_map`, updates `img_shape`, and writes `pad_shape`, `pad_fixed_size`, and `pad_size_divisor`. Exactly one fixed-size/divisor mode is active unless `pad_to_square=True`. `size` is width-height; `pad_shape` is height-width plus channels when present. |
| `Normalize` | `Normalize(mean, std, to_rgb=True)` | Requires `img`, replaces it with normalized values through MMCV image helpers, and writes `img_norm_cfg` with mean/std/to-rgb arrays. If `to_rgb=True`, means/stds are expected in RGB order even though many decoded images are BGR. |
| `RandomFlip` | `RandomFlip(prob=None, direction='horizontal', swap_seg_labels=None)` | Requires `img`; optional boxes, segmentation map, and keypoints are flipped consistently. Writes `flip` and `flip_direction`; writes `swap_seg_labels` when segmentation labels are swapped. `prob` must be a float or list of floats summing to at most 1, and directions are `horizontal`, `vertical`, or `diagonal`. |
| `CenterCrop` | `CenterCrop(crop_size, auto_pad=False, pad_cfg=dict(type='Pad'), clip_object_border=True)` | Crops `img`, optional boxes, segmentation map, and keypoints around the center. Updates `img_shape` and `pad_shape`; `auto_pad=True` pads images smaller than `crop_size` before cropping. `crop_size` follows width-height order; verify output metadata as height-width. |
| `RandomGrayscale` | `RandomGrayscale(prob=0.1)` | Randomly converts the image to grayscale while preserving a 3-channel-style image output when needed. The random decision is decorated with `cache_randomness`. |
| `MultiScaleFlipAug` | `MultiScaleFlipAug(transforms, scales=None, scale_factor=None, allow_flip=False, flip_direction='horizontal', resize_cfg=dict(type='Resize', keep_ratio=True), flip_cfg=dict(type='RandomFlip'))` | Test-time augmentation helper. For each scale and optional flip direction, applies resize/flip then the packed `transforms`, returning lists under `inputs` and `data_sample`. Use only when the downstream packer writes those keys. |

## Formatting

| API | Signature | Behavior |
| --- | --- | --- |
| `to_tensor` | `to_tensor(data)` | Converts `torch.Tensor`, `np.ndarray`, non-string sequences, `int`, and `float` to PyTorch tensors. Raises `TypeError` for unsupported data such as strings. Requires PyTorch. |
| `ToTensor` | `ToTensor(keys)` | Converts each key to a tensor. Dot-separated nested keys such as `instances.bbox` are supported. Missing nested keys raise `KeyError`. Requires PyTorch. |
| `ImageToTensor` | `ImageToTensor(keys)` | Converts image arrays from `(H, W, C)` to contiguous tensor `(C, H, W)`; 2D images become `(1, H, W)`. Requires PyTorch. |

## Wrappers

| API | Signature | Behavior |
| --- | --- | --- |
| `KeyMapper` | `KeyMapper(transforms=None, mapping=None, remapping=None, auto_remap=None, allow_nonexist_keys=False)` | Maps outer dict keys into standard inner keys for wrapped transforms, then remaps outputs. `auto_remap=True` uses the inverse mapping and cannot be combined with explicit `remapping`. `...` marks a key ignored. `allow_nonexist_keys=True` allows missing mapped inputs by using an internal ignore marker. |
| `TransformBroadcaster` | `TransformBroadcaster(transforms, mapping=None, remapping=None, auto_remap=None, allow_nonexist_keys=False, share_random_params=False)` | Applies wrapped transforms to several mapped targets or elements of a sequence. All broadcast sequences must have consistent length. `share_random_params=True` uses cached random methods so all targets receive the same random choices. |
| `RandomChoice` | `RandomChoice(transforms, prob=None)` | Chooses one candidate sub-pipeline. `prob`, when set, must match the number of candidates and sum to 1. Pipeline selection is decorated with `cache_randomness`. |
| `RandomApply` | `RandomApply(transforms, prob=0.5)` | Applies the wrapped transform or sub-pipeline with probability `prob`. The random decision is decorated with `cache_randomness`. |
| `cache_randomness` | `@cache_randomness` on an instance method | Marks a method returning random parameters as cacheable under `cache_random_params`, enabling wrappers such as `TransformBroadcaster(share_random_params=True)` to reuse one decision. The method must be an instance method whose first argument is `self`. |
| `avoid_cache_randomness` | `@avoid_cache_randomness` on a `BaseTransform` subclass | Marks transforms that must not be used with cached randomness. It rejects classes that also define `@cache_randomness` methods and raises when such transforms are run under cache mode. The marker is not inherited by subclasses. |

## Version and Lite Notes

- This skill targets MMCV version 2.2.0 behavior.
- The lite install imports as `mmcv` but does not include compiled `mmcv._ext` ops; transform APIs documented here are pure-Python/Numpy/MMEngine-style surfaces unless a downstream image helper needs an optional backend.
- No console entry points are needed for transform pipelines; use Python imports, config dictionaries, or the bundled checker script.
