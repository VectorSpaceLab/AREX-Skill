---
name: parameters-random-and-utilities
description: "Use when controlling imgaug stochastic parameters, seeds,
  deterministic replay, dtype conversion, sample data, grids, or utility
  helpers."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Parameters, Randomness, and Utilities

Use this sub-skill when the task is about **how imgaug samples augmentation parameters**, controls reproducibility, handles dtype/range conversion, loads built-in example data, or uses utility functions such as resizing, grids, and display helpers.

## What this sub-skill covers

- Parameter shortcuts: scalar values, `(a, b)` tuples, lists, and `imgaug.parameters.StochasticParameter` objects.
- Distribution objects such as `Choice`, `Uniform`, `Normal`, and `Clip`.
- Seeds, `RNG`, deterministic replay, and deprecated `random_state`/`deterministic` API warnings.
- Dtype conversion, clipping, range checks, and compatibility with current NumPy.
- Sample quokka images and annotations from `imgaug.data`.
- Utility helpers: resize, draw grids, and headless-safe visualization alternatives.

## What it does not cover

- Building high-level image pipelines belongs to [`../augmentation-pipelines/SKILL.md`](../augmentation-pipelines/SKILL.md).
- Constructing keypoints, boxes, dense maps, and mixed batches belongs to [`../augmentables-and-batches/SKILL.md`](../augmentables-and-batches/SKILL.md).
- Background/multicore execution belongs to [`../multicore-and-diagnostics/SKILL.md`](../multicore-and-diagnostics/SKILL.md).

## Typical triggers

- “How do tuple parameters work in imgaug?”
- “Make this imgaug pipeline reproducible.”
- “Why does imgaug warn about `random_state`?”
- “Use the built-in quokka image as a tiny fixture.”
- “Fix dtype clipping or NumPy import errors.”

## Fast path

1. Read [`references/parameters-and-rng.md`](references/parameters-and-rng.md) for stochastic parameters and reproducibility.
2. Read [`references/data-and-dtype-utilities.md`](references/data-and-dtype-utilities.md) for dtype helpers, resizing, grids, and sample data.
3. Run [`scripts/smoke_parameters_and_data.py`](scripts/smoke_parameters_and_data.py) to verify parameter sampling, quokka data, and dtype conversion.
4. Read [`references/troubleshooting.md`](references/troubleshooting.md) for NumPy 2, deprecations, dtype range, and display failures.

## Core parameter pattern

Many augmenter parameters accept flexible forms:

```python
import imgaug.augmenters as iaa
import imgaug.parameters as iap

# Shortcut for a uniform blur range.
blur = iaa.GaussianBlur(sigma=(0.0, 3.0))

# Explicit stochastic distribution clipped to a safe range.
param = iap.Clip(iap.Normal(1.0, 0.1), 0.1, 3.0)
blur2 = iaa.GaussianBlur(sigma=param)
```

## Reproducibility pattern

Use a `seed` on an augmenter or convert a pipeline to deterministic form when the same sampled transform must be replayed.

```python
seq = iaa.Sequential([iaa.Fliplr(0.5), iaa.Add((0, 5))], seed=1)
det = seq.to_deterministic()
out_a = det(images=images)
out_b = det(images=images)
```

For aligned images and annotations, a single call containing every augmentable remains the safest pattern.

## Utility warning signs

- `AttributeError` involving `np.sctypes`: install `numpy<2` for imgaug 0.4.0.
- Unexpected clipping or rounding: inspect dtype helpers and value ranges before conversion.
- Display failure on a server: avoid `ia.imshow`; write grids to image files instead.
- Deprecation warnings around `random_state` or `deterministic`: prefer `seed`, `RNG`, and `to_deterministic()` patterns.
