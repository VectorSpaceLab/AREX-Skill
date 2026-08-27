# Training Troubleshooting

## `checkpoint dir not found!`

The bundled training runtime requires `--checkpoint-dir` to point to an existing directory. Create it first:

```bash
mkdir -p checkpoints/my-style
python sub-skills/training/scripts/validate_training_inputs.py --checkpoint-dir checkpoints/my-style --style style.jpg --train-path train2014 --vgg-path imagenet-vgg-verydeep-19.mat
```

## `style path not found!` or unreadable style image

Check that the path is relative to the current working directory or pass an absolute/user-resolved path in your own shell. The style image must be readable by the Python image stack. Grayscale images are expanded to RGB, but corrupt or unsupported files fail during image loading.

## `train path not found!` or empty training directory

The default training directory is `data/train2014`, but it is not created unless the user downloads data. Use a real image directory and validate a small sample:

```bash
python sub-skills/training/scripts/validate_training_inputs.py --checkpoint-dir checkpoints/x --style style.jpg --train-path data/train2014 --vgg-path data/imagenet-vgg-verydeep-19.mat --sample-count 10
```

If the directory includes non-image files, remove them or point to a clean image-only subdirectory.

## `vgg network data not found!`

Training requires a VGG `.mat` file. The documented default is `data/imagenet-vgg-verydeep-19.mat`, but the file is external. Do not assume it exists. Acquire it through an approved network/data setup path, then pass `--vgg-path` explicitly.

## Test preview validation errors

If either `--test` or `--test-dir` is used, both must be valid. `--test-dir` must exist before the bundled training runtime runs. Preview failures do not necessarily mean training data is invalid; they often come from a missing preview directory or wrong current working directory.

## Slow or stalled training

Full training is expected to take hours on a GPU and can be impractical on CPU. Verify TensorFlow GPU visibility before promising a production run. If using CPU intentionally, frame it as debugging or a tiny dry run, not as a realistic full training plan.

## TensorFlow graph or checkpoint compatibility errors

The bundled runtime uses TensorFlow v1-style sessions/Saver through compatibility APIs in modern TensorFlow. A checkpoint produced with one TensorFlow graph/version may not restore under an incompatible runtime. If restore fails after training, test with the same script version and TensorFlow runtime that produced the checkpoint before attempting migration.

## Unexpected loss or poor visual results

The validation helper cannot detect artistic quality. Check:

- Style image resolution and content.
- Training corpus variety.
- `--content-weight`, `--style-weight`, and `--tv-weight` balance.
- Whether the run trained for enough iterations.
- Whether preview images were generated from the intended checkpoint.

## `--slow` confusion

`--slow` is a debug mode for direct pixel optimization. It is not the fast transform-network training path. If a user wants a reusable checkpoint for fast image/video stylization, avoid `--slow` unless they explicitly need loss-function debugging.
