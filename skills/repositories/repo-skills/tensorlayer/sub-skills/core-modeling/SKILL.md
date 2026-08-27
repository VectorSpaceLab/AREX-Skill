---
name: core-modeling
description: "Routes TensorLayer layer, model, serialization, and
  pretrained-constructor workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Core Modeling

Use this sub-skill for TensorLayer layer composition, custom model classes, pretrained constructors, and save/load behavior. This is the route for model-building questions that stay inside the core TensorLayer API surface.

## Typical requests

- Build a static `Input -> layer -> Model` network.
- Write a custom `Model` subclass.
- Save or restore weights or model state.
- Compare static and dynamic TensorLayer model patterns.
- Instantiate pretrained vision constructors with `pretrained=False`.

## Read first

- `references/api-reference.md` for verified signatures and supported model APIs.
- `references/workflows.md` for tiny model patterns and round-trip recipes.
- `references/troubleshooting.md` for import, naming, serialization, and constructor failures.

## Bundled check

- `scripts/smoke_model.py` builds a tiny dense model, runs a forward pass, saves and reloads weights, and can optionally instantiate the main pretrained image constructors without downloading weights.

## Boundaries

Include here:
- `tensorlayer.layers`
- `tensorlayer.models`
- `tensorlayer.activation`
- `tensorlayer.cost`
- `tensorlayer.initializers`
- `tensorlayer.optimizers`
- save/load and model-naming behavior

Exclude or route elsewhere:
- data loading, preprocessing, TFRecord, or visualization helpers -> `data-and-utilities`
- `tl.utils.fit/test/predict`, `tl train`, or distributed execution -> `training-and-cli`
- object detection, pose wrappers, and application tutorials -> `vision-and-apps`
- text, seq2seq, and NLP helpers -> `text-and-sequence`
- reward utilities and RL examples -> `reinforcement-learning`

## Fast path

1. Build the smallest model that matches the question.
2. Keep `pretrained=False` unless the user explicitly needs weights.
3. Use the smoke script before expanding the architecture.
