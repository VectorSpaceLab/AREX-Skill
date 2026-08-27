# Data Loading Troubleshooting

Use this reference when fastMRI data loading, masking, transforms, or cache setup fails.

## Import Errors

### `ModuleNotFoundError: No module named 'requests'`

`fastmri.data.mri_data` imports `requests` for `AnnotatedSliceDataset` annotation downloads, but this checkout's package metadata may not declare it. Install `requests` in the user's working environment or avoid `AnnotatedSliceDataset` when annotations are not needed. If using a locked environment, record this as an optional fastMRI data dependency.

## Dataset Construction Errors

### Invalid challenge

Symptom:

```text
ValueError: challenge should be either "singlecoil" or "multicoil"
```

Fix: pass exactly `challenge="singlecoil"` or `challenge="multicoil"`. Do not pass split names such as `multicoil_train`, organ names such as `brain`, or leaderboard labels.

### Both sampling modes are set

Symptoms:

```text
either set sample_rate (sample by slices) or volume_sample_rate (sample by volumes) but not both
```

or for combined datasets:

```text
either set sample_rates (sample by slices) or volume_sample_rates (sample by volumes) but not both
```

Fix: choose one sampling strategy. Use `sample_rate`/`sample_rates` when individual slices can be mixed freely. Use `volume_sample_rate`/`volume_sample_rates` when all slices from selected volumes should stay together.

### Combined dataset length mismatch

Symptom:

```text
ValueError: Lengths of roots, transforms, challenges, sample_rates do not match
```

Fix: provide one `challenge` and one transform per root, or omit optional sequences so they default to matching lengths. For mixed singlecoil/multicoil roots, use matching entries such as `challenges=["singlecoil", "multicoil"]` and transforms compatible with each challenge.

## HDF5 Layout Errors

### Missing `kspace`

`SliceDataset` indexes `hf["kspace"].shape[0]` and reads `hf["kspace"][slice]`. If `kspace` is absent, the file is not compatible with the standard loader. Use `scripts/inspect_fastmri_h5.py` to identify offending files.

### Missing train/val target reconstruction

For `challenge="singlecoil"`, `SliceDataset` looks for `reconstruction_esc`; for `challenge="multicoil"`, it looks for `reconstruction_rss`. If the key is missing, `target` becomes `None`. That is legal for test/challenge inference, but training losses usually require target data.

Fixes:

- Confirm the chosen challenge matches the file's data track.
- Use target-aware transforms/losses only for train/val data with reconstruction keys.
- For test/challenge inference, use transforms that tolerate `target is None`.

### Missing or corrupt `ismrmrd_header`

Symptoms include HDF5 key errors, XML parse errors, or:

```text
RuntimeError: Element not found
```

`SliceDataset` parses `ismrmrd_header` to compute `encoding_size`, `recon_size`, `padding_left`, and `padding_right`. If the header is absent or missing ISMRMRD elements, standard metadata indexing fails.

Fixes:

- Inspect the file with `scripts/inspect_fastmri_h5.py` to see which XML fields are missing.
- Regenerate the fixture with a minimal compatible header if this is synthetic data.
- For real data, replace corrupt files or obtain the correct fastMRI release files.

### Test/challenge files lack targets

This is expected for many fastMRI test/challenge files. The loader returns `target=None`; `UnetDataTransform` creates a zero target tensor, and `VarNetDataTransform` creates `target=torch.tensor(0)` with `max_value=0.0`.

Avoid writing custom transforms that blindly access `target.shape` or `attrs["max"]` unless `target is not None`.

## Mask and Transform Errors

### Unsupported mask type

`create_mask_for_mask_type` supports only `random`, `equispaced`, `equispaced_fraction`, `magic`, and `magic_fraction`. Use exact strings. The class names are `EquiSpacedMaskFunc` and `EquispacedMaskFractionFunc`; their capitalization differs.

### Mask shape mismatch

`apply_mask` expects torch tensors with complex values in the final dimension of size `2`, and mask generation uses `shape[-2]` as the k-space width. Use `to_tensor` for NumPy complex arrays before masking.

For VarNet test/challenge transforms without a `mask_func`, the HDF5 file must contain a `mask` key because the transform reshapes the dataset-provided mask. If there is no file mask, provide a `mask_func` or use a custom transform.

### U-Net vs VarNet tuple shapes differ

`UnetDataTransform` returns image-domain `UnetSample(image, target, mean, std, fname, slice_num, max_value)`. `VarNetDataTransform` returns k-space-domain `VarNetSample(masked_kspace, mask, num_low_frequencies, target, fname, slice_num, max_value, crop_size)`.

Fix downstream code by consuming named fields or matching the expected model family. Route model construction and training-loop changes to `../lightning-training/`; route low-level tensor/operator shape debugging to `../mri-operators/`.

### Cropping surprises on unusual headers

`UnetDataTransform` crops to `target.shape[-2:]` when a target exists, otherwise to `attrs["recon_size"]`. It also has a special fallback when the image width is smaller than the requested crop. `VarNetDataTransform` reports `crop_size=(attrs["recon_size"][0], attrs["recon_size"][1])`.

Use the HDF5 inspector to compare `kspace` shape, target shape, and header `recon_size` before debugging model outputs.

## Cache Problems

### Stale `dataset_cache.pkl` after moving data

With `use_dataset_cache=True`, `SliceDataset` loads raw sample metadata from `dataset_cache_file` if it finds a cache entry for `root`. Moving data, changing headers, changing filters, or reusing a cache path across different experiments can leave stale metadata.

Fixes:

- Delete the cache file and let the dataset rebuild it.
- Use a unique `dataset_cache_file` per data root or experiment.
- Disable caching while debugging layout or metadata filters.

### Filter removes everything

`raw_sample_filter` receives a `FastMRIRawDataSample` with `.fname`, `.slice_ind`, and `.metadata`. If a filter relies on attrs such as `acquisition`, confirm the metadata exists in the parsed headers/attrs. Start with `transform=None` and inspect `dataset.raw_samples[:3]` before adding transforms.

## Annotation-Specific Problems

### Annotation CSV download fails

`AnnotatedSliceDataset` downloads fastMRI+ CSVs with `requests` into `.annotation_cache` when needed. Network restrictions, missing `requests`, or unavailable URLs can fail before data loading.

Fixes:

- Install `requests` if missing.
- Pre-populate `.annotation_cache` with the expected CSV when offline.
- Use plain `SliceDataset` if annotations are not required.

### Annotation policy error

`subsplit` must be `"knee"` or `"brain"`; `multiple_annotation_policy` must be `"first"`, `"random"`, or `"all"`. Note that the source error text mentions `"single"`, but the accepted policy is `"first"`.
