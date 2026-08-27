---
name: data-and-config
description: "Author, validate, and troubleshoot SimpleTuner dataloader and
  configuration backend workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: AGPL 3.0
---

# data-and-config

Use this sub-skill when a task is about SimpleTuner configuration backends, `data_backend_config`, dataloader JSON structure, dataset backends, cache datasets, captions/metadata, or data preparation for image/video/audio/conditioning/ControlNet runs.

This is an operating sub-skill: keep work self-contained, use the bundled references and scripts here, and do not require access to the original source checkout.

## Route by task

- **Find or author the active training config and `data_backend_config` path:** read [references/configuration-backends.md](references/configuration-backends.md).
- **Author or review a dataloader JSON/TOML/env-backed dataset plan:** read [references/dataloader-schema.md](references/dataloader-schema.md), then run [scripts/validate_dataloader_config.py](scripts/validate_dataloader_config.py) on the JSON dataloader file.
- **Prepare captions, metadata, caches, image/video/audio data, grounding annotations, or ControlNet conditioning:** read [references/data-preparation.md](references/data-preparation.md). For Canny ControlNet data, use [scripts/make_controlnet_canny_edges.py](scripts/make_controlnet_canny_edges.py).
- **Diagnose empty datasets, filtering, cache, credential, caption, audio, or conditioning failures:** read [references/troubleshooting.md](references/troubleshooting.md) first, then re-check the dataloader with the validator.

## Boundaries

Handle here:

- `CONFIG_BACKEND`, `CONFIG_PATH`, `ENV`, `SIMPLETUNER_ENV`, `SIMPLETUNER_ENVIRONMENT`, `SIMPLETUNER_CONFIG_BACKEND`, `CONFIG_TYPE`, and `DATALOADER_CONFIG` only as they affect config selection and `data_backend_config`.
- Dataset `type` values `local`, `aws`, `memory`, `csv`, `huggingface`, and `webshart`.
- Dataset `dataset_type` values `image`, `video`, `audio`, `text_embeds`, `image_embeds`, `conditioning_image_embeds`, and `conditioning`.
- Text/image/conditioning caches, default text embed cache selection, captions, filtering, bbox/grounding annotations, and ControlNet conditioning directories.

Reroute out of this sub-skill:

- Training launch, Accelerate, distributed, DeepSpeed, FSDP, checkpoint resume topology, and GPU runtime tuning to `training-workflows`.
- Model-family selection, adapter extraction/conversion, LyCORIS/LoRA export, CaptionFlow, distillation, and model registry work to `model-and-adapter-tooling`.
- WebUI/API/queue/server operation to `webui-and-operations`.
- Source-code changes, WebUI dataset blueprint/template changes, docs translation updates, and test selection to `repo-development`. When a dataloader option is added or changed in code, explicitly ask the maintainer workflow to update the WebUI dataset blueprint/template surface as well.

## Safe operating checklist

1. Resolve the config backend and environment before editing paths. If the user only gives an environment name, inspect which of `config.json`, `config.toml`, or `config.env` is actually selected by SimpleTuner rules.
2. Treat the dataloader as a JSON array of dataset entries unless a wrapper service has provided an object with a `datasets` array.
3. Ensure enabled training plans have at least one primary dataset (`image`, `video`, or `audio`) and a usable `text_embeds` cache, unless the task is intentionally about a cache-only or maintenance case.
4. Keep cache directories separated by role. Do not reuse a VAE cache, text embed cache, conditioning image embed cache, or memory backend mount unintentionally.
5. For ControlNet or reference conditioning, validate both the source dataset and conditioning dataset side: matching stems, `conditioning_data`, `conditioning_type`, and `source_dataset_id` where strict alignment is required.
6. Do not run network, model download, training, cloud, or destructive data commands unless the user explicitly asks for them. The bundled validator is local-only; the Canny helper only writes under user-provided output directories and refuses overwrites unless requested.

## Bundled commands

```bash
python skills/disco/simple-tuner/sub-skills/data-and-config/scripts/validate_dataloader_config.py \
  --input config/multidatabackend.json --expect-training-set
```

```bash
python skills/disco/simple-tuner/sub-skills/data-and-config/scripts/make_controlnet_canny_edges.py \
  --input-dir datasets/source-images \
  --output-original-dir datasets/controlnet/images \
  --output-edges-dir datasets/controlnet/canny
```

## Evidence basis

This sub-skill distills repository-relative evidence from `documentation/DATALOADER.md`, `documentation/data_presets/*.md`, `documentation/HUGGINGFACE_DATASETS.md`, `documentation/CONTROLNET.md`, `config/*.example`, `simpletuner/helpers/configuration/*`, `simpletuner/helpers/data_backend/*`, `simpletuner/simpletuner_sdk/server/data/dataset_blueprints.py`, `tests/test_backend_config.py`, `tests/test_config*.py`, `tests/test_dataset*.py`, `tests/helpers/data_backend/*`, and `scripts/datasets/controlnet/create_canny_edge.py`.
