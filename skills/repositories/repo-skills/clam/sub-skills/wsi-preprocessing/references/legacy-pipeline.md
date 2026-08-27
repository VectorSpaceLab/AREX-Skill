# Legacy Saved-Patch Pipeline

The current CLAM README recommends `create_patches_fp.py` and `extract_features_fp.py`. The old `create_patches.py` plus `extract_features.py` path saves patch image data and coordinates during patching, which is slower and can consume much more storage. Use it only when a user explicitly needs saved patch images rather than coordinate `.h5` files loaded from WSIs during feature extraction.

## When Legacy Is Appropriate

Consider the legacy pipeline only if the user needs one of these outcomes:

- Inspect or reuse individual patch images outside CLAM feature extraction.
- Archive patch image bags because original WSI access will not be available later.
- Reproduce an older CLAM experiment that documented `create_patches.py` outputs.

Prefer the fast pipeline for normal CLAM training/evaluation workflows because CLAM models consume features, and fast feature extraction can read WSI regions from coordinate `.h5` files on demand.

## Command Shape

The legacy command mirrors the fast pipeline but calls `create_patches.py`:

```bash
python create_patches.py \
  --source DATA_DIRECTORY \
  --save_dir RESULTS_DIRECTORY \
  --patch_size 256 \
  --step_size 256 \
  --patch_level 0 \
  --preset bwh_biopsy.csv \
  --seg --patch --stitch
```

Legacy-only details:

- `create_patches.py` supports `--custom_downsample` with choices `1` or `2`; CLAM docs do not recommend it unless native downsamples are insufficient.
- Its patching parameters include `white_thresh` and `black_thresh` for blank/black patch exclusion.
- Its `.h5` outputs include patch image arrays along with coordinates, unlike fast coordinate-only bags.

## Risks and Guardrails

- Warn about storage before running legacy patching on many slides or small strides.
- Use a small pilot slide subset first by editing `process=1` for only selected rows in a copied process list.
- Keep `--stitch` optional; stitched images are QC artifacts and not required downstream.
- If the user only needs CLAM feature extraction, cross-link them to `../feature-extraction/SKILL.md` and keep preprocessing on `create_patches_fp.py`.
