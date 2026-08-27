# Training Configuration

## Purpose

This reference summarizes the config keys that Luminoth actually reads during
training and evaluation.

## Minimal config shape

```yaml
train:
  run_name: my-run
  job_dir: jobs/

dataset:
  type: object_detection
  dir: datasets/voc/tf

model:
  type: fasterrcnn
  network:
    num_classes: 20
```

## Required keys by workflow

### Local training

At minimum, the model needs:

- `model.type`
- `dataset.type`
- `dataset.dir`

It is strongly recommended to set:

- `train.job_dir`
- `train.run_name`

because that is where checkpoints, summaries, and TensorBoard output live.

### Evaluation

Evaluation also requires:

- `train.job_dir`
- `train.run_name`

without those values the evaluator cannot find the run directory.

## Commonly adjusted keys

| Key | Meaning |
| --- | --- |
| `train.run_name` | Name of the training run inside the job directory. |
| `train.job_dir` | Base directory for checkpoints and summaries. |
| `train.num_epochs` | Number of passes over the dataset. |
| `train.batch_size` | Training batch size. Faster R-CNN typically uses 1. |
| `train.debug` | Enables extra logging. |
| `train.tf_debug` | Enables TensorFlow debug mode. |
| `dataset.dir` | Location of the TFRecord dataset. |
| `dataset.split` | Split to consume. |
| `dataset.image_preprocessing` | Resize settings. |
| `dataset.data_augmentation` | Ordered augmentation list. |
| `model.type` | `fasterrcnn` or `ssd`. |
| `model.network.num_classes` | Number of classes to predict. |

## Model family notes

- `fasterrcnn` has RCNN/RPN-specific subkeys such as `model.network.with_rcnn`,
  `model.rpn`, and `model.rcnn`.
- `ssd` has SSD-specific keys such as `model.proposals`, `model.anchors`, and
  `model.variances`.
- The `tfrecord` dataset type still exists for compatibility, but the package
  warns that `object_detection` is the preferred name.

## Override syntax

Use dotted keys with `--override` / `-o`.

Examples:

```bash
lumi train -c ./config.yml -o model.network.num_classes=3
lumi eval -c ./config.yml -o train.run_name=my-run
```

Overrides are merged on top of the config files and then validated by the
package's config loader.

## What to read next

- `references/workflows.md` for the full config flow.
- `references/cloud.md` for cloud-specific settings and prerequisites.
- `scripts/check_config_keys.py` to verify a config before a run.
