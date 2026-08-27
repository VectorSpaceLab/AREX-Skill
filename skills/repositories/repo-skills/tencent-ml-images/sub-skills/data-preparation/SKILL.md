---
name: data-preparation
description: "Guides Tencent ML-Images URL lists, image-label lists,
  dictionaries, and TFRecord preparation workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Data Preparation

Use this sub-skill when the task is about preparing data for Tencent ML-Images
training or finetuning: downloading OpenImages URLs, validating image/label
lists, interpreting class dictionaries or the semantic hierarchy, and writing
TFRecord shards.

## Read first

- Read [references/data-formats.md](references/data-formats.md) when you need the
  exact row formats for URL lists, local image lists, dictionaries, semantic
  hierarchy files, or TFRecord features.
- Read [references/workflows.md](references/workflows.md) for safe downloader and
  TFRecord conversion recipes that replace the original shell examples.
- Read [references/troubleshooting.md](references/troubleshooting.md) when URLs,
  images, labels, TensorFlow file APIs, or output directories fail.

## Bundled helpers

Run these helper scripts from the generated skill tree, not from the original
repository examples:

- `scripts/validate_ml_images_lists.py` checks URL-list/image-list/dictionary
  shape, label tokens, class-id bounds, duplicate image rows, and optionally
  whether image paths exist.
- `scripts/download_urls.py` is a Python 3 adaptation of the downloader. It is
  dry-run safe by default when `--dry-run` is supplied and supports `--limit` so
  agents can inspect URL handling without bulk download side effects.
- `scripts/make_tfrecords.py` is a safer TensorFlow 1.x/compat TFRecord writer
  for local images and label-list shards. It refuses to overwrite existing
  shards unless `--overwrite` is explicit.

## Route by task

- **Understand data files**: start with `references/data-formats.md`; then use
  `scripts/validate_ml_images_lists.py` against the user's copy of the files.
- **Download a tiny URL sample**: read `references/workflows.md`, run the
  downloader with `--dry-run --limit N`, and only remove `--dry-run` after the
  user has approved network writes.
- **Convert image lists to TFRecords**: validate the list first, then run
  `scripts/make_tfrecords.py` into a fresh output directory. Route onward to
  [../resnet-training/SKILL.md](../resnet-training/SKILL.md) for the train/val
  directory layout consumed by the model scripts.
- **Debug invalid data**: use the symptom table in
  `references/troubleshooting.md`; do not guess class counts or label encodings.

## Key operating constraints

- The public project uses legacy TensorFlow 1.x data APIs. Prefer a TensorFlow
  1.x runtime for native conversion; a modern TensorFlow 2 runtime may need
  `tf.compat.v1` behavior and should be tested with the bundled converter first.
- URL downloads are network-bound and many public image URLs may be expired. A
  failed download is not necessarily a parser bug.
- The ML-Images multi-label files use zero-based class ids and may include
  confidence scores such as `5193:0.9`. The ImageNet finetuning path may use a
  single scalar class id instead.
- Treat the tracked tiny examples as schema demonstrations. Do not bundle or
  require the full ML-Images, OpenImages, ImageNet, or checkpoint artifacts.
