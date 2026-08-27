---
name: "tensorflow-template-application"
description: "Route TensorFlow template application workflows for data
  preparation, TF1 training/export, and serving/client tasks."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# TensorFlow Template Application

This skill routes the TensorFlow 1.x template application's public workflows.
Use it when the user asks about CSV or LIBSVM conversion, TFRecords, dense or
sparse training, checkpointing, SavedModel export, TensorBoard, TensorFlow
Serving requests, or the repo's legacy client examples.

## Start here

- Read `references/installation.md` for the TF1-compatible package set and
  optional serving add-ons.
- Run `scripts/check_tf1_environment.py` after installation to confirm the
  core TF1 symbols, `trainer` import, and the TFRecord smoke check.
- Read `references/troubleshooting.md` when a task fails because of TF2,
  flags, shapes, checkpoints, or serving mismatches.

## Route map

### `sub-skills/data-preparation/`

Use this route for:

- dense CSV to TFRecords conversion
- sparse LIBSVM to TFRecords conversion
- TFRecords inspection and schema checks
- tiny iris fixture generation from `sklearn`
- questions about dense `features` versus sparse `ids` and `values`

Read next:

- `sub-skills/data-preparation/references/data-formats.md`
- `sub-skills/data-preparation/references/workflows.md`
- `sub-skills/data-preparation/references/troubleshooting.md`

### `sub-skills/training-and-export/`

Use this route for:

- dense and sparse training commands
- checkpoint restore and SavedModel export
- local inference from checkpoints or exported models
- model, optimizer, and loss flag questions
- TensorBoard event inspection
- legacy queue or distributed training notes

Read next:

- `sub-skills/training-and-export/references/model-overview.md`
- `sub-skills/training-and-export/references/cli-reference.md`
- `sub-skills/training-and-export/references/workflows.md`
- `sub-skills/training-and-export/references/troubleshooting.md`

### `sub-skills/serving-and-clients/`

Use this route for:

- dense and sparse TensorFlow Serving PredictRequest payloads
- Python gRPC client helpers
- minimal-model latency and QPS benchmarks
- the legacy Django HTTP wrapper
- alternate Java, Go, C++, Android, and iOS client examples as reference-only

Read next:

- `sub-skills/serving-and-clients/references/python-grpc-client.md`
- `sub-skills/serving-and-clients/references/minimal-benchmark.md`
- `sub-skills/serving-and-clients/references/http-service.md`
- `sub-skills/serving-and-clients/references/alternate-clients.md`
- `sub-skills/serving-and-clients/references/troubleshooting.md`

## Quick rules

- The installed distribution name is `trainer`, not the repository name.
- TensorFlow 2.x is not the default fit here because the source relies on
  `tf.contrib`, `tf.app.flags`, and `tf.python_io`.
- Dense and sparse trainer modules register global flags at import time, so run
  them in separate Python processes.
- Use the bundled scripts under each sub-skill instead of pointing future
  agents back to the original checkout.

## Helpful root files

- `references/repo-provenance.md` records the source snapshot and refresh
  baseline.
- `references/repo-routing-metadata.json` places this skill in the router.
- `references/installation.md` captures the public install guidance.
- `references/troubleshooting.md` collects cross-cutting failure modes.

## Minimal smoke check

When you only need a quick environment check, run:

```bash
python scripts/check_tf1_environment.py
```

Add `--check-serving` when the serving extras are installed and you want to
verify the Python serving imports too.

## Common task routing cues

- CSV, LIBSVM, TFRecords, iris fixture, or DICOM labels file questions usually
  belong to `data-preparation`.
- Model architecture, optimizer, checkpoint, export, or TensorBoard questions
  usually belong to `training-and-export`.
- PredictRequest construction, benchmark mode, or HTTP wrapper questions
  usually belong to `serving-and-clients`.

If a task spans routes, start with the most concrete file or payload shape and
then follow the linked sub-skill references.
