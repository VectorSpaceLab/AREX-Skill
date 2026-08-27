# Data formats for Lightly CLI and embedding workflows

This reference covers the self-contained data contracts future agents need before running LightlySSL CLI commands or high-level embedding APIs.

## Supported media extensions

Image extensions recognized by Lightly's folder dataset path:

```text
.jpg .jpeg .png .ppm .bmp .pgm .tif .tiff .webp
```

Video extensions recognized by Lightly's folder scanner:

```text
.mp4 .mov .avi .mpg .hevc .m4v .webm .mpeg
```

Direct video-file datasets require the optional video dependency branch. Install with `pip install "lightly[video]"` when the task truly needs video files instead of extracted image frames.

## Image folder layouts

### Flat unlabeled image directory

Use this when all samples should receive the default label `0`:

```text
images/
  img_000.jpg
  img_001.png
  img_002.webp
```

Commands:

```bash
lightly-ssl-train input_dir=images
lightly-embed input_dir=images
```

### Weak-label / class-subdirectory image directory

If the input root contains subdirectories, Lightly treats it as a class-directory dataset via the torchvision-style layout:

```text
labeled_images/
  weak-label-0/
    a.jpg
    b.jpg
  weak-label-1/
    c.jpg
    d.jpg
```

Notes:

- Directory names become labels.
- Avoid mixing root-level images with class subdirectories; class-directory loading may ignore root-level images.
- Keep generated `lightly_outputs/` directories outside the input root when possible to avoid accidental rescans.

### Video directory

A video input can be flat or nested:

```text
videos/
  clip_a.mp4
  clip_b.mov
  nested/
    clip_c.avi
```

Notes:

- Each video frame is exposed as a sample.
- Frames are labeled by video source rather than by a human class label.
- Direct video reading can be slower than reading extracted image frames.
- Use `pip install "lightly[video]"` before relying on this path.

## YOLO labels for `lightly-crop`

`lightly-crop` expects one label file per input image. The label filename is the image filename with its extension replaced by `.txt`.

Flat layout:

```text
images/
  img_0.jpg
  img_1.png
labels/
  img_0.txt
  img_1.txt
```

Class-subdirectory layout must mirror relative subdirectories:

```text
images/
  class_a/
    img_0.jpg
labels/
  class_a/
    img_0.txt
```

Each non-empty label row uses five space-separated values:

```text
class_id x_center y_center width height
```

Example:

```text
0 0.50 0.50 0.40 0.30
1 0.25 0.75 0.20 0.10
```

Practical validation rules:

- `class_id` should be a non-negative integer.
- `x_center`, `y_center`, `width`, and `height` are normalized fractions.
- `x_center` and `y_center` should be in `[0, 1]`.
- `width` and `height` should be positive and usually in `(0, 1]`.
- Lightly adds `crop_padding` to width and height before cropping.
- Malformed rows with the wrong number of fields or non-numeric values fail when parsed.

Optional class-name YAML:

```yaml
names: [cat, dog, car]
```

Pass it with:

```bash
lightly-crop input_dir=images label_dir=labels output_dir=crops label_names_file=data.yaml
```

Generate a small valid crop fixture without source-repo dependencies:

```bash
python scripts/create_tiny_yolo_crop_fixture.py /tmp/lightly-yolo-fixture
```

## Embedding CSV format

`lightly-embed` writes an `embeddings.csv` file in the current Hydra run directory. Lightly-compatible embedding CSV files use this shape:

```csv
filenames,embedding_0,embedding_1,embedding_2,labels
img_0.jpg,0.12,-0.04,1.25,0
img_1.jpg,0.09,-0.10,1.31,0
```

Header requirements:

- First column: `filenames`.
- Embedding columns: `embedding_0`, `embedding_1`, ... with integer suffixes.
- Label column: `labels`.
- No whitespace-padded header names.
- Empty rows are invalid.
- Some Lightly tooling tolerates extra columns such as `masked` or `selected`, but basic interoperable files should stick to `filenames`, `embedding_*`, and `labels`.

Python utilities in `lightly.utils.io` can save, load, and validate this format when a task needs programmatic embedding I/O.

## Checkpoint and embedding path state

Default CLI config variable names:

- `LIGHTLY_LAST_CHECKPOINT_PATH`: intended to hold the latest checkpoint path from `lightly-ssl-train`.
- `LIGHTLY_LAST_EMBEDDING_PATH`: intended to hold the latest embedding CSV path from `lightly-embed`.

Caveat: a command run as a child process cannot permanently export environment variables into an already-running parent shell. Always capture printed artifact paths or specify stable Hydra/checkpoint output directories when building reproducible workflows.

## Pre-run validation helper

Use the bundled validator before executing commands:

```bash
python scripts/validate_lightly_image_folder.py images
python scripts/validate_lightly_image_folder.py images --label-dir labels --label-names-file data.yaml
```

The validator checks recognized media extensions, empty folders, mixed class-subdirectory plus root-file layouts, video warnings, and optional YOLO label consistency.
