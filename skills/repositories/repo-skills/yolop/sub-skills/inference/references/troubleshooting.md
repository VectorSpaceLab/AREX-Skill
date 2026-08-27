# Inference Troubleshooting

## Missing or incompatible checkpoint

Symptoms:

- `FileNotFoundError` for `weights/End-to-end.pth`.
- `KeyError: 'state_dict'` while loading weights.
- Many missing/unexpected keys.

Recovery:

- Use an epoch checkpoint dictionary for native demo/test scripts.
- If using a bare `final_state.pth`, load it manually or adapt the script to accept a bare state dict.
- Ensure architecture variants match the checkpoint. The default active `get_net(cfg)` uses the no-share YOLOP architecture.

## Numeric camera source fails

Symptoms:

- `Failed to open 0` or OpenCV camera errors.
- GUI/display errors in headless sessions.

Recovery:

- Use a file, folder, or video path for automated checks.
- Only use numeric camera ids on a machine with camera access and GUI/video permissions.
- The bundled helper rejects numeric sources by default to avoid unsafe headless behavior.

## No images or videos found

`LoadImages` supports extensions such as `.bmp`, `.jpg`, `.jpeg`, `.png`, `.tif`, `.tiff`, `.dng` and video extensions such as `.mov`, `.avi`, `.mp4`, `.mpg`, `.mpeg`, `.m4v`, `.wmv`, `.mkv`.

Recovery:

- Pass a file, a directory containing supported files, or a glob.
- Check that paths are visible from the process working directory.

## Empty detections

YOLOP can produce segmentation overlays even when `non_max_suppression` returns no boxes.

Recovery:

- Lower `--conf-thres` temporarily.
- Confirm the checkpoint is the YOLOP multitask checkpoint.
- Confirm image preprocessing matches the source loader and `--img-size`.
- Inspect raw `det_out` shape with the root `check_install.py` or a custom debug run.

## Output directory surprises

The source `tools/demo.py` deletes an existing `--save-dir` with `shutil.rmtree` before writing outputs. Use the bundled helper if you need safer output-directory behavior.

## CUDA or half-precision errors

Recovery:

- Re-run with `--device cpu` to separate model/data issues from CUDA issues.
- Install matching torch/torchvision CUDA wheels.
- If dtype mismatch appears, disable half precision in a local wrapper or ensure input tensors use `.half()` when the model is half.

## Segmentation overlay size mismatch

The demo uses `shapes` from the letterbox loader to crop padding and interpolate masks back to the original frame. If a custom loader is used, it must preserve the same `(original_shape, ((ratio_h, ratio_w), pad))` convention or `scale_coords`/mask interpolation will misalign outputs.
