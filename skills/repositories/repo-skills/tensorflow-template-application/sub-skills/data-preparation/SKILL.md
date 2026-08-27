---
name: "data-preparation"
description: "Route CSV, LIBSVM, TFRecords, and iris fixture questions."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# Data Preparation

Use this sub-skill for:

- dense CSV conversion with a configurable label position and label type
- sparse LIBSVM conversion with `id:value` pairs
- TFRecords inspection for dense or sparse `tf.train.Example` schemas
- tiny iris CSV fixtures generated from `sklearn`
- DICOM conversion caveats when the external labels file is missing

## Route elsewhere

- Model training, export, inference, checkpoints, or TensorBoard -> `../training-and-export/SKILL.md`
- Serving requests or client payloads -> `../serving-and-clients/SKILL.md`

## Bundled helpers

- `scripts/convert_csv_to_tfrecords.py`
- `scripts/convert_libsvm_to_tfrecords.py`
- `scripts/inspect_tfrecords.py`
- `scripts/create_iris_csv_fixture.py`

## Canonical rules

- Dense CSV defaults to features first and label last. Use `--label-position first` only for legacy label-first files.
- Sparse LIBSVM keeps the label first, followed by `id:value` tokens.
- Dense TFRecords store `label` plus a float list named `features`.
- Sparse TFRecords store `label` plus `ids` and `values`.
- If a TFRecord does not match the chosen schema, treat that as a schema error instead of printing empty fields.
- The iris fixture comes from local `sklearn.datasets.load_iris()`; it does not download anything.
- DICOM conversion is reference-only here because the source workflow depends on `pydicom` and an external labels CSV that is not present in this checkout.

## Read next

- `references/data-formats.md`
- `references/workflows.md`
- `references/troubleshooting.md`
