# Workflows and Recipes

## When to read

Read this after choosing the Python API or CLI route. It distills the
repository examples into self-contained patterns. Do not assume an `examples/`
checkout, sample images, notebooks, or videos are present; ask the user for
image/video inputs or use the bundled helper scripts.

For exact function signatures, read [api-reference.md](api-reference.md). For
console syntax, read [cli-reference.md](cli-reference.md).

## Fast path: inspect one image

Use [../scripts/showcase_api.py](../scripts/showcase_api.py) when you need a
safe, headless demonstration over user-provided images:

```bash
python scripts/showcase_api.py --image ./person.jpg
```

It loads the image, prints detected face boxes, extracts landmarks and
encodings, and handles the no-face case without indexing into an empty list.

## Detect faces in a photo

```python
import face_recognition

image = face_recognition.load_image_file("person.jpg")
locations = face_recognition.face_locations(image, model="hog")
for top, right, bottom, left in locations:
    face_crop = image[top:bottom, left:right]
```

Use `model="hog"` first for normal CPU work. Switch to `model="cnn"` when the
user needs the CNN detector and accepts slower CPU runtime or has CUDA-enabled
dlib for acceleration.

## Extract landmarks

```python
image = face_recognition.load_image_file("people.jpg")
locations = face_recognition.face_locations(image)
landmarks = face_recognition.face_landmarks(image, face_locations=locations, model="large")
```

The large model returns facial features such as eyes, eyebrows, nose, lips, and
chin. The small model returns fewer points and is faster. When adapting makeup,
blink-detection, or annotation examples, keep GUI/display work optional and
separate from landmark extraction so headless runs still work.

## Recognize a person from known and unknown photos

```python
import face_recognition

known = face_recognition.load_image_file("known_person.jpg")
unknown = face_recognition.load_image_file("unknown.jpg")

known_boxes = face_recognition.face_locations(known)
unknown_boxes = face_recognition.face_locations(unknown)
if not known_boxes or not unknown_boxes:
    raise ValueError("Need at least one face in each image")

known_encoding = face_recognition.face_encodings(known, known_face_locations=known_boxes)[0]
unknown_encoding = face_recognition.face_encodings(unknown, known_face_locations=unknown_boxes)[0]

distance = face_recognition.face_distance([known_encoding], unknown_encoding)[0]
match = face_recognition.compare_faces([known_encoding], unknown_encoding, tolerance=0.6)[0]
print(distance, match)
```

When the input may contain multiple faces, loop over `(box, encoding)` pairs
instead of assuming index `0` is the desired person. Use distances to choose the
closest known face, then apply the tolerance threshold.

## Folder-based recognition from the CLI

The CLI labels known faces from filename stems and prints CSV-like rows:

```bash
face_recognition --show-distance true ./known_people ./unknown_images
```

Use this for quick folder workflows. For production workflows, keep the known
folder curated: one clear face per known image, meaningful filenames, no
ambiguous groups, and a threshold tuned with `--show-distance`.

## Batch and CNN workflows

`batch_face_locations(images, number_of_times_to_upsample=0, batch_size=128)`
uses the CNN detector over a list of images. It is most useful for same-shaped
video frames or large image batches. Use it when:

- all images can be loaded into memory for a batch;
- image shapes are consistent;
- the user accepts CNN runtime cost; and
- CUDA-enabled dlib is available if performance matters.

If a user only needs correctness on a few images, plain `face_locations(...,
model="hog")` is usually simpler.

## Optional recipe families

These patterns were present in repository examples but are optional for the
core skill. Do not install their dependencies unless the user asks for that
workflow.

| Pattern | Extra requirements | Guidance |
| --- | --- | --- |
| Webcam or video file recognition | OpenCV (`cv2`), camera/video device, GUI/display for preview | Convert frames from BGR to RGB before calling `face_recognition`; process fewer or smaller frames for speed; keep `cv2.imshow` optional in headless systems. |
| Faster webcam loop | OpenCV and NumPy | Resize frames (often 1/4 size), process every other frame, and scale boxes back to full resolution before drawing. |
| Multiprocessing webcam loop | OpenCV plus multiprocessing-safe environment | Use only when live FPS matters; isolate capture, processing, and display; be careful with macOS start methods. |
| KNN classifier | scikit-learn, pickle model persistence, training folder with one subfolder per class | Train from face encodings, choose `n_neighbors` or default to roughly `sqrt(samples)`, save/reload the classifier, and threshold nearest-neighbor distance. |
| SVM classifier | scikit-learn and curated training directory | Similar to KNN, but train an `svm.SVC`; avoid hardcoded absolute training paths. |
| Flask upload service | Flask and HTTP upload validation | Treat the repository service as a toy pattern: validate file extension, compute encodings, compare to known encodings, and return JSON. Do not hardcode a single celebrity identity in production. |
| Raspberry Pi camera | Raspberry Pi 2+, `picamera[array]`, camera enabled in `raspi-config` | Capture RGB frames into a NumPy array and run the same API; keep resolution modest for speed. |
| Blink/drowsiness demo | OpenCV, scipy, camera/GUI | Uses eye landmarks and Euclidean distances; keep safety/alert side effects separate from the face API. |
| Benchmarking | representative images and repeated timings | Benchmark only when performance is the task; record image sizes, detector model, CPU/GPU state, and iterations. |
| Notebook tracking demo | notebook runtime, video/display dependencies | Treat as an exploratory pattern rather than production code. |

## Deployment and packaging workflows

For container, cloud, CUDA, Docker Compose, or standalone executable packaging,
read [deployment.md](deployment.md). The important operational fact is that
`face_recognition` depends on compiled `dlib` and model data, so deployment
failures often look like install/build/import failures rather than ordinary
Python syntax errors.

## User-facing caveats

- The default match threshold of `0.6` is a starting point, not a universal
  identity guarantee.
- The documented model performs worse on children and can vary across
  demographic groups. Include fairness, privacy, consent, and legal caveats
  before building user-facing identification systems.
- If an image has no faces, the API returns empty lists; make this a normal
  branch, not an exception path.
- If a known image has multiple people, decide whether to reject it or choose a
  specific detected box. The CLI keeps only the first encoding and warns.
