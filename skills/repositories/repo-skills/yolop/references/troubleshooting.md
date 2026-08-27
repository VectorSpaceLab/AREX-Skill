# YOLOP Cross-Cutting Troubleshooting

## When to read

Read this when YOLOP imports fail, a script cannot find `lib`, torch/torchvision device behavior is confusing, configuration changes appear ignored, or optional CUDA/ONNX/TensorRT dependencies fail.

## `ModuleNotFoundError: No module named 'lib'`

Likely causes:

- Running a source script from a directory that did not add the YOLOP checkout root to `sys.path`.
- Using the generated skill scripts without passing `--repo-root`.
- Treating YOLOP as a pip-installed distribution even though the checkout has no package metadata.

Recovery:

1. Run the source scripts from the YOLOP checkout root with `PYTHONPATH=.`.
2. For bundled skill helpers, pass `--repo-root /path/to/YOLOP`.
3. Verify with `python scripts/check_install.py --repo-root /path/to/YOLOP --device cpu`.

## Missing Python dependencies

Common missing modules include `cv2`, `yacs`, `prefetch_generator`, `tensorboardX`, `scipy`, `sklearn`, `onnx`, `onnxruntime`, and `onnxsim`.

Recovery:

```bash
python -m pip install -r requirements.txt
python -m pip install onnx onnxruntime onnxsim  # only needed for export/ONNX tasks
```

Install torch and torchvision first with a matching CPU or CUDA wheel pair. The README baseline is PyTorch 1.7+/torchvision 0.8+, but modern pairs can work for inspection if the model and ONNX smokes pass.

## Torch/torchvision mismatch

Symptoms:

- `torchvision.ops.nms` import or runtime errors.
- CUDA runtime errors after installing a CPU-only torch wheel.
- `AssertionError: CUDA unavailable, invalid device ... requested` from `select_device`.

Recovery:

1. Check `python - <<'PY'` imports for `torch`, `torchvision`, and `torchvision.ops.nms`.
2. Keep torch and torchvision versions from the same release family and backend tag.
3. Use `--device cpu` for smoke/inference checks unless a CUDA-capable torch wheel is installed.
4. Do not treat CPU success as proof of CUDA speed or TensorRT readiness.

## Config changes appear ignored

Symptoms:

- Passing `--dataDir`, `--prevModelDir`, `--conf_thres`, or `--iou_thres` has no effect.
- Evaluation thresholds still use `cfg.TEST.NMS_CONF_THRESHOLD` and `cfg.TEST.NMS_IOU_THRESHOLD`.

Likely cause: the current `update_config(cfg, args)` only applies a few CLI fields; several parser options have commented-out config assignments.

Recovery:

- Edit a copied config or patch `cfg` in code before constructing datasets/models.
- For source script runs, update `lib/config/default.py` or modify `update_config` deliberately.
- Record any local config patch because it changes reproducibility.

## Dataset path errors

Symptoms:

- `FileNotFoundError` for image, label, mask, or lane roots.
- `StopIteration`, zero-length dataset, or `Path.iterdir()` failures.
- Detection JSON loads but masks/lanes are missing.

Recovery:

1. Read `sub-skills/data-preparation/references/data-layout.md`.
2. Run the bundled layout checker from that sub-skill.
3. Make sure `DATASET.DATAROOT`, `LABELROOT`, `MASKROOT`, and `LANEROOT` each point to roots that contain `train/` and `val/` subdirectories.
4. Detection JSON names, image names, drivable mask names, and lane mask names must correspond after replacing roots and changing `.png`/`.jpg`/`.json` extensions.

## ONNX export outputs look wrong

Symptoms:

- Exported model has more than `det_out`, `drive_area_seg`, and `lane_line_seg` outputs.
- ONNXRuntime inference returns detection feature maps where segmentation masks are expected.

Likely cause: exporting `lib.models.get_net(cfg)` directly can flatten the eval detection tuple into extra ONNX outputs. The source `export_onnx.py` uses an export-specific `MCnet` wrapper that returns exactly three outputs.

Recovery:

- Use `sub-skills/export/scripts/export_onnx_model.py`, which imports the export-specific wrapper.
- Verify output names with `sub-skills/export/scripts/run_onnx_inference.py --dry-run` or an ONNXRuntime session inspection.

## TensorRT/ZED deployment failures

The C++ deployment path is hardware- and SDK-specific. It needs CUDA, TensorRT, ZED SDK, OpenCV C++, and the repo's plugin/layer code. A Python CPU environment cannot validate it.

Recovery:

- Read `sub-skills/export/references/tensorrt-deployment.md` before attempting a build.
- Confirm the CMake file matches your platform paths; the source evidence uses CUDA 10.2-era include/library paths and aarch64 TensorRT paths.
- Use the bundled `.wts` exporter only to prepare model weights; it does not build or validate a TensorRT engine.
