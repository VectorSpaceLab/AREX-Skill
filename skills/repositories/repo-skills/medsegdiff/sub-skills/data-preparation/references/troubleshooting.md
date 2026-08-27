# Data troubleshooting

Use the smallest reproducer first: run the bundled validator, print the
selected loader and `len(dataset)`, then fetch one item and inspect the three
returned fields. The validator is deterministic and offline, but intentionally
does not replace each loader's actual decode/transform path.

## Missing or unusable ISIC CSV

**Symptoms**

- `FileNotFoundError` for `ISBI2016_ISIC_Part3B_Training_GroundTruth.csv` or
  its Test variant.
- `pandas.errors.ParserError`, unexpected row counts, or paths that cannot be
  opened.

**Cause and recovery**

The source hard-codes the `Part3B` filename and reads columns by position, but
the README and checked-in example CSVs use `Part1` names and a blank index
column. First list the files under the selected `data_path`; then either
prepare a CSV with the exact filename expected by this source and columns at
positions 1/2, or make an explicit source-compatible loader change. Ensure the
CSV's image and mask entries are relative to the same `data_path`; the loader
joins them directly and does not search `Train/` or `Test/` automatically.
Do not rename a file blindly if the rows still point to another root.

For a missing row target, check that both paths exist and that image opens as
RGB and mask as grayscale. A successful CSV parse is not proof that all row
paths are valid.

## Custom 2D counts, names, or shapes

**Symptoms**

- `IndexError` during `__getitem__`.
- Image and mask content are visibly from different cases.
- Collation fails because image sizes differ.

**Cause and recovery**

`CustomDataset` independently sorts `images/*.png` and `masks/*.png` and uses
corresponding positions. It does not compare counts, stems, or dimensions.
The safe fix is to use one-to-one identical stems and equal counts, then run:

```bash
python scripts/validate_dataset_layout.py DATA_ROOT --kind custom2d
```

If the validator reports a missing counterpart, rename or regenerate the file
outside this skill and rerun it. Do not rely on lexicographic coincidence or
silently drop a mask. If dimensions differ, decide whether to resample the
mask with a nearest-neighbor policy in an explicit transform/loader extension;
the source does not solve this.

## BRATS missing modalities or malformed filenames

**Symptoms**

- An assertion such as `datapoint is incomplete, keys are ...`.
- A leaf is ignored or a modality is keyed incorrectly.
- Test data unexpectedly requires a segmentation or training data accepts a
  missing one.

**Cause and recovery**

For every leaf case, use filenames whose underscore-separated token at index 3
is exactly `t1`, `t1ce`, `t2`, `flair`, and, for training, `seg`. The normal
example is `brats_train_001_t1_123_w.nii.gz`. `BRATSDataset3D` strips `.nii`
from that token before matching; `BRATSDataset` does not. This subtle
source-level difference means validate the exact loader path you will use.

Run:

```bash
python scripts/validate_dataset_layout.py CASE_ROOT --kind brats --mode 3d
python scripts/validate_dataset_layout.py CASE_ROOT --kind brats --mode train
```

The validator rejects missing/extra recognized modality keys and malformed
names, but does not load every NIfTI by default. A `test_flag=True` case must
have only the four modalities; a training case needs `seg`. Remove unrelated
files from a leaf or isolate them in another directory if exact-key discovery
would be affected.

## BRATS fixed-slice failures

**Symptoms**

- `IndexError` around slice 154.
- `len(BRATSDataset3D)` is much larger than expected.
- A case has a different depth but still contributes 155 items.

**Cause and recovery**

`BRATSDataset3D` hard-codes 155 items per discovered case and indexes the last
axis from 0 through 154. Confirm every modality in every case has at least 155
slices and compatible dimensions. It does not enumerate actual depth and does
not validate depth at construction. If your data has another depth, use an
explicit loader extension that defines the policy; do not assume the fixed
loader will adapt.

## Custom 3D pairing and shape errors

**Symptoms**

- `Number of images and masks must be the same`.
- `Image and segmentation shape mismatch`.
- Empty dataset despite having NIfTI files.

**Cause and recovery**

`CustomDataset3D` only discovers `.nii.gz` directly under `images/` and
`masks/`, sorts both lists, pairs by position, and enumerates the last axis.
Put one image and one mask per case in those directories, use identical sorted
stems, and ensure every pair has the same NIfTI shape. If there are no matching
files, `len(dataset)` is zero; the source does not fail early. The validator
catches the common empty/count/shape cases when nibabel is available.

The training launcher in this source passes three positional arguments to a
two-argument `CustomDataset3D` constructor. If that branch raises `TypeError`,
fix the caller/class interface deliberately and then rerun a one-item smoke
check; changing the data layout will not fix an arity error.

## Cropping, resizing, and transform surprises

- `BRATSDataset` alone applies an `8:-8` crop to the final two dimensions;
  `BRATSDataset3D` does not. Do not attribute a 224x224 shape to all BRATS
  loaders.
- The launchers resize every selected dataset to `(image_size, image_size)`.
  ISIC and custom 2D then use `ToTensor()`; NIfTI loaders already return
  tensors. A PIL-only transform cannot be assumed to work on NIfTI tensors.
- Image and mask transforms are invoked with the same restored PyTorch RNG
  state. Keep paired random geometry synchronized; use a mask-safe interpolation
  policy when adding resampling.
- No cited loader normalizes image intensities. NIfTI values remain the
  floating values returned by nibabel; any normalization must be explicit and
  recorded.
- ISIC/custom 2D masks are not binarized by the loader. BRATS and custom 3D
  labels are binarized (`> 0` becomes `1.0`). A transform can change values
  after that point.

## Empty datasets and false-positive validation

A validator success means only that the selected directory has a recognized
shape and naming pattern. It does not guarantee the loader can open every
image, that an ISIC CSV has the exact source filename, that BRATS volumes have
155 slices, or that a transform can process the tensors. Always perform a
single-item loader smoke test, and stop with an actionable error if `len(dataset)
== 0`.

## Extension guidance

When adding a dataset, preserve the three-field tuple `(input, target, path)`
and make the path stable enough for downstream tracing. Define whether inputs
are PIL or tensors, the target channel shape, mask interpolation and
binarization, volume axis/slice policy, and intensity normalization. Add a
validator fixture and a one-item smoke test before routing the extension into a
launcher. Keep training flags, checkpoint handling, and evaluation formulas in
sibling skills.
