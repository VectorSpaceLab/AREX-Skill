# Registered dataset layouts

The dispatcher in `dataset/__init__.py` uses exact, case-sensitive string
comparisons. The values below are the supported source spellings; there are no
case-insensitive aliases. `<data_path>` is always supplied by the caller.
This reference describes layouts and adapter behavior only. It does not provide
downloaders or assume a checkout-relative directory.

## Registry and source adapter table

| `-dataset` value | Source adapter | Required layout under `<data_path>` | Returned image/label behavior |
|---|---|---|---|
| `isic` | `ISIC2016` | `ISBI2016_ISIC_Part1_Training_GroundTruth.csv` and `ISBI2016_ISIC_Part1_Test_GroundTruth.csv`; each CSV's zero-based columns 1 and 2 name an image and mask resolved under the same root | RGB image and one grayscale foreground mask; a positive prompt label is the default |
| `decathlon` | MONAI `get_decath_loader` | `dataset_0.json` at the data root, with `training` and `validation` entries; the referenced image/label files must resolve to the `imagesTr` and `labelsTr` tree used by the Decathlon/BTCV layout | MONAI loads channel-first 3D image and label volumes, then applies CT scaling, foreground crop, RAS orientation, spacing, and training crop transforms |
| `REFUGE` | `REFUGE` | `Training-400/<case>/<case>.jpg` and seven `<case>_seg_cup_1.png` ... `_7.png` plus seven `<case>_seg_disc_1.png` ... `_7.png`; the same structure is required under `Test-400` | RGB image; two output mask channels formed by averaging raters, concatenated cup then disc |
| `LIDC` | `LIDC` class, but the registry branch is broken | One or more filenames containing `.pickle`; each pickle maps a case to `image`, `masks`, and `series_uid`, with image and masks expected in `[0,1]` | The class averages raters and repeats the 2D image to three channels. The dispatcher calls undefined `MyLIDC`, so `-dataset LIDC` is blocked until source code is fixed and verified. The class also concatenates `data_path + filename`; do not hide that path bug with a guessed layout. |
| `DDTI` | `DDTI` | `Training/images/<name>` paired with `Training/masks/<name>`, and the same pair under `Test` | RGB image and one binary mask; connected foreground components larger than 400 pixels can yield up to two click prompts |
| `Brat` | `Brat` | `Data/<case>/<case>_t1.nii.gz`, `_flair.nii.gz`, `_t2.nii.gz`, `_t1ce.nii.gz`, and `_seg.nii.gz` | Reads all four modalities but returns only the first (`t1`) as one channel; selects label value `4` and returns one binary mask channel |
| `STARE` | `STARE` | `masks/<stem>.ah.ppm` and `images/<stem>.ppm`; stems are enumerated from `masks` | RGB image and one grayscale vessel mask |
| `kits` | `KITS` | `kits21/data/<case>/imaging.nii.gz` and `aggregated_AND_seg.nii.gz` | One channel after axis transpose and one clipped binary mask; source also mentions `aggregated_OR_seg.nii.gz` and `aggregated_MAJ_seg.nii.gz`, but this adapter selects `AND` |
| `WBC` | `WBC` | `Dataset1/<stem>.bmp` paired with `Dataset1/<stem>.png` | RGB image and one selected class mask. The guide describes two foreground categories, but this source filters to class `1`; it ignores the `mode` argument |
| `segrap` | `SegRap` | `SegRap2023_Training_Set_120cases/<case>/image.nii.gz` and `SegRap2023_Training_Set_120cases_OneHot_Labels/Task001/<case>.nii.gz` | One image channel; selects label value `1` from the task volume and returns one binary mask |
| `toothfairy` | `ToothFairy` | `Dataset/<case>/data.npy` and `gt_sparse.npy` | One image and one clipped binary mask channel after axis transpose and `numpy.resize` to configured image/output sizes |
| `atlas` | `Atlas` | `train/dataset.json` with a `training` list; each entry's `image` and `label` is resolved below `train` | One image and one mask channel after selecting label value `1` and transposing axes; the loader does not resize this data |
| `pendal` | `Pendal` | `Images/<name>` paired with `Segmentation1/<name>` | RGB image and one binarized mask; `Segmentation2` exists in the guide but is not selected by this adapter |
| `lnq` | `LNQ` | `train/` must contain a `.png` marker named `<stem>.png`, plus `<stem>-ct.nrrd` and `<stem>-seg.nrrd`; the marker supplies the enumerated stem | One integer image and one integer binary mask channel after SimpleITK loading and axis transpose |

The order above is intentionally the source registry order (apart from the
same names being grouped in the requested catalog). The exact accepted set is:

```text
isic, decathlon, REFUGE, LIDC, DDTI, Brat, STARE, kits,
WBC, segrap, toothfairy, atlas, pendal, lnq
```

`refuge`, `brat`, `KITS`, `Segrap`, and other case variants are not equivalent.
A public dataset name such as BTCV or BraTS is also not itself a registry value:
BTCV uses the `decathlon` branch, while the direct brain-tumor adapter uses
`Brat`.

## 2D adapter details

The common 2D transforms resize the image to `(image_size, image_size)`, convert
it to a tensor, and multiply image values by 255. Masks are transformed
separately to `(out_size, out_size)`. Therefore the usual item is
`image=[3,H,W]`, `label=[1,H_out,W_out]`; REFUGE is the two-channel exception.
LIDC's class repeats its one image plane to three channels, but the broken
registry branch means that behavior is not runnable through `get_dataloader`
until fixed.

- **ISIC:** check every image/mask value referenced by both CSV files. The
  loader does not derive mask names from a fixed stem.
- **REFUGE:** all seven raters for both cup and disc are required even though
  the adapter averages them. Its returned channel order is cup then disc.
- **DDTI:** the default prompt mode is `click`; the connected-component helper
  ignores components of area 400 or less and caps the returned prompts at two.
- **WBC:** masks are integer-divided by 127 and only class `1` is retained.
- **STARE:** filenames are derived from the mask directory; verify both the
  `.ah.ppm` mask and matching `.ppm` image.
- **Pendal:** only `Segmentation1` is read by the source.

For the built-in RGB adapters, `pt` is generated by `random_click` in x/y order
when click prompting is enabled. A blank target can produce `p_label=0` and a
fallback location; it is not a valid foreground annotation merely because a
point exists.

## 3D direct adapters

Brat, KITS, Atlas, LNQ, SegRap, and ToothFairy expose one channel and a depth
axis as `[1,H,W,D]` after their source-specific transpose/read operations.
Brat, KITS, SegRap, and ToothFairy use `numpy.resize` in the inspected code; it
is not physical resampling or interpolation. Atlas and LNQ leave the in-plane
shape supplied by their reader. `nibabel` is required for NIfTI adapters and
`SimpleITK` for LNQ; do not replace missing medical-image dependencies with a
2D reader.

The current 3D training/evaluation loop regenerates prompts with
`generate_click_prompt`, selects one connected label per slice, flattens depth
to 2D slices, and repeats the image slice to three channels. The documented
custom contract uses one `[x,y]` point per slice (`pt` shape `[2,D]`), but the
source helper obtains coordinates from `torch.nonzero` in row/column order and
only reverses them for visualization. If using source-generated prompts, test
coordinate orientation with the selected model rather than relying on a visual
overlay alone.

## MONAI Decathlon/BTCV path

The README's BTCV preparation uses this logical layout:

```text
<data_path>/
  imagesTr/              # training image volumes
  labelsTr/              # training label volumes
  dataset_0.json         # MONAI training/validation split
```

The source opens `dataset_0.json` at the root, reads its `training` and
`validation` lists with MONAI, and applies the following training transforms:

1. load `image` and `label` with `ensure_channel_first=True`;
2. scale image CT values from `[-175,250]` to `[0,1]` with clipping;
3. crop foreground using the image;
4. orient both volumes to `RAS`;
5. resample to `(1.5,1.5,2.0)` using bilinear image and nearest label modes;
6. randomly crop `(roi_size, roi_size, chunk)` with positive/negative label
   sampling and `num_sample` samples, followed by flips, rotations, and
   intensity shift.

Validation performs loading, scaling, foreground crop, orientation, spacing,
and metadata tracking but not the random training crop. `roi_size` and `chunk`
therefore describe post-transform tensors, not necessarily raw file dimensions.
Validate a representative post-transform shape in the real MONAI environment;
the bundled metadata helper cannot prove it. Evaluation uses `evl_chunk`
windows, and the source loop can skip a trailing depth remainder when the
window is not a divisor. Prefer a positive divisor or record that limitation.
