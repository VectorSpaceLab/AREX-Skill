# MTCNN alignment workflows

Facenet's alignment workflow detects faces with MTCNN and writes cropped face thumbnails into a class-folder output directory.

## Build the command

Use the bundled command builder:

```bash
python scripts/build_alignment_command.py RAW_DATA_DIR ALIGNED_DATA_DIR --image-size 182 --margin 44
```

It emits a module-style command equivalent to the repository alignment script:

```bash
python -m align.align_dataset_mtcnn RAW_DATA_DIR ALIGNED_DATA_DIR --image_size 182 --margin 44
```

The module must be importable in the Facenet environment. Prefer module execution over hard-coded source paths.

## Main options

- `input_dir`: class-folder directory containing unaligned images.
- `output_dir`: destination class-folder directory for aligned thumbnails.
- `--image_size`: aligned output thumbnail size; repository default is `182`.
- `--margin`: extra pixels around the detected bounding box; repository default is `44`.
- `--random_order`: shuffles work order for multi-process/manual sharding.
- `--gpu_memory_fraction`: caps TensorFlow GPU memory usage if TensorFlow uses a GPU.
- `--detect_multiple_faces`: writes multiple cropped faces per image instead of choosing one.

## Detector behavior

The alignment script uses:

- minimum face size `20`
- MTCNN thresholds `[0.6, 0.7, 0.7]`
- scale factor `0.709`

When multiple faces are detected and `--detect_multiple_faces` is false, the script prefers a large face near the image center. When no face is detected, it writes the output filename without bounding-box coordinates in the bounding-box log.

## Safe operating pattern

1. Validate the raw dataset layout.
2. Align to a new output directory, not over the original raw photos.
3. Inspect the bounding-box log for no-face rows and unusually many multi-face rows.
4. Validate the aligned output layout.
5. Use aligned output for classifier, evaluation, or training workflows.

## Common adaptation

If SciPy image I/O fails in a modern environment, patch the execution environment or script to use Pillow/OpenCV for read/resize/save. Do not change the data contract: output should remain class-folder images with optional bounding-box logs.
