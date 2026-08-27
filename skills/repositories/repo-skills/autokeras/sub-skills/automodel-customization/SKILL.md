---
name: automodel-customization
description: "Build custom AutoKeras AutoModel graphs, blocks, multimodal
  inputs, and multitask outputs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# AutoModel customization

Use this sub-skill when a task needs more control than the one-class task APIs provide: custom blocks, functional graph topology, multimodal inputs, multitask outputs, or explicit node/block/head wiring.

## Fast route

1. Choose input nodes: `ak.ImageInput()`, `ak.TextInput()`, `ak.StructuredDataInput(...)`, or generic `ak.Input()`.
2. Connect nodes through blocks and reductions using Keras-functional style calls.
3. End every output branch with a `ClassificationHead` or `RegressionHead`.
4. Build `ak.AutoModel(inputs=..., outputs=..., max_trials=..., overwrite=...)`.
5. Pass `x` and `y` to `fit` in the same nesting/order as `inputs` and `outputs`.

Read [references/api-reference.md](references/api-reference.md) for verified AutoModel, node, block, and head signatures. Read [references/custom-search-spaces.md](references/custom-search-spaces.md) for custom topology recipes. Read [references/multimodal-multitask.md](references/multimodal-multitask.md) for ordered multiple input/output workflows. Read [references/troubleshooting.md](references/troubleshooting.md) for graph connectivity, array-count, backend, pretrained, and runtime failures.

## Bundled helpers

Run helpers with `--help` first. They default to safe dry-run construction and use synthetic data.

- [scripts/build_tiny_custom_image_automodel.py](scripts/build_tiny_custom_image_automodel.py) builds a small image custom search graph.
- [scripts/build_tiny_multimodal_automodel.py](scripts/build_tiny_multimodal_automodel.py) builds a two-input, two-output multimodal/multitask graph.

## Route elsewhere

- High-level `ImageClassifier`, `TextClassifier`, or `StructuredDataClassifier` style workflows: [../task-apis/SKILL.md](../task-apis/SKILL.md).
- Tuner selection, search directories, export/reload, callbacks, objectives, or old search cleanup: [../search-and-export/SKILL.md](../search-and-export/SKILL.md).
