# Image Stylization Troubleshooting

## `Checkpoint not found!` or `No checkpoint found...`

The path passed to `--checkpoint` must exist. If it is a directory, it must contain TensorFlow checkpoint state. If it is a file/prefix, TensorFlow Saver must be able to restore it directly.

Recovery:

1. Validate path semantics:

   ```bash
   python sub-skills/image-stylization/scripts/validate_image_stylization_inputs.py --checkpoint checkpoints/wave --in-path input.jpg --out-path output.jpg
   ```

2. If the validator passes but restore fails, inspect checkpoint file completeness and TensorFlow graph/version compatibility.

## `In path not found!`

The input file or directory does not exist relative to the process working directory. Pass an explicit path and re-run the validation helper.

## Output path confusion

If `--in-path` is a file and `--out-path` is an existing directory, the script writes `<out-dir>/<input-basename>`. If `--in-path` is a directory, `--out-path` should be a directory, and output basenames mirror input basenames.

Create output directories before running directory mode.

## Different image dimensions assertion

Without `--allow-different-dimensions`, directory mode assumes every image has the same shape as the first input. The raw error mentions resizing images or using `--allow-different-dimensions`.

Recovery options:

- Resize images to a common shape before batching.
- Pass `--allow-different-dimensions` so the script groups by shape.
- Use the validation helper to list shape groups before running inference.

## TensorFlow restore or variable-shape errors

A checkpoint must match the transform graph architecture. Restore errors can occur when a checkpoint came from a different implementation, modified architecture, or incompatible TensorFlow version. Re-run with the script version that produced the checkpoint, or retrain a compatible checkpoint.

## CPU slowness

`ffwd_to_img` defaults to CPU and the CLI can be forced to `/cpu:0`. This is useful for a tiny debug run but slow for large images or directories. If a GPU is available, first verify TensorFlow GPU visibility, then pass `--device /gpu:0`.

## Image format or grayscale surprises

The bundled image utility expands grayscale images to RGB and writes clipped `uint8` outputs. Corrupt images, uncommon formats, or non-image files in a directory can still fail. Clean the directory or use a filtered staging directory.

## Batch memory errors

Large same-size images at high batch size can exceed CPU/GPU memory. Lower `--batch-size`; if mixed dimensions are present, grouping by shape can also reduce surprise batch allocations.
