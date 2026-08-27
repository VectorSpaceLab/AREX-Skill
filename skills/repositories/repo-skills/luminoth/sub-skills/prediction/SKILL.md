---
name: prediction
description: "Runs Luminoth image and video predictions, demo web serving, and
  public Detector/read_image/vis_objects API workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# Luminoth Prediction

Use this sub-skill for Luminoth inference workflows: `lumi predict` over images
or videos, `lumi server web`, and the public Python API exposed as
`Detector`, `read_image`, and `vis_objects`.

Before acting, use the root router at [../../SKILL.md](../../SKILL.md) when the
user's request may also involve installation, package-level troubleshooting, or
another Luminoth workflow.

## Route by task

| User goal | Use this file | Notes and cross-links |
| --- | --- | --- |
| Run one or many image predictions | [references/workflows.md](references/workflows.md#image-prediction-cli) | Produces JSON lines for images and can save annotated images. |
| Run video predictions | [references/workflows.md](references/workflows.md#video-prediction-cli) | Requires video dependencies; video JSON output is intentionally not emitted. |
| Predict a mixed directory of images and videos | [references/workflows.md](references/workflows.md#mixed-directory-jobs) and [scripts/check_prediction_inputs.py](scripts/check_prediction_inputs.py) | The bundled checker reports recognized files, ignored suffixes, class-filter conflicts, and ffmpeg availability. |
| Serve the demo web app or call its POST API | [references/workflows.md](references/workflows.md#demo-web-server-and-post-api) | This is a demo interface, not production serving. |
| Use Luminoth from Python | [references/api-reference.md](references/api-reference.md) | Covers `Detector(checkpoint=None, config=None, prob=0.7, classes=None)`, `read_image(path)`, and `vis_objects(...)`. |
| Diagnose prediction failures | [references/troubleshooting.md](references/troubleshooting.md) | Includes missing checkpoint, missing ffmpeg, media format, web API, and CLI misuse cases. |

## Boundary and handoff rules

- Stay here for inference, visualization, class filtering, media outputs,
  demo-server startup, and `/api/<model_name>/predict/` usage.
- Route checkpoint refresh/list/download/import/export, aliases, IDs, and local
  index repair to [../checkpoints/SKILL.md](../checkpoints/SKILL.md).
- Route training/evaluation, model configs, training run directories, and
  TensorBoard to [../training/SKILL.md](../training/SKILL.md).
- Route dataset conversion or TFRecord/class-file preparation to
  [../dataset-preparation/SKILL.md](../dataset-preparation/SKILL.md).
- Do not edit checkpoint indexes, package checkpoints, convert datasets, or run
  train/eval lifecycle tasks from this sub-skill.

## Common response shape

When a prediction request arrives, answer in this order:

1. Decide whether the user wants CLI output, saved media, the Flask demo, or
   the Python API.
2. Confirm whether a checkpoint, an explicit config, or the default `accurate`
   alias should be used.
3. Check the input media type and whether any video output requires FFmpeg.
4. Decide whether class filters, `--max-detections`, or `--min-prob` need to be
   mentioned in the final command.
5. If the task spans checkpoint discovery or package installation, route that
   part to the owning sibling sub-skill before continuing.

## Safe preflight

For CLI prediction jobs, especially mixed image/video directories, run the
bundled checker before invoking `lumi predict`:

```bash
# From this prediction sub-skill directory, or replace scripts/... with the
# absolute path to this bundled helper in the installed skill tree.
python scripts/check_prediction_inputs.py ./media --save-media-to ./preds --output ./preds/objects.json
```

The checker is self-contained and does not import Luminoth. It validates the
media paths and flags that Luminoth's prediction CLI will otherwise skip,
ignore, or fail on late.

## Good prediction handoffs

- If the user only needs a checkpoint id or alias, answer with the checkpoints
  sub-skill first and come back here only after the checkpoint exists.
- If the user only needs a config decision, answer with the training sub-skill
  first and come back here only after the run config is settled.
- If the user is asking for output interpretation, mention the JSON object shape
  and the media artifact that will be written.
- If the user is asking for code, prefer the Python API reference over CLI prose
  so the response stays aligned with the public signatures.

## Source artifact policy

The repository's prediction CLI and Flask demo are exposed by the installed
`lumi` entry point, so their source implementations are reference-only in this
skill. The bundled helper is a safe preflight tool rather than a copy of the
runtime prediction implementation: it performs no inference, network access,
checkpoint mutation, or writes except normal terminal output.
