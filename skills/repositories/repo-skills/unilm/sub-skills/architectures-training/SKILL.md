---
name: architectures-training
description: "Plan and sanity-check UniLM architecture research,
  long-context/distributed training, decoding acceleration, PFPO/ReSA math
  evaluation, and credential-safe offline workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Architectures and Training

Use this sub-skill for low-level UniLM umbrella research tasks that involve Diff-Transformer, YOCO, DeepNet, LongNet/LongViT, RetNet, X-MoE, BitNet, aggressive decoding, PFPO, ReSA, or distributed launch planning. It is a planning and safety skill: it helps construct, review, and troubleshoot commands without running expensive training, long-context evaluation, downloads, credentialed callers, or GPU-only kernels by default.

Do not use this sub-skill for ordinary UniLM or s2s fine-tuning; route those to `../language-seq2seq/SKILL.md`. Route E5/SimLM retrieval training to `../embeddings-retrieval/SKILL.md`, and route Kosmos, TextDiffuser, audio, document, or multimodal inference/training to the relevant multimodal or vision sub-skill.

## Start Here

1. Classify the request: YOCO long-context, architecture module explanation, decoding acceleration, PFPO/ReSA math evaluation, or distributed training review.
2. Read `references/workflows.md` for concrete command templates, required inputs, data assumptions, and architecture-specific routing.
3. Read `references/distributed-training.md` before suggesting `torchrun`, DeepSpeed, fairseq, FSDP, multi-node, long-context, flash-attention, or custom-kernel runs.
4. Read `references/troubleshooting.md` when diagnosing missing checkpoints/data/configs, credentialed callers, old vendored fairseq expectations, JSONL mismatches, OOM, or benchmark-scale safety.
5. Run `scripts/check_training_plan.py --help` and then a mode-specific dry run to validate required fields and produce a safe command template before telling a user to launch anything.

## Bundled Helper

- `scripts/check_training_plan.py` validates command plans for `yoco-needle`, `yoco-task`, `diff-transformer`, `gad-decoding`, `pfpo-offline-eval`, and `resa-math-eval`; run it whenever a request asks for a command, launch review, or dry-run alternative.

## Safety Defaults

- Treat all native YOCO training/evaluation, PFPO training, GAD/IAD decoding, and ReSA evaluation as expensive unless the user explicitly confirms resources, data, checkpoints, and runtime compatibility.
- Never run PFPO `openai_api_caller_v1.py` or `service_api_caller_v1.py` without explicit credential/service confirmation; prefer offline JSON/JSONL validation and local result aggregation.
- Do not vendor or depend on the original repo checkout. The references in this sub-skill summarize the source evidence and the helper emits templates with placeholder paths only.
