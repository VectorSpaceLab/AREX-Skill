---
name: sliced-inference
description: "Guide SAHI standard and sliced prediction APIs, CLI commands,
  slicing choices, batching, exports, progress callbacks, and video
  visualization."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# sliced-inference

Use this sub-skill when the task is to build or debug SAHI prediction calls: `AutoDetectionModel`, `get_prediction`, `get_sliced_prediction`, high-level `predict`, `predict-fiftyone`, `sahi predict`, folder or video inference, slicing parameters, progress reporting, batching, and prediction export routing.

Do not use it as the owner for detector-specific installation or weights. Route those questions to `../model-integrations/SKILL.md`. Route COCO conversion/evaluation to `../dataset-tools/SKILL.md`, postprocess backend internals to `../postprocess-backends/SKILL.md`, and result object serialization details to `../annotations-and-results/SKILL.md`.

## Start here

1. Choose the API surface in [CLI and Python workflows](references/cli-and-python.md):
   - `get_prediction` for one standard full-image call.
   - `get_sliced_prediction` for one image with tiles and optional standard+slice aggregation.
   - `predict` / `sahi predict` for files, folders, videos, and automatic exports.
   - `predict-fiftyone` for interactive FiftyOne review when that optional dependency is installed.
2. Choose the inference mode:
   - Standard only: disable sliced prediction.
   - Sliced only: disable standard prediction.
   - Standard+sliced: default for sliced workflows; useful when small and large objects both matter.
3. Tune `slice_height`, `slice_width`, overlap, batching, progress, and duplicate handling with [Slicing parameters](references/slicing-parameters.md).
4. If behavior is wrong, use [Troubleshooting](references/troubleshooting.md) before changing model code.
5. To validate that base SAHI prediction plumbing works without model weights or downloads, run the bundled [synthetic smoke script](scripts/sliced_prediction_smoke.py).

## Safe local smoke

From this sub-skill directory, run:

```bash
python scripts/sliced_prediction_smoke.py --mode sliced --slice-size 128 --batch-size 2
```

The smoke script constructs a deterministic in-memory `DetectionModel` subclass, creates a synthetic image, exercises the selected prediction path, asserts expected result structure, and prints success. It does not download weights, contact a network service, train a model, or write outputs by default.

## Boundaries and assumptions

- A real detector still needs a supported `model_type`, installed optional backend packages, and accessible local weights or model objects; this sub-skill only shows how those model objects are used by prediction APIs.
- Optional detector frameworks were not assumed to be installed or runtime-verified here.
- COCO result JSON export is covered only as prediction-output routing. Dataset conversion, slicing, evaluation, and error analysis belong to `../dataset-tools/SKILL.md`.
- NMS/NMM/GreedyNMM parameter placement is covered here; algorithm details and backend acceleration belong to `../postprocess-backends/SKILL.md`.
