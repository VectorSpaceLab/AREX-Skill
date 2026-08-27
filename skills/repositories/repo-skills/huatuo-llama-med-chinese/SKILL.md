---
name: huatuo-llama-med-chinese
description: "Guides Huatuo-Llama-Med-Chinese / BenTsao Chinese medical LLM
  inference, LoRA fine-tuning, prompt/data formats, and checkpoint export
  workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Huatuo-Llama-Med-Chinese / BenTsao

Use this repo skill for tasks about the Huatuo-Llama-Med-Chinese / BenTsao repository: Chinese medical instruction-tuned LLM adapters, LoRA inference, literature-dialogue inference, LoRA fine-tuning, prompt templates, medical QA data schemas, CMCOQA benchmark assets, and adapter checkpoint export.

This repository is script-oriented rather than an installable Python package. Treat its public operations as reproducible workflows around Transformers, PEFT, LoRA adapter directories, prompt templates, and JSON/JSONL data assets.

## Start here

1. Identify the user intent and route to the focused sub-skill below.
2. Read [references/model-overview.md](references/model-overview.md) when selecting a base-model family, LoRA adapter, prompt template, or resource profile.
3. Read [references/installation.md](references/installation.md) before constructing a runtime environment; `requirements.txt` does not include every required backend package.
4. Use [scripts/check_skill_assets.py](scripts/check_skill_assets.py) for a safe check of this skill's bundled files, and use sub-skill validators/builders for task-specific dry runs.
5. Read [references/troubleshooting.md](references/troubleshooting.md) before running expensive GPU/model workflows.
6. Read [references/repo-provenance.md](references/repo-provenance.md) when checking whether this skill is stale for a newer checkout.

## Route map

| User task | Read this |
| --- | --- |
| Build or review a command for medical QA inference, literature single-/multi-turn inference, Gradio serving, LoRA/template selection, or CUDA/model-asset readiness. | [sub-skills/inference/SKILL.md](sub-skills/inference/SKILL.md) |
| Plan LoRA instruction fine-tuning, choose training hyperparameters, validate training data, reason about W&B/DDP/checkpoints, or build a safe fine-tuning command. | [sub-skills/finetuning/SKILL.md](sub-skills/finetuning/SKILL.md) |
| Validate or edit prompt templates, instruction JSONL files, literature-dialogue JSON, knowledge-tuning text, or CMCOQA benchmark question assets. | [sub-skills/prompt-data-formats/SKILL.md](sub-skills/prompt-data-formats/SKILL.md) |
| Merge/export a LoRA adapter to Hugging Face `hf_ckpt/` or original LLaMA `ckpt/` layout, or diagnose `BASE_MODEL`/adapter/export issues. | [sub-skills/checkpoint-export/SKILL.md](sub-skills/checkpoint-export/SKILL.md) |

## Public workflow surfaces

- **Inference:** medical-knowledge QA, literature single-turn QA, literature multi-turn interactive QA, and Gradio-style serving over a base model plus LoRA adapter.
- **Fine-tuning:** PEFT LoRA supervised instruction tuning over JSONL records with `instruction`, `input`, and `output` fields.
- **Formats:** model-family prompt templates, response split markers, JSONL/JSON schemas, knowledge-tuning question samples, and CMCOQA benchmark questions.
- **Export:** CPU-side LoRA merge/export recipes for Hugging Face checkpoints and LLaMA-7B-compatible original state-dict layouts.

## Installation and runtime stance

- Use Python 3.9+; the original repository recommends Python 3.9 or later.
- Install a compatible ML stack for real model execution: Torch, Transformers, PEFT, Accelerate, SentencePiece, and task-specific extras such as Gradio, Datasets, W&B, and bitsandbytes.
- Do not assume `pip install -r requirements.txt` is sufficient for every task; Torch is imported by the scripts but is not listed there.
- Actual batch/literature inference and fine-tuning are GPU/model-asset workflows. The safe bundled scripts in this skill build commands or validate formats; they do not download model weights, load checkpoints, train, or serve.
- Treat generated medical answers as research outputs only, not clinical advice.

## Minimal safe checks

Run these checks before escalating to any model download, GPU run, or training job:

```bash
python scripts/check_skill_assets.py --skill-root .
python sub-skills/prompt-data-formats/scripts/validate_assets.py --asset-root <asset-root> --max-records 100
python sub-skills/inference/scripts/build_inference_command.py --help
python sub-skills/finetuning/scripts/build_finetune_command.py --help
python sub-skills/checkpoint-export/scripts/build_export_command.py --help
```

Replace `<asset-root>` with a directory containing compatible `templates/`, `data/`, `data-literature/`, and/or `benchmark/` assets. The validators and command builders are safe by default and use only the Python standard library.

## Boundaries and safety

- This skill does not provide clinical validation, medical diagnosis, or factual guarantees for model output.
- This skill does not include base model weights, LoRA adapter weights, or benchmark gold answers.
- This skill does not import the live ML stack during safe validation. A user must explicitly authorize downloads, GPU execution, training, or serving.
- This skill is not a generic Transformers/PEFT manual. Use it when the task specifically matches Huatuo/BenTsao workflows, prompt/data assets, or adapter export assumptions.
