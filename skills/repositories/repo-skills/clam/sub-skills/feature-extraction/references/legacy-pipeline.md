# Legacy Saved-Patch Pipeline

The current CLAM workflow uses `create_patches_fp.py` plus `extract_features_fp.py`: patching stores coordinates, and feature extraction reads image regions from WSIs on demand. The older `create_patches.py` plus `extract_features.py` workflow saved image patches into HDF5 files and is storage-heavy.

Use this reference only when maintaining an older project whose patch HDF5 files contain saved images rather than coordinates.

## Legacy Command Shape

```bash
python extract_features.py \
  --data_dir DIR_TO_PATCH_BAGS \
  --csv_path CSV_FILE_NAME \
  --feat_dir FEATURES_DIRECTORY \
  --model_name resnet50_trunc \
  --batch_size 256 \
  --slide_ext .svs \
  --target_patch_size 224 \
  --no_auto_skip
```

The legacy script expects `DIR_TO_PATCH_BAGS/patches/<slide_id>.h5` and uses `Whole_Slide_Bag`, which reads an `imgs` dataset plus `coords` from each HDF5 file. It does not need `--data_slide_dir` because the images are already saved in the patch bags.

## Important Differences From Fast Extraction

- Fast extraction reads `coords` from coordinate HDF5 files and opens the original WSI files during feature extraction.
- Legacy extraction reads stored patch images from an `imgs` dataset and does not open WSI files.
- Fast extraction creates both `h5_files/` and `pt_files/` output directories before writing outputs.
- Legacy extraction writes to `feat_dir/h5_files/` and `feat_dir/pt_files/`; if maintaining this path, pre-create those subdirectories before running.
- The legacy path can be brittle in current CLAM code because it is no longer the recommended workflow; prefer regenerating coordinate files and using `extract_features_fp.py` when practical.

## Migration Advice

If a user has raw WSIs available, route them to `../wsi-preprocessing/SKILL.md` to regenerate fast coordinate files, then return to this sub-skill's `workflows.md` reference for feature extraction. Keep legacy saved-patch bags only when raw slides are unavailable or project reproducibility requires the old artifacts.
