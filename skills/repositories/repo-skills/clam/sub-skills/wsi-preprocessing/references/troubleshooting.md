# WSI Preprocessing Troubleshooting

## OpenSlide or Native Library Failures

Symptoms include `openslide` import errors, missing shared libraries, unsupported vendor messages, or failures while opening a slide. Confirm that the runtime environment includes OpenSlide and `openslide-python`, and that the slide extension/vendor is supported by OpenSlide. If the slide path exists but cannot be opened, try a known-good WSI first to separate environment issues from corrupted or unsupported files.

## Missing Source or Save Directory

`--source` must be a directory containing slide files, not a CSV. `--save_dir` is the output root where CLAM creates `masks/`, `patches/`, and `stitches/`. `--process_list` is resolved under `--save_dir`, so pass only a filename such as `process_list_review.csv` after copying/editing it there.

## Slides Skipped Unexpectedly

Common causes:

- `process=0` in the process list means the row is not selected for the next run.
- Existing `patches/<slide_id>.h5` files are skipped by default and get `status=already_exist`.
- Include `--no_auto_skip` only when the user intentionally wants to rerun patch generation for slides with existing `.h5` files.
- If only `--seg` is passed, CLAM saves masks/process-list updates but does not create new coordinate `.h5` files.

## `failed_seg` or Segmentation Level Too Large

`create_patches_fp.py` aborts segmentation for a slide when the chosen segmentation level has width × height greater than `1e8`, marking `status=failed_seg`. Use `seg_level=-1` to choose the OpenSlide level nearest 64x downsample, or manually choose a lower-resolution level after inspecting available pyramid levels with slide tooling. Avoid forcing level `0` for segmentation on very large slides.

## Poor Tissue Mask

Tuning options:

- Increase `sthresh` to classify less foreground; decrease it when tissue is missing.
- Set `use_otsu=True` for slides with variable staining or backgrounds.
- Increase `mthresh` to smooth speckle; keep it odd.
- Increase `close` to bridge gaps; lower it if tissue regions merge too aggressively.
- Lower `a_t` for small biopsies; raise it to remove small debris.
- Adjust `a_h` and `max_n_holes` when holes/vessels are over- or under-excluded.
- Use `keep_ids` and `exclude_ids` after reviewing mask contours when global thresholds cannot isolate desired tissue.

## Preset File Mistakes

Preset CSVs should include one row with CLAM parameter columns. For fast preprocessing, important columns are `seg_level`, `sthresh`, `mthresh`, `close`, `use_otsu`, `keep_ids`, `exclude_ids`, `a_t`, `a_h`, `max_n_holes`, `vis_level`, `line_thickness`, `use_padding`, and `contour_fn`. Existing CLAM presets also include `white_thresh` and `black_thresh` for compatibility with the legacy saved-patch pipeline. From this reference directory, use `../scripts/build_preset_template.py` to avoid misspelled or missing columns.

## Missing Output Files

- No `masks/` images: ensure `--seg` is set; the fast script saves mask QC images when processing rows.
- No `patches/*.h5`: ensure `--patch` is set, rows have `process=1`, and existing files are not being skipped.
- No `stitches/` images: ensure `--stitch` is set and matching `.h5` files exist under `patches/`.
- Empty or missing coordinate bags can result from no detected tissue contours, too strict `contour_fn`, too high `a_t`, or mask thresholds that remove tissue.

## Legacy Storage Blowups

The legacy `create_patches.py` pipeline stores patch image data and coordinates, so output size grows quickly with slide area, small `step_size`, and low `patch_level`. Prefer `create_patches_fp.py` unless saved patch images are explicitly required. If legacy is unavoidable, pilot a few slides with a copied process list before scaling up.
