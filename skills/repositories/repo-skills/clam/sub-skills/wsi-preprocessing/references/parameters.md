# WSI Preprocessing Parameters

`create_patches_fp.py` combines CLI flags with preset/process-list columns. The CLI controls paths and high-level stages; presets and process lists control segmentation, filtering, visualization, and patch inclusion details.

## CLI Flags

| Flag | Default | Use |
| --- | --- | --- |
| `--source` | none | Directory of raw WSI files readable by OpenSlide. |
| `--save_dir` | none | Output root containing `masks/`, `patches/`, `stitches/`, and `process_list_autogen.csv`. |
| `--patch_size` | `256` | Pixel size of each patch at `--patch_level`. |
| `--step_size` | `256` | Coordinate stride at `--patch_level`; match `--patch_size` for non-overlap. |
| `--patch_level` | `0` | OpenSlide pyramid level used for coordinate generation; `0` is highest resolution. |
| `--seg` | off | Run tissue segmentation and mask visualization. |
| `--patch` | off | Save `.h5` coordinate files under `patches/`. |
| `--stitch` | off | Save downsampled stitch QC images when matching `.h5` files exist. |
| `--preset` | none | Load default parameters from a named preset CSV. |
| `--process_list` | none | Load an editable process CSV from inside `--save_dir`. |
| `--no_auto_skip` | off | Disable the default skip of slides with existing `patches/<slide_id>.h5`. |

`--no_auto_skip` is inverted in source: the parser stores `False` when the flag is present, and that value is passed as `auto_skip`. In user terms, omit `--no_auto_skip` to preserve existing `.h5` files; include it to reprocess and overwrite/regenerate coordinate bags.

## Segmentation Columns

These columns appear in presets and `process_list_autogen.csv`.

| Column | Source default | Meaning and tuning guidance |
| --- | --- | --- |
| `seg_level` | `-1` | Level used for segmentation. `-1` asks OpenSlide for the level nearest 64x downsample, or `0` if the slide has one level. Avoid levels whose width × height exceeds `1e8`; CLAM marks them `failed_seg`. |
| `sthresh` | `8` | HSV saturation threshold. Higher values usually detect less foreground and more background. Ignored when `use_otsu=True`. |
| `mthresh` | `7` | Median filter size before thresholding. Use positive odd integers. Increase to smooth speckled masks. |
| `close` | `4` | Morphological closing kernel after thresholding. Increase to bridge small gaps; set `0` or negative to avoid closing. |
| `use_otsu` | `False` | Use Otsu thresholding instead of the fixed `sthresh`. Helpful when staining/background varies across slides. |
| `keep_ids` | `none` | Comma-separated contour indices to keep after reviewing masks, or `none`. |
| `exclude_ids` | `none` | Comma-separated contour indices to remove after reviewing masks, or `none`. |

## Contour Filtering Columns

CLAM scales `a_t` and `a_h` relative to a 512 × 512 reference patch at level 0, then applies the thresholds at the selected segmentation level.

| Column | Source default | Meaning and tuning guidance |
| --- | --- | --- |
| `a_t` | `100` | Minimum foreground contour area. Lower it for small biopsies; raise it to remove tiny artifacts. |
| `a_h` | `16` | Minimum hole/cavity area to exclude. Lower it when holes should be removed aggressively; raise it when vessel/lumen-like holes should remain tissue. |
| `max_n_holes` | `8` | Maximum holes kept per foreground contour. Higher can improve exclusion detail but costs more compute. |

Preset examples from CLAM evidence:

| Preset | Typical use | Key differences |
| --- | --- | --- |
| `bwh_biopsy.csv` | BWH biopsy slides | Lower `a_t=1`, `a_h=1`, `max_n_holes=2`, `close=2`, `line_thickness=50`. |
| `bwh_resection.csv` | BWH resection slides | Larger tissue/hole filters, `a_t=100`, `a_h=16`, `close=4`. |
| `tcga.csv` | TCGA slides | Moderate filters, `a_t=16`, `a_h=4`, default thresholding. |

## Visualization Columns

| Column | Source default | Meaning and tuning guidance |
| --- | --- | --- |
| `vis_level` | `-1` | Level for mask QC visualization. `-1` chooses the level nearest 64x downsample, or `0` for single-level slides. |
| `line_thickness` | `250` | Contour line thickness in level-0 pixel units. Lower values can be easier to inspect on biopsy presets. |

The source function default shows `line_thickness=500`, but the CLI path initializes `250`; generated commands should assume CLI behavior unless calling the function directly.

## Patching Columns

Fast coordinate patching writes coordinates and attributes to `.h5`, not patch image tiles.

| Column | Source default | Meaning and tuning guidance |
| --- | --- | --- |
| `use_padding` | `True` | Include candidate positions up to contour bounds even if the patch extends beyond slide bounds. Use `False` to avoid padded border patches. |
| `contour_fn` | `four_pt` | Foreground check: `four_pt`, `four_pt_hard`, `center`, or `basic`. `four_pt` checks four shifted points near the patch center; `center` is more permissive; `basic` checks the top-left point. |

`build_preset.py` still exposes `white_thresh` and `black_thresh` because the old saved-patch pipeline used image-content filtering. The fast `create_patches_fp.py` process list does not use those two columns for coordinate selection.

## Process List Columns and Semantics

`process_list_autogen.csv` includes at least:

```text
slide_id,process,status,seg_level,sthresh,mthresh,close,use_otsu,keep_ids,exclude_ids,a_t,a_h,max_n_holes,vis_level,line_thickness,use_padding,contour_fn
```

Important semantics:

- `slide_id` is the filename from `--source`, including extension.
- `process=1` means include the slide in the next run; after processing, CLAM sets the row back to `0`.
- `status` starts as `tbp`, becomes `processed`, `already_exist`, or `failed_seg` depending on the run.
- `--process_list process_list_review.csv` resolves to `SAVE_DIR/process_list_review.csv`; it is not read from the WSI source directory.
- If `--patch` is set and `patches/<slide_id_without_extension>.h5` already exists, CLAM skips that slide unless `--no_auto_skip` is present.
- Copy the autogenerated CSV before manual editing because CLAM rewrites `process_list_autogen.csv` during processing.
