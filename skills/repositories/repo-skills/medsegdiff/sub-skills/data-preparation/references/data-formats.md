# Data formats and loader contracts

This reference records the source-grounded layouts and behavior of
`guided_diffusion/isicloader.py`, `bratsloader.py`, and
`custom_dataset_loader.py`, plus the dataset branching in the segmentation
launchers. The data itself is not part of the generated skill.

## ISIC (`ISICDataset`)

The README's canonical tree is:

```text
DATA_ROOT/
├── Train/
│   ├── ISBI2016_ISIC_Part1_Training_GroundTruth.csv
│   ├── ISBI2016_ISIC_Part1_Training_Data/
│   │   └── ISIC_0000000.jpg ...
│   └── ISBI2016_ISIC_Part1_Training_GroundTruth/
│       └── ISIC_0000000_Segmentation.png ...
└── Test/
    ├── ISBI2016_ISIC_Part1_Test_GroundTruth.csv
    ├── ISBI2016_ISIC_Part1_Test_Data/
    │   └── ISIC_0000003.jpg ...
    └── ISBI2016_ISIC_Part1_Test_GroundTruth/
        └── ISIC_0000003_Segmentation.png ...
```

The source constructor is exact and important:

```python
ISICDataset(args, data_path, transform=None, mode="Training", plane=False)
```

It reads `os.path.join(data_path,
"ISBI2016_ISIC_Part3B_" + mode + "_GroundTruth.csv")` with `encoding="gbk"`,
then uses the second and third CSV columns as **relative paths from
`data_path`**. The checked-in CSV examples under `data/isic_csv/` instead are
named `ISBI2016_ISIC_Part1_Training_GroundTruth.csv` and contain a blank first
column followed by `img,seg`; the README also documents the Part1 names. Thus,
with this source commit, a normal Part1 README tree does not satisfy the
constructor without a filename/data-root adaptation. Confirm the actual CSV
name before calling the loader; do not paper over this mismatch in a validator.

For each row, the loader opens the image as RGB and the mask as grayscale L.
It returns `(img, mask, name)`, where `name` is the CSV image-path string. With
the launcher transform (`Resize((image_size, image_size))` then `ToTensor()`),
images and masks are resized and converted to tensors. The same PyTorch RNG
state is restored before transforming the mask, so random transforms that use
PyTorch RNG are synchronized; deterministic resize/ToTensor has no additional
randomness. The loader does not itself binarize the mask or normalize intensity
beyond whatever the supplied transform does.

## BRATS common case and full-volume loader

The README describes a root containing leaf case directories:

```text
DATA_ROOT/
├── training/
│   ├── slice0001/
│   │   ├── brats_train_001_t1_123_w.nii.gz
│   │   ├── brats_train_001_t1ce_123_w.nii.gz
│   │   ├── brats_train_001_t2_123_w.nii.gz
│   │   ├── brats_train_001_flair_123_w.nii.gz
│   │   └── brats_train_001_seg_123_w.nii.gz
│   └── slice0002/...
└── testing/
    └── slice1000/...
```

`BRATSDataset(directory, transform, test_flag=False)` recursively walks
`directory`. A directory is treated as a case only when `os.walk` reports no
subdirectories in that directory. Every filename is split on `_`, and token
index 3 is used as the modality key. Training requires exactly the keys
`t1`, `t1ce`, `t2`, `flair`, and `seg`; `test_flag=True` requires exactly the
four image keys and omits `seg`. The source asserts this key-set equality for
each leaf, so malformed names or extra/missing recognized keys stop
construction rather than being skipped.

Each NIfTI is loaded with nibabel and converted from `get_fdata()` to a tensor;
modalities are stacked in the sequence order above. For training, the result is
split into `image = out[:-1, ...]` (four modalities) and
`label = out[-1, ...][None, ...]` (one channel). Both are cropped as
`[..., 8:-8, 8:-8]`; the source comment calls this a 224x224 crop for a
256x256 in-plane input. Every positive segmentation value is mapped to `1.0`
and every zero/non-positive value to `0.0`. With `test_flag=True`, the four
image channels are cropped and returned twice as `(image, image, path)`;
there is no ground-truth segmentation channel.

The transform, if supplied, is applied to the image and (for training) the
label. PyTorch RNG state is captured/restored around the two calls so random
PyTorch transforms use the same random choices. The loader does not perform
intensity normalization. The returned `path` is the last modality's path in
training and is the path of the last image modality in testing.

## BRATS fixed-slice loader (`BRATSDataset3D`)

`BRATSDataset3D(directory, transform, test_flag=False)` discovers the same leaf
case structure and modality keys, but strips `.nii` from token index 3 before
matching. Training requires `t1,t1ce,t2,flair,seg`; test mode requires the four
image keys.

The constructor does not inspect volume depth. `__len__()` is
`len(database) * 155`, unconditionally. For item index `x`,
`case_index = x // 155` and `slice_index = x % 155`; it loads each case volume
and selects `volume[:, :, slice_index]`. Therefore every case must be readable
and deep enough for indices 0 through 154, or item access will fail. This is a
fixed virtual-slice contract, not “all available slices.”

Training returns `(image, label, virtual_path)` where `image` has four stacked
modalities, `label` is one channel and is binarized with `torch.where(label >
0, 1, 0).float()`, and the virtual path is derived from the last loaded
modality by removing the `.nii` suffix and appending
`_slice{slice_index}.nii`. No 8-pixel crop is applied in this class. Test mode
returns `(image, image, virtual_path)` with four image channels. A supplied
transform is applied after slice extraction; training restores PyTorch RNG
state before applying it to the label. The launcher uses `Resize((image_size,
image_size))` for BRATS and does not add `ToTensor()` because the slices are
already tensors.

## Custom 2D (`CustomDataset`)

Use:

```text
DATA_ROOT/
├── images/
│   ├── case-001.png
│   └── case-002.png
└── masks/
    ├── case-001.png
    └── case-002.png
```

The constructor is `CustomDataset(args, data_path, transform=None,
mode="Training", plane=False)`. It glob-sorts `images/*.png` and
`masks/*.png` independently and pairs entries by sorted **position**, not by
basename. The source does not assert equal counts or matching names. Equal
counts and identical case order should therefore be treated as a preparation
requirement; a safer validator rejects otherwise.

Each image is opened as RGB and each mask as grayscale L. The return tuple is
`(img, mask, name)`, where `name` is the image's full path. If a transform is
provided, the source restores the PyTorch RNG state before applying that same
transform to the mask. The launcher uses `Resize((image_size,image_size))`
then `ToTensor()` for this branch. There is no loader-level mask binarization
or intensity normalization.

## Custom 3D (`CustomDataset3D`)

Use paired directories:

```text
DATA_ROOT/
├── images/
│   ├── case-001.nii.gz
│   └── case-002.nii.gz
└── masks/
    ├── case-001.nii.gz
    └── case-002.nii.gz
```

The class signature in the source is `CustomDataset3D(data_path, transform)`.
It glob-sorts the two directories independently, asserts equal counts, zips
by sorted position, and then loads every mask/image pair with nibabel to assert
identical shapes. For each case it enumerates every index along the final axis
(`range(img.shape[-1])`), so its length is the sum of case depths, unlike the
fixed 155 BRATS loader.

For an item, it reloads both NIfTI volumes, selects `[:, :, slice_index]`,
converts each slice to float32, and adds two singleton dimensions. The exact
pre-transform shapes are therefore `(1, 1, H, W)` for both image and label.
The label is binarized with `label > 0`. It returns
`(image, label, virtual_path)`, where the virtual path is the image path with
`.nii` removed and `_slice{slice_index}.nii` appended. Transforms are applied
after those dimensions are added, with PyTorch RNG restoration before the
label transform. The loader does not normalize intensities.

There is an integration caveat: the checked-in training launcher calls
`CustomDataset3D(args, args.data_dir, transform_train)` (three positional
arguments), while the class accepts only `(data_path, transform)`; that branch
will raise a `TypeError` until the caller or class is adapted. The launcher also
uses a loose `Path(args.data_dir).glob("*\\*.nii.gz")` test, so select the
custom-3D route deliberately and verify the actual launcher behavior after any
fix. `segmentation_sample.py` imports only `CustomDataset` in this source
commit.

## Transforms and tensor expectations

The launchers select datasets as follows: `data_name == 'ISIC'` selects ISIC;
`data_name == 'BRATS'` selects `BRATSDataset3D`; otherwise a path glob decides
between custom 3D and custom 2D. They build a `torchvision.transforms.Compose`
with resize to `(image_size, image_size)`; ISIC/custom 2D add `ToTensor()`,
while NIfTI loaders already yield tensors. Do not pass a PIL-only transform to
a NIfTI loader or assume `ToTensor()` is applied to a NIfTI tensor.

A `DataLoader` batches the returned tuples. The first two fields are the input
and target-like tensor; the third is a path or virtual path used for tracing
and output naming. This file does not specify training flags or evaluation
formulas.
