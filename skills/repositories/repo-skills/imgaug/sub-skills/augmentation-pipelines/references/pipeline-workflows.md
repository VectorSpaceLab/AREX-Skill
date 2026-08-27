# Image pipeline workflows

## Read this when

You need to build, explain, or debug an imgaug image-only augmentation pipeline.

## Minimal recipe

```python
import numpy as np
import imgaug.augmenters as iaa

images = np.zeros((8, 64, 64, 3), dtype=np.uint8)
seq = iaa.Sequential([
    iaa.Fliplr(0.5),
    iaa.Affine(rotate=(-10, 10)),
    iaa.GaussianBlur(sigma=(0.0, 1.0)),
])
images_aug = seq(images=images)
```

## Verified signatures

- `Sequential(children=None, random_order=False, seed=None, name=None, ...)`
- `SomeOf(n=None, children=None, random_order=False, seed=None, name=None, ...)`
- `OneOf(children, seed=None, name=None, ...)`
- `Sometimes(p=0.5, then_list=None, else_list=None, seed=None, name=None, ...)`
- `WithChannels(channels=None, children=None, seed=None, name=None, ...)`
- `Affine(scale=None, translate_percent=None, translate_px=None, rotate=None, shear=None, order=1, cval=0, mode='constant', fit_output=False, backend='auto', ...)`
- `Resize(size, interpolation='cubic', ...)`
- `Fliplr(p=1, ...)`
- `Add(value=(-20, 20), per_channel=False, ...)`
- `AdditiveGaussianNoise(loc=0, scale=(0, 15), per_channel=False, ...)`
- `GaussianBlur(sigma=(0.0, 3.0), ...)`
- `LinearContrast(alpha=(0.6, 1.4), per_channel=False, ...)`
- `BlendAlpha(factor=(0.0, 1.0), foreground=None, background=None, per_channel=False, ...)`
- `Superpixels(p_replace=(0.5, 1.0), n_segments=(50, 120), max_size=128, interpolation='linear', ...)`

## Common choices

- **Ordered pipeline:** `Sequential([...], random_order=False)`.
- **Random subset:** `SomeOf((1, 3), [...])` when a task says “apply some of these”.
- **Single branch:** `OneOf([...])` when only one family should run.
- **Probability gate:** `Sometimes(0.5, aug)` for 50% inclusion.
- **Selected channels:** `WithChannels([0, 1], children=[...])`.
- **Deterministic reuse:** `seq.to_deterministic()`.

## Output expectations

- Most image pipelines should preserve `(N, H, W, C)` shape unless a size-changing augmenter is intentionally used.
- Most examples assume RGB `uint8` images.
- If the task starts from OpenCV data, convert BGR to RGB before color augmenters.

## Validation checklist

- The output dtype remains compatible with the intended use.
- A deterministic replay gives the same output when that is required.
- The pipeline can be applied to a tiny array without errors.
- When the task also includes annotations, move to the augmentables sub-skill and use one aligned call.
