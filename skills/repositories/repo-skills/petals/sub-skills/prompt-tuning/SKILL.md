---
name: prompt-tuning
description: "Operate Petals prompt-tuning, deep prompt-tuning, and
  adapter-aware training workflows without relying on the original repository
  checkout."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Petals Prompt Tuning

Use this sub-skill for distributed prompt tuning or deep prompt tuning on a Petals model, including causal-LM chat tuning, sequence-classification tuning, and prompt tuning on top of a preloaded PEFT/LoRA adapter.

Route generation-only work to `client-inference`, server adapter flags to `server-swarms`, and low-level LoRA/block conversion to `distributed-blocks`.

## Procedure

1. Pick a recipe in [references/workflows.md](references/workflows.md).
2. Choose `tuning_mode="ptune"` or `"deep_ptune"`; always set `pre_seq_len > 0`.
3. Load a distributed model constructor with `pre_seq_len` and `tuning_mode`.
4. Preprocess data into fixed-length `input_ids` and labels; omit zero-valued attention masks before Petals forwards.
5. Print trainable parameters. Expected trainables are prompt embeddings and, for classification, the classifier head.
6. Use a normal PyTorch optimizer over `requires_grad` parameters only.
7. Keep Hugging Face, dataset, W&B, CUDA, and swarm requirements explicit.

Read [references/api-reference.md](references/api-reference.md), [references/troubleshooting.md](references/troubleshooting.md), and use `python scripts/prompt_tuning_skeleton.py --help` for no-download planning.
