# MONAI Data and Transform Workflows

## Dictionary Transform Pipeline

Use dictionary transforms for segmentation-style examples because they keep image, label, paths, metadata, and auxiliary fields synchronized by key.

```python
from monai.transforms import (
    Compose,
    EnsureChannelFirstd,
    EnsureTyped,
    LoadImaged,
    NormalizeIntensityd,
    RandCropByPosNegLabeld,
    ScaleIntensityRanged,
    Spacingd,
)

keys = ("image", "label")
train_transforms = Compose(
    [
        LoadImaged(keys=keys, image_only=False),
        EnsureChannelFirstd(keys=keys, channel_dim="no_channel"),
        Spacingd(keys=keys, pixdim=(1.5, 1.5, 2.0), mode=("bilinear", "nearest")),
        ScaleIntensityRanged(keys="image", a_min=-175, a_max=250, b_min=0.0, b_max=1.0, clip=True),
        RandCropByPosNegLabeld(
            keys=keys,
            label_key="label",
            spatial_size=(96, 96, 96),
            pos=1,
            neg=1,
            num_samples=4,
            image_key="image",
            image_threshold=0,
            allow_smaller=True,
        ),
        EnsureTyped(keys=keys, track_meta=True),
    ],
    map_items=True,
)
```

Workflow notes:

- Use `keys=("image", "label")` consistently for spatial transforms so image and label receive matching crops, flips, orientation, and spacing changes.
- Use interpolation modes by key: continuous images usually use `"bilinear"` or `"trilinear"`; labels usually use `"nearest"` to preserve class ids.
- `RandCropByPosNegLabeld` returns a list of samples; keep `Compose(map_items=True)` so later transforms apply to each crop.
- Place `EnsureTyped(track_meta=True)` after loading/spatial transforms when downstream code needs `MetaTensor` metadata and inverse traces.
- For optional keys such as masks, weights, or unlabeled validation labels, either split transforms by stage or set `allow_missing_keys=True` only where missing keys are legitimate.

## Datalist and Dataset Creation

MONAI's Decathlon-style datalist loader accepts JSON with `training`, `validation`, or `test` entries. Training entries are usually dictionaries with at least `image` and `label`; test entries may be bare image paths and are normalized into `{"image": path}` dictionaries.

```python
from monai.data import CacheDataset, DataLoader, Dataset, load_decathlon_datalist

train_files = load_decathlon_datalist("dataset.json", is_segmentation=True, data_list_key="training", base_dir="data")
val_files = load_decathlon_datalist("dataset.json", is_segmentation=True, data_list_key="validation", base_dir="data")

train_ds = CacheDataset(train_files, transform=train_transforms, cache_rate=1.0, num_workers=4, progress=True)
val_ds = Dataset(val_files, transform=val_transforms)
train_loader = DataLoader(train_ds, batch_size=2, shuffle=True, num_workers=4)
```

Checklist:

- Confirm every item has the keys consumed by the first transform; print `train_files[0].keys()` before building the dataset.
- Use `base_dir` to resolve relative paths in a datalist; avoid hard-coding absolute machine paths in reusable examples.
- Use plain `Dataset` for small data, debugging, heavy random transforms, or when caching is not worth memory/disk cost.
- Use `DataLoader` from `monai.data`, not raw `torch.utils.data.DataLoader`, unless you intentionally override collation and random-state handling.

## Choosing a Cache Dataset

| Class | Use when | Important notes |
| --- | --- | --- |
| `Dataset` | You need direct, uncached transform execution. | Easiest for debugging and dynamic transforms. |
| `CacheDataset` | Deterministic preprocessing fits in RAM. | Caches results before the first random transform in a `Compose`; tune `cache_rate`, `cache_num`, `copy_cache`, and `runtime_cache`. |
| `PersistentDataset` | Deterministic preprocessing should persist across runs. | Stores cache files under `cache_dir`; clear cache after transform or data changes if hash behavior is uncertain. |
| `SmartCacheDataset` | Large datasets need a rolling in-memory subset. | Requires lifecycle management in long runs; use when full RAM cache is impossible. |
| `CacheNTransDataset` | You intentionally want to cache a fixed number of leading transforms. | Useful for advanced pipelines where the first random boundary is not the desired cache boundary. |

Cache design pattern:

1. Put file IO, orientation, spacing, foreground crop, and deterministic intensity transforms before random augmentations.
2. Put `Rand*` crop/flip/noise/deformation transforms after deterministic work so they remain fresh each epoch.
3. For `PersistentDataset`, choose a project cache directory outside any publishable skill/runtime content and clear it when debugging stale results.
4. If metadata or inverse behavior matters, preserve `MetaTensor` and verify `applied_operations` after cached loading.

## Metadata and `MetaTensor`

`LoadImaged(image_only=False)` and typed transforms can produce `MetaTensor` values with affine, space, source metadata, and `applied_operations` traces. MONAI tensor operations generally propagate metadata from the first `MetaTensor` argument.

Practical inspection:

```python
sample = train_ds[0]
image = sample["image"]
print(type(image), tuple(image.shape))
print(image.affine)
print(image.meta.keys())
print(len(image.applied_operations))
```

Batch handling:

- A batch of `MetaTensor` values may carry batched metadata; call `decollate_batch(batch)` before per-case inverse transforms or per-case metric/postprocessing workflows.
- Slicing the first dimension of a batch returns matching per-item metadata; slicing other dimensions can preserve batched metadata.
- If a model or export path rejects `MetaTensor`, convert only at that boundary with `.as_tensor()` and keep preprocessing metadata in the data path.

## Lazy Resampling Workflow

Lazy resampling fuses compatible spatial operations and applies fewer interpolations. It is useful for pipelines with multiple lazy-capable spatial transforms such as spacing, orientation, flip, crop, rotate, and zoom.

```python
lazy_transforms = Compose(
    [
        Spacingd(keys=("image", "label"), pixdim=(1.5, 1.5, 2.0), mode=("bilinear", "nearest"), lazy=True),
        RandCropByPosNegLabeld(keys=("image", "label"), label_key="label", spatial_size=(96, 96, 96), lazy=True),
        EnsureTyped(keys=("image", "label"), track_meta=True),
    ],
    lazy=None,
    log_stats="monai.transforms",
)
```

Operational guidance:

- `Compose(lazy=False)` applies transforms immediately; this is the safest baseline.
- `Compose(lazy=True)` asks all lazy-capable transforms to accumulate pending operations.
- `Compose(lazy=None)` respects each transform's own `lazy` flag.
- Non-lazy transforms or explicit `ApplyPendingd` force pending operations to materialize.
- Some transforms require current data values, including foreground/label-based crops; they may force pending operations before computing their decision.
- Use `log_stats=True` or a logger name when diagnosing whether operations are accumulating or being applied.

## Inverse Transform Workflow

Use inverse transforms when predictions or augmented outputs must be returned to the original image space.

1. Keep `MetaTensor` tracking enabled and preserve `applied_operations` through loading, spatial transforms, and collation.
2. Apply invertible preprocessing with the same transform object or `Compose` instance used for forward processing.
3. Decollate batches before per-item inverse operations.
4. Invert spatial transforms on predictions after model inference and before saving or comparison in source image space.
5. Verify image and label traces stay synchronized when random transforms are applied to both keys.

Minimal pattern:

```python
from monai.data import decollate_batch

for batch in loader:
    cases = decollate_batch(batch)
    restored_cases = [train_transforms.inverse(case) for case in cases]
```

If inversion fails, inspect whether metadata was stripped, batching was not decollated, a non-invertible transform changed the needed key, pending lazy transforms were not applied, or a different transform instance is being used for inverse.

## Validation Steps Before Training

Run these checks before routing data into a trainer, bundle, or Auto3DSeg workflow:

- `first_item = dataset[0]`: assert `"image"` and expected label keys exist.
- Assert shape is channel-first: `len(image.shape) == spatial_dims + 1` for a single item, and batch shape adds one leading dimension.
- Assert label dtype and interpolation are compatible with class ids after spatial transforms.
- Assert `isinstance(image, MetaTensor)` if inverse, affine, lazy, or writer metadata is required.
- Iterate one `DataLoader` batch with the planned `batch_size`, `num_workers`, and `collate_fn`.
- If a transform returns multiple crops, confirm the resulting list/batch dimensions and downstream `prepare_batch` expectations.
- If caching is enabled, run once with plain `Dataset` and once with cache to distinguish transform bugs from cache lifecycle issues.
