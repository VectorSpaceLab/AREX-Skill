# Troubleshooting

## When to read

Read this when installation, import, CLI execution, optional examples, or face
matching behavior is confusing. Run [../scripts/check_install.py](../scripts/check_install.py)
for a safe diagnostic summary.

## Install and import failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'dlib'` | `dlib` did not install or the command is using a different Python environment. | Install `face_recognition` into the same Python that runs the task. If `dlib` must build from source, ensure CMake and a C++ compiler are available, or use conda/Docker with a compatible dlib package. |
| pip fails while building `dlib` | No wheel for the chosen Python/platform, missing compiler/CMake, or too little build memory. | Use a Python version with known wheel/build support, install build tools, or use a container/conda environment. Do not keep retrying the same build without changing the cause. |
| `Please install face_recognition_models...` | The model-data package is missing or cannot import. | Install or reinstall `face_recognition_models` in the same environment, then run `python -c "import face_recognition"`. |
| `ModuleNotFoundError: No module named 'pkg_resources'` while importing `face_recognition_models` | Newer or stripped `setuptools` package lacks the deprecated `pkg_resources` API used by `face_recognition_models`. | Install a compatible `setuptools` that provides `pkg_resources`, for example `python -m pip install 'setuptools<81'`, then re-run the import check. |
| `pkg_resources is deprecated` warning | `face_recognition_models` imports `pkg_resources`. | This warning is not fatal if import succeeds. Pin `setuptools<81` only if import actually fails. |
| CLI command exists but exits before help output | Console script imports the package and hits a dependency/model failure. | Run `python scripts/check_install.py`; fix imports before debugging CLI arguments. |

## API and data issues

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `IndexError` after `face_encodings(image)[0]` | No face was detected, so the list is empty. | Call `face_locations` first, check for an empty list, and return a no-face branch or ask for a better image. |
| Wrong person matches or many false positives | Tolerance too high for the data, poor image quality, or similar-looking faces. | Use `face_distance` or CLI `--show-distance true`, then lower tolerance below `0.6` if needed. |
| Too many false negatives | Tolerance too low, poor lighting, occlusion, small faces, or mismatched known/unknown images. | Inspect distances, improve known images, try upsampling or CNN detection, and avoid overly strict thresholds. |
| No faces in small or distant images | Detector scale missed the face. | Increase `number_of_times_to_upsample` or CLI `--upsample`, crop/resize the input, or try the CNN model. |
| Boxes appear swapped or crops are wrong | Coordinates are being treated as `(left, top, right, bottom)` or `(x, y, w, h)`. | Use `(top, right, bottom, left)` and crop as `image[top:bottom, left:right]`. |
| OpenCV frames produce poor results | OpenCV uses BGR, while the package expects RGB arrays. | Convert with `rgb_frame = frame[:, :, ::-1]` before calling the API. |

## CLI behavior issues

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Known person is always ignored | No face found in the known image, unsupported extension, or image has multiple faces and only the first is considered. | Keep one clear face per known image and use `.jpg`, `.jpeg`, or `.png`. Review CLI warnings before trusting output. |
| Output contains `unknown_person` | Face was detected but no known encoding matched under tolerance. | Use `--show-distance true` and tune `--tolerance`; improve known images if distances are high. |
| Output contains `no_persons_found` | No face was detected in the checked image. | Improve/crop image, increase upsample, or try `face_detection --model cnn`. |
| Multiprocessing behaves oddly | Platform multiprocessing start method or old Python constraints. | Reproduce with `--cpus 1`; only increase CPU count after single-process output is correct. |

## CNN, CUDA, and performance

- `model="cnn"` and `batch_face_locations` are accuracy/batch patterns, not a
  guarantee of GPU use.
- GPU acceleration requires dlib built with CUDA plus compatible NVIDIA driver
  and runtime. Verify with:

```python
import dlib
print(dlib.DLIB_USE_CUDA)
print(dlib.cuda.get_num_devices())
```

- If CUDA is unavailable, use HOG for CPU-first workflows or accept slower CNN
  runtime. Do not count a CPU import check as proof of GPU acceleration.
- Resize frames and process every other frame for webcam/video speed. Scale
  boxes back to the original resolution before drawing.

## Optional dependency issues

| Workflow | Missing dependency symptom | Action |
| --- | --- | --- |
| Webcam/video/IP camera/drawing | `ModuleNotFoundError: No module named 'cv2'`, camera read failure, `cv2.imshow` display errors | Install OpenCV only for that workflow; keep image-only API logic separate from camera/display code. |
| KNN/SVM classifier examples | `ModuleNotFoundError: No module named 'sklearn'` | Install scikit-learn only when training a classifier; validate training directory structure and one face per training image. |
| Flask upload service | `ModuleNotFoundError: No module named 'flask'` or HTTP upload errors | Install Flask only for service workflows; validate upload file names and extensions before calling face APIs. |
| Blink/drowsiness demo | `ModuleNotFoundError: No module named 'scipy'` or camera/display failures | Install scipy/OpenCV only for that demo; keep alert side effects opt-in. |
| Raspberry Pi camera | `ModuleNotFoundError: No module named 'picamera'` or camera capture failure | Use Raspberry Pi hardware, enable camera support, and keep resolution modest. |

## Headless agent safety

Many human-facing examples display images with Pillow or OpenCV. In headless
agent runs, prefer structured text or explicitly requested output files. The
bundled [showcase API script](../scripts/showcase_api.py) is intentionally
headless.

## Fairness, privacy, and product caveats

- The model is documented as worse on children and variable across demographic
  groups. Do not describe output as a legal or biometric identity guarantee.
- Obtain consent and follow privacy laws before collecting, storing, or
  comparing face encodings.
- Save only the minimum face data needed for the user-approved task, and treat
  128-dimensional encodings as sensitive biometric-derived data.
