# CLI Reference

## When to read

Read this when the user wants shell commands instead of Python API calls. The
installed package exposes two console scripts: `face_recognition` for identity
matching and `face_detection` for face boxes.

Run [scripts/check_install.py](../scripts/check_install.py) if either command is
missing or fails before showing help.

## `face_recognition`: identify known people

```bash
face_recognition [OPTIONS] KNOWN_PEOPLE_FOLDER IMAGE_TO_CHECK
```

### Inputs

- `KNOWN_PEOPLE_FOLDER`: a folder containing one image per known person.
  The image filename stem becomes the person's label. For example,
  `alice.jpg` labels the first usable face as `alice`.
- `IMAGE_TO_CHECK`: a single image file or a folder of images to identify.
- Recognized image extensions are `.jpg`, `.jpeg`, and `.png`, matched
  case-insensitively.

### Options

| Option | Meaning |
| --- | --- |
| `--cpus INTEGER` | Number of CPU processes to use. `-1` means all available cores. Default is `1`. |
| `--tolerance FLOAT` | Match threshold. Default is `0.6`; lower is stricter. |
| `--show-distance BOOLEAN` | Add the computed distance column. Click accepts values such as `true`, `false`, `1`, or `0`. |
| `--help` | Show command help. |

### Output rows

Without `--show-distance`, each output row is:

```text
image_path,name
```

With `--show-distance true`, each output row is:

```text
image_path,name,distance
```

Special labels:

- `unknown_person`: a detected face did not match any known encoding under the
  chosen tolerance.
- `no_persons_found`: no faces were detected in the image being checked.

Warnings from known-person setup:

- `WARNING: More than one face found in ... Only considering the first face.`
- `WARNING: No faces found in ... Ignoring file.`

Treat these warnings as data-quality signals. Fix known images before trusting
large batches.

### Common command patterns

```bash
# Recognize every face in one image or a folder.
face_recognition ./known_people ./unknown_images

# Make matching stricter.
face_recognition --tolerance 0.54 ./known_people ./unknown_images

# Print distances for threshold tuning.
face_recognition --show-distance true ./known_people ./unknown_images

# Use all CPU cores for a large folder.
face_recognition --cpus -1 ./known_people ./unknown_images
```

## `face_detection`: print face box coordinates

```bash
face_detection [OPTIONS] IMAGE_TO_CHECK
```

### Inputs and output

`IMAGE_TO_CHECK` can be a single image or a folder. Each output row is:

```text
image_path,top,right,bottom,left
```

Coordinates use the same `(top, right, bottom, left)` order as the Python API.

### Options

| Option | Meaning |
| --- | --- |
| `--cpus INTEGER` | Number of CPU processes to use. `-1` means all available cores. Default is `1`. |
| `--model TEXT` | Detector model. Use `hog` for CPU-friendly default behavior or `cnn` for the CNN detector. |
| `--upsample INTEGER` | How many times to upsample before looking for faces. Higher can find smaller faces but is slower. Default is `0` in the CLI. |
| `--help` | Show command help. |

### Common command patterns

```bash
# Detect boxes in one file.
face_detection ./image.jpg

# Detect boxes in every supported image in a folder.
face_detection ./images

# Use the CPU-friendly HOG detector explicitly.
face_detection --model hog ./images

# Use the CNN detector, which can be accelerated by CUDA-enabled dlib.
face_detection --model cnn --upsample 0 ./images
```

## Multiprocessing notes

Both CLIs support `--cpus`. The package chooses Python multiprocessing and uses
a `forkserver` context when that start method is available, which avoids a known
macOS libdispatch crash pattern. On very old Python versions, non-default CPU
counts fall back to single-threaded behavior.

## Choosing API versus CLI

Use the CLI when the user has folder-based known/unknown image inputs and wants
CSV-like text output. Use the Python API when the task needs custom input
validation, database/cache storage of encodings, tolerance calibration, GUI or
service integration, or robust no-face/multiple-face handling.
