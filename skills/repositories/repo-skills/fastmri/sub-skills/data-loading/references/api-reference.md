# Data Loading API Reference

Use this reference for exact fastMRI data-loading APIs in this checkout.

## Imports

```python
from fastmri.data import SliceDataset, CombinedSliceDataset
from fastmri.data.mri_data import AnnotatedSliceDataset, fetch_dir
from fastmri.data.subsample import (
    MaskFunc,
    RandomMaskFunc,
    EquiSpacedMaskFunc,
    EquispacedMaskFractionFunc,
    MagicMaskFunc,
    MagicMaskFractionFunc,
    create_mask_for_mask_type,
)
from fastmri.data.transforms import UnetDataTransform, VarNetDataTransform, apply_mask, to_tensor
```

`AnnotatedSliceDataset` is implemented in `fastmri.data.mri_data`; do not rely on it being exported from `fastmri.data`.

## Dataset Constructors

```python
SliceDataset(
    root,
    challenge,
    transform=None,
    use_dataset_cache=False,
    sample_rate=None,
    volume_sample_rate=None,
    dataset_cache_file="dataset_cache.pkl",
    num_cols=None,
    raw_sample_filter=None,
)
```

Exact live signature:

```text
SliceDataset(root, challenge, transform=None, use_dataset_cache=False, sample_rate=None, volume_sample_rate=None, dataset_cache_file='dataset_cache.pkl', num_cols=None, raw_sample_filter=None)
```

- `root`: split directory containing `.h5` files.
- `challenge`: exactly `"singlecoil"` or `"multicoil"`.
- `transform`: callable receiving `(kspace, mask, target, attrs, fname, slice_num)`.
- `use_dataset_cache`: enables metadata caching in `dataset_cache_file`.
- `sample_rate`: fraction of slices to keep after metadata indexing.
- `volume_sample_rate`: fraction of volumes/files to keep after metadata indexing.
- `num_cols`: optional tuple of accepted encoded column counts, matched against `metadata["encoding_size"][1]`.
- `raw_sample_filter`: callable receiving `FastMRIRawDataSample(fname, slice_ind, metadata)` and returning a boolean.

```python
CombinedSliceDataset(
    roots,
    challenges,
    transforms=None,
    sample_rates=None,
    volume_sample_rates=None,
    use_dataset_cache=False,
    dataset_cache_file="dataset_cache.pkl",
    num_cols=None,
    raw_sample_filter=None,
)
```

Exact live signature:

```text
CombinedSliceDataset(roots, challenges, transforms=None, sample_rates=None, volume_sample_rates=None, use_dataset_cache=False, dataset_cache_file='dataset_cache.pkl', num_cols=None, raw_sample_filter=None)
```

- Use one entry per split/root.
- `roots`, `challenges`, `transforms`, `sample_rates`, and `volume_sample_rates` must have matching lengths after defaults are expanded.
- Set either `sample_rates` or `volume_sample_rates`, not both.
- A single `num_cols` or `raw_sample_filter` is applied to all child `SliceDataset` instances.

```python
AnnotatedSliceDataset(
    root,
    challenge,
    subsplit,
    multiple_annotation_policy,
    transform=None,
    use_dataset_cache=False,
    sample_rate=None,
    volume_sample_rate=None,
    dataset_cache_file="dataset_cache.pkl",
    num_cols=None,
    annotation_version=None,
)
```

- `subsplit`: exactly `"knee"` or `"brain"`.
- `multiple_annotation_policy`: `"first"`, `"random"`, or `"all"`.
- Downloads fastMRI+ CSV annotations into `.annotation_cache` using `requests` if the CSV is not already cached.
- Adds `attrs["annotation"]` to returned samples.

## Dataset Examples

Single split, multicoil validation data:

```python
from pathlib import Path
from fastmri.data import SliceDataset

dataset = SliceDataset(
    root=Path("/data/brain/multicoil_val"),
    challenge="multicoil",
    transform=None,
)
kspace, mask, target, attrs, fname, slice_num = dataset[0]
```

Combine train and validation roots without mixing sampling modes:

```python
from fastmri.data import CombinedSliceDataset

dataset = CombinedSliceDataset(
    roots=[Path("/data/knee/multicoil_train"), Path("/data/knee/multicoil_val")],
    challenges=["multicoil", "multicoil"],
    transforms=[None, None],
    volume_sample_rates=[0.25, 0.25],
)
```

Filter selected volumes or acquisitions:

```python
def keep_coronal_pd(raw_sample):
    return raw_sample.metadata.get("acquisition") == "CORPD_FBK"

dataset = SliceDataset(
    root=Path("/data/knee/singlecoil_train"),
    challenge="singlecoil",
    raw_sample_filter=keep_coronal_pd,
    num_cols=(640,),
)
```

## Mask APIs

```python
create_mask_for_mask_type(mask_type_str, center_fractions, accelerations)
```

Exact live signature:

```text
create_mask_for_mask_type(mask_type_str, center_fractions, accelerations)
```

Supported `mask_type_str` values:

- `"random"` → `RandomMaskFunc`.
- `"equispaced"` → `EquiSpacedMaskFunc`.
- `"equispaced_fraction"` → `EquispacedMaskFractionFunc`.
- `"magic"` → `MagicMaskFunc`.
- `"magic_fraction"` → `MagicMaskFractionFunc`.

Mask constructors share this signature:

```python
MaskClass(center_fractions, accelerations, allow_any_combination=False, seed=None)
```

- `center_fractions` and `accelerations` are paired by index unless `allow_any_combination=True`.
- The mask object returns `(mask, num_low_frequencies)` when called with a k-space shape.
- Shape must have at least three dimensions; the column dimension is `shape[-2]`.

`apply_mask(data, mask_func, offset=None, seed=None, padding=None)` returns:

```python
masked_data, mask, num_low_frequencies
```

- `data` should be a torch tensor with complex values represented in final dimension size `2`.
- `padding=(left, right)` zeroes mask columns before `left` and from `right` onward.
- Tests verify that `apply_mask` preserves the global NumPy RNG state when a seed is supplied.

## Transform APIs

```python
UnetDataTransform(which_challenge, mask_func=None, use_seed=True)
```

- `which_challenge`: exactly `"singlecoil"` or `"multicoil"`.
- Converts k-space to tensor, optionally applies a mask, inverse FFTs to image space, crops to target or `attrs["recon_size"]`, takes absolute value, RSS-combines multicoil images, instance-normalizes, clamps to `[-6, 6]`, and returns `UnetSample`.
- `UnetSample` fields: `image`, `target`, `mean`, `std`, `fname`, `slice_num`, `max_value`.

```python
VarNetDataTransform(mask_func=None, use_seed=True)
```

- Converts k-space to tensor and returns k-space-domain `VarNetSample`.
- With `mask_func`, applies `apply_mask(..., padding=(attrs["padding_left"], attrs["padding_right"]))`.
- Without `mask_func`, expects the dataset-provided `mask` to be present and reshapes it to the k-space mask shape.
- `VarNetSample` fields: `masked_kspace`, `mask`, `num_low_frequencies`, `target`, `fname`, `slice_num`, `max_value`, `crop_size`.

`use_seed=True` derives a deterministic seed from `fname`, keeping the same synthetic mask across slices of a volume. Use `use_seed=False` for training setups that intentionally vary masks per slice/worker.

## Sampling and Cache Rules

- `SliceDataset` rejects setting both `sample_rate` and `volume_sample_rate`.
- `CombinedSliceDataset` rejects setting both `sample_rates` and `volume_sample_rates`.
- If no sampling mode is provided, each dataset behaves as full sampling.
- `use_dataset_cache=True` stores metadata keyed by the `root` object in `dataset_cache_file`; stale cache files can point at moved or old data layouts.
- Delete or relocate `dataset_cache.pkl` after moving files, changing headers, changing filters, or switching roots.

## Data Module Handoff

When the user asks for full dataloaders or training loops, route to `../lightning-training/`. The key handoff facts are:

- `FastMriDataModule` expects transforms to be created first and passed in.
- It derives split paths as `<data_path>/<challenge>_<train|val|test>` unless `test_path` overrides test data.
- It enforces the same `sample_rate` vs `volume_sample_rate` mutual exclusion for train/val/test variants.
