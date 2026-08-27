# API Reference

## When to read

Read this when a task needs the `face_recognition` Python API rather than the
CLI. Signatures below were verified by installed-package inspection and by the
repository source/tests for version 1.4.0.

## Public import surface

```python
import face_recognition
```

The root package exports these public helpers:

| Function | Signature | Core return |
| --- | --- | --- |
| `load_image_file` | `load_image_file(file, mode='RGB')` | `numpy.ndarray` image array |
| `face_locations` | `face_locations(img, number_of_times_to_upsample=1, model='hog')` | list of `(top, right, bottom, left)` tuples |
| `batch_face_locations` | `batch_face_locations(images, number_of_times_to_upsample=1, batch_size=128)` | list of per-image location lists |
| `face_landmarks` | `face_landmarks(face_image, face_locations=None, model='large')` | list of landmark dictionaries |
| `face_encodings` | `face_encodings(face_image, known_face_locations=None, num_jitters=1, model='small')` | list of 128-value NumPy arrays |
| `compare_faces` | `compare_faces(known_face_encodings, face_encoding_to_check, tolerance=0.6)` | list of boolean-like match values |
| `face_distance` | `face_distance(face_encodings, face_to_compare)` | NumPy array of Euclidean distances |

Importing the package loads dlib detectors and model paths from
`face_recognition_models`. If import fails before any function runs, check the
install/model guidance in [troubleshooting](troubleshooting.md).

## Images and coordinates

- `load_image_file(file, mode='RGB')` accepts a filesystem path or file-like
  object that Pillow can open.
- Use `mode='RGB'` for normal color images. `mode='L'` converts to grayscale;
  `mode=None` preserves the image mode from Pillow.
- Returned arrays are NumPy arrays. OpenCV frames are BGR by default; convert to
  RGB before passing them to these functions, e.g. `rgb_frame = frame[:, :, ::-1]`.
- Face boxes use CSS order `(top, right, bottom, left)`, not `(x, y, w, h)`.
  Crop a detected face with `face_image = image[top:bottom, left:right]`.
- Boxes are trimmed to image bounds, which matters for partial faces near an
  image edge.

## Face detection

```python
image = face_recognition.load_image_file("person.jpg")
locations = face_recognition.face_locations(image, number_of_times_to_upsample=1, model="hog")
```

- `model='hog'` is the default and is usually the CPU-friendly first choice.
- `model='cnn'` uses dlib's CNN detector. It can run much faster when dlib was
  built with CUDA, but CUDA is not required by the core skill coverage.
- `number_of_times_to_upsample` increases the search scale; higher values can
  find smaller faces but slow detection.
- No detected face returns `[]`; do not index into an empty result.

### Batched CNN detection

```python
batch_locations = face_recognition.batch_face_locations(images, number_of_times_to_upsample=0, batch_size=128)
```

Use batched detection when you have many same-shaped frames or images and want
to use the CNN detector. Keep all images the same shape before batching; this
matches the repository's video-frame example assumptions and avoids confusing
coordinate trimming. GPU acceleration is an optional performance optimization;
CPU execution can be slow.

## Landmarks

```python
locations = face_recognition.face_locations(image)
landmarks = face_recognition.face_landmarks(image, face_locations=locations, model="large")
```

- `model='large'` returns 68-point landmarks grouped as `chin`,
  `left_eyebrow`, `right_eyebrow`, `nose_bridge`, `nose_tip`, `left_eye`,
  `right_eye`, `top_lip`, and `bottom_lip`.
- `model='small'` returns 5-point landmarks grouped as `nose_tip`, `left_eye`,
  and `right_eye`.
- Supplying `face_locations` avoids re-detecting faces.
- Invalid landmark models raise `ValueError` with the supported model names.

## Encodings and matching

```python
known_image = face_recognition.load_image_file("known.jpg")
unknown_image = face_recognition.load_image_file("unknown.jpg")

known_locations = face_recognition.face_locations(known_image)
unknown_locations = face_recognition.face_locations(unknown_image)

if not known_locations or not unknown_locations:
    raise ValueError("No face found in one of the images")

known_encoding = face_recognition.face_encodings(
    known_image,
    known_face_locations=known_locations,
    num_jitters=1,
    model="small",
)[0]
unknown_encoding = face_recognition.face_encodings(
    unknown_image,
    known_face_locations=unknown_locations,
    num_jitters=1,
    model="small",
)[0]

distances = face_recognition.face_distance([known_encoding], unknown_encoding)
matches = face_recognition.compare_faces([known_encoding], unknown_encoding, tolerance=0.6)
```

- Each encoding is a 128-dimensional NumPy vector.
- `known_face_locations` lets you reuse previously detected boxes and avoids a
  second detection pass.
- `num_jitters` resamples a face before computing an encoding. Larger values
  can improve robustness but are proportionally slower.
- `model='small'` is the default and uses the 5-point predictor; `model='large'`
  uses the 68-point predictor.
- `face_distance` returns one distance per known encoding. Lower is more
  similar; the README and CLI use `0.6` as the default match threshold.
- `compare_faces` is a threshold wrapper around `face_distance`. Lower
  `tolerance` is stricter.
- Empty `face_encodings` returns `[]`. Empty `face_distance` inputs return an
  empty NumPy array, and `compare_faces` returns an empty list.

## Defensive usage patterns

- Detect faces first, then pass known boxes into landmarks/encodings.
- Reject or manually review known-person training images with zero or multiple
  faces; the CLI only keeps the first face in a multi-face known image.
- Use `face_distance` to calibrate tolerance for the dataset instead of assuming
  the default threshold is right for every population, camera, or lighting
  condition.
- Avoid GUI calls such as image viewers in headless agents; print structured
  locations/distances or write explicitly requested output files.
- For optional video/webcam workflows, isolate OpenCV-specific BGR/RGB
  conversion and camera/display failures from core `face_recognition` API
  failures.
