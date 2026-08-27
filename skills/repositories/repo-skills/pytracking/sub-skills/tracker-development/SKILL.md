---
name: tracker-development
description: "Implement, adapt, and debug PyTracking tracker packages and
  parameter modules safely, including BaseTracker contracts, registration,
  output dictionaries, multi-object/segmentation conventions, and runtime
  checkpoint handoff."
disable-model-invocation: true
metadata:
  disco-role: operating
license: GPL 3.0
---

# Tracker Development

Use this sub-skill when a task asks to **create, adapt, review, or debug a PyTracking tracker implementation or parameter file**. This includes tracker package layout, `BaseTracker.initialize()` / `track()` contracts, `get_tracker_class()` registration, `TrackerParams` and feature parameters, output dictionaries, segmentation or multi-object conventions, and connecting an LTR-trained checkpoint to a runtime parameter module.

Do **not** use this sub-skill to run evaluations, videos, webcams, or experiments; route command execution to `tracking-evaluation`. Route full training, training-setting edits, and checkpoint creation to `ltr-training`. Route saved-result analysis, plots, VOS metrics, VOT packaging, and benchmark submission packaging to `analysis-and-packaging`.

## Fast routing

- Need the file layout and implementation checklist for a new tracker and parameter module: read [references/extension-guide.md](references/extension-guide.md).
- Need `TrackerParams`, `FeatureParams`, `Choice`, feature extractors, `TensorList`, DCF/Fourier/optimization utilities, or checkpoint handoff details: read [references/parameter-and-library-api.md](references/parameter-and-library-api.md).
- Need symptom-to-fix guidance for import errors, missing `parameters()`, bad output keys, segmentation/multi-object mistakes, or checkpoint loading failures: read [references/troubleshooting.md](references/troubleshooting.md).
- Need a safe static layout check without importing tracker code: run [scripts/validate_tracker_layout.py](scripts/validate_tracker_layout.py).

## Standard development loop

1. Choose a Python module-safe tracker package name such as `mytracker`; this becomes both the runtime tracker name and the folder under `pytracking/tracker/` and `pytracking/parameter/`.
2. Implement a class inheriting `BaseTracker` and provide `initialize(self, image, info) -> dict` and `track(self, image, info=None) -> dict`.
3. Register the class in the tracker package `__init__.py` with `get_tracker_class()`.
4. Create at least one parameter module with `parameters()` returning a `TrackerParams` object.
5. Connect checkpoints through runtime parameters only after the selected `.pth` or `.pth.tar` file is present under the user's configured network path, or after the user explicitly chooses an absolute path.
6. Validate the layout statically before trying imports or tracker runs.

```bash
python skills/disco/pytracking/sub-skills/tracker-development/scripts/validate_tracker_layout.py \
  --repo-root /path/to/pytracking-checkout \
  --tracker-name mytracker \
  --param-name default
```

## Guardrails

- Keep runtime tracker output dictionaries compatible with the PyTracking evaluator; do not invent result keys that replace `target_bbox`.
- Do not run dataset/video/webcam/experiment commands from this sub-skill. After static layout and parameter review, hand execution to `tracking-evaluation`.
- Do not start or modify LTR training here. If the needed network does not exist yet, hand the training task to `ltr-training`.
- Do not analyze benchmark results or package submissions here; use `analysis-and-packaging`.
- Do not make future agents depend on hidden inspection environments or generated review artifacts. Use only the user's checkout and the bundled helper script.
