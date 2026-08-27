---
name: finetuning
description: "Guide InternLM-XComposer supervised finetuning, data manifests,
  runnable launchers, DeepSpeed configs, LoRA settings, and adapter merge."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Finetuning Sub-skill

Use this sub-skill for supervised finetuning of InternLM-XComposer family models, especially the 2.5 training path. It covers:

- `data.json` and `data.txt` preparation for text-only, single-image, and multi-image samples;
- 2.5 placeholder rules, plus legacy 1.0/2.0 compatibility notes;
- torchrun + DeepSpeed templates and manual FSDP planning on the same `finetune.py` entrypoint;
- full-parameter and LoRA training arguments;
- PEFT adapter loading and `merge_peft_adapter.py` merge planning;
- the file-level data-mixing behavior used by the loader.

Route non-training tasks to sibling sub-skills:

- inference, Gradio, LMDeploy, and composition: `model-inference`;
- reward scoring or preference training: `reward-model`;
- benchmarks, converters, and related projects: `evaluation-and-projects`;
- OmniLive audio/video/service workflows: `omnilive`.

## Quick compatibility notes

- InternLM-XComposer 2.5 uses `conversations` in actual JSON examples and loader code.
- 2.5 single-image samples do not require `<ImageHere>`; multi-image samples should keep one `<ImageHere>` token per image, in order.
- 2.0 finetuning examples require `<ImageHere>` on image-bearing samples.
- 1.0 legacy finetuning examples are placeholder-free in the published README guidance.

## Operating checklist

1. Identify the target family: 2.5 default, or 2.0 / 1.0 compatibility guidance.
2. Validate the manifest with `scripts/validate_finetune_data.py`.
3. Render a safe command with `scripts/render_finetune_command.py` when planning only.
4. For approved execution, use the bundled runnable training bundle in `entrypoints/xcomposer25/` instead of relying on source checkout files.
5. If using LoRA, keep both training and `entrypoints/xcomposer25/merge_peft_adapter.py` aligned with `references/workflows.md`.
6. Review `references/troubleshooting.md` before changing batch size, `hd_num`, `max_length`, or backend flags.

## Bundled references

- `references/data-formats.md`
- `references/workflows.md`
- `references/training-arguments.md`
- `references/troubleshooting.md`

## Bundled scripts and entrypoints

Safe planners/validators:

- `scripts/validate_finetune_data.py`
- `scripts/render_finetune_command.py`

Runnable self-contained entrypoints:

- `entrypoints/xcomposer25/finetune.py`
- `entrypoints/xcomposer25/data_mix.py`
- `entrypoints/xcomposer25/ixc_utils.py`
- `entrypoints/xcomposer25/ds_config_zero2.json`
- `entrypoints/xcomposer25/launch_full.sh`
- `entrypoints/xcomposer25/launch_lora.sh`
- `entrypoints/xcomposer25/merge_peft_adapter.py`
- `entrypoints/xcomposer25/data.txt` and `entrypoints/xcomposer25/data/` source-format fixtures

Read `entrypoints/xcomposer25/README.md` before running any entrypoint. These files are real training/merge entrypoints and will import torch/Transformers/DeepSpeed/PEFT, load checkpoints, and write outputs when executed.

## Boundaries

- Do not start actual training, checkpoint download, or merge execution in Creator mode.
- Do not depend on the source checkout remaining available after the skill is drafted; use the bundled references and scripts instead.
- Keep launcher advice self-contained and edit-safe; let the user choose exact paths, GPUs, and ports.
