# Workflows

## 1) Validate a custom pair file

Use the bundled validator before any batch run:

```bash
python scripts/validate_pair_file.py \
  --pair-file <pairs.txt> \
  --input-dir <images_dir>
```

Add `--require-gt` when you plan to run `--eval`.
That catches bad token counts, rotation mistakes, and broken matrix fields early.

## 2) Run a bounded smoke check

```bash
python scripts/run_pair_matching_smoke.py \
  --repo-root <repo-root> \
  --output-dir <outdir> \
  --device cpu \
  --max-length 1 \
  --resize 320 240
```

This is the safest way to confirm the local environment, manifest, and output layout.

## 3) Indoor batch matching

```bash
python match_pairs.py \
  --input_pairs assets/scannet_sample_pairs_with_gt.txt \
  --input_dir assets/scannet_sample_images \
  --output_dir dump_match_pairs_indoor \
  --resize 640 \
  --superglue indoor \
  --max_keypoints 1024 \
  --nms_radius 4
```

Add `--eval` if you want pose metrics and the manifest has 38-token rows.

## 4) Outdoor batch matching

```bash
python match_pairs.py \
  --input_pairs assets/phototourism_sample_pairs.txt \
  --input_dir assets/phototourism_sample_images \
  --output_dir dump_match_pairs_outdoor \
  --resize 1600 \
  --resize_float \
  --superglue outdoor \
  --max_keypoints 2048 \
  --nms_radius 3 \
  --viz
```

This is the right profile for large outdoor scenes and long baselines.

## 5) Match plus pose evaluation

```bash
python match_pairs.py \
  --input_pairs assets/scannet_sample_pairs_with_gt.txt \
  --input_dir assets/scannet_sample_images \
  --output_dir dump_match_pairs_eval \
  --eval \
  --viz
```

Use this when you need `AUC@5/10/20`, `Prec`, and `MScore`.

## 6) Cache-safe rerun

```bash
python match_pairs.py ... --cache
```

Use cache only when the settings are unchanged.
If you change resize, weights, thresholds, or image inputs, create a new output directory or delete the old `.npz` files first.

## 7) Visualization choices

- High-quality figures: `--viz --viz_extension pdf`
- Faster rendering: `--viz --fast_viz`
- OpenCV preview window: `--viz --fast_viz --opencv_display`

Remember the constraints from the CLI reference.

## 8) Full dataset caution

The bundled sample manifests are tiny and are not the full paper benchmarks.
For full ScanNet, YFCC, or Phototourism runs, you need the external datasets plus the curated manifests that match the expected folder layout.
