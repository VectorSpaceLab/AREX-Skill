# Inference Troubleshooting

## `ModuleNotFoundError: mmcv._ext`

Likely cause: `mmcv-lite` is installed or the installed `mmcv` wheel does not match the Python/PyTorch/CUDA ABI.

Fix:

- Install full `mmcv`, not `mmcv-lite`, for MMDetection models that import `mmcv.ops`.
- Match the `mmcv` build to the installed PyTorch and CUDA runtime.
- Reinstall MMDetection dependencies in a clean environment if mixed wheels were installed.

## CPU RoIPool Unsupported

Symptom: CPU inference asserts that `RoIPool` is not supported.

Fix:

- Use a CUDA device for models containing `RoIPool`, or choose a model/config that avoids `RoIPool`.
- If CPU-only is mandatory, validate the model architecture before committing to that route.

## `show=True` Hangs or Fails

Likely cause: no GUI/display, disabled X11 forwarding, or OpenCV GUI support missing.

Fix:

- Set `show=False`.
- Save visualizations with `out_dir='outputs'` and `no_save_vis=False`.
- For pure JSON output, set `no_save_vis=True` and `no_save_pred=False`.

## No Files Written

Check these combinations:

- `out_dir=''` means no output directory is used.
- `no_save_pred=True` disables JSON prediction files.
- `no_save_vis=True` disables visualization image files.
- Setting both `no_save_pred=True` and `no_save_vis=True` means no files should be expected.
- `return_vis=True` returns visualization arrays in memory; it is not a substitute for `out_dir` when files are required.

## Empty or Unexpected Predictions

Possible causes:

- `pred_score_thr` is too high for visualization or downstream filtering.
- Wrong config/checkpoint pairing.
- Randomly initialized model because no checkpoint was loaded.
- Missing checkpoint metadata caused fallback COCO classes or random palette.
- Input arrays are RGB when the API expects BGR.
- Open-vocabulary prompt format does not match the model's expected `texts`, `custom_entities`, or `tokens_positive` behavior.

## Invalid Device String

Symptoms include PyTorch device parsing errors or CUDA unavailable errors.

Fix:

- Use `device='cpu'` for CPU.
- Use `device='cuda:0'`, `cuda:1`, etc. only when CUDA is installed and visible.
- If `device=None` is allowed by the API, MMEngine chooses an available device for `DetInferencer`.

## Network or Download Failure

Model aliases and URL weights may trigger downloads.

Fix:

- Prefer local checkpoint files in restricted environments.
- Pre-download weights and pass `weights='checkpoint.pth'`.
- If using a checkpoint-only route, verify the checkpoint contains enough config metadata or pass `model='config.py'` explicitly.

## Config or Checkpoint Metadata Missing

Symptoms:

- default COCO classes are used unexpectedly;
- palette warnings mention random fallback;
- checkpoint-only initialization fails because config cannot be recovered.

Fix:

- Pass both `model='config.py'` and `weights='checkpoint.pth'`.
- Set `palette='coco'`, `palette='voc'`, `palette='citys'`, or `palette='random'` deliberately.
- Ensure custom checkpoints preserve `dataset_meta` when training/exporting.

## NumPy/OpenCV/Torch ABI Issues

Symptoms can include import crashes, OpenCV decode failures, or extension loading errors after package upgrades.

Fix:

- Align Python, PyTorch, CUDA, `mmcv`, NumPy, and OpenCV versions.
- Avoid mixing packages from incompatible channels or indexes.
- Recreate the environment if binary packages were upgraded independently.

## Video Codec or Webcam Failure

Video and webcam routes depend on OpenCV codecs, camera permissions, display availability, and output container support.

Fix:

- First prove image inference with the same model/checkpoint.
- Use file output instead of live display.
- Try a different fourcc/container if video writing fails.
- For servers, process frames from files or streams and avoid GUI calls.

## Large-Image Failure

Common causes:

- `sahi` is not installed for slicing workflows.
- Patch size or batch size is too large for memory.
- TTA requested but the config lacks `tta_model` or `tta_pipeline`.
- Merge IoU threshold is inappropriate for object density.

Fix:

- Install large-image dependencies only when needed.
- Reduce patch size or batch size.
- Disable TTA unless the config supports it.
- Tune overlap and NMS merge thresholds on representative images.
