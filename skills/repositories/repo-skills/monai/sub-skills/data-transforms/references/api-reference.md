# MONAI Data and Transform API Reference

This reference summarizes commonly used APIs for data and transform workflows. Signatures reflect live inspection of the installed MONAI package used during skill creation.

## Core Transform APIs

| API | Signature | Notes |
| --- | --- | --- |
| `monai.transforms.Compose` | `Compose(transforms=None, map_items=True, unpack_items=False, log_stats=False, lazy=False, overrides=None)` | Chains callables; dictionary transforms must pass through unused keys. `map_items=True` applies later transforms to each item returned by multi-sample transforms. `lazy` controls lazy resampling. |
| `monai.transforms.LoadImaged` | `LoadImaged(keys, reader=None, dtype=np.float32, meta_keys=None, meta_key_postfix="meta_dict", overwriting=False, image_only=True, ensure_channel_first=False, simple_keys=False, prune_meta_pattern=None, prune_meta_sep=".", allow_missing_keys=False, expanduser=True, *args, **kwargs)` | Loads dictionary file paths or path lists. Optional readers depend on file type and installed packages. Set `image_only=False` when metadata is needed. |
| `monai.transforms.EnsureChannelFirstd` | `EnsureChannelFirstd(keys, strict_check=True, allow_missing_keys=False, channel_dim=None)` | Converts data to channel-first. Use `channel_dim="no_channel"` for scalar medical volumes with no explicit channel. Use `strict_check=False` only when metadata is known to be incomplete. |
| `monai.transforms.Spacingd` | `Spacingd(keys, pixdim, diagonal=False, mode="bilinear", padding_mode="border", align_corners=False, dtype=np.float64, scale_extent=False, recompute_affine=False, min_pixdim=None, max_pixdim=None, ensure_same_shape=True, allow_missing_keys=False, lazy=False)` | Resamples by physical spacing. For image/label pairs, use per-key `mode`, often `("bilinear", "nearest")`. Can participate in lazy resampling. |
| `monai.transforms.RandCropByPosNegLabeld` | `RandCropByPosNegLabeld(keys, label_key, spatial_size, pos=1.0, neg=1.0, num_samples=1, image_key=None, image_threshold=0.0, fg_indices_key=None, bg_indices_key=None, allow_smaller=False, allow_missing_keys=False, lazy=False)` | Returns `num_samples` crops using positive/negative label sampling. Requires current label values, so it may force pending lazy operations needed for correct sampling. |

## Dataset and Loader APIs

| API | Signature | Notes |
| --- | --- | --- |
| `monai.data.Dataset` | `Dataset(data, transform=None)` | Generic map-style dataset. Wraps callable or sequence transforms in `Compose` when needed. Slices return PyTorch `Subset`. |
| `monai.data.CacheDataset` | `CacheDataset(data, transform=None, cache_num=sys.maxsize, cache_rate=1.0, num_workers=1, progress=True, copy_cache=True, as_contiguous=True, hash_as_key=False, hash_func=pickle_hashing, runtime_cache=False)` | In-memory cache for deterministic work before the first random transform. Tune memory with `cache_rate` or `cache_num`. |
| `monai.data.PersistentDataset` | `PersistentDataset(data, transform, cache_dir, hash_func=pickle_hashing, pickle_module="pickle", pickle_protocol=2, hash_transform=None, reset_ops_id=True, track_meta=False, weights_only=True)` | Disk cache for deterministic preprocessing. Cached data should be tensors, primitives, or dictionaries of loadable values; clear cache after data/transform changes when uncertain. |
| `monai.data.DataLoader` | `DataLoader(dataset, num_workers=0, **kwargs)` | Extends PyTorch DataLoader with default `list_data_collate` and `worker_init_fn`; recommended for MONAI randomizable transforms and multi-crop samples. |
| `monai.data.MetaTensor` | `MetaTensor(x, affine=None, meta=None, applied_operations=None, *args, **kwargs)` | Tensor subclass carrying affine, metadata, and transform traces. Use MONAI `DataLoader` for metadata-aware batching. |
| `monai.data.load_decathlon_datalist` | `load_decathlon_datalist(data_list_file_path, is_segmentation=True, data_list_key="training", base_dir=None)` | Loads Medical Segmentation Decathlon-style JSON entries and resolves relative paths against `base_dir` or the JSON file's directory. |

## Data Layout Contracts

| Stage | Expected contract | Common assertion |
| --- | --- | --- |
| Raw datalist item | Dictionary with keys consumed by transforms, usually `image` and optional `label`; values are paths, path lists, arrays, or tensors. | `set(required_keys) <= set(item)` |
| Loaded image | Usually `MetaTensor` or tensor/array with spatial dimensions and optional metadata. | `hasattr(image, "shape")` |
| Channel-first sample | Single sample shape is `(C, spatial...)`; a no-channel 3D image becomes `(1, H, W, D)`. | `image.ndim == 4` for one 3D case |
| Batched sample | Batch shape is `(B, C, spatial...)`; metadata may become batched. | `batch["image"].shape[0] == batch_size` |
| Multi-crop transform | A transform such as `RandCropByPosNegLabeld(num_samples=N)` returns a list of dictionaries. | `len(dataset[0]) == N` before collation if inspected directly |
| Label tensor | Label keys should keep integer-like class ids; spatial resampling should use nearest-neighbor mode. | `label.unique()` stays within expected classes |
| Invertible item | `MetaTensor.applied_operations` contains the trace needed by `Compose.inverse`. | `len(image.applied_operations) > 0` after spatial transforms |

## Readers, Writers, and Optional Dependencies

MONAI exposes reader and writer classes through `monai.data` and uses optional packages for many medical/image formats.

- `NumpyReader` handles common NumPy formats and is usually the safest dependency-light option for tiny validation.
- `PILReader` depends on Pillow for standard image files.
- `NibabelReader` depends on nibabel for NIfTI-style medical images.
- `ITKReader` depends on ITK for broader medical image formats.
- `NrrdReader` depends on pynrrd for NRRD.
- DICOM, whole-slide, object-store, LMDB, and other advanced workflows require optional extras; do not assume those packages are installed.

Use `LoadImaged(reader=...)` to force a reader when auto-selection is ambiguous. For reusable skills or examples, describe optional dependencies instead of importing them unconditionally.

## Compose and Randomness Contracts

- `Compose` propagates MONAI random seeds to contained `Randomizable` transforms when `set_determinism()` is used.
- Dictionary transforms should copy through unused keys; if adapting a non-MONAI callable, wrap or write it so it does not drop metadata or unrelated keys.
- `map_items=True` is important after transforms returning lists of crops; disabling it passes the list wholesale to the next transform.
- `log_stats=True` or `log_stats="logger.name"` is useful to diagnose lazy execution and transform ordering.
- `overrides` only matter for lazy execution and can override supported arguments such as `mode`, `padding_mode`, `dtype`, `align_corners`, `resample_mode`, and `device`.

## Cache Boundary Rules

- `CacheDataset` and `PersistentDataset` are designed to cache deterministic transforms before the first `Randomizable` transform in a `Compose` pipeline.
- Avoid placing random augmentation before expensive deterministic preprocessing if you expect caching to save time.
- `PersistentDataset` hashes data items and may hash transforms; stale or incompatible caches can still occur after code or transform changes, so clearing cache is a valid recovery step.
- `copy_cache=True` protects cached objects from in-place downstream transforms at additional memory cost.
- `as_contiguous=True` can improve tensor layout for later operations; disable only for a known reason.

## Collation and Decollation APIs

- `monai.data.DataLoader` defaults to `list_data_collate`, which understands lists of crops and MONAI metadata better than PyTorch's default collation.
- `monai.data.decollate_batch(batch)` splits a batched dictionary or tensor structure into per-case items, which is usually required before inverse transforms, per-case postprocessing, or saving.
- `PadListDataCollate` can pad variable shapes during collation, but inverse handling must account for the padding transform.
- When multiprocessing is enabled, keep transforms pickle-safe and avoid mutable global state in custom callables.

## Safe Minimal Validation Pattern

```python
from monai.data import DataLoader, Dataset, MetaTensor
from monai.transforms import Compose, EnsureChannelFirstd, EnsureTyped, ScaleIntensityd

items = [{"image": [[1, 2], [3, 4]], "label": [[0, 1], [1, 0]]}]
transforms = Compose([
    EnsureChannelFirstd(keys=("image", "label"), channel_dim="no_channel"),
    ScaleIntensityd(keys="image"),
    EnsureTyped(keys=("image", "label"), track_meta=True),
])
dataset = Dataset(items, transform=transforms)
sample = dataset[0]
assert isinstance(sample["image"], MetaTensor)
loader = DataLoader(dataset, batch_size=1)
assert next(iter(loader))["image"].shape[0] == 1
```
