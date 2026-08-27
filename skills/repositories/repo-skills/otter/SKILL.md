---
name: otter
description: "Operate Otter multimodal model inference, MIMIC-IT data
  preparation, training, evaluation, and serving workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Otter repo skill

Use this repo skill when the task involves Otter, OtterHD, OpenFlamingo-style multimodal in-context instruction tuning, MIMIC-IT data, Otter model checkpoints, Otter benchmark evaluation, or the repo's controller/worker/Gradio serving stack.

Otter is a multimodal model codebase for image/video/text instruction tuning and evaluation. The installable distribution is `otter-ai`, imported as `otter_ai`; many workflow scripts live in a target Otter checkout rather than the Python package, so this skill provides bundled validators and command builders instead of requiring the source checkout used to create the skill.

## First steps

1. Read [repository provenance](references/repo-provenance.md) when checking whether this skill matches a checkout or deciding whether to refresh it.
2. For installation and import checks, read [installation](references/installation.md) and run the safe bundled probe:

```bash
python scripts/check_otter_environment.py --json
```

3. Route to the narrowest sub-skill below. Keep heavyweight jobs opt-in: model downloads, training, benchmark datasets, API calls, and servers all require explicit user approval.
4. If a cross-cutting dependency or backend error appears before a workflow is chosen, start with [troubleshooting](references/troubleshooting.md).

## Sub-skill routes

| Task signal | Read |
|---|---|
| Load `OtterForConditionalGeneration`, call `generate`, build `vision_x`/`lang_x`, validate batch inference YAML, or plan checkpoint conversion | [model-inference](sub-skills/model-inference/SKILL.md) |
| Construct SFT, OtterHD/Fuyu finetuning, pretraining, Accelerate, DeepSpeed, W&B, checkpoint, or offline commands | [training](sub-skills/training/SKILL.md) |
| Validate MIMIC-IT YAML, instruction JSON, image parquet/JSON, Convert-It adapters, Syphus preflight, or large data conversion | [data-preparation](sub-skills/data-preparation/SKILL.md) |
| Configure benchmark YAMLs, supported model/dataset registry names, GPT-judged benchmark credentials, or output/cache paths | [benchmark-evaluation](sub-skills/benchmark-evaluation/SKILL.md) |
| Plan or debug controller, model worker, Gradio, local CLI, worker registration, endpoints, ports, and load-bit serving | [serving](sub-skills/serving/SKILL.md) |

## Installation quick notes

- Preferred public setup for a target checkout: Python 3.9, then `python -m pip install -e .` or the repo's documented Conda environment.
- The package metadata pulls a broad stack for training, serving, benchmarks, and APIs. For pure package inspection, verify `otter_ai` imports before running large workflows.
- The inspected compatible stack used `transformers==4.35.1`, `tokenizers==0.14.1`, `huggingface_hub==0.17.3`, `accelerate==0.23.0`, and `peft==0.4.0`. Newer `accelerate`/`peft` can require newer Hugging Face Hub APIs and break imports with the repo-pinned Transformers version.
- CUDA was available during construction and a tiny torch CUDA allocation passed, but no model checkpoints, datasets, benchmark runs, servers, Syphus API calls, or training jobs were executed.

## Backend and safety boundaries

- CPU/import/parser checks can validate routing, schemas, and command construction.
- Real Otter/OtterHD generation, training, model-worker serving, and most benchmark runs are optional GPU-heavy workflows; CPU checks are not proof that those workloads fit in memory or run at target throughput.
- Syphus and some benchmark judges require API credentials or a local OpenAI-compatible service. Do not run them without explicit credential and cost approval.
- Serving opens ports and starts long-lived processes. Use the serving sub-skill's builders and preflight checks before launch.

## Common workflow handoffs

- Prepared a MIMIC-IT YAML and want to train: validate it with [data-preparation](sub-skills/data-preparation/SKILL.md), then build the launch command with [training](sub-skills/training/SKILL.md).
- Need to evaluate a model checkpoint: use [benchmark-evaluation](sub-skills/benchmark-evaluation/SKILL.md) for benchmark YAML validation, then [model-inference](sub-skills/model-inference/SKILL.md) if a failure is about prompt/media tensors.
- Need a web demo: verify imports with [serving](sub-skills/serving/SKILL.md), then debug model loading with [model-inference](sub-skills/model-inference/SKILL.md) if the worker cannot instantiate Otter.

## What this skill deliberately does not do

- It does not prove full GPU training/generation throughput or model quality.
- It does not include model weights, datasets, private credentials, or external downloads.
- It does not require the checkout used during skill creation; when a workflow needs repo scripts, this skill gives distilled commands, validators, wrappers, and troubleshooting for a target Otter checkout or deployment.
