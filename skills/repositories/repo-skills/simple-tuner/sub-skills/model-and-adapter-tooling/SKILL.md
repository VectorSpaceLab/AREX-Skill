---
name: model-and-adapter-tooling
description: "Choose SimpleTuner model families, adapters, LoRA formats,
  conversion/extraction tools, CaptionFlow, Prompt2Effect, and
  distillation/experimental workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: AGPL 3.0
---

# SimpleTuner model and adapter tooling

Use this sub-skill when a task is about selecting a SimpleTuner model family or flavour, choosing PEFT/LyCORIS/ControlNet/slider adapter settings, loading or exporting LoRA formats, inspecting the model registry, merging sharded safetensors, planning CaptionFlow, Prompt2Effect, distillation, evaluation, or experimental regularizers.

## First actions

1. Identify the user's requested output: training config advice, adapter format decision, checkpoint conversion/extraction, registry inspection, CaptionFlow setup, Prompt2Effect planning, or distillation/evaluation planning.
2. Confirm the model identity in SimpleTuner terms: `model_family`, `model_flavour`, `model_type`, `lora_type`, `lora_format`, and whether the run is plain LoRA, LyCORIS, ControlNet, full-rank, validation-only, or adapter conversion only.
3. If the request can mutate checkpoints, write model files, merge shards, download models, train, caption datasets, run Prompt2Effect, or run a distillation/evaluation job, stop and get explicit user approval for the side effect, target paths, and expected cost before continuing.
4. Use the references below instead of reopening the source checkout:
   - [Model registry and adapters](references/model-registry-and-adapters.md)
   - [Conversion and extraction](references/conversion-and-extraction.md)
   - [Distillation and experimental features](references/distillation-and-experimental.md)
   - [Troubleshooting](references/troubleshooting.md)

## Bundled safe helpers

These helpers are read-only or dry-run by default and do not download models, train, or submit cloud jobs.

- Inspect installed registry metadata without importing every heavy model class:

  ```bash
  python skills/disco/simple-tuner/sub-skills/model-and-adapter-tooling/scripts/inspect_model_registry.py --format markdown
  ```

- Preflight sharded safetensors and duplicate tensor keys before any write:

  ```bash
  python skills/disco/simple-tuner/sub-skills/model-and-adapter-tooling/scripts/merge_safetensors_shards.py \
    --src-dir PATH/TO/SHARDS \
    --dst-file PATH/TO/MERGED.safetensors \
    --dry-run --json
  ```

Only run the merge with `--no-dry-run` after the user approves the output file. Use `--overwrite` only when the user explicitly approves replacing an existing file.

## Routing boundaries

- Reroute dataloader layouts, cache directories, paired reference datasets, conditioning schemas, and dataset validation to `data-and-config`.
- Reroute generic `simpletuner train`, distributed, DeepSpeed/FSDP, memory/offload, checkpoint resume, and validation scheduling to `training-workflows`.
- Reroute WebUI server/API/job queue/cloud worker flow to `webui-and-operations`.
- Reroute code changes, tests, documentation/translations, and public-text privacy checks to `repo-development`.

## Fast decision checklist

- Registry inspection: use `inspect_model_registry.py`; do not instantiate model classes unless a task explicitly needs runtime class behavior.
- PEFT LoRA: use `model_type: "lora"`, `lora_type: "standard"`, and model-family target defaults unless the user has a known target-module reason.
- LyCORIS/LoKr: use `lora_type: "lycoris"` and a `lycoris_config`; do not reuse generic target names for Flux.2 without checking the Flux.2 target guidance.
- ControlNet: pair image data with conditioning data and set `controlnet: true`; route conditioning layout details to `data-and-config`.
- LoRA export format: keep Diffusers/PEFT for SimpleTuner or Diffusers continuation; choose ComfyUI-style only for user-requested ComfyUI-compatible artifacts and model families that support the selected mapping.
- Prompt2Effect: plan manifest, prepare, train, and generate phases; treat it as checkpoint-writing/training work requiring approval.
- Distillation: text encoder training is blocked for SimpleTuner distillation methods; most methods are expensive and dataset-sensitive.

## Source evidence distilled

This sub-skill is distilled from `documentation/QUICKSTART.md`, selected `documentation/quickstart/*.md`, `documentation/LYCORIS.md`, `documentation/CONTROLNET.md`, `documentation/CAPTIONFLOW.md`, `documentation/SLIDER_LORA.md`, `documentation/TREAD.md`, `documentation/distillation/*.md`, `documentation/experimental/*.md`, `documentation/evaluation/*.md`, `simpletuner/helpers/models/model_metadata.json`, `simpletuner/helpers/models/registry.py`, `simpletuner/helpers/training/lora_format.py`, conversion/extraction source scripts, Prompt2Effect source scripts, and focused adapter/registry/distillation tests.
