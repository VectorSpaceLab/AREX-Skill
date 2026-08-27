---
name: search-and-export
description: "Configure AutoKeras search, tuners, persistence, callbacks,
  export_model, and saved Keras model reloads."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# AutoKeras search and export

Use this sub-skill when the request is about controlling AutoKeras search behavior, tuner selection, objectives, search directories, callbacks, persistence, `overwrite`, model export, or reloading saved Keras models.

## Fast route

1. For smoke checks, set `max_trials=1`, `epochs=1`, `overwrite=True`, and an explicit scratch `directory`.
2. For real searches, choose a stable `directory`/`project_name`, decide whether to resume (`overwrite=False`) or start fresh (`overwrite=True`), and set an objective compatible with the metrics/losses.
3. Choose `tuner` from `"greedy"`, `"random"`, `"hyperband"`, `"bayesian"`, or pass a tuner class.
4. Use `callbacks` and `epochs` deliberately; `epochs=None` can trigger adaptive early stopping.
5. After fitting, call `export_model()`, save with Keras, and reload with `custom_objects=ak.CUSTOM_OBJECTS` when AutoKeras custom layers are present.

Read [references/search-configuration.md](references/search-configuration.md) for constructor and `fit` controls. Read [references/tuner-reference.md](references/tuner-reference.md) for tuner names/classes and task-specific defaults. Read [references/export-and-reload.md](references/export-and-reload.md) for saving and loading exported Keras models. Read [references/troubleshooting.md](references/troubleshooting.md) for invalid tuner names, missing validation data, stale search directories, objective mismatches, OOM, slow searches, and custom-object reload errors.

## Bundled helper

- [scripts/export_tiny_model.py](scripts/export_tiny_model.py) constructs or optionally fits/exports/reloads a tiny offline AutoKeras model. It defaults to dry-run mode; use `--run-fit` only when a tiny local search is acceptable.

## Route elsewhere

- Image/text/structured task setup and data formats: [../task-apis/SKILL.md](../task-apis/SKILL.md).
- Custom `AutoModel` graph topology, nodes, blocks, heads, multimodal or multitask composition: [../automodel-customization/SKILL.md](../automodel-customization/SKILL.md).
