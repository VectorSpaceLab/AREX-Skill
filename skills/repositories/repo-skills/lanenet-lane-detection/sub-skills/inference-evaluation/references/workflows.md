# LaneNet Inference and Evaluation Workflows

This reference covers checkpoint-backed inference and evaluation only. Create datasets in `../data-preparation/`, create checkpoints in `../training/`, and export frozen models in `../model-export/`.

## Environment and run directory

LaneNet source imports are repo-root-relative: the config loader reads `./config/tusimple_lanenet.yaml`, and the default postprocessor remap path is `./data/tusimple_ipm_remap.yml`. In normal use, run from the repository root, or pass `--repo_root` to the bundled scripts so they can change to the correct working directory before importing LaneNet modules.

Verified runtime facts for this repo skill:

- TensorFlow 1.15 with CUDA is verified and preferred for throughput.
- CPU inference/evaluation is functionally supported because the graph uses standard TensorFlow ops, but it is slower.
- Default GPU session knobs are `GPU_MEMORY_FRACTION=0.9` and `TF_ALLOW_GROWTH=True`.
- Default DBSCAN knobs are `DBSCAN_EPS=0.35` and `DBSCAN_MIN_SAMPLES=1000`.
- The default model front-end is `bisenetv2`; checkpoint variables must match the front-end and training configuration.

## Checkpoint and weights expectations

`--weights_path` should normally point to the TensorFlow checkpoint base path, for example `weights/tusimple_lanenet/model.ckpt-12345`. Do not pass only a directory unless the wrapper can resolve a latest checkpoint from it, and do not pass the `.index`, `.meta`, or `.data-00000-of-00001` shard unless the wrapper strips the suffix for you.

A usable checkpoint usually has files like:

```text
model.ckpt-12345.index
model.ckpt-12345.meta
model.ckpt-12345.data-00000-of-00001
checkpoint
```

Pretrained weights are not bundled. If the user asks for pretrained inference, have them provide a local checkpoint they downloaded separately, or route checkpoint creation to `../training/`.

### Saver modes

The original single-image test path restores exponential-moving-average variables, while the original batch evaluator restores raw variables. This skill's wrappers expose `--use_moving_average` to make the restore mode explicit:

- Single-image wrapper default: `--use_moving_average 1`, matching the original test behavior.
- Batch-evaluation wrapper default: `--use_moving_average 0`, matching the original evaluator behavior.

If restore fails with missing variables, retry the other saver mode only after confirming the checkpoint was trained with the same front-end and embedding dimension.

## Single-image inference

Use this workflow for a single RGB road image and a LaneNet checkpoint.

```bash
python <skill-dir>/scripts/test_lanenet.py \
  --repo_root . \
  --image_path data/tusimple_test_image/0.jpg \
  --weights_path weights/tusimple_lanenet/model.ckpt-12345 \
  --with_lane_fit 1 \
  --save_dir outputs/lanenet-single \
  --show 0
```

Exact core arguments:

| Argument | Meaning |
| --- | --- |
| `--image_path` | Input image path. The script reads it with OpenCV in BGR order. |
| `--weights_path` | TensorFlow checkpoint base path or checkpoint directory. |
| `--with_lane_fit` | Boolean; `1` fits TuSimple-style lane curves, `0` overlays clustered masks directly. |

Useful wrapper-only safety arguments:

| Argument | Meaning |
| --- | --- |
| `--repo_root` | Repository root used for imports, config, and remap resolution. Defaults to current directory. |
| `--save_dir` | Directory for noninteractive outputs. If omitted, no images are written. |
| `--show` | Boolean; display Matplotlib windows only when a GUI is safe. Defaults to `0`. |
| `--loop_times` | Number of graph forward passes for timing. Use `1` for smoke checks; use larger values for benchmarking. |
| `--use_moving_average` | Restore moving-average variables when `1`; raw variables when `0`. |
| `--ipm_remap_file` | Remap YAML path used by the postprocessor. Defaults to the TuSimple remap file. |
| `--force_cpu` | Hide CUDA devices for a CPU-only functional check. |

### Preprocessing performed by the script

The single-image script mirrors the repository test path:

1. Read the source image with OpenCV.
2. Keep an unresized copy for visualization and lane-fit overlay.
3. Resize the network input to width `512`, height `256`.
4. Normalize each pixel as `image / 127.5 - 1.0`.
5. Feed a TensorFlow placeholder with shape `[1, 256, 512, 3]`.

### Graph outputs

`LaneNet.inference(...)` returns two tensors:

- `binary_seg_ret`: predicted binary lane/non-lane class map, later displayed as `binary_seg * 255`.
- `instance_seg_ret`: per-pixel embedding map with `EMBEDDING_FEATS_DIMS` channels, default `4`, used for DBSCAN clustering.

The postprocessor consumes both outputs. It first morphologically closes the binary mask and removes connected components smaller than `MIN_AREA_THRESHOLD`, then clusters embedding features with DBSCAN. With lane fit enabled, it fits second-order lane curves in TuSimple geometry and draws lane points on the source image.

### Saved outputs from the bundled wrapper

When `--save_dir` is provided, expect:

| File | Meaning |
| --- | --- |
| `source_image.png` | Original input image copy. |
| `binary_image.png` | Binary segmentation prediction scaled to 0/255. |
| `instance_embedding.png` | First three embedding channels min-max scaled for visualization. |
| `mask_image.png` | DBSCAN-clustered lane mask at network resolution, if clustering succeeds. |
| `source_overlay.png` | Source image with fitted lane points or direct mask overlay, if postprocess succeeds. |
| `postprocess_summary.json` | Shapes, checkpoint path used, fit count, and output-file list. |

A successful run should log image load, checkpoint restore, average inference time, and a postprocess summary. If `mask_image` or `source_overlay` is absent, read the troubleshooting reference before assuming the checkpoint is bad.

## Custom-image inference

For images not drawn from TuSimple geometry, start without lane fitting:

```bash
python <skill-dir>/scripts/test_lanenet.py \
  --repo_root . \
  --image_path path/to/custom_road_image.jpg \
  --weights_path weights/custom_or_pretrained/model.ckpt-12345 \
  --with_lane_fit 0 \
  --save_dir outputs/custom-no-fit \
  --show 0
```

Use `--with_lane_fit 0` because fitted lanes are hard-coded for the TuSimple data source and remap geometry. Inspect `binary_image.png` and `mask_image.png` first. If the binary image contains lane pixels but the mask is empty or black, tune DBSCAN. A common custom-data adjustment from repo evidence is increasing `DBSCAN_EPS` from `0.35` to around `0.5` and reducing `DBSCAN_MIN_SAMPLES` from `1000` toward `250`; treat those as starting points, not universal values.

For persistent custom-data tuning, edit the runtime config in the repo checkout or create a separate config copy before running. Do not change the bundled skill files just to tune a user's experiment.

## TuSimple batch evaluation/inference

Use this workflow to run inference over a TuSimple test image tree and save overlays.

```bash
python <skill-dir>/scripts/evaluate_lanenet_on_tusimple.py \
  --repo_root . \
  --image_dir TUSIMPLE_ROOT/test_set/clips \
  --weights_path weights/tusimple_lanenet/model.ckpt-12345 \
  --save_dir outputs/tusimple-test-output
```

Exact core arguments:

| Argument | Meaning |
| --- | --- |
| `--image_dir` | Directory searched recursively for `*.jpg`; for standard behavior it must include a `clips` path component. |
| `--weights_path` | TensorFlow checkpoint base path or checkpoint directory. |
| `--save_dir` | Output root for postprocessed source-overlay images. |

Useful wrapper-only safety arguments:

| Argument | Meaning |
| --- | --- |
| `--repo_root` | Repository root used for imports, config, and remap resolution. |
| `--max_images` | Optional cap for smoke checks. |
| `--allow_non_tusimple_layout` | If `1`, save paths relative to `--image_dir` even when no `clips` component exists. Defaults to strict TuSimple validation. |
| `--skip_existing` | If `1`, keep existing output images instead of overwriting. |
| `--use_moving_average` | Restore moving-average variables when `1`; raw variables when `0`. |
| `--with_lane_fit` | Usually keep `1` for TuSimple; use `0` for custom non-TuSimple layouts. |
| `--force_cpu` | Hide CUDA devices for a CPU-only functional check. |

### Batch output path behavior

For a standard TuSimple path such as:

```text
TUSIMPLE_ROOT/test_set/clips/0530/1492626047222176976_0/20.jpg
```

The evaluator saves:

```text
SAVE_DIR/0530/1492626047222176976_0/20.jpg
```

The original path logic assumes the string `clips` exists in every image path. The bundled wrapper validates this upfront so failures are easier to diagnose. For small synthetic smoke trees that do not mimic TuSimple, pass `--allow_non_tusimple_layout 1` and read the saved relative paths carefully.

### Batch validation signals

A healthy batch run should show:

- A nonzero image count found under `--image_dir`.
- A successful checkpoint restore.
- Periodic mean inference-time logs.
- Saved `.jpg` overlays under `--save_dir` preserving the post-`clips` subdirectory structure.
- Optional JSONL summary records when `--summary_jsonl` is left enabled.

## Output interpretation checklist

Use this order when debugging quality:

1. `binary_image.png`: if fully black, the model did not predict lane pixels after preprocessing. Check checkpoint/domain, image normalization, and resize assumptions before DBSCAN tuning.
2. `instance_embedding.png`: if constant or noisy while binary output has lanes, suspect checkpoint/architecture mismatch or poor embedding training.
3. `mask_image.png`: if absent or black while binary output has lanes, inspect DBSCAN settings and `MIN_AREA_THRESHOLD`.
4. `source_overlay.png`: if mask exists but overlay/fitted lanes are wrong, disable lane fit for custom data or verify the TuSimple remap file and geometry.
5. Fit parameter logs: with lane fit enabled, each detected lane reports a second-order polynomial parameter vector. Few or no fit parameters can be normal for poor clustering; malformed values point to wrong remap/geometry.
