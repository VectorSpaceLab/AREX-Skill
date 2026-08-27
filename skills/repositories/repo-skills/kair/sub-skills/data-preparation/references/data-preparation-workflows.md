# KAIR data-preparation workflows

Use these workflows as safe operating plans. The bundled scripts in this sub-skill are read-only. KAIR's original preparation helpers are treated as source evidence and command names only; several of them write, move, copy, or delete data and should not be run blindly.

## General preparation sequence

1. Identify the downstream owner:
   - Image training/testing needs image folders or paired image folders.
   - VRT/RVRT training usually needs LMDBs plus meta-info files.
   - VRT/RVRT testing usually needs frame folders and does not require LMDB.
2. Sketch the intended tree under `trainsets/` or `testsets/`.
3. Check the tree with the read-only checker:

   ```bash
   python sub-skills/data-preparation/scripts/check_dataset_layout.py image --root trainsets/trainH
   python sub-skills/data-preparation/scripts/check_dataset_layout.py video --root testsets/REDS4/sharp_bicubic --paired-root testsets/REDS4/GT
   python sub-skills/data-preparation/scripts/check_dataset_layout.py meta --meta-info data/meta_info/meta_info_REDS_GT.txt
   ```

4. For LMDB work, generate a plan first:

   ```bash
   python sub-skills/data-preparation/scripts/plan_lmdb_conversion.py --dataset reds
   ```

5. Only after the plan is reviewed should a user run a writer in their own KAIR checkout or write a short conversion script around KAIR's `make_lmdb_from_imgs(...)` helper.

## DIV2K subimages and LMDBs

### Intended input

```text
trainsets/DIV2K/
  DIV2K_train_HR/
  DIV2K_train_LR_bicubic/
    X2/
    X3/
    X4/
```

### Subimage plan

KAIR's hard-coded extraction helper crops large DIV2K images into overlapping patches. Distilled defaults:

| Folder | Output folder | Crop | Step | Notes |
| --- | --- | ---: | ---: | --- |
| `DIV2K_train_HR` | `DIV2K_train_HR_sub` | 480 | 240 | HR patches. |
| `DIV2K_train_LR_bicubic/X2` | `DIV2K_train_LR_bicubic/X2_sub` | 240 | 120 | Matches HR x2 scale. |
| `DIV2K_train_LR_bicubic/X3` | `DIV2K_train_LR_bicubic/X3_sub` | 160 | 80 | Matches HR x3 scale. |
| `DIV2K_train_LR_bicubic/X4` | `DIV2K_train_LR_bicubic/X4_sub` | 120 | 60 | Matches HR x4 scale. |

The source extraction logic removes `x2`, `x3`, `x4`, and `x8` from LR filenames before adding `_sNNN`, so patch keys should align across HR and LR scales.

Safety notes:

- The original extraction script exits if the save folder already exists.
- It writes many PNGs and uses multiprocessing; confirm disk and memory budget.
- It is better to run extraction on a copy or empty output folders.

### LMDB plan

After subimages exist, create LMDBs from flat patch folders:

```text
trainsets/DIV2K/DIV2K_train_HR_sub           -> trainsets/DIV2K/DIV2K_train_HR_sub.lmdb
trainsets/DIV2K/DIV2K_train_LR_bicubic/X2_sub -> trainsets/DIV2K/DIV2K_train_LR_bicubic_X2_sub.lmdb
trainsets/DIV2K/DIV2K_train_LR_bicubic/X3_sub -> trainsets/DIV2K/DIV2K_train_LR_bicubic_X3_sub.lmdb
trainsets/DIV2K/DIV2K_train_LR_bicubic/X4_sub -> trainsets/DIV2K/DIV2K_train_LR_bicubic_X4_sub.lmdb
```

Use nonrecursive PNG keys such as `0801_s001`. Generate the exact plan with:

```bash
python sub-skills/data-preparation/scripts/plan_lmdb_conversion.py --dataset div2k
```

## REDS for VRT/RVRT video SR and deblurring

### Intended folders

Training configs use LMDB paths, but source frames should first be arranged as clip folders:

```text
trainsets/REDS/
  train_sharp/
    000/00000000.png ...
  train_sharp_bicubic/
    000/00000000.png ...
trainsets/REDS_blur/
  train_blur/
    000/00000000.png ...
```

Testing uses frame folders directly:

```text
testsets/REDS4/
  GT/{000,011,015,020}/00000000.png ...
  sharp_bicubic/{000,011,015,020}/00000000.png ...
  blur/{000,011,015,020}/00000000.png ...
```

### Regrouping behavior

The REDS regrouping helper copies validation folders into the training folder with validation indices offset by 240. It uses shell `cp -r`. That is not destructive to validation data, but it can duplicate a large amount of data and can overwrite/merge if the destination already exists. Review the destination before running anything.

KAIR training excludes REDS4 validation clips (`000`, `011`, `015`, `020`) through `val_partition: REDS4` in configs, while the `official` partition uses `240` through `269`.

### LMDB and config-critical paths

The VRT/RVRT REDS video SR configs expect:

```text
dataroot_gt: trainsets/REDS/train_sharp_with_val.lmdb
dataroot_lq: trainsets/REDS/train_sharp_bicubic_with_val.lmdb
meta_info_file: data/meta_info/meta_info_REDS_GT.txt
io_backend.type: lmdb
filename_tmpl: 08d
filename_ext: png
```

The LMDB keys must match meta-info clip/frame keys such as `000/00000000`. If the bicubic source has an extra scale directory such as `train_sharp_bicubic/X4/000/00000000.png`, convert from the `X4` directory or flatten the tree before conversion; otherwise the LMDB keys become `X4/000/00000000` and will not match the config-generated keys.

Check before training:

```bash
python sub-skills/data-preparation/scripts/check_dataset_layout.py video --root testsets/REDS4/sharp_bicubic --paired-root testsets/REDS4/GT --min-frames 1
python sub-skills/data-preparation/scripts/check_dataset_layout.py meta --meta-info data/meta_info/meta_info_REDS_GT.txt
python sub-skills/data-preparation/scripts/plan_lmdb_conversion.py --dataset reds
```

## Vimeo90K for VRT/RVRT

### Intended folders

```text
trainsets/vimeo90k/
  vimeo_septuplet/
    sequences/00001/0001/im1.png ... im7.png
    sep_trainlist.txt
  vimeo_septuplet_matlabLRx4/
    sequences/00001/0001/im1.png ... im7.png
  vimeo_septuplet_BDLRx4/
    sequences/00001/0001/im1.png ... im7.png
```

Testing uses similar sequence folders under `testsets/vimeo90k/...` plus meta-info files such as `meta_info_Vimeo90K_test_GT.txt` or fast/medium/slow subsets.

### LR generation

Bicubic and blur-downsampled LR generation is MATLAB-only in the source workflow. Treat MATLAB scripts as reference-only because they require MATLAB and carry local path assumptions. If the user lacks MATLAB, use an explicitly reviewed Python/OpenCV or BasicSR-compatible generator, then verify the sequence layout and frame counts.

### LMDB plan

KAIR LMDB key conventions:

- LQ BI: `00001/0001/im1` through `im7` from `vimeo_septuplet_matlabLRx4/sequences`.
- LQ BD: `00001/0001/im1` through `im7` from `vimeo_septuplet_BDLRx4/sequences`.
- GT all-frame LMDB for VRT/RVRT configs: keys `00001/0001/im1` through `im7` from clean `vimeo_septuplet/sequences`.
- Some source helper logic keeps only `im4` for a center-frame GT LMDB; that is insufficient for configs that name `vimeo90k_train_GT_all.lmdb`.

Plan command:

```bash
python sub-skills/data-preparation/scripts/plan_lmdb_conversion.py --dataset vimeo90k
```

## DVD video deblurring layout

Original DVD quantitative data is arranged like:

```text
quantitative_datasets/
  720p_240fps_1/
    GT/00000.jpg ...
    input/00000.jpg ...
```

KAIR training/testing expects REDS-like paired clip folders, for example:

```text
trainsets/DVD/
  train_GT/720p_240fps_1/00000.jpg ...
  train_GT_blurred/720p_240fps_1/00000.jpg ...
testsets/DVD10/
  test_GT/clip/00000.jpg ...
  test_GT_blurred/clip/00000.jpg ...
```

The source preparation helper moves `GT` and `input` folders and removes the old clip folders. That is destructive. Work on a copy, confirm the output names, and generate/check meta-info before LMDB conversion.

Meta-info lines use five-digit JPEG starts, for example:

```text
720p_240fps_1 100 (720,1280,3) 00000
```

Plan command:

```bash
python sub-skills/data-preparation/scripts/plan_lmdb_conversion.py --dataset dvd
```

## GoPro video deblurring layout

Original GoPro Large clips have `sharp` and `blur` subfolders under train/test clips. KAIR expects:

```text
trainsets/GoPro/
  train_GT/GOPR0372_07_00/000047.png ...
  train_GT_blurred/GOPR0372_07_00/000047.png ...
testsets/GoPro11/
  test_GT/clip/000001.png ...
  test_GT_blurred/clip/000001.png ...
```

The source helper moves `sharp` to `*_GT`, moves `blur` to `*_GT_blurred`, then removes the original `train` or `test` folder. Treat it as destructive and run only on a prepared copy.

Meta-info examples:

```text
GOPR0372_07_00 100 (720,1280,3) 000047
```

Plan command:

```bash
python sub-skills/data-preparation/scripts/plan_lmdb_conversion.py --dataset gopro
```

## DAVIS video denoising layout

For video denoising, clean DAVIS frames are used as GT and as the clean source for generated noise:

```text
trainsets/DAVIS/
  train_GT/bear/00000.jpg ...
testsets/DAVIS-test/
  bear/00000.jpg ...
```

The source meta generator scans `train_GT/*`, records frame counts and start frames, and asserts the expected DAVIS training frame total. Training configs use the same LMDB for `dataroot_gt` and `dataroot_lq` in nonblind denoising.

Plan command:

```bash
python sub-skills/data-preparation/scripts/plan_lmdb_conversion.py --dataset davis
```

## UDM10 and Vid4 video SR testing

UDM10 is used mostly as a BDx4 VSR test set. The source UDM10 helper moves `truth` folders into `GT` and `blur4` folders into `BDx4`, then removes the original per-clip folder. Treat it as destructive.

Expected test layout:

```text
testsets/UDM10/
  GT/clip/frame.png ...
  BDx4/clip/frame.png ...

testsets/Vid4/
  GT/clip/frame.png ...
  BIx4/clip/frame.png ...
  BDx4/clip/frame.png ...
```

LMDB is usually unnecessary for test-only UDM10/Vid4 use.

## Set8 video denoising

Set8 is normally a test-time frame-folder dataset:

```text
testsets/Set8/
  tractor/frame.png ...
  touchdown/frame.png ...
  park_joy/frame.png ...
```

Use the same root for LQ and GT when the model/test script injects Gaussian noise. LMDB conversion is not normally needed for Set8.

## MATLAB scripts are reference-only

KAIR includes MATLAB scripts for Vimeo LR generation, UDM10 blur/downsample generation, and video deblurring evaluation. They are not bundled as runtime helpers because they require MATLAB and assume local dataset paths. Preserve the intent instead:

- Use MATLAB or an equivalent reviewed generator to create LR folders.
- Verify output frame counts and naming with the read-only checker.
- For final model metrics, route model execution to `../video-restoration/SKILL.md`; this sub-skill only verifies that the expected folders exist.

## Source-script decisions

| Source helper | Runtime decision | Reason |
| --- | --- | --- |
| `create_lmdb.py` | Adapted into `scripts/plan_lmdb_conversion.py` and this reference. | The source CLI writes LMDBs, has hard-coded paths, exits if the target exists, and can use high-memory multiprocessing. |
| `extract_subimages.py` | Distilled into DIV2K guidance. | It writes many patch files and has hard-coded DIV2K paths. |
| `regroup_reds_dataset.py` | Reference-only with warnings. | It copies validation folders and can duplicate/merge large trees. |
| `prepare_DVD.py` | Reference-only with warnings. | It moves folders and removes original clip directories. |
| `prepare_GoPro_as_video.py` | Reference-only with warnings. | It moves `sharp`/`blur` folders and removes original `train`/`test` folders. |
| `prepare_UDM10.py` | Reference-only with warnings. | It moves folders and removes original clip directories. |
| `prepare_DAVIS.py` | Reference-only meta-info behavior. | It writes meta-info and asserts a fixed frame total; path assumptions should be reviewed. |
| MATLAB scripts | Reference-only. | MATLAB dependency and local path assumptions. |
