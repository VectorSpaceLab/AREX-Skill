# Image Stylization Workflow

## Purpose

This reference explains how to apply a trained Fast Style Transfer checkpoint to still images using the bundled image stylization runtime workflow.

## Required inputs

| Input | Flag | Notes |
| --- | --- | --- |
| Trained checkpoint | `--checkpoint` | Directory with TensorFlow checkpoint state or a checkpoint path/prefix accepted by Saver restore. |
| Content image or image directory | `--in-path` | File mode stylizes one image; directory mode stylizes top-level files. |
| Output file or directory | `--out-path` | File mode can use an output file or existing directory. Directory mode expects an output directory. |
| Device | `--device` | TensorFlow device string such as `/cpu:0` or `/gpu:0`. |
| Batch size | `--batch-size` | Used for directory batching. Single-image helper uses batch size 1. |

## Single-image recipe

1. Verify the checkpoint and input file exist.
2. Choose an output file path, or an existing output directory if you want to preserve the input basename.
3. Use CPU for small debugging, GPU for throughput if TensorFlow GPU is verified.

```bash
python sub-skills/image-stylization/scripts/run_image_stylization.py \
  --checkpoint checkpoints/wave \
  --in-path content/chicago.jpg \
  --out-path outputs/chicago_wave.jpg \
  --device /cpu:0 \
  --batch-size 1
```

Preflight:

```bash
python sub-skills/image-stylization/scripts/validate_image_stylization_inputs.py \
  --checkpoint checkpoints/wave \
  --in-path content/chicago.jpg \
  --out-path outputs/chicago_wave.jpg \
  --device /cpu:0 \
  --batch-size 1
```

## Directory recipe

The directory path is scanned only one level deep. The script constructs input paths from the listed filenames and writes outputs with the same basenames under `--out-path`.

```bash
mkdir -p outputs/stylized
python sub-skills/image-stylization/scripts/run_image_stylization.py \
  --checkpoint checkpoints/wave \
  --in-path content/images \
  --out-path outputs/stylized \
  --device /gpu:0 \
  --batch-size 4
```

If images are not all the same dimensions, either resize them first or pass:

```bash
--allow-different-dimensions
```

That option groups images by shape and runs one group at a time.

## Checkpoint expectations

`evaluate.ffwd` creates the transform network graph, then restores variables with TensorFlow Saver. If the checkpoint argument is a directory, the script calls TensorFlow's checkpoint-state lookup and restores `model_checkpoint_path`. If it is not a directory, it tries to restore the path directly.

Checkpoint restore can fail even when the path exists if the checkpoint was produced by a different graph, incompatible TensorFlow version, or incomplete checkpoint file set.

## Image IO behavior

The bundled `utils.py` module loads images with RGB semantics and stacks grayscale images to three channels. It saves output by clipping to `[0, 255]` and writing `uint8` image data.

The transform network expects tensors shaped like the input images. Directory mode without mixed-dimension support uses the first image shape for the whole batch.

## Device and batch decisions

- `--device /cpu:0`: safest for tiny tests and systems without TensorFlow GPU.
- `--device /gpu:0`: preferred for large images or directories when TensorFlow sees a GPU.
- Increase `--batch-size` only when images are the same size and memory is sufficient.
- Decrease `--batch-size` on out-of-memory errors.

## Output validation

After a successful run, check that:

- The expected output file exists.
- Directory mode produced one output per top-level input file.
- Output dimensions match input dimensions for each image.
- The output is a valid image file readable by Pillow or imageio.
