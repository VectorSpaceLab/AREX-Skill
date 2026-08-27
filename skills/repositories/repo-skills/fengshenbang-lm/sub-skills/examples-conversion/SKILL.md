---
name: examples-conversion
description: "Plan Fengshen example-family workflows and conversion utilities
  without launching downloads, training, services, or checkpoint mutation."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# Fengshenbang-LM examples and conversion planning

Use this sub-skill when the user asks for Fengshen model-family example recipes, CLUE/classification recipe adaptation, NLG/NLT task recipes, Taiyi Stable Diffusion usage or fine-tuning requirements, Ziya inference/quantization/fine-tuning/conversion planning, or checkpoint conversion utilities. This skill is for safe planning and dry-run checklists; it does not run training, servers, downloads, or checkpoint conversion.

## First route the task

| User intent | Start here | Route elsewhere when needed |
|---|---|---|
| CLUE leaderboard, high-level classification scripts, AFQMC/TNEWS/OCNLI/C3/CHID/CSL/IFLYTEK/WSC/CMRC2018 recipe | [references/clue-and-task-recipes.md](references/clue-and-task-recipes.md) | Common `fengshen-pipeline` command mechanics and schema fixture generation belong to `../pipelines-cli/SKILL.md`; data loaders and Trainer/checkpoint flags belong to `../data-training/SKILL.md`. |
| Summary, question generation, generative QA, translation, medical close-book QA, reasoning generation | [references/nlg-nlt-recipes.md](references/nlg-nlt-recipes.md) | Core model/config/tokenizer classes belong to `../model-zoo/SKILL.md`; universal dataloaders and scheduler details belong to `../data-training/SKILL.md`. |
| Taiyi Stable Diffusion inference, CPU/full precision vs FP16 CUDA, fine-tune, DreamBooth | [references/taiyi-diffusion.md](references/taiyi-diffusion.md) | Taiyi CLIP/model internals belong to `../model-zoo/SKILL.md`; distributed training argument details belong to `../data-training/SKILL.md`. |
| Ziya LLaMA inference, bitsandbytes/llama.cpp quantization, full-parameter fine-tune, HF/Fengshen/TP conversion | [references/ziya-llama.md](references/ziya-llama.md) and `scripts/plan_ziya_conversion.py` | LLaMA class/config internals belong to `../model-zoo/SKILL.md`; full training loop and Deepspeed mechanics belong to `../data-training/SKILL.md`. |
| Delta weights, TF checkpoint, Diffusers-to-original Stable Diffusion, LLaMA HF/Fengshen/TP conversions | [references/conversion-utilities.md](references/conversion-utilities.md) and `scripts/plan_ziya_conversion.py` | If the user wants an actual conversion, require explicit source/output paths, dependency/hardware checks, backup plan, and mutation acknowledgement before using package utilities. |
| FastDemo/Streamlit/FastAPI demo caveats | [references/troubleshooting.md](references/troubleshooting.md) | Production API/server design is outside this repo skill; keep to caveats and minimal request shape. |
| Unsure which family applies | [references/model-family-recipes.md](references/model-family-recipes.md) and `scripts/check_recipe_requirements.py` | Model class selection goes to `../model-zoo/SKILL.md`. |

## Safety contract

- Treat all bundled scripts as non-mutating dry-run helpers. They may print plans/checklists but must not install packages, download models or datasets, start services, launch training, call `from_pretrained`, or write checkpoint outputs.
- Do not copy or run source example shell scripts verbatim. Many examples encode local machine paths, Slurm settings, checkpoint output directories, or GPU-only assumptions.
- Before any real training/conversion outside this skill, ask for: model/checkpoint source, target output directory, whether network downloads are permitted, device/VRAM, expected precision, and whether overwriting/removing output directories is allowed.
- For checkpoint conversion, assume outputs are mutating and large. Require a new empty output directory or backup plan. Never point output to the same directory as an input checkpoint.
- For CPU-only environments, keep to help/static planning for Ziya, Taiyi FP16, diffusion fine-tuning, DreamBooth, Deepspeed, and full LLaMA fine-tuning.

## Bundled helpers

```bash
python scripts/check_recipe_requirements.py --recipe taiyi-inference --device cpu --precision fp32
python scripts/check_recipe_requirements.py --recipe taiyi-inference --device cuda --precision fp16 --gpus 1 --vram-gb 16
python scripts/plan_ziya_conversion.py --source-format hf --target fs-finetune --model-size 13b --gpus 8 --vram-gb 80
python scripts/plan_ziya_conversion.py --source-format hf --target fs-finetune --model-size 13b --gpus 24 --vram-gb 24
```

The helpers are checkout-independent and safe to run from any directory.

## Verification expectations for future agents

Use this sub-skill to satisfy these difficult cases without opening the source checkout:

1. Decide whether a Ziya HF checkpoint should be converted to Fengshen format and then tensor-parallel shards before full-parameter fine-tuning. The answer must identify delta merge prerequisites, HF-to-Fengshen conversion, TP choice, output mutation risk, dependencies, and resource gates.
2. Choose between Taiyi Stable Diffusion CPU/full-precision and FP16 CUDA inference. The answer must distinguish full precision from FP16, list `diffusers`/`accelerate`/`torch` dependency gates, explain network/offline model-cache effects, and avoid launching image generation.

## Non-goals

- Do not document every Trainer, dataloader, checkpoint, or optimizer flag here; link to `../data-training/SKILL.md`.
- Do not explain core model classes, auto config keys, or tokenizer internals here; link to `../model-zoo/SKILL.md`.
- Do not reproduce common `fengshen-pipeline` mechanics here; link to `../pipelines-cli/SKILL.md`.
- Do not claim native execution of heavy examples was verified. The portable verification scope is static planning, help/checklist behavior, and non-mutating script execution.
