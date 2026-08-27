# Setup and Scope

Read this before using the Tencent ML-Images skill in a new checkout.

## Scope summary

This repo skill covers three user-facing workflows:

1. Data preparation: URL lists, image lists, dictionaries, semantic hierarchy,
   and TFRecord conversion.
2. ResNet training: pretraining on ML-Images, finetuning on ImageNet, flag
   translation, graph construction, and training troubleshooting.
3. Checkpoint inference: top-k classification and feature extraction from a
   pretrained checkpoint.

## Runtime shape

The public repository is a legacy TensorFlow 1.x project. The verified smoke
used:

- Python 3.6
- TensorFlow 1.6.0
- OpenCV 4.2.0
- NumPy 1.19.5

That environment was sufficient to import `flags`, import `models.resnet`,
build a placeholder ResNet graph, and inspect the TFRecord CLI. A newer
TensorFlow 1.15 stack was less stable because `flags.py` collided with the
`log_dir` flag that newer TensorFlow/absl stacks introduce.

## Packaging shape

No `pyproject.toml`, `setup.py`, or `setup.cfg` was present in the repository.
This means there is no installable Python distribution metadata to publish in
this skill. Future agents should operate from a checkout and use the bundled
helpers rather than expecting an editable install target.

## Practical prerequisites

- A TensorFlow 1.x-compatible runtime that still exposes `tf.app`, `tf.contrib`,
  `tf.gfile`, and `tf.python_io`-era APIs.
- OpenCV for inference preprocessing helpers.
- Access to local data files or checkpoints appropriate to the workflow.
- For full training/finetuning, a practical GPU runtime and enough data storage
  for TFRecords and checkpoints.

## Recommended first command

Run the root helper before deeper workflow work:

```bash
python scripts/check_legacy_env.py
```

If you have a checkout path, add `--repo-root <checkout>` and, if desired,
`--smoke-graph`.

## When to read a sub-skill

- `data-preparation`: as soon as the task mentions URL lists, image lists, or
  TFRecord generation.
- `resnet-training`: when the user asks for a training or finetuning command,
  graph smoke, or flag translation.
- `checkpoint-inference`: when the user has a checkpoint and wants labels or
  features.

## Exclusions

- Full ML-Images pretraining and ImageNet finetuning are documented, but the
  skill does not claim to reproduce the authors' unreleased distributed training
  setup.
- Dataset/checkpoint downloads are external artifacts and should remain user-
  approved side effects.
- The skill does not bundle the original repo's large outputs or image assets.
