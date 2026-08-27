---
name: luminoth
description: "Routes Luminoth object-detection dataset, training, prediction,
  and checkpoint workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# Luminoth

Luminoth is an alpha TensorFlow 1.x object-detection toolkit. Use this skill for
workflow guidance around dataset conversion, training, evaluation, prediction,
checkpoint packaging, and the demo web app.

This skill is self-contained for future agents. Do not depend on the original
checkout after reading the bundled references and scripts.

## Read first

- `references/repo-provenance.md` when checking whether this skill still matches
the repository snapshot you are using.
- `references/installation.md` for supported Python/TensorFlow versions,
optional extras, and a minimal install smoke.
- `references/troubleshooting.md` for cross-cutting install, import, and runtime
failures.
- `scripts/check_luminoth_install.py` for a safe import and CLI smoke check.
- `references/repo-routing-metadata.json` if you need to understand how this
skill is meant to be routed by a managed repo-skills router.

## Route by task

| User goal | Read or run | Notes |
| --- | --- | --- |
| Convert or merge object-detection datasets | [sub-skills/dataset-preparation/SKILL.md](sub-skills/dataset-preparation/SKILL.md) | Covers `lumi dataset transform`, `lumi dataset merge`, reader layouts, `classes.json`, TFRecord output, and dataset validation. |
| Train or evaluate a model locally or in Google Cloud | [sub-skills/training/SKILL.md](sub-skills/training/SKILL.md) | Covers `lumi train`, `lumi eval`, config files, overrides, TensorBoard, and the optional `lumi cloud gc` workflow. |
| Predict images or videos, serve the demo web app, or use the Python API | [sub-skills/prediction/SKILL.md](sub-skills/prediction/SKILL.md) | Covers `lumi predict`, `lumi server web`, `Detector`, `read_image`, and `vis_objects`. |
| Inspect, download, import, export, or package checkpoints | [sub-skills/checkpoints/SKILL.md](sub-skills/checkpoints/SKILL.md) | Covers the local checkpoint index, remote index refresh, alias/id rules, and checkpoint tarballs. |

## What to do before deeper work

- Run the bundled install smoke if you only need to confirm the package is
importable:

  ```bash
  python scripts/check_luminoth_install.py
  ```

- Use the sub-skill that owns the workflow instead of mixing several routes in
one place. In particular:
  - dataset conversion belongs before training,
  - checkpoints belong before prediction or web serving,
  - training/eval configuration belongs before `lumi eval`, and
  - Google Cloud usage is an optional branch of the training sub-skill, not a
    separate root route.

## Quick capability map

- Public CLI entry point: `lumi`.
- Main model families: Faster R-CNN and SSD.
- Dataset registry: `object_detection` / `tfrecord`.
- Supported dataset readers: `coco`, `csv`, `flat`, `imagenet`, `openimages`,
`pascal`, and `taggerine`.
- Common prediction fallback: `accurate` checkpoint when neither config nor
checkpoint is specified.

## When to read the root references

Use the root references when you need cross-cutting information that is shared
by several sub-skills:

- installation details and supported dependency groups,
- TensorFlow / FFmpeg / Google Cloud prerequisites,
- deprecation or maintenance caveats,
- staleness checks for the generated skill, and
- router metadata for managed import or refresh decisions.

## Cross-skill routing reminders

- If the request starts with raw data and no TFRecords, route to dataset
preparation first.
- If the request is about a run directory, checkpoint alias, remote checkpoint,
or tarball, route to checkpoints.
- If the request is about `lumi predict`, the Flask demo, image/video inputs, or
Python inference APIs, route to prediction.
- If the request is about `lumi train`, `lumi eval`, config merging, TensorBoard,
or Google Cloud training, route to training.

## Maintenance note

Read `references/repo-provenance.md` before deciding whether this skill is
fresh enough for the current checkout. If the repo commit, dirty state, package
version, or supported workflows changed, refresh this skill instead of guessing.
