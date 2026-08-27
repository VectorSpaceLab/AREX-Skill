---
name: models-and-architectures
description: "Choose, inspect, and debug CVNets model families."
metadata:
  disco-role: operating
disable-model-invocation: true
license: NOASSERTION
---

# Models and Architectures

Use this sub-skill when the user wants help choosing a CVNets model family, debugging a registry lookup, understanding how pretrained weights are loaded, or checking whether a model is exportable.

This sub-skill owns the model registry surface, the task-family map, the special cases around ByteFormer, CLIP, and audio/bytes workflows, and the expectations around pretrained loading and exportability. It does not own the full training loop or the dataset/config layout.

## Read these first

- `../../references/api-reference.md` — verified `get_model` and registry entry points.
- `../../references/configuration.md` — the keys that select a model family.
- `../../references/model-overview.md` — the repo-wide family summary.
- `references/model-overview.md` — deeper family notes and common shape expectations.
- `references/troubleshooting.md` — registry, pretrained, tokenizer, and export failures.
- `scripts/check_model_build.py` — safe model-build smoke from a config file.

## Owns

- Model-family selection and registry lookups.
- Pretrained model loading and reserved-name handling.
- ByteFormer, CLIP, audio classification, and other model families that are not just plain image backbones.
- Model-info and exportability expectations.
- Shape, class-count, and head/backbone compatibility questions.

## Excludes

- Training orchestration, DDP, checkpointing, and optimizer setup; route to `training-and-evaluation`.
- Dataset roots, sampler names, collate functions, tokenizers, and augmentation pipelines; route to `data-and-config`.
- CoreML conversion, benchmark throughput, and loss-landscape generation; route to `conversion-and-profiling`.

## Workflow

1. Identify the task category and the intended `model.<category>.name` value.
2. Check whether the model is a pure backbone, a task head, or a multimodal/audio family with extra inputs.
3. Confirm whether pretrained loading is intended and whether the checkpoint matches the head class count.
4. Use `scripts/check_model_build.py` for a safe registry/build smoke before guessing at the failure.
5. If the issue is really a config or dataset problem, hand off to `data-and-config` rather than forcing the model route.

## Common signals

- `get_model` uses the dataset category and model-name pair from the config.
- `model.info()` is the normal model summary path in the training/evaluation flows.
- `__base__` is a registry-only placeholder, not a final user-facing model name.
- Some families need additional tokenizer, byte-encoding, or export-specific inputs in addition to an image tensor.

## When to switch away

- If the config file itself is the problem, switch to `data-and-config`.
- If the user needs an actual train/eval run, switch to `training-and-evaluation`.
- If the user needs export, throughput, or loss-landscape commands, switch to `conversion-and-profiling`.
