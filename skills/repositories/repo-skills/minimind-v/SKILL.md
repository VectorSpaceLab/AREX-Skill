---
name: minimind-v
description: "Routes MiniMind-V tiny vision-language model setup, data
  validation, architecture/API inspection, inference/WebUI, training, and
  checkpoint conversion workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# MiniMind-V Repo Skill

Use this skill when a task concerns MiniMind-V, the compact PyTorch vision-language model repository built around a MiniMind language backbone plus a frozen SigLIP2 vision encoder.

This skill is for operating MiniMind-V workflows in a user's own checkout or exported model directory. It is self-contained: use the bundled references and safe helpers here instead of reopening the repository used to generate the skill.

## Route here for

- Preparing MiniMind-V resources: dependencies, tokenizer files, SigLIP2, native `.pth` weights, Transformers exports, ALLaVA-style parquet data, or sample image folders.
- Explaining MiniMind-V model internals: `VLMConfig`, `MiniMindVLM`, 64 visual tokens, `<|image_pad|>`, dense/MoE choices, projector behavior, or generation semantics.
- Planning or checking command-line image QA inference and optional Gradio WebUI serving.
- Planning Pretrain/SFT runs, DDP launch, freeze policy, checkpoint/resume behavior, or training command construction.
- Converting native MiniMind-V checkpoints to Transformers format, inspecting export directories, or explaining reverse conversion limits.

## Route elsewhere

- General LLM/VLM theory without MiniMind-V-specific APIs, files, checkpoints, or data layout.
- Downloading large datasets/model weights as an unattended action; ask for explicit approval and budget first.
- Running long training, launching a public listener, or executing untrusted `trust_remote_code=True` loads without user approval.
- Editing MiniMind-V source code as a maintainer task unless the user is working in a checkout and asks for repo maintenance.

## Minimal setup and import check

From a MiniMind-V checkout, install only the dependency subset needed for the selected workflow. For general use the project documents:

```bash
pip install -r requirements.txt
```

Install `torch`/`torchvision` separately for the host backend because the repository comments those lines out. A lightweight source/API check that does not load weights is:

```bash
python - <<'PY'
from model.model_vlm import VLMConfig
cfg = VLMConfig()
print(cfg.model_type, cfg.image_special_token, cfg.image_token_len)
PY
```

Use [`scripts/check_minimind_v_environment.py`](scripts/check_minimind_v_environment.py) for a broader read-only preflight before running model, data, training, serving, or export commands.

## First-step checklist

1. Identify the user's task family: resources/data, architecture/API, inference/WebUI, training, or conversion.
2. If the task touches local files, ask which MiniMind-V checkout or export directory the user wants to inspect. Use relative project paths in commands.
3. Prefer bundled safe helpers before expensive or stateful actions:
   - `scripts/check_minimind_v_environment.py` for cross-cutting dependency/resource checks.
   - sub-skill helpers for parquet validation, API inspection, inference preflight, WebUI model scanning, training command building, or Transformers export inspection.
4. Treat full generation, training, WebUI launch, network downloads, and checkpoint conversion as explicit user actions, not routine verification.
5. Keep resource acquisition separate from training/inference/conversion plans.

## Sub-skill routing

| User intent | Read |
| --- | --- |
| Dependency/resource layout, tokenizer/SigLIP2/model/data placement, parquet schema, image bytes, `<image>` expansion, data validation | [`data-and-resources`](sub-skills/data-and-resources/SKILL.md) |
| `MiniMindVLM`, `VLMConfig`, `MiniMindConfig`, projector, pixel tensor shapes, cache/generate behavior, dense vs MoE architecture | [`model-architecture-and-api`](sub-skills/model-architecture-and-api/SKILL.md) |
| `eval_vlm.py` planning, native `.pth` vs Transformers inference, image QA smoke checks, WebUI scanner/serving decisions | [`inference-and-serving`](sub-skills/inference-and-serving/SKILL.md) |
| Pretrain/SFT planning, `freeze_llm`, DDP, bf16/fp16, SwanLab/W&B logging, output names, checkpoint resume | [`training`](sub-skills/training/SKILL.md) |
| Native `.pth` to Transformers export, export layout inspection, `config.json`/tokenizer metadata, reverse conversion limits | [`model-export-and-format-conversion`](sub-skills/model-export-and-format-conversion/SKILL.md) |

## Repo-level references and helpers

- Read [`references/installation-and-environment.md`](references/installation-and-environment.md) before planning installs or backend checks.
- Read [`references/troubleshooting.md`](references/troubleshooting.md) for cross-cutting failures that span multiple workflows.
- Read [`references/repo-provenance.md`](references/repo-provenance.md) before deciding whether this skill matches a current MiniMind-V checkout or needs refresh.
- Import metadata for `repo-skills-router` lives in [`references/repo-routing-metadata.json`](references/repo-routing-metadata.json).

## Core facts to preserve

- MiniMind-V is a script-style repository, not an installable Python distribution with package metadata.
- The default VLM uses a MiniMind language backbone with `hidden_size=768`, `num_hidden_layers=8`, optional MoE, and a frozen SigLIP2 P32 256x256 vision encoder.
- One image is represented by 64 consecutive `<|image_pad|>` tokens by default, matching SigLIP2's 8x8 patch-token output.
- Native weights use names such as `out/llm_768.pth`, `out/pretrain_vlm_768.pth`, `out/sft_vlm_768.pth`, with `_moe` added for MoE variants.
- Full training and quality inference require external model weights, SigLIP2 resources, parquet data, and a suitable torch backend; do not treat source import success as proof those resources exist.
