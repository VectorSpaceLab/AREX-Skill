# MONAI Data and Transform Troubleshooting

## Quick Triage Flow

1. Reproduce with `Dataset(data[:1], transform=transforms)[0]` before using caching or multiprocessing.
2. Print the input item keys and the transform `keys` arguments; fix key mismatches before debugging shapes.
3. Assert channel-first sample shapes after `EnsureChannelFirstd` and before spatial transforms.
4. Disable cache, lazy execution, and multiprocessing one at a time to isolate lifecycle issues.
5. If inverse transforms are involved, inspect `MetaTensor.applied_operations` before and after collation/decollation.

## Optional Reader Dependency Errors

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `LoadImaged` cannot find a suitable reader. | File extension requires an optional package that is not installed. | Install only the needed optional reader dependency, or use a dependency-light format such as `.npy` for validation. |
| NIfTI files fail to load. | Nibabel or ITK is missing, or the file is malformed. | Use `reader="NibabelReader"` or `reader="ITKReader"` only when that package is available; verify with a tiny known-good file. |
| DICOM, NRRD, whole-slide, cloud, or LMDB paths fail. | The corresponding optional extra is not part of MONAI's core install. | Document the required optional dependency and provide a fallback path for smoke tests. |
| Auto-reader chooses the wrong backend. | Multiple readers can match a file extension. | Pass an explicit `reader` to `LoadImaged` and keep `image_only=False` if metadata is needed. |

## Missing Keys and Dictionary Pipeline Errors

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `KeyError: 'label'` in validation/test data. | A transform expects labels on unlabeled data. | Split train/val/test transforms or set `allow_missing_keys=True` for transforms where a missing label is valid. |
| Optional key disappears after a custom transform. | Custom transform did not copy through unused dictionary keys. | Rewrite the transform to copy the input dict and update only owned keys, or adapt it with MONAI-compatible pass-through semantics. |
| `RandCropByPosNegLabeld` fails. | `label_key` is absent, empty, wrong shape, or not aligned with image. | Check `sample[label_key].shape`, label foreground values, and that image/label spatial transforms share the same keys. |
| Multi-crop output surprises downstream code. | `RandCropByPosNegLabeld(num_samples>1)` returns a list of dictionaries. | Keep `Compose(map_items=True)`, use MONAI `DataLoader`, and inspect `dataset[0]` and one collated batch. |

## Channel-First and Shape Errors

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Model receives `(H, W, D)` or `(B, H, W, D)`. | Missing channel dimension. | Add `EnsureChannelFirstd(keys, channel_dim="no_channel")` for scalar volumes or the correct source channel dimension for multi-channel images. |
| `EnsureChannelFirstd` raises strict metadata errors. | Channel metadata is missing or ambiguous. | Pass `channel_dim` explicitly; use `strict_check=False` only after verifying the source layout. |
| Image and label shapes diverge. | Spatial transforms were applied to only one key or used incompatible crop/pad parameters. | Apply geometry transforms to both keys and assert equal spatial shape after each major stage. |
| Labels contain interpolated class values. | Label was resampled with linear interpolation. | Use per-key spatial modes such as `mode=("bilinear", "nearest")`. |

## Metadata and `MetaTensor` Problems

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Output is plain `torch.Tensor` but inverse/affine is needed. | Metadata tracking was disabled or conversion stripped metadata. | Use `EnsureTyped(track_meta=True)` and avoid `.as_tensor()` until model/export boundaries. |
| Metadata is wrong after batching. | Batched metadata is being inspected as if it were a single case. | Use `decollate_batch(batch)` before per-case metadata checks or inverse operations. |
| Model/export code rejects `MetaTensor`. | Some downstream APIs expect raw tensors. | Convert at the boundary with `.as_tensor()` while keeping metadata in the preprocessing/inversion path. |
| Affine warnings appear when constructing `MetaTensor`. | Both `affine` and `meta["affine"]` were supplied. | Provide one authoritative affine source and verify it after load/spacing/orientation transforms. |

## Lazy Resampling Surprises

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Lazy pipeline output differs from eager output. | Compatible spatial operations are fused and ordering/resampling differs. | Compare with `Compose(lazy=False)` as baseline, then enable `log_stats` to see pending/apply boundaries. |
| Pending operations remain longer than expected. | Only lazy-capable transforms accumulate operations; non-lazy transforms force application. | Insert `ApplyPendingd` at a deliberate boundary or add a non-lazy terminal transform that materializes data. |
| Crop or foreground transform forces data update. | Some transforms need current voxel values to decide crop windows. | Expect pending operations to apply before value-dependent transforms such as foreground or label-based crops. |
| `overrides` appear ignored. | Overrides only apply when lazy execution is active. | Use `Compose(lazy=True)` or `Compose(lazy=None)` with transform-level `lazy=True`. |

## Cache and Dataset Lifecycle Issues

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Cached results do not reflect transform edits. | Persistent cache or runtime cache is stale. | Clear the cache directory or disable caching to confirm the new transform behavior. |
| Random augmentations are repeated unexpectedly. | Random transforms were accidentally cached or random state is fixed. | Place `Rand*` transforms after deterministic cached work and review `set_determinism()` usage. |
| Cache memory is too high. | `CacheDataset(cache_rate=1.0)` stores too much data. | Lower `cache_rate`, set `cache_num`, switch to `PersistentDataset`, or use plain `Dataset` for debugging. |
| In-place transform corrupts cached values. | Cached object is reused and mutated downstream. | Keep `copy_cache=True`, avoid in-place mutation, or clone tensors in custom transforms. |
| `PersistentDataset` load fails after dependency/version changes. | Cache content is incompatible with current transform or serialization settings. | Delete and rebuild cache; keep cache content limited to tensors, primitives, or dictionaries of safe values. |

## Multiprocessing and Collation Errors

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Works with `num_workers=0` but fails with workers. | Custom transform is not pickle-safe, uses non-fork-safe resources, or depends on mutable globals. | Keep `num_workers=0` while debugging, then make custom transforms top-level classes/functions with serializable state. |
| Batch collation fails for variable shapes. | Items have different spatial sizes after transforms. | Add deterministic crop/pad/resize before collation or use `PadListDataCollate` with inverse implications understood. |
| Patch samples collate into unexpected dimensions. | A transform returned a list of dictionaries. | Use MONAI `DataLoader` default `list_data_collate`; inspect one `dataset[0]` and one `next(iter(loader))`. |
| Randomness is inconsistent across workers. | Worker random states are not initialized for MONAI randomizable transforms. | Use `monai.data.DataLoader`, which sets `worker_init_fn` by default, and set deterministic seeds only when reproducibility is required. |

## Inverse Transform Failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `Compose.inverse` raises because no transform trace exists. | Data is plain tensor, metadata tracking was disabled, or a transform stripped `applied_operations`. | Preserve `MetaTensor` through preprocessing and check `len(image.applied_operations)` before batching. |
| Inverse fails on a batch. | Inverse is being applied to batched metadata instead of per-case metadata. | Use `decollate_batch(batch)` and invert each case separately. |
| Inverse gives wrong shape after padding collation. | Padding from collation was not inverted or was inverted in the wrong order. | Account for `PadListDataCollate.inverse` before applying the preprocessing inverse chain. |
| Lazy spatial inverse fails or is incomplete. | Pending lazy operations were never materialized or the inverse path used a different transform object. | Materialize pending operations with `ApplyPendingd` or a non-lazy boundary, preserve the original `Compose`, and inspect `applied_operations`. |
| Label and image inverse traces diverge. | Random spatial transform did not operate on both keys or one key was missing. | Apply spatial random transforms to both keys together and verify matching trace fields after decollation. |

## Minimal Debug Script Strategy

When a complex pipeline fails, make a tiny item with NumPy arrays and run:

1. `Compose([...])({"image": image, "label": label})` directly.
2. `Dataset([item], transform=transforms)[0]`.
3. `DataLoader(Dataset([item], transform=transforms), batch_size=1, num_workers=0)`.
4. The same loader with planned workers and cache.
5. Optional inverse or lazy path only after the eager single-sample path works.

The bundled `../scripts/check_data_pipeline.py` implements a safe version of this strategy without requiring external image-reader dependencies.
