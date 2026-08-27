---
name: task-apis
description: "Use AutoKeras supervised task APIs for image, text, and
  structured-data classification and regression workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# AutoKeras task APIs

Use this sub-skill when the user wants AutoKeras' high-level supervised task classes rather than a custom `AutoModel` graph:

- `ak.ImageClassifier` and `ak.ImageRegressor`
- `ak.TextClassifier` and `ak.TextRegressor`
- `ak.StructuredDataClassifier` and `ak.StructuredDataRegressor`

## Fast route

1. Set the Keras backend before importing Keras or AutoKeras.
2. Pick the task class by input modality and target type.
3. Keep first runs small: `max_trials=1`, `epochs=1`, explicit `directory=...`, and `overwrite=True` for disposable smoke checks.
4. Pass data in the shape expected by the task class; use `validation_data` for deterministic tiny checks or a non-zero `validation_split` for ordinary training.
5. Call `fit`, then `predict`, `evaluate`, or `export_model` depending on the requested deliverable.

Read [references/api-reference.md](references/api-reference.md) for verified constructor arguments and method behavior. Read [references/data-formats.md](references/data-formats.md) when data shape, `column_names`, `column_types`, label encoding, or CSV/DataFrame handling matters. Read [references/workflows.md](references/workflows.md) for image, text, and structured-data recipes that avoid external downloads. Read [references/troubleshooting.md](references/troubleshooting.md) when a run fails or behaves unexpectedly.

## Bundled offline helpers

Run these helpers with `--help` first. They default to dry-run construction so future agents can inspect setup without launching a model search; add `--run-fit` only for a tiny local smoke run.

- [scripts/run_tiny_image_task.py](scripts/run_tiny_image_task.py) constructs or runs an image classifier/regressor on synthetic arrays.
- [scripts/run_tiny_text_task.py](scripts/run_tiny_text_task.py) constructs or runs a text classifier/regressor on synthetic full-sentence strings.
- [scripts/run_tiny_structured_task.py](scripts/run_tiny_structured_task.py) constructs or runs a structured-data classifier/regressor on tiny mixed tabular data.

## Route elsewhere

- Custom topologies, blocks, multimodal inputs, multitask outputs, or manual `AutoModel` graphs: [../automodel-customization/SKILL.md](../automodel-customization/SKILL.md).
- Tuner selection, search persistence, `overwrite`, objectives, callbacks, `export_model`, or reloading saved Keras models: [../search-and-export/SKILL.md](../search-and-export/SKILL.md).
- Benchmark-scale timing, downloaded public datasets, Colab/Drive workflows, Docker, or release automation are not part of this operating sub-skill.
