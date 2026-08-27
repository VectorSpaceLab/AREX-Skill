---
name: data-and-config
description: "Parse, edit, and validate CVNets configs and data layouts."
metadata:
  disco-role: operating
disable-model-invocation: true
license: NOASSERTION
---

# Data and Config

Use this sub-skill when the user needs to understand or change a CVNets YAML config, dataset root, sampler, collate function, transform pipeline, tokenizer, or video-reader layout.

This sub-skill owns the dotted-option conventions, config loading, dataset registration, sampler and collate selection, augmentation plumbing, tokenizer settings, and the data formats behind image, audio, video, ByteFormer, and CLIP workflows. It does not own the training loop or the model-family choice itself.

## Read these first

- `../../references/api-reference.md` — parser and loader contracts.
- `../../references/configuration.md` — common config sections and override rules.
- `../../references/model-overview.md` — which `dataset.category` points at which model family.
- `references/data-formats.md` — dataset, tokenizer, byte, and video layout details.
- `references/troubleshooting.md` — config, dataset-root, tokenizer, and optional-backend failures.
- `../../scripts/inspect_config.py` — inspect a config without running training.
- `../../scripts/check_install.py` — confirm optional audio/video/export dependencies.

## Owns

- YAML config structure and dotted-key semantics.
- Dataset roots, split names, and dataset/category registration.
- Samplers, collate functions, transforms, and tokenizers.
- Image-text zero-shot layouts, byte-based image/audio recipes, and video-reader settings.
- Quick config inspection and option-override validation.

## Excludes

- Choosing or debugging the architecture family; route to `models-and-architectures`.
- Training, resume, finetuning, or evaluation orchestration; route to `training-and-evaluation`.
- CoreML conversion, benchmark throughput, and loss-landscape generation; route to `conversion-and-profiling`.

## Workflow

1. Inspect the config with `scripts/inspect_config.py` before touching the command line.
2. Confirm `dataset.category`, `dataset.name`, the relevant `dataset.root_*` fields, and the matching `model.<category>.name`.
3. Choose the sampler and collate names that match the modal data path.
4. Check whether the workflow depends on CLIP tokenizer files, byte encodings, PyAV/decord, or other optional extras.
5. If the config is the only problem, fix it here before involving the training or model sub-skill.

## Common signals

- `load_config_file` flattens YAML into dotted keys and warns on unexpected entries.
- `--common.override-kwargs` is for small targeted overrides, not for inventing new registry entries.
- `dataset.collate_fn_name_*` controls the collate function for train, val, and test.
- `sampler.name` and the `sampler.bs.*` or `sampler.vbs.*` settings determine the batch and crop behavior.
- `text_tokenizer.clip.*`, `video_reader.*`, `image_augmentation.*`, `audio_augmentation.*`, and `dataset.root_*` are the most common locations for modality-specific mistakes.

## When to switch away

- If the config is fine and the failure is in the model family, switch to `models-and-architectures`.
- If the config is fine and the failure is in the training or evaluation loop, switch to `training-and-evaluation`.
- If the config is fine and the failure is in conversion or profiling, switch to `conversion-and-profiling`.
