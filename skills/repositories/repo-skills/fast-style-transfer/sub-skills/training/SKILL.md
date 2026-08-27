---
name: training
description: "Plans and validates Fast Style Transfer style.py training runs,
  VGG/COCO assets, checkpoints, loss weights, and long GPU-oriented training
  workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: CC BY-NC 4.0
---

# Training

Use this sub-skill when the user wants to train a Fast Style Transfer transform network, prepare the bundled training runtime inputs, understand loss-weight/checkpoint options, debug VGG/COCO/data-layout problems, or decide whether a training run is safe to launch.

## Read and run

- Read [references/training-workflow.md](references/training-workflow.md) for the end-to-end training workflow, asset layout, command templates, outputs, and checkpoint handoff.
- Read [references/cli-reference.md](references/cli-reference.md) for verified the bundled training runtime flags/defaults and `optimize.optimize` behavior.
- Read [references/troubleshooting.md](references/troubleshooting.md) when paths, TensorFlow, VGG, data shapes, performance, or checkpoint outputs fail.
- Run [scripts/validate_training_inputs.py](scripts/validate_training_inputs.py) before a long training run. It validates paths and options, samples image files, and prints JSON; it never downloads data or trains.

## When to use this route

Use training guidance for requests like:

- "Train a style transfer network from this painting."
- "What files do I need before running the bundled training runtime?"
- "Build a short sanity check before launching a GPU training job."
- "Why does the bundled training runtime say the VGG network or train path is missing?"
- "How do I choose `--content-weight`, `--style-weight`, `--tv-weight`, or checkpoint frequency?"

Route away from this sub-skill when the user already has a trained checkpoint and wants to apply it to images or videos:

- Still images/directories: [../image-stylization/SKILL.md](../image-stylization/SKILL.md)
- Videos: [../video-stylization/SKILL.md](../video-stylization/SKILL.md)

## Training workflow summary

A normal training run needs:

1. A TensorFlow environment compatible with the script.
2. A writable checkpoint directory that already exists.
3. A style image readable by `imageio`/Pillow.
4. A content training directory containing images.
5. A VGG19 `.mat` file for perceptual losses.
6. Optional test image and test output directory for checkpoint previews.

Minimal command shape:

```bash
python sub-skills/training/scripts/run_training.py \
  --checkpoint-dir checkpoints/udnie \
  --style assets/style/udnie.jpg \
  --train-path data/train2014 \
  --vgg-path data/imagenet-vgg-verydeep-19.mat \
  --content-weight 1.5e1 \
  --checkpoint-iterations 1000 \
  --batch-size 20
```

Before launching, run the bundled validator with the same paths:

```bash
python sub-skills/training/scripts/validate_training_inputs.py \
  --checkpoint-dir checkpoints/udnie \
  --style assets/style/udnie.jpg \
  --train-path data/train2014 \
  --vgg-path data/imagenet-vgg-verydeep-19.mat \
  --content-weight 1.5e1 \
  --checkpoint-iterations 1000 \
  --batch-size 20
```

## Key decisions

- **Training corpus**: COCO `train2014` is the documented corpus, but any image directory can be used if the images are readable and representative.
- **VGG asset**: the bundled training runtime defaults to `data/imagenet-vgg-verydeep-19.mat`; pass `--vgg-path` explicitly when the asset lives elsewhere.
- **Checkpoint directory**: the directory must exist before the script runs. The script saves a TensorFlow checkpoint path ending in `fns.ckpt` inside it.
- **Preview image**: if `--test` is provided, `--test-dir` must also exist.
- **Backend**: GPU is not required for parser validation, but full training is normally a GPU workflow.
- **Slow mode**: `--slow` switches to direct pixel optimization for debugging; it is not the normal feed-forward training path.

## Validation limits

The validator and parser help checks catch missing files, bad numeric values, and obvious data-layout issues. They do not prove that:

- VGG `.mat` contents are semantically correct.
- A TensorFlow checkpoint will be compatible with another TensorFlow version.
- Training will converge or produce a visually pleasing result.
- A GPU backend is installed unless TensorFlow actually sees GPU devices.

After a checkpoint is created, use the image or video sub-skills to consume it.
