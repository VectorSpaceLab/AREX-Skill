# PocketFlow Overview

PocketFlow is a TensorFlow 1.x framework for compressing and accelerating deep learning models. It combines model helpers, dataset helpers, learners, optional distillation, optional reinforcement-learning search, and conversion utilities.

## Architecture

```text
Dataset helper -> ModelHelper -> Learner -> checkpoints -> conversion/benchmark/deployment
                      ^            |
                      |            + optional distillation / RL / AutoML hparams
                      + run script + path.conf + execution mode
```

## Main object roles

| Role | Meaning | Owning sub-skill |
| --- | --- | --- |
| Dataset helper | Builds TensorFlow 1.x train/eval iterators from local or HDFS-style data paths. | [custom-models-data](../sub-skills/custom-models-data/SKILL.md) |
| ModelHelper | Defines forward passes, loss/metrics, learning rate, names, warm-start, and dump/eval hooks. | [custom-models-data](../sub-skills/custom-models-data/SKILL.md) |
| Run script | Registers common flags, instantiates ModelHelper, creates learner, dispatches train/eval. | [custom-models-data](../sub-skills/custom-models-data/SKILL.md) |
| Learner | Applies full-precision, pruning, sparsification, quantization, distillation, or search logic. | [compression-learners](../sub-skills/compression-learners/SKILL.md) |
| `path.conf` | Maps dataset/model paths for local, HDFS, Docker, and Seven modes. | [execution-config](../sub-skills/execution-config/SKILL.md) |
| Conversion tools | Export trained checkpoints to PB/TFLite or benchmark artifacts. | [deployment-conversion](../sub-skills/deployment-conversion/SKILL.md) |

## Supported built-in task families

- CIFAR-10 classification with LeNet/ResNet helpers.
- ImageNet/ILSVRC-12 classification with ResNet/MobileNet helpers.
- Pascal VOC detection with SSD/VGG and Faster R-CNN-style helpers.
- Fashion-MNIST custom example pattern for user-defined datasets/models.

## Learner families

- Baseline: `full-prec`.
- Channel pruning: `channel`, `chn-pruned-rmt`, `chn-pruned-gpu`, `dis-chn-pruned`.
- Weight sparsification: `weight-sparse`.
- Quantization: `uniform`, `uniform-tf`, `non-uniform`.
- Cross-cutting: `--enbl_dst` for distillation where supported; DDPG-based search for selected learner families.

## Verification notes

This generated skill is based on source/docs plus live import inspection in a compatible TensorFlow 1.10 environment. Safe checks covered imports, flags/help surfaces, and utility scripts. Full model training, performance reproduction, Docker/Seven jobs, dataset downloads, checkpoint downloads, and mobile-device tests were intentionally not run as default verification.
