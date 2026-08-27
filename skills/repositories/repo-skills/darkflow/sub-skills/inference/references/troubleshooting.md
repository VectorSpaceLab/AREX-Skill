# Inference Troubleshooting

## Purpose

Read this when prediction, JSON output, camera/video demos, Python API calls, or protobuf export/load fail.

## Common failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `Failed to find any images in ...` | The selected `--imgdir` is empty or has unsupported extensions | Use a directory containing `.jpg`, `.jpeg`, or `.png` files |
| No annotated images or JSON files appear | Wrong `--imgdir`, write permissions, or the run failed before postprocessing | Check the command output and inspect `<image_dir>/out/` |
| `return_predict()` assertion says the image is not a `np.ndarray` | A file path was passed to `return_predict()` | Load with `cv2.imread()` or another image reader first |
| Weight file not found | `--load` points to a missing `.weights` file, or `--binary` does not contain the expected file | Pass an explicit weights path or fix the binary directory |
| Label count mismatch | Custom labels and model config disagree | Use `../../../references/model-overview.md` and update labels/config together |
| `Cannot capture source` | The webcam is unavailable or the video file cannot be opened | Use a valid video path, verify camera access, or avoid demo mode on headless hosts |
| `--saveVideo` produces no `video.avi` | Demo mode failed, there was no write permission, or the video source ended early | Run without `--saveVideo` first, then check the working directory and permissions |
| `.pb` load fails or predictions look wrong | The `.pb` and `.meta` files are not the matching pair | Keep exported `.pb` and `.meta` together and pass both paths explicitly |
| GPU mode fails or is ignored | The environment has a CPU TensorFlow build or an incompatible TF1.x CUDA stack | Use CPU mode (`--gpu 0.0`) unless the user has a verified TensorFlow 1.x GPU install |

## Output interpretation

Prediction dictionaries contain:

- `label`: class name selected from the active labels source
- `confidence`: per-detection confidence score
- `topleft`: top-left bounding-box pixel coordinate
- `bottomright`: bottom-right bounding-box pixel coordinate

For CLI JSON output, each image has its own JSON file under the output folder.

## Recovery order

1. Run `../../../scripts/check_install.py` if import or CLI availability is uncertain.
2. Run `flow --help` to verify the `flow` entry point.
3. Verify the model, weights/checkpoint, and labels are compatible.
4. Try a small image folder with `--json` before a long demo or video run.
5. Escalate only after the exact failing command and model artifact paths are known.
