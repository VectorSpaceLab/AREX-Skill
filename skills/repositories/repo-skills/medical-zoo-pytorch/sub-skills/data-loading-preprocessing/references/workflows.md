# Workflows

This route focuses on preparing data for later training or inference.
Keep model selection, losses, and trainer details in sibling sub-skills.

## 1) Choose the loader family

Use the dataset key that matches the on-disk layout in [data-layout.md](./data-layout.md).
The main dispatcher accepts these keys:

- `iseg2017`
- `iseg2019`
- `brats2018`
- `brats2019`
- `brats2020`
- `mrbrains4`
- `mrbrains9`
- `ixi`
- `miccai2019`
- `COVID_CT`
- `COVIDx`
- `covid_seg`

## 2) Prepare the arguments

The data loaders reuse a small set of arguments. The exact subset depends on the dataset:

| Argument | Used for | Meaning |
| --- | --- | --- |
| `dataset_name` | all dispatcher branches | Selects the loader family. |
| `batchSz` | all dispatcher branches | Batch size passed to `DataLoader`. |
| `dim` | 3D loaders, pathology crops, some inference helpers | Crop size or voxel size tuple. |
| `split` | iSEG, BraTS, and some validation splits | Fraction used to split train/val subjects. |
| `samples_train` / `samples_val` | patch generators | Number of patches to generate for each split. |
| `classes` | BraTS, MRBRAINS, MICCAI2019, COVIDx | Target class count or class collapse mode. |
| `threshold` | 3D patch generators | Minimum label fraction inside a candidate crop. |
| `normalization` | medical image preprocessing | Intensity normalization mode. |
| `augmentation` | 3D patch loaders | Enables paired augmentation during train. |
| `loadData` | patch loaders with cached lists | Reuse previously generated patch lists. |
| `inModalities` | IXI and segmentation loaders | Number of modalities to combine. |

## 3) Run preprocessing helpers

### Medical image I/O

Typical call flow:

1. Load a NIfTI or Analyze image with `load_medical_image(...)`.
2. Optionally convert to canonical orientation with `to_canonical=True`.
3. Optionally resample with `resample=(vx, vy, vz)`.
4. Normalize intensities with `normalization="mean"`, `"max"`, `"full_volume_mean"`, `"max_min"`, or `"brats"`.
5. Crop with `crop_size` and `crop` when generating subvolumes.

Useful direct helpers:

- `load_affine_matrix(path)`
- `medical_image_transform(tensor, normalization=...)`
- `rescale_data_volume(array, out_dim)`
- `transform_coordinate_space(modality_1, modality_2)`
- `crop_img(tensor, crop_size, crop)`

### Subvolume generation

Use `create_sub_volumes(...)` when you want random label-aware crops written to disk.
The helper expects modality path lists, the dataset name, the split name, the desired crop size, the full-volume size, and a destination folder.
It writes `.npy` files and returns the saved path tuples.

Use `generate_padded_subvolumes(...)` when you want to tile a full 3D tensor into padded non-overlapping blocks.
It expects a tensor shaped like `(modalities, D, H, W)`.

For visualization or inference preparation, use `get_viz_set(...)` to stack full volumes and remap labels with `fix_seg_map(...)`.

## 4) Use the dispatcher

The top-level dataset dispatcher is the quickest way to wire a dataset into a batch loop:

```python
train_loader, val_loader, full_volume, affine = lib.medloaders.generate_datasets(args, path=dataset_root)
```

A few branch notes:

- `ixi` returns `(generator, affine)` instead of the usual four-tuple.
- `load=True` means the loader should reuse cached patch lists where supported.
- Most 3D branches return `full_volume` and `affine` from the validation loader for visualization.

## 5) Handle paired augmentation

The 3D augmentation package works on image/label pairs:

```python
from lib.augment3D import RandomChoice, GaussianNoise, RandomFlip, ElasticTransform

transform = RandomChoice(
    transforms=[GaussianNoise(mean=0, std=0.01), RandomFlip(), ElasticTransform()],
    p=0.5,
)
images, label = transform([img_a, img_b], label)
```

Useful operators:

- `RandomFlip`
- `RandomRotation`
- `RandomShift`
- `RandomZoom`
- `ElasticTransform`
- `GaussianNoise`
- `RandomCropToLabels`
- `RandomChoice`
- `ComposeTransforms`

## 6) Use the bundled smoke checks

The synthetic smoke scripts are safe entry points for this sub-skill:

```bash
python scripts/smoke_preprocessing.py
python scripts/smoke_augmentations.py
python scripts/smoke_dataloaders.py
```

What they cover:

- `smoke_preprocessing.py` checks NIfTI loading, resampling, coordinate transforms, cropping, and intensity normalization.
- `smoke_augmentations.py` checks paired 3D augmentation operators on synthetic volumes.
- `smoke_dataloaders.py` checks a synthetic patch-generation path and manifest-backed 2D loaders.

## 7) Notebook quickstart caveat

The original notebook copies a training script into the notebook working directory because relative imports break in notebook execution contexts.
In this skill, prefer the packaged module import path and run the bundled smoke scripts or your own wrapper from a normal shell.
