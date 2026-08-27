# Dataset API reference

The signatures and behaviors below are taken from the cited loader source at
source commit `28b343fddd6bb6dc1bccdaed94ca7ebefe9142f3`. This is a behavioral
reference for preparing data; it is not a copy of the repository and does not
bundle data.

## `ISICDataset`

```python
ISICDataset(args, data_path, transform=None, mode="Training", plane=False)
```

- `args` is accepted but not read by the constructor.
- `data_path` is the root against which the CSV's second and third columns are
  joined.
- `mode` is interpolated into the source filename
  `ISBI2016_ISIC_Part3B_{mode}_GroundTruth.csv`; the launcher uses the default
  `Training` for training and `mode="Test"` for sampling.
- `plane` is accepted but unused.
- `__len__()` is the number of rows loaded into `name_list`.
- `__getitem__(index)` returns `(PIL-or-transformed image, PIL-or-transformed
  mask, csv image name)`. The image is opened RGB, the mask L. The transform is
  called on both, with the PyTorch RNG state restored before the mask call.

The CSV is read with pandas `read_csv(..., encoding="gbk")`, and columns are
selected positionally (`iloc[:, 1]`, `iloc[:, 2]`). A header or column order
change can therefore alter behavior even if column labels look reasonable.

## `BRATSDataset`

```python
BRATSDataset(directory, transform, test_flag=False)
```

- `directory` is expanded with `os.path.expanduser` and recursively scanned.
- A leaf directory (one with no subdirectories) is interpreted as a case.
- The filename token at underscore-separated position 3 is the modality key.
- Training key set: `{"t1", "t1ce", "t2", "flair", "seg"}`.
- Test key set: `{"t1", "t1ce", "t2", "flair"}`.
- Construction asserts exact key-set equality per leaf.
- `__len__()` is the number of discovered cases.
- Full NIfTI arrays are stacked in `seqtypes` order.
- Training: crop image and label on the last two axes with `8:-8`, map label
  values to binary, apply optional synchronized transform, return
  `(image, label, path)`.
- Test: crop the four-channel image, use it as both first and second tuple
  values, and return `(image, image, path)`.

The returned image has four modality channels in training/test, and training's
label has one channel. The exact spatial dimensions after the crop depend on
the input dimensions; the source comment specifically describes 256x256 to
224x224 behavior.

## `BRATSDataset3D`

```python
BRATSDataset3D(directory, transform, test_flag=False)
```

The discovery rules and modality key sets match `BRATSDataset`, except token
position 3 has `.nii` split off before matching. The item API is slice-based:

```text
case = index // 155
slice = index % 155
```

`__len__()` is `number_of_cases * 155`, regardless of actual NIfTI depth. Item
access reads all modalities for the case and selects `[:, :, slice]`.

- Training: `(four-channel image, one-channel binary label, virtual path)`.
- Test: `(four-channel image, same image, virtual path)`.
- Virtual path: `path.split('.nii')[0] + '_slice' + str(slice) + '.nii'`.
- Optional transform receives the stacked slice; training synchronizes its
  random state between image and label.
- No 8-pixel crop is performed by this class.

The fixed 155 behavior means a shallow synthetic volume is useful for shape
checks but cannot be treated as a valid BRATS3D fixture unless it has at least
155 slices (or the class is explicitly extended).

## `CustomDataset`

```python
CustomDataset(args, data_path, transform=None, mode="Training", plane=False)
```

- `args`, `mode`, and `plane` are accepted for interface compatibility; only
  `data_path` and `transform` affect discovery/reading.
- `images/*.png` and `masks/*.png` are globbed and sorted separately.
- No count, basename, or shape assertion exists in the source; positional
  pairing is the consequence of `zip`-like list indexing in `__getitem__`.
- The image is RGB; the mask is L.
- Return tuple: `(image, mask, image_full_path)`.
- A supplied transform runs on both image and mask with restored PyTorch RNG
  state before the mask operation.

Use equal sorted lists with equal dimensions as an external preparation
invariant even though the source does not enforce it.

## `CustomDataset3D`

```python
CustomDataset3D(data_path, transform)
```

- Discovers sorted `images/*.nii.gz` and `masks/*.nii.gz` lists.
- Asserts equal list lengths, pairs by sorted position, then asserts each
  image/mask NIfTI shape matches.
- Enumerates every final-axis index for each case.
- `__len__()` is total enumerated slices.
- On access, reads both volumes and constructs float32 tensors of shape
  `(1, 1, H, W)` from `[:, :, slice_index]`.
- Binarizes label values with `torch.where(label > 0, 1, 0).float()`.
- Applies optional transform to image and label with synchronized PyTorch RNG.
- Return tuple: `(image, label, image_path_with_virtual_slice_suffix)`.

The source uses `CustomDataset3D(data_path, transform)` but the training
launcher passes an extra `args` positional value. Treat that as a source-level
integration defect, not as a valid three-argument constructor.

## Safe caller sequence

1. Choose one loader explicitly; do not infer behavior from a folder name.
2. Use the validator in `scripts/validate_dataset_layout.py` to catch basic
   missing files, count mismatches, and BRATS naming/modality errors.
3. Instantiate with the exact constructor above and a transform compatible
   with its input type.
4. Inspect `len(dataset)` and one tuple before constructing a large
   `DataLoader`.
5. Verify channel count and spatial shape after the transform. A successful
   layout validation alone does not prove nibabel decoding, image readability,
   or full loader compatibility.
