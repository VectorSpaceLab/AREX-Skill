# Reproducibility and replay

Albumentations has two different reproducibility tools:

- `seed` / `set_random_seed` reproduces a sequence of random draws for equivalent pipeline instances.
- `A.ReplayCompose` records the exact transforms and parameters sampled for one call so they can be reapplied later.

Use the first for repeatable experiments and tests. Use the second when the exact same random crop, flip, or color parameters must be applied to another compatible sample.

## Deterministic seeds

`A.Compose(..., seed=137)` stores an internal random state independent of global `numpy.random.seed()` and `random.seed()`. Two `Compose` instances with the same transform graph and same seed produce the same sequence of outputs. Repeated calls on one instance still advance that instance's internal random state.

```python
import albumentations as A

first = A.Compose([A.RandomCrop(16, 16), A.HorizontalFlip(p=0.5)], seed=137)
second = A.Compose([A.RandomCrop(16, 16), A.HorizontalFlip(p=0.5)], seed=137)
```

To restart the sequence after constructing or loading a pipeline, call:

```python
pipeline.set_random_seed(137)
```

The seed is propagated to child transforms. In worker contexts with PyTorch available, `Compose` adjusts its effective seed using the worker's torch seed so workers are not all identical. For dataset-specific seeding decisions, route to `../framework-integration/`.

## Save and load reproducibility

Serialization preserves config and, for `Compose`, includes the base `seed` value. It does not preserve "the next random number" after previous calls. For equality checks, reset both objects to the same seed before applying them.

```python
serialized = A.to_dict(pipeline)
loaded = A.from_dict(serialized)

pipeline.set_random_seed(137)
loaded.set_random_seed(137)
```

If the pipeline contains bboxes, keypoints, masks, volumes, or additional targets, validate the loaded pipeline on the same target set and schema. Route target-format repair to `../targets-and-formats/`.

## Replay exact parameters

`A.ReplayCompose(transforms, bbox_params=None, keypoint_params=None, additional_targets=None, p=1.0, is_check_shapes=True, save_key="replay")` behaves like `Compose` but inserts a replay dictionary in the output under `save_key`.

```python
import numpy as np
import albumentations as A

image = np.arange(32 * 32 * 3, dtype=np.uint8).reshape(32, 32, 3)
other = image.copy()

replayer = A.ReplayCompose([
    A.RandomCrop(16, 16, p=1.0),
    A.HorizontalFlip(p=0.5),
])
recorded = replayer(image=image)
replayed = A.ReplayCompose.replay(recorded["replay"], image=other)
```

The replay dictionary contains transform config plus per-transform `params` and `applied` flags. Nested compose-style transforms are restored recursively.

## Replay constraints

Replay is exact only when the new data is compatible with the recorded parameters:

- Keep target keys compatible with the original call: if replay was recorded with `image` and `mask`, replay with corresponding target keys when expecting geometry to match.
- Keep shapes compatible with sampled parameters. A crop recorded for a 32x32 image may be invalid or semantically wrong on a differently sized image.
- Keep bbox/keypoint params and label fields consistent with the original pipeline.
- Do not edit the replay dictionary unless you understand the serialized transform schema, `applied` flags, and `params` structure.

When replaying after a shape change, first reproduce on the original shape. If the original-shape replay matches but the resized/new-shape replay fails, record a new replay after the shape-changing step or move deterministic preprocessing before `ReplayCompose`.

## Inspect applied params without replay

For debugging a normal pipeline, create the top-level compose with `save_applied_params=True`:

```python
pipeline = A.Compose(
    [A.RandomCrop(16, 16), A.HorizontalFlip(p=0.5)],
    save_applied_params=True,
)
result = pipeline(image=image)
print(result["applied_transforms"])
```

`result["applied_transforms"]` is a list of `(transform_class_name, params_copy)` for transforms that have sampled params. It is initialized only on the top-level compose. Use it to inspect what happened in one call; use `ReplayCompose` when those parameters must be reapplied.

## Practical validation checklist

- Confirm `A.to_dict(pipeline)["transform"]` contains expected `transforms`, `bbox_params`, `keypoint_params`, `additional_targets`, `is_check_shapes`, and `seed` fields.
- Round-trip through the chosen persistence format: `A.save` then `A.load` for JSON or YAML.
- Reset both original and loaded pipelines with the same `set_random_seed(seed)` before output comparison.
- For `ReplayCompose`, assert `"replay" in result` or your custom `save_key` is present before calling `ReplayCompose.replay`.
- Compare arrays with `np.testing.assert_array_equal` for exact uint8 workflows; choose tolerance-aware checks only when transforms legitimately introduce floating-point differences.
