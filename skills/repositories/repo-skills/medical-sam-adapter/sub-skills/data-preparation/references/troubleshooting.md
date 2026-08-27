# Data-preparation troubleshooting

Use the metadata validator first, then diagnose the source adapter and runtime
separately. Do not change a dataset's case-sensitive name, download missing
files from a runtime skill, or alter label rank just to suppress an error.

## The dispatcher rejects a dataset name

Use exactly:

```text
isic, decathlon, REFUGE, LIDC, DDTI, Brat, STARE, kits,
WBC, segrap, toothfairy, atlas, pendal, lnq
```

`REFUGE`, `Brat`, `WBC`, and `LIDC` are not lowercase aliases. `BTCV` is a
layout handled by `decathlon`; `Brat` is the direct brain-tumor adapter. Check
[dataset layouts](dataset-layouts.md) before changing the command.

## Files are missing or cases do not pair

- **ISIC:** both ground-truth CSVs must exist. For every row, verify the image
  and mask values in zero-based columns 1 and 2 resolve under the caller's
  `data_path`. Do not assume a fixed filename template.
- **REFUGE:** every case needs its JPG and all seven cup plus seven disc rater
  PNGs under the exact case directory. Averaging fewer raters changes the source
  target and is not an acceptable silent fallback.
- **DDTI:** list the same filenames under `Training/images` and `Training/masks`,
  and under `Test`. A missing mask or a component too small for the source's
  400-pixel cutoff can leave no useful positive click.
- **WBC:** the source hard-codes `Dataset1` and requires matching `.bmp` image
  and `.png` mask stems. It selects class `1`, not every category mentioned by
  the guide.
- **STARE:** derive stems from `masks`; verify `<stem>.ah.ppm` and
  `<stem>.ppm` in `images`.
- **Pendal:** verify matching files in `Images` and `Segmentation1`. The source
  does not select `Segmentation2`.
- **Brat:** every case needs all four modality files and `_seg.nii.gz`, even
  though the returned image is only `t1` and the selected label value is `4`.
- **KITS:** the root must contain `kits21/data/<case>/imaging.nii.gz` and the
  exact `aggregated_AND_seg.nii.gz` selected by the adapter.
- **Atlas:** `train/dataset.json` must parse and contain a `training` list whose
  `image` and `label` entries resolve below `train`.
- **LNQ:** the source enumerates `.png` files but then reads matching
  `-ct.nrrd` and `-seg.nrrd`; a marker PNG without both NRRDs is incomplete.
- **SegRap:** verify the image case directory and matching `Task001` label
  file. **ToothFairy:** verify both `data.npy` and `gt_sparse.npy` per case.
- **Decathlon/BTCV:** keep `dataset_0.json` at the data root with `imagesTr`
  and `labelsTr` available. Verify both `training` and `validation` entries
  and their resolved image/label files.

## LIDC is still blocked after the pickle files are fixed

The registry branch in `dataset/__init__.py` constructs `MyLIDC`, but the
inspected `dataset/lidc.py` defines `LIDC`, not `MyLIDC`. This is a source-level
blocker. Separately, the class builds a pickle path by concatenating
`data_path + filename`, so a caller cannot claim the branch is fixed merely
because pickle files exist. Repair and test the source outside this operating
skill before selecting `-dataset LIDC`.

## The validator reports a rank, channel, or depth error

- A single item must be `[C,H,W]` or `[C,H,W,D]`; do not include `B`.
- The label must have the same rank and aligned spatial axes. H/W may differ
  only when the run intentionally uses the source's separate `image_size` and
  `out_size`; use strict spatial validation for an exact-size custom contract.
- A 3D image and label must have identical `D`. `chunk` is a depth window, not
  another dimension. For a 3D item, `pt` must contain one point per slice.
- Built-in 2D images are normally `C=3`; REFUGE has two label channels in cup,
  disc order. Direct 3D adapters normally have `C=1` image and label.
- Do not call a `[2,H,W]` REFUGE label a decoder multimask result. It is two
  averaged rater-derived targets. Conversely, `-multimask_output` cannot repair
  a wrong number of target channels.

## Prompt or mask behavior is surprising

2D points from `random_click` are x/y coordinates. For a 3D custom item, use
`pt=[2,D]` with one point per slice and aligned `p_label` values. The source's
3D `generate_click_prompt` obtains row/column indices and reverses them only
for visualization; this is an implementation asymmetry, not evidence that a
blank mask is valid. Re-check the target values and coordinate convention with
the selected model.

The current core loop accesses `pack['image_meta_dict']['filename_or_obj']`
when naming visualizations. If a custom item omitted the README's nominally
optional metadata, add a stable case name rather than debugging it as a model
failure. Optional `box` fields are not consumed by the core prompt call.

## NIfTI, NRRD, or MONAI failures

- For Brat, KITS, Atlas, and SegRap, install/verify compatible `nibabel` and
  inspect a real NIfTI in the target environment. A JSON/NPZ declaration cannot
  prove affine, orientation, spacing, or label values.
- For LNQ, verify `SimpleITK` and the paired NRRDs; the marker PNG is not a
  substitute for a volume.
- For `decathlon`, verify MONAI/PyTorch compatibility, JSON path resolution,
  and post-transform dimensions. `LoadImaged`, `Orientationd`, `Spacingd`,
  `RandCropByPosNegLabeld`, cache creation, and device placement are not run by
  the safe helper.
- A missing dependency is unresolved until the intended CUDA environment is
  tested; a CPU import is not a substitute.

## Checkpoint path passes but loading fails

Keep the diagnosis separate from data layout. `-sam_ckpt` is the base
SAM-family checkpoint and `-weights` is the saved experiment wrapper. Confirm
network, encoder, mask-output count, and device match. The wrapper record is
expected to include `epoch`, `best_tol`, and `state_dict` (and normally
`optimizer`/`path_helper` for training). Do not infer compatibility from a
filename and do not deserialize an untrusted file during path-only preflight.

The parser's `-pretrain` option is declared as `bool` but is later used like a
path when truthy. Inspect or fix that interface before relying on it. Missing
base-model files must be reported, not auto-downloaded.

## CUDA or out-of-memory errors

1. Check `torch.cuda.is_available()`, selected `-gpu_device`, and one CUDA
   allocation. The core workflow has no supported CPU substitute.
2. For 2D, lower `-b`, then `-image_size`; reduce visualization pressure if
   needed.
3. For MONAI 3D, lower `-b`, `-chunk`, and `-num_sample`; during evaluation
   lower `-evl_chunk`. Keep `-evl_chunk` a divisor of post-transform depth when
   possible because the source loop can skip a tail remainder.
4. Re-run the sample declaration check after any shape-changing option. Do not
   remove `-thd`, change mask rank, or call a CPU run verified.

For command construction and adaptation choices, route to
[training](../../training/SKILL.md). For independent metrics and checkpoint
schema, route to [evaluation](../../evaluation/SKILL.md). For root-level
cross-workflow failures, use the root skill's shared troubleshooting reference.
