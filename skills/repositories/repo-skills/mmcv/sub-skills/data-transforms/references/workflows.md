# MMCV Transform Workflows

These recipes are self-contained patterns for composing MMCV 2.2.0 transform pipelines. They use `mmcv.transforms` and the MMEngine registry, not repository-local test files.

## Build a Minimal Image Pipeline

```python
from mmcv.transforms import Compose

pipeline = Compose([
    dict(type='LoadImageFromFile'),
    dict(type='Resize', scale=(64, 48), keep_ratio=False),
    dict(type='Pad', size=(80, 64), pad_val=dict(img=0, seg=255)),
    dict(type='Normalize', mean=[0, 0, 0], std=[1, 1, 1], to_rgb=False),
])

result = pipeline({'img_path': 'sample.jpg'})
assert result['img_shape'] == (64, 80)  # height-width after Pad
assert result['ori_shape'] == (original_h, original_w)
```

Use this for standalone checks when no downstream project-specific packer is involved. If `LoadImageFromFile(ignore_empty=True)` returns `None`, `Compose` returns `None` and later transforms do not run.

## Add Annotations

```python
pipeline = Compose([
    dict(type='LoadImageFromFile'),
    dict(type='LoadAnnotations', with_bbox=True, with_label=True, with_seg=True),
    dict(type='Resize', scale=(640, 480), keep_ratio=False),
    dict(type='RandomFlip', prob=0.5, direction='horizontal'),
    dict(type='Pad', size_divisor=32),
])

sample = {
    'img_path': 'image.jpg',
    'instances': [
        {'bbox': [10, 12, 40, 50], 'bbox_label': 1},
    ],
    'seg_map_path': 'seg.png',
}
```

Checklist:

- `gt_bboxes` must be `(N, 4)` in x/y order before geometry transforms.
- `gt_seg_map` should be height-width and use integer labels.
- `Resize(scale=(w, h))` stores `img_shape=(h, w)` after resizing.
- `Pad(size=(w, h))` stores `pad_shape` from the actual image array.

## Register a Custom Transform

```python
import mmcv
from mmcv.transforms import BaseTransform, TRANSFORMS

@TRANSFORMS.register_module()
class MyFlip(BaseTransform):
    def __init__(self, direction='horizontal'):
        self.direction = direction

    def transform(self, results):
        results['img'] = mmcv.imflip(results['img'], direction=self.direction)
        results['img_shape'] = results['img'].shape[:2]
        return results
```

Then use it from config after the module defining `MyFlip` has been imported:

```python
pipeline = [
    dict(type='LoadImageFromFile'),
    dict(type='MyFlip', direction='vertical'),
]
```

Rules for custom transforms:

- Inherit `BaseTransform` and implement `transform(self, results)`.
- Return the mutated dict; return `None` only when intentionally dropping a sample.
- Read and write standard keys when possible (`img`, `img_shape`, `gt_bboxes`, `gt_seg_map`, `gt_keypoints`) so wrappers and downstream packers can compose with it.
- Update metadata whenever changing image shape or geometric alignment.

## Use Cached Randomness in Custom Transforms

```python
import random
import mmcv
from mmcv.transforms import BaseTransform, TRANSFORMS
from mmcv.transforms.utils import cache_randomness

@TRANSFORMS.register_module()
class MyRandomFlip(BaseTransform):
    def __init__(self, prob=0.5, direction='horizontal'):
        self.prob = prob
        self.direction = direction

    @cache_randomness
    def should_flip(self):
        return random.random() < self.prob

    def transform(self, results):
        if self.should_flip():
            results['img'] = mmcv.imflip(results['img'], self.direction)
            results['flip'] = True
            results['flip_direction'] = self.direction
        else:
            results['flip'] = False
            results['flip_direction'] = None
        return results
```

Use `@cache_randomness` when the same random choice must be shared by `TransformBroadcaster(share_random_params=True)`. If a random transform cannot expose its randomness through a decorated method, decorate the class with `@avoid_cache_randomness` so shared-random wrappers fail clearly.

## Remap Nonstandard Keys with KeyMapper

```python
from mmcv.transforms import Compose

pipeline = Compose([
    dict(
        type='KeyMapper',
        mapping={'img': 'gt_img'},
        auto_remap=True,
        transforms=[
            dict(type='Resize', scale=(128, 128), keep_ratio=False),
            dict(type='RandomFlip', prob=1.0, direction='horizontal'),
        ],
    ),
])

result = pipeline({'gt_img': image_array})
assert 'gt_img' in result
```

Use explicit `remapping` when the inner transform creates keys whose output names differ from the input mapping. Be careful: with explicit remapping, unmapped intermediate keys are not retained in wrapper output.

## Allow or Reject Missing Wrapper Inputs Deliberately

```python
strict = dict(
    type='KeyMapper',
    mapping={'img': 'optional_img'},
    allow_nonexist_keys=False,
    auto_remap=True,
    transforms=[dict(type='Normalize', mean=[0, 0, 0], std=[1, 1, 1])],
)

lenient = dict(
    type='KeyMapper',
    mapping={'img': 'optional_img'},
    allow_nonexist_keys=True,
    auto_remap=False,
    transforms=[],
)
```

Prefer strict behavior for required image fields. Use lenient mapping only for wrappers that tolerate missing inputs or for transforms that create replacement outputs independently.

## Broadcast One Transform to Multiple Images

```python
pipeline = Compose([
    dict(
        type='TransformBroadcaster',
        mapping={'img': ['lq', 'gt']},
        auto_remap=True,
        share_random_params=True,
        transforms=[
            dict(type='RandomFlip', prob=0.5, direction='horizontal'),
        ],
    ),
])
```

`share_random_params=True` ensures cacheable random decisions are identical for all broadcast targets. All mapped lists must have the same length. Use `...` in mapping for metadata keys that should be visible for one target but ignored for another.

## Random Policy Wrappers

```python
pipeline = Compose([
    dict(
        type='RandomChoice',
        transforms=[
            [dict(type='Resize', scale=(320, 240), keep_ratio=True)],
            [dict(type='Resize', scale=(640, 480), keep_ratio=True)],
        ],
        prob=[0.4, 0.6],
    ),
    dict(type='RandomApply', transforms=[dict(type='RandomGrayscale', prob=1.0)], prob=0.2),
])
```

`RandomChoice` probabilities must match the number of candidate sub-pipelines and sum to 1. `RandomApply` wraps one transform or sub-pipeline and applies it with the given probability.

## Test-Time Augmentation

```python
pipeline = Compose([
    dict(
        type='MultiScaleFlipAug',
        scales=[(640, 480), (800, 600)],
        allow_flip=True,
        flip_direction=['horizontal', 'vertical'],
        transforms=[
            dict(type='Normalize', mean=[0, 0, 0], std=[1, 1, 1], to_rgb=False),
            # Add the downstream project packer that writes inputs/data_sample.
        ],
    ),
])
```

Use `MultiScaleFlipAug` only when the inner `transforms` end with a packer that returns `inputs` and `data_sample`. Generic MMCV does not provide every project-specific packing transform; downstream OpenMMLab libraries often add those packers to the same registry.

## Tiny Pipeline Smoke Check

Run the bundled helper to verify installed imports, a generated fixture image, shape metadata, optional torch tensor conversion, and error reporting:

```bash
python scripts/transform_pipeline_check.py --help
python scripts/transform_pipeline_check.py --width 5 --height 4 --resize-width 8 --resize-height 6 --pad-width 10 --pad-height 8
```

If you use the script outside this skill tree, the path can be copied; it does not rely on source repository files.
