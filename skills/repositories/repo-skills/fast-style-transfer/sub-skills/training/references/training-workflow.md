# Training Workflow

## Purpose

This reference distills the bundled training runtime, bundled optimizer/VGG modules, and public source evidence into a practical training plan. It is written for command construction and debugging with the skill-owned runtime wrappers.

## Inputs

| Input | Bundled training flag | Required | Notes |
| --- | --- | --- | --- |
| Checkpoint output directory | `--checkpoint-dir` | yes | Must already exist. Script saves `fns.ckpt` below this directory. |
| Style image | `--style` | yes | Loaded through repo image utility; grayscale is expanded to RGB. |
| Training image directory | `--train-path` | default `data/train2014` | Should contain readable content images. Non-image files can break batch loading. |
| VGG19 `.mat` | `--vgg-path` | default `data/imagenet-vgg-verydeep-19.mat` | Used by the bundled VGG module to compute perceptual features. |
| Preview image | `--test` | optional | If set, `--test-dir` must also be set and exist. |
| Preview output directory | `--test-dir` | required when `--test` is set | Stores intermediate preview images. |

## Output

The bundled training runtime calls `optimize.optimize(...)` and saves TensorFlow checkpoints through `tf.compat.v1.train.Saver()` to a save path formed as:

```text
<checkpoint-dir>/fns.ckpt
```

Use the checkpoint directory or compatible checkpoint path with image/video stylization workflows after training.

## Standard launch pattern

```bash
mkdir -p checkpoints/udnie previews/udnie
python sub-skills/training/scripts/run_training.py \
  --checkpoint-dir checkpoints/udnie \
  --style assets/style/udnie.jpg \
  --train-path data/train2014 \
  --test assets/content/stata.jpg \
  --test-dir previews/udnie \
  --vgg-path data/imagenet-vgg-verydeep-19.mat \
  --epochs 2 \
  --batch-size 4 \
  --checkpoint-iterations 2000 \
  --content-weight 7.5e0 \
  --style-weight 1e2 \
  --tv-weight 2e2 \
  --learning-rate 1e-3
```

For large runs, create directories and validate inputs first:

```bash
python sub-skills/training/scripts/validate_training_inputs.py \
  --checkpoint-dir checkpoints/udnie \
  --style assets/style/udnie.jpg \
  --train-path data/train2014 \
  --test assets/content/stata.jpg \
  --test-dir previews/udnie \
  --vgg-path data/imagenet-vgg-verydeep-19.mat
```

## Loss and architecture facts

Training uses a feed-forward transformation network from the bundled `transform.py` module by default. The architecture is:

- 9x9 convolution to 32 channels.
- Downsampling convolutions to 64 and 128 channels.
- Five residual blocks at 128 channels.
- Two transpose-convolution upsampling stages.
- Final 9x9 convolution to 3 channels with `tanh * 150 + 255/2` output scaling.
- Instance normalization after convolutions.

The loss in the bundled `optimize.py` module combines:

- Content loss at VGG layer `relu4_2`.
- Style Gram-matrix losses at `relu1_1`, `relu2_1`, `relu3_1`, `relu4_1`, and `relu5_1`.
- Total variation regularization.

Default weights from the bundled training runtime are `content_weight=7.5`, `style_weight=100.0`, `tv_weight=200.0`, and `learning_rate=0.001`.

## Data assumptions

- Training batches are resized to `(256, 256, 3)` inside `optimize.optimize`.
- The training set is trimmed so its length is divisible by batch size.
- Style image features are precomputed from the style image's own size.
- Images are expected to be loadable by `imageio.imread(..., pilmode='RGB')` or equivalent compatibility behavior.

## Slow mode

`--slow` is a debugging path inspired by Gatys-style direct pixel optimization. It changes the optimization target and internally adjusts epochs/learning rate if values are too small. Do not use it as the normal fast feed-forward model training path.

## Checkpoint handoff

When training finishes or reaches a checkpoint interval, use the checkpoint with:

```bash
python sub-skills/image-stylization/scripts/run_image_stylization.py --checkpoint checkpoints/udnie --in-path input.jpg --out-path output.jpg
```

or:

```bash
python sub-skills/video-stylization/scripts/run_video_stylization.py --checkpoint checkpoints/udnie --in-path input.mp4 --out-path output.mp4
```

Use the sibling sub-skills for those consumption workflows.
