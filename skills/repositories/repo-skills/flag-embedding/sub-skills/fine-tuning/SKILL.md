---
name: fine-tuning
description: "Prepare FlagEmbedding fine-tuning data and safe training commands
  for embedders and rerankers."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Fine-Tuning

Use this sub-skill when the task is to prepare or validate FlagEmbedding fine-tuning data, choose the correct training module for an embedder or reranker, or build a bounded `torchrun` command without launching training automatically.

Read first:

- `references/data-formats.md` for JSONL schemas, hard negatives, teacher scores, `prompt`, and embedder ICL `type` handling.
- `references/training-commands.md` for module entry points, command patterns, DeepSpeed config shapes, LoRA flags, flash-attn caveats, and bge-m3 unified fine-tuning.
- `references/troubleshooting.md` when JSONL validation, optional finetune extras, CUDA, DeepSpeed, flash-attn, cache/token, OOM, or distributed launch issues appear.

Bundled helpers:

- `scripts/validate_train_jsonl.py` validates embedder or reranker JSONL before training. Use `--knowledge-distillation` only when score fields are intended for KD.
- `scripts/split_jsonl_by_text_length.py` splits JSONL by safe character or token-estimate length without downloading tokenizers.

Route away:

- Inference-only model loading, encoding, reranking, and score computation belongs to sibling `inference`.
- Post-training retrieval, reranking, MTEB, BEIR, or custom benchmark work belongs to sibling `evaluation`.
- Broad package installation, import failures, and backend setup outside fine-tuning belongs to the root troubleshooting reference.

Operational constraints:

- Do not run full training unless the user explicitly asks for it and model, data, devices, caches, output directory, and runtime budget are clear.
- Treat hard-negative mining and teacher-score generation as model-loading workflows with network/cache/device dependencies unless every model artifact is already local.
- The optional `FlagEmbedding[finetune]` extra adds DeepSpeed and flash-attn, but full GPU training and flash-attn compatibility were not verified by this sub-skill.
