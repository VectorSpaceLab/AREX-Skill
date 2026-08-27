---
name: data-and-utilities
description: "Routes TensorLayer file, preprocessing, iteration, and
  visualization workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Data and Utilities

Use this sub-skill for TensorLayer file helpers, preprocessing, minibatch iteration, TFRecord round-trips, and lightweight visualization workflows. This is the route for data handling before or around model training.

## Typical requests

- Load a dataset or inspect a packaged dataset helper.
- Apply affine/image preprocessing to a small fixture.
- Build or read a TFRecord file.
- Iterate over minibatches or sequence batches.
- Save or display a small image with TensorLayer helpers.

## Read first

- `references/api-reference.md` for the data-helper surface and verified signatures.
- `references/workflows.md` for tiny preprocessing and TFRecord patterns.
- `references/troubleshooting.md` for download, path, OpenCV, and schema failures.

## Bundled checks

- `scripts/smoke_prepro.py` checks affine rotation and transform behavior on a tiny synthetic image.
- `scripts/smoke_tfrecord.py` writes and reads a tiny TFRecord in a temporary directory.

## Boundaries

Include here:
- `tensorlayer.files`
- `tensorlayer.prepro`
- `tensorlayer.iterate`
- `tensorlayer.visualize`
- tiny dataset-loading and preprocessing helpers

Exclude or route elsewhere:
- core layer/model definitions -> `core-modeling`
- supervised training loops and CLI help -> `training-and-cli`
- pretrained image model constructors and app wrappers -> `vision-and-apps`
- NLP and seq2seq workflows -> `text-and-sequence`
- RL reward utilities and episode helpers -> `reinforcement-learning`

## Fast path

1. Identify whether the problem is file, preprocessing, iteration, or visualization.
2. Prefer a synthetic or tiny fixture over bundled large data.
3. Use the smoke scripts before moving to the full repo example.
