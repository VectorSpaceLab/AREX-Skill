# Facenet data formats

## Class-folder image datasets

Facenet treats each immediate subdirectory of `data_dir` as one identity/class:

```text
data_dir/
  Alice_Smith/
    Alice_Smith_0001.png
    Alice_Smith_0002.jpg
  Bob_Jones/
    Bob_Jones_0001.png
```

Important behavior:

- Class directories are sorted lexicographically before labels are assigned.
- Images inside each class directory are listed from the filesystem and are not filtered by metadata.
- Empty class directories are invalid for classifier/training workflows.
- The repository commonly uses aligned face patches rather than raw photos for training/evaluation.

Use `scripts/validate_facenet_dataset.py` to catch missing classes, empty classes, low image counts, and non-image files.

## LFW pairs files

`lfw.read_pairs()` skips the first line and then expects either:

- same-person row: `Name index1 index2`
- different-person row: `Name1 index1 Name2 index2`

`lfw.get_paths()` converts these rows to image paths such as:

```text
<lfw_dir>/<Name>/<Name>_0001.jpg
<lfw_dir>/<Name>/<Name>_0001.png
```

Rows are skipped when either referenced file is missing. A high skip count usually means the aligned LFW directory, extension, or pair-file identity names do not match.

## Learning-rate schedules

Training scripts read schedule lines of the form:

```text
epoch:learning_rate
```

Comments after `#` are ignored. A learning rate of `-` stops softmax training when selected by epoch. Use the training sub-skill's schedule validator before launching a long run.

## MS-Celeb TSV conversion

The repository contains a decoder for MS-Celeb-1M TSV records with six tab-separated columns: MID, query/name, image rank, image URL, page URL, and base64 image bytes. This is a large file-writing conversion workflow and is not bundled as a default run helper. Use it only when the user explicitly supplies TSV files and output policy.

## Image size conventions

- `align_dataset_mtcnn.py` defaults to output size `182` and margin `44`.
- Inference/evaluation scripts commonly default to model input size `160`.
- Training examples use model definitions with configurable `--image_size`, usually `160`.

Do not silently mix raw photos, 182-pixel aligned thumbnails, and 160-pixel model inputs without checking the intended script.
