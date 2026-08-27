# Cross-Cutting Troubleshooting

## TensorFlow import or version errors

**Symptoms**

- `ModuleNotFoundError: No module named 'tensorflow'`
- Attribute errors around `tf.compat.v1`, `tf.Graph`, `tf.nn.conv2d_transpose`, or Saver APIs.
- TensorFlow imports but no GPU devices are listed.

**Likely causes**

- Dependencies were not installed in the Python used to run the scripts.
- A TensorFlow version too old or too new for the script compatibility surface is active.
- A CPU-only TensorFlow wheel is installed when the user expected GPU execution.

**Recovery**

1. Run the root inspector with the same Python that will run the scripts:

   ```bash
   python scripts/inspect_fast_style_transfer.py --json
   ```

2. If working inside a checkout and imports still fail, run:

   ```bash
   python scripts/inspect_fast_style_transfer.py --repo-root /path/to/fast-style-transfer --json
   ```

3. Install a TensorFlow version that supports the repository's `tf.compat.v1` usage and your Python version. For GPU execution, verify `tf.config.list_physical_devices('GPU')` before a long run.

## External asset failures

**Symptoms**

- `vgg network data not found!`
- `style path not found!`
- `train path not found!`
- Checkpoint restore errors or `No checkpoint found...`.

**Likely causes**

- VGG `.mat`, training data, or pretrained checkpoint files were not downloaded or are in a different directory.
- A checkpoint directory was passed when it contains no TensorFlow checkpoint state.
- A path was created relative to a different working directory than the script run.

**Recovery**

- Use [setup-and-assets.md](setup-and-assets.md) to identify which asset is required for the current workflow.
- Run the nearest bundled validation helper before running the actual script.
- Pass explicit paths instead of relying on defaults such as `data/imagenet-vgg-verydeep-19.mat` or `data/train2014`.
- Do not run the repository's network downloader automatically unless network and disk usage are authorized.

## CPU/GPU performance mismatch

**Symptoms**

- Image stylization works but is slow.
- Training appears stuck for hours.
- Video processing is much slower than expected.

**Likely causes**

- The script is running on `/cpu:0` or TensorFlow cannot see the GPU.
- Batch size is too large for available memory or too small to utilize the GPU.
- Full training is expected to take hours even on historical high-end GPUs.

**Recovery**

- Confirm TensorFlow GPU devices with the root inspector or a direct import check.
- For image stylization, set `--device /gpu:0` only when TensorFlow GPU is verified.
- For video stylization, reduce `--batch-size` on memory errors; increase cautiously only after a short successful run.
- For training, treat CPU as a validation/debug backend, not a practical full-run backend.

## Source checkout path confusion

The generated skill's wrappers and validation helpers are bundled runtime entry points. They do not require a particular absolute checkout path. When the optional inspector accepts `--repo-root`, use it only to compare a local checkout against the provenance baseline or to diagnose a modified copy; ordinary training, image, and video commands should use the skill-owned wrappers plus user-supplied assets.

## What validation cannot prove

The bundled validation helpers can prove path existence, parser compatibility, dependency availability, image/video metadata, and obvious option errors. They cannot prove:

- A checkpoint is semantically compatible with the current graph.
- A full training run will converge or produce a visually pleasing style.
- External downloads are available.
- A GPU TensorFlow build is correctly installed unless the GPU is actually visible to TensorFlow.
- Moviepy/ffmpeg can encode every target codec/container combination.
