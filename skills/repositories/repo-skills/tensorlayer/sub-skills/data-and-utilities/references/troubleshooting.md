# Troubleshooting

## Download and data-path problems

### Dataset helpers try to download or look in the wrong directory

Some dataset helpers default to a `data/` path or expect existing files. Pass an explicit temporary directory or use a synthetic fixture when you only need the API behavior.

### Example scripts expect repo sample images

The public tutorials often rely on sample images or downloaded data. Bundled smoke scripts should not. If a tutorial path mentions `data/tiger.jpeg`, `data/cat/`, or `data/dog/`, replace it with a generated fixture.

## OpenCV and visualization problems

### `opencv-python` is missing

Affine image helpers depend on OpenCV. Install `opencv-python` before running the preprocessing smoke.

### Matplotlib or display backends fail

Use headless-friendly checks. The bundled scripts avoid interactive windows and only inspect output arrays or written files.

## TFRecord/schema problems

### Parsed shapes are wrong

Check the feature names, decode path, and reshape dimensions. Keep the record schema simple: one raw-bytes feature and one integer label feature for the smoke case.

### Reader returns empty batches

Confirm the temp file was closed before reading and that the reader and writer agree on the exact number of examples.

## Next checks

- `scripts/smoke_prepro.py`
- `scripts/smoke_tfrecord.py`
