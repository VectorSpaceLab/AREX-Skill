# Troubleshooting

## Purpose

Read this when Darkflow fails to install, import, build, or run. The repo is old enough that the most useful fixes are compatibility-oriented rather than version-agnostic.

## Install and build failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `CompileError` from `setup.py develop` mentioning `nms.pxd` or `cy_yolo2_findboxes.pyx` | Cython is too new for the bundled extension sources | Reinstall with `Cython<3` and rerun `pip install -e .` |
| `AttributeError: module 'enum' has no attribute 'IntFlag'` while pip is resolving old wheels | A legacy build dependency or wheel path is colliding with Python 3.6 compatibility assumptions | Stick to the verified Python 3.6 install path and let pip settle on 3.6-compatible wheels; if the resolver churns on `opencv-python`, pin a 3.6-compatible wheel such as the one selected by the verified install |
| `ModuleNotFoundError` for `tensorflow` or `cv2` | Core runtime dependencies were not installed | Install the package's runtime stack before editable install; do not rely on the repo alone |
| Editable install succeeds on a modern Python but imports fail later | The legacy TensorFlow 1.x stack is not actually compatible with the chosen interpreter | Use a Python 3.6 environment for the verified path |

## CLI and workflow failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `Failed to find any images in ...` | The `--imgdir` folder is empty or contains unsupported file extensions | Point `--imgdir` at a folder with `.jpg`, `.jpeg`, or `.png` files |
| Output images or JSON files never appear under `imgdir/out/` | The image folder is wrong, the input images are unsupported, or the process cannot write output | Check the input folder, file permissions, and the output path that `cliHandler` auto-creates |
| `return_predict()` raises an assertion about `np.ndarray` | A file path string was passed instead of a loaded image array | Load the image with OpenCV first and pass the array |
| `Cannot capture source` or a missing video file assertion in demo mode | `--demo` points to a bad path or no camera device is available | Recheck `--demo`, use `camera` only when a webcam exists, or supply a valid video file |
| `file ... does not exist` in demo mode | The requested input video path is wrong | Fix the path or use `camera` |
| `labels.txt and ... indicate inconsistent class numbers` | The custom `labels.txt` does not match the class count in the config | Make the class count, filter count, and label file agree |
| `Annotation directory not found ...` | The `--annotation` path is wrong or missing | Point `--annotation` at a Pascal VOC XML folder |
| `Could not find and load ...` or checkpoint restore failures | The `--load` value does not match the model, checkpoint step, or `.weights` file | Verify the `--model`, `--binary`, and `--load` combination; use `--load -1` to resume the latest checkpoint |

## Benign warnings you can ignore

- TensorFlow 1.4.1 emits several `FutureWarning` messages during import under Python 3.6 in the verified environment. They are noisy but not fatal.
- The verified environment reported `gpu_built = False`, which means the CPU build was active. That is fine for install and CLI inspection.

## When to stop and escalate

Stop and ask for a different environment or a narrower scope when:

- the machine cannot provide a Python 3.6-compatible install path
- the user needs GPU verification for the legacy TensorFlow 1.x stack but no compatible GPU wheel/toolkit is available
- the workflow depends on external weights, datasets, or network downloads that the user does not want to allow
- the issue is a malformed user dataset and the bundled validator already reports the specific bad files

## Related helpers

- `../scripts/check_install.py` for a safe import and version smoke check
- `../scripts/flow.py` when the installed `flow` executable is not on `PATH`
- `../sub-skills/training/scripts/check_voc_dataset.py` for annotation and label validation
