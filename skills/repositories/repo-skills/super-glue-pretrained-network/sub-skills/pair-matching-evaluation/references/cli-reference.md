# CLI Reference

This sub-skill centers on `match_pairs.py`, the batch pair runner for matching, optional pose evaluation, and visualization.
Use the bundled smoke wrapper for a one-pair check; use the full CLI when you need all flags.

## Canonical command shapes

```bash
python match_pairs.py --input_pairs <pairs.txt> --input_dir <images_dir> --output_dir <outdir>
python match_pairs.py --input_pairs <pairs.txt> --input_dir <images_dir> --output_dir <outdir> --eval
python match_pairs.py --input_pairs <pairs.txt> --input_dir <images_dir> --output_dir <outdir> --viz --fast_viz
```

## Path and run control

- `--input_pairs`:
  Text manifest of image pairs. Default: `assets/scannet_sample_pairs_with_gt.txt`.
- `--input_dir`:
  Directory that contains the images referenced by the manifest. Default: `assets/scannet_sample_images/`.
- `--output_dir`:
  Directory that receives `.npz` outputs and optional visualizations. Default: `dump_match_pairs/`.
- `--max_length`:
  Maximum number of pairs to process. The code default is `-1` (no limit).
- `--shuffle`:
  Deterministically shuffles the loaded pairs with a fixed seed of 0.
- `--cache`:
  Reuses existing `.npz` outputs when they already exist and load cleanly.

## Resize and preprocessing

- `--resize`:
  Accepts one or two integers.
  - `W H` -> resize to exact width and height
  - `N` -> resize the largest dimension to `N`
  - `-1` -> keep original size
- `--resize_float`:
  Casts images to float before resizing. Recommended for large outdoor images.

The parser default is `640 480`.
For the paper-style indoor recipe, the README recommends `--resize 640` with indoor weights.
For the outdoor recipe, use `--resize 1600 --resize_float`.

## Matching parameters

- `--superglue {indoor,outdoor}`:
  Selects the pretrained weights. Default: `indoor`.
- `--max_keypoints`:
  SuperPoint keypoint cap. Default: `1024`.
- `--keypoint_threshold`:
  SuperPoint confidence threshold. Default: `0.005`.
- `--nms_radius`:
  SuperPoint NMS radius. Default: `4`.
- `--sinkhorn_iterations`:
  SuperGlue Sinkhorn iterations. Default: `20`.
- `--match_threshold`:
  SuperGlue match threshold. Default: `0.2`.

## Visualization and evaluation

- `--viz`:
  Saves match visualizations.
- `--eval`:
  Runs pose evaluation and saves per-pair evaluation `.npz` files.
  Every row in the pair file must then have 38 tokens.
- `--fast_viz`:
  Uses the OpenCV renderer instead of Matplotlib.
- `--viz_extension {png,pdf}`:
  Output extension for viz images. Default: `png`.
- `--opencv_display`:
  Opens an OpenCV preview window while saving results.
- `--show_keypoints`:
  Adds the detected keypoints to the visualization.

## Device selection

- The underlying script uses CUDA automatically when `torch.cuda.is_available()` is true.
- `--force_cpu` overrides that behavior and forces CPU mode.
- The smoke wrapper exposes a `--device {auto,cpu,cuda}` choice and translates `cpu` to `--force_cpu`.

## Flag constraints

These assertions are enforced by the script:

- `--opencv_display` requires `--viz`.
- `--opencv_display` also requires `--fast_viz`.
- `--fast_viz` requires `--viz`.
- `--fast_viz` cannot be combined with `--viz_extension pdf`.
- `--eval` requires 38-token rows in the manifest.

## Recommended profiles

### Indoor

```bash
python match_pairs.py \
  --resize 640 \
  --superglue indoor \
  --max_keypoints 1024 \
  --nms_radius 4
```

### Outdoor

```bash
python match_pairs.py \
  --resize 1600 \
  --superglue outdoor \
  --max_keypoints 2048 \
  --nms_radius 3 \
  --resize_float
```

## Smoke wrapper

For a bounded local check, prefer:

```bash
python scripts/run_pair_matching_smoke.py --repo-root <repo-root> --output-dir <outdir>
```

Add `--device cpu` for a strict CPU run or `--device cuda` to require a visible GPU.
