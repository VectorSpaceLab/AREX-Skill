# Inference and Evaluation Troubleshooting

Use this reference when checkpoint inference or TuSimple evaluation fails. Keep fixes scoped to inference/evaluation; route data generation to `../data-preparation/`, checkpoint creation to `../training/`, and frozen export to `../model-export/`.

## Quick triage order

1. Validate `--repo_root` or current directory: the source tree must contain `lanenet_model/`, `local_utils/`, `config/`, and the TuSimple remap file.
2. Validate `--weights_path`: use a checkpoint base path or a directory with a resolvable latest checkpoint.
3. Validate the image path or image tree and ensure OpenCV can read at least one image.
4. Run single-image inference with `--save_dir` and `--show 0`; inspect binary, embedding, mask, and overlay files separately.
5. If the binary output has lane pixels but the mask is empty, tune DBSCAN/postprocess. If the binary output is black, investigate checkpoint/domain/preprocessing first.

## Common failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `No checkpoint found` or missing `.index`/`.data` files | `--weights_path` points to a nonexistent path, a download was not extracted, or only one checkpoint shard was copied. | Provide the checkpoint base path such as `model.ckpt-12345`, or pass the directory containing the TensorFlow `checkpoint` state and shard files. Do not assume pretrained weights are bundled. |
| TensorFlow restore `NotFoundError`, `Key ... not found in checkpoint`, or shape mismatch | Checkpoint was trained with different front-end/config, different embedding dimension, or different saver mode. Single-image testing defaults to moving-average restore; batch evaluation defaults to raw restore. | Confirm `MODEL.FRONT_END` and `MODEL.EMBEDDING_FEATS_DIMS` match the checkpoint. Retry `--use_moving_average 0` or `1` as appropriate. If both fail, route checkpoint creation/compatibility to `../training/`. |
| Import/config error for `./config/tusimple_lanenet.yaml` | Script was run from the wrong working directory and repo-root-relative config loading failed. | Run from repo root or pass `--repo_root` to the bundled wrapper. Avoid editing the skill's bundled scripts just to change experiment paths. |
| Assertion that remap file does not exist | `LaneNetPostProcessor` constructor requires the IPM remap file path even when lane fit is disabled. | Run from repo root, restore the TuSimple remap YAML into the expected data path, or pass `--ipm_remap_file` to a readable remap file. |
| Black or empty `binary_image.png` | Model predicted no lane pixels after preprocessing, often due to wrong checkpoint, custom domain shift, bad image read, or mismatched preprocessing. | Verify OpenCV reads the image, confirm resize/normalization are `512x256` and `image / 127.5 - 1.0`, check checkpoint compatibility, and try a known TuSimple sample image before changing DBSCAN. |
| `mask_image.png` missing or black while binary output has lanes | DBSCAN found no stable lane clusters after connected-component filtering. Defaults can be too strict for custom data. | Tune `POSTPROCESS.DBSCAN_EPS` upward from `0.35` and reduce `POSTPROCESS.DBSCAN_MIN_SAMPLES` from `1000`; a documented starting point is `0.5` and `250`. Also check `MIN_AREA_THRESHOLD=100`. |
| Custom-data overlay is distorted or lane curves are nonsensical | Lane fitting assumes TuSimple geometry and `data_source='tusimple'`. | Run custom data with `--with_lane_fit 0` and inspect direct cluster-mask overlay. Train/tune on custom data for production quality. |
| `ValueError: Wrong data source now only support tusimple` | Lane fitting was requested with an unsupported `data_source`. | Use `data_source='tusimple'` only for lane fitting, or disable lane fit for custom/non-TuSimple images. |
| Batch evaluator fails around path splitting on `clips` | The image tree does not include a `clips` path component, but TuSimple save-path logic expects it. | Use a TuSimple-style `test_set/clips/.../*.jpg` tree. For synthetic smoke trees only, use the bundled wrapper's `--allow_non_tusimple_layout 1` and interpret output paths as relative to `--image_dir`. |
| Batch evaluator creates no outputs | No `.jpg` files found, all outputs already exist and skipping is enabled, or `save_dir` is invalid. | Confirm recursive image count, choose a writable `--save_dir`, and use `--skip_existing 0` if you need to regenerate overlays. |
| Matplotlib window never returns or job hangs in CI/SSH | Interactive `plt.show()` blocks without a GUI or waits for the user to close windows. | Use bundled wrappers with `--show 0 --save_dir <dir>`. If Matplotlib is imported in custom code, set a noninteractive backend before importing pyplot. |
| CUDA OOM during inference/evaluation | GPU memory fraction is high, multiple processes are using the GPU, or batch evaluator is competing with another job. | Keep `TF_ALLOW_GROWTH=True`, lower `GPU_MEMORY_FRACTION` in the runtime config if needed, close other jobs, or run the wrapper with `--force_cpu 1` for a slower functional check. |
| `cv2.imread` returns `None` or resize fails | Input is not a readable image file, path is wrong, or image codec is unsupported. | Check path spelling, use a standard JPEG/PNG, and verify the file can be opened by OpenCV before running TensorFlow. |
| Saved overlay exists but appears unchanged | Postprocess returned no mask or skipped existing output. | Inspect `postprocess_summary.json` or batch JSONL records. Disable skip-existing for batch reruns and inspect binary/mask intermediates from a single-image run. |

## Missing pretrained weights

The repository documentation describes external pretrained weights, but this generated skill does not bundle weights. When a user says "run pretrained inference" without a local checkpoint:

1. State that a local checkpoint is required.
2. Ask them to provide the checkpoint directory or base path after downloading weights outside the skill.
3. If they want to create weights, route to `../training/`.
4. Do not fabricate model filenames or imply that `weights/tusimple_lanenet/` exists.

## Checkpoint path details

Prefer:

```text
--weights_path weights/tusimple_lanenet/model.ckpt-12345
```

Avoid passing only:

```text
model.ckpt-12345.index
model.ckpt-12345.data-00000-of-00001
model.ckpt-12345.meta
```

The bundled wrappers strip common shard suffixes and can resolve a directory through TensorFlow's checkpoint state when possible, but future custom code should pass the checkpoint base path directly.

## Empty or black mask decision tree

| Observation | Interpret as | Next step |
| --- | --- | --- |
| `binary_image.png` all or almost all black | Inference/domain/checkpoint issue before postprocess. | Test a known TuSimple sample image; verify checkpoint/front-end; confirm preprocessing. |
| `binary_image.png` has lane pixels but `mask_image.png` absent | DBSCAN/connected-component filtering issue. | Lower `DBSCAN_MIN_SAMPLES`, increase `DBSCAN_EPS`, and consider lowering `MIN_AREA_THRESHOLD`. |
| `mask_image.png` exists but `source_overlay.png` is wrong on custom data | Lane-fit geometry issue. | Re-run with `--with_lane_fit 0`. |
| TuSimple image works but custom image fails | Domain shift or DBSCAN parameters. | Tune DBSCAN and consider custom training. |

## DBSCAN tuning guidance

Default values are optimized for TuSimple-style inference:

```text
POSTPROCESS.DBSCAN_EPS = 0.35
POSTPROCESS.DBSCAN_MIN_SAMPLES = 1000
POSTPROCESS.MIN_AREA_THRESHOLD = 100
```

For custom images that produce black masks after a nonempty binary prediction, start with:

```text
POSTPROCESS.DBSCAN_EPS = 0.5
POSTPROCESS.DBSCAN_MIN_SAMPLES = 250
```

Tune one parameter at a time and save outputs after each run. Larger `eps` can merge lanes; smaller `min_samples` can admit noise. If binary segmentation itself is wrong, DBSCAN tuning will not fix the model.

## Lane fit and data source limits

Lane fitting is TuSimple-specific:

- It assumes a 720x1280 source geometry during remapping from the 256x512 network mask.
- It samples y positions from 240 to 720.
- It requires the IPM remap matrices loaded from the remap YAML.
- It raises an error for any `data_source` other than `tusimple` in the source implementation.

For custom images, use `--with_lane_fit 0`. This still uses DBSCAN clusters, but overlays the resized mask directly over the source image instead of fitting TuSimple curves.

## Headless/noninteractive runs

The original single-image script displays four Matplotlib figures and blocks at `plt.show()`. In servers, CI, SSH sessions, and subagent checks, prefer:

```bash
python <skill-dir>/scripts/test_lanenet.py \
  --repo_root . \
  --image_path path/to/image.jpg \
  --weights_path path/to/model.ckpt \
  --save_dir outputs/single \
  --show 0
```

Only use `--show 1` when an interactive display is available and blocking is intended.

## Batch image tree requirements

Strict TuSimple layout should include `clips` as a path component:

```text
TUSIMPLE_ROOT/test_set/clips/<date>/<clip_id>/<frame>.jpg
```

The output path is the part after `clips`, written under `--save_dir`. If the input path lacks `clips`, the original evaluator's path split crashes. The bundled wrapper detects this condition before the expensive TensorFlow graph run.

## Save directory behavior

The batch wrapper requires a writable `--save_dir` because unattended display of many images is not practical. It creates missing directories and skips existing output images by default. Use a new output directory for each experiment, or set `--skip_existing 0` to regenerate outputs after changing DBSCAN or lane-fit settings.
