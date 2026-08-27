# Training Workflows

## Purpose

Read this when preparing a Darkflow training run, adapting a model configuration to a new class set, fine-tuning from pretrained weights, training from scratch, or resuming checkpoints.

## Custom class configuration

For a custom dataset, never edit the original base config in place. Copy it to a new filename first, then update:

1. Final `[region]` layer `classes` to the number of class labels.
2. Penultimate `[convolutional]` layer `filters` to `num * (classes + 5)`.
3. Label file to contain exactly one class name per line.
4. Training command to point at the copied config and the matching labels.

Example calculation: if `num = 5` and the dataset has 3 classes, set `filters = 5 * (3 + 5) = 40`.

## Validate data before training

Run the bundled validator before launching training:

```bash
python scripts/check_voc_dataset.py --labels <labels.txt> --annotations <annotations_dir> --images <images_dir>
```

This catches missing XML fields, unknown object labels, zero-sized images in annotations, and missing image files.

## Fine-tune from pretrained weights

Use pretrained Darknet weights when the base model family matches the copied config:

```bash
flow --model <custom.cfg> --load <pretrained.weights> --train --dataset <images_dir> --annotation <annotations_dir>
```

Useful optional controls:

```bash
flow --model <custom.cfg> --load <pretrained.weights> --train \
  --dataset <images_dir> --annotation <annotations_dir> \
  --trainer adam --lr 0.00001 --batch 16 --epoch 1000 --save 2000
```

Fine-tuning is usually the best path for small custom datasets because the loader can reuse compatible early layers and initialize only mismatched output layers.

## Train from scratch

Omit `--load` to initialize a new model from the config:

```bash
flow --model <custom.cfg> --train --dataset <images_dir> --annotation <annotations_dir> --trainer adam
```

This is slower and needs more data. Use it only when no compatible pretrained weights are appropriate.

## Checkpointing and resume

Darkflow saves TensorFlow checkpoints under the backup directory, defaulting to `ckpt/`.

Common resume patterns:

```bash
flow --train --model <custom.cfg> --load -1
flow --model <custom.cfg> --load <checkpoint_step>
```

`--load -1` reads the latest checkpoint entry from the checkpoint file. A positive integer loads a specific saved step.

After training, hand off to `../../inference/SKILL.md` for prediction, JSON output, or `.pb` export.

## TensorBoard summaries

Add `--summary <summary_dir>` to write TensorBoard graph and scalar summaries. The source creates the summary directory if needed and writes training summaries under it.

## Verification expectations

- A short validation run should create a checkpoint file named with the model name and step.
- The same config and checkpoint step should be loadable by `TFNet` or the `flow` CLI.
- Full benchmark-quality training is long-running and should be treated as an explicit user-approved job.
