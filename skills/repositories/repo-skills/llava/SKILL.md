---
name: llava
description: "Guides LLaVA vision-language model inference, serving, training,
  fine-tuning, evaluation, benchmark conversion, checkpoint utilities, and
  troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# LLaVA Repo Skill

Use this skill when a task involves the LLaVA package: Large Language and Vision Assistant, visual instruction tuning, image-question chat, multimodal model workers, LLaVA fine-tuning, LoRA/QLoRA, LLaVA benchmark evaluation, or checkpoint utilities.

This skill is self-contained for operating the public `llava` package. Do not rely on a source checkout being present. Use the bundled references and scripts here instead of reopening original repository docs or scripts.

## First checks

1. Confirm the package and backend with [`scripts/check_install.py`](scripts/check_install.py):

```bash
python scripts/check_install.py --require-cuda
```

2. For installation and dependency pin notes, read [`references/install-and-compatibility.md`](references/install-and-compatibility.md).
3. For model families, checkpoint types, and license reminders, read [`references/model-overview.md`](references/model-overview.md).
4. For repository staleness checks, read [`references/repo-provenance.md`](references/repo-provenance.md).

## Route by task

| User task | Read |
| --- | --- |
| Run one image prompt, inspect `load_pretrained_model`, choose conversation mode, launch CLI, controller, worker, or Gradio UI | [`sub-skills/chat-and-serve/SKILL.md`](sub-skills/chat-and-serve/SKILL.md) |
| Prepare custom training JSON, choose pretrain/fine-tune/LoRA/QLoRA commands, validate image paths, pick DeepSpeed config, merge LoRA, apply deltas, consolidate checkpoints | [`sub-skills/train-and-finetune/SKILL.md`](sub-skills/train-and-finetune/SKILL.md) |
| Evaluate custom VQA data, run benchmark-style inference, chunk across GPUs, validate question/answer JSONL, convert submissions, understand GPT/OpenAI judge caveats | [`sub-skills/evaluate-and-benchmark/SKILL.md`](sub-skills/evaluate-and-benchmark/SKILL.md) |

## Common operating rules

- Actual LLaVA generation, model workers, benchmark inference, and training are GPU-centered workflows. CPU checks can verify imports, parsers, data conversion, and JSON validation, but they do not validate generation quality or CUDA memory behavior.
- The package metadata pins core runtime versions tightly, including `torch==2.1.2`, `torchvision==0.16.2`, `transformers==4.37.2`, `tokenizers==0.15.1`, and `accelerate==0.21.0`. Treat unpinned upgrades as a likely source of import errors.
- The training extra adds DeepSpeed, Ninja, and W&B. Optional acceleration paths such as FlashAttention, xFormers, SGLang, MPS, Intel dGPU/CPU, and OpenAI-based judging need separate installation or credentials and are not covered by a basic install check.
- Prefer `python -m llava...` module invocations for public package workflows. If a bundled helper prints a command, review it before running because model downloads, datasets, GPU memory, ports, and credentials may still be required.
- Keep data paths, checkpoint paths, and output directories explicit. Many original examples assumed repository-local folders; this generated skill uses placeholders and bundled validators instead.

## Minimal public install sketch

```bash
conda create -n llava python=3.10 -y
conda activate llava
pip install --upgrade pip
pip install -e .
# For training workflows only:
pip install -e ".[train]"
# Optional, hardware-specific acceleration when you choose to use it:
# pip install flash-attn --no-build-isolation
```

If you are not in a source checkout, install the published package or a pinned VCS/archive build that matches the provenance baseline in [`references/repo-provenance.md`](references/repo-provenance.md). Do not copy private environment paths into user-facing outputs.

## Troubleshooting map

- Install/import/version/backend failures: [`references/troubleshooting.md`](references/troubleshooting.md).
- Chat, serving, image-token, worker registration, and quantization failures: [`sub-skills/chat-and-serve/references/troubleshooting.md`](sub-skills/chat-and-serve/references/troubleshooting.md).
- Training data, DeepSpeed, LoRA, checkpoint, W&B, and memory failures: [`sub-skills/train-and-finetune/references/troubleshooting.md`](sub-skills/train-and-finetune/references/troubleshooting.md).
- Evaluation data layout, chunk merging, submission conversion, GPT judging, and benchmark failures: [`sub-skills/evaluate-and-benchmark/references/troubleshooting.md`](sub-skills/evaluate-and-benchmark/references/troubleshooting.md).

## Before making claims

Run the nearest bundled diagnostic or validator before telling a user that an environment, data file, benchmark output, or command is ready. If a requested workflow needs a large checkpoint, dataset download, external judge, long training run, or unavailable hardware, state the limitation explicitly and provide the safe preparation steps instead of fabricating a pass.
