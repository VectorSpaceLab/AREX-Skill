---
name: training
description: "Build Tevatron dense, sparse, distillation, GradCache, LoRA,
  DeepSpeed, and JAX training commands safely."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Training

Use this sub-skill when the task is to assemble, review, or troubleshoot Tevatron retriever training commands. It covers dense PyTorch training, teacher distillation, GradCache, LoRA, DeepSpeed launcher/config choices, SPLADE and UniCOIL sparse patterns, RepLLaMA-style LLM retriever training, and JAX/Tevax TPU or GPU routes.

Do not use this sub-skill for embedding checkpoints, FAISS/Pyserini search, reranker training, raw data conversion, or multimodal/Qwen training details; route those to the sibling workflow that owns encoding/retrieval, reranking, data preparation, or multimodal LLM usage.

## Start Here

1. Read `references/training-workflows.md` for command templates and validation checkpoints.
2. Read `references/arguments-reference.md` when choosing `ModelArguments`, `DataArguments`, training arguments, or sparse/JAX-specific names.
3. Use `scripts/build_training_command.py --help` to generate a command plan without launching training.
4. Use `references/troubleshooting.md` before recommending dependency installs, checkpoint deletion, or memory fixes.

## Route by Request

- **Dense retriever training**: use `tevatron.retriever.driver.train` with `--do_train`, model/data arguments, and PyTorch/Transformers training flags.
- **Memory-constrained training**: add `--grad_cache` plus query/passage chunk sizes, or choose DeepSpeed ZeRO-3 for large models.
- **LoRA LLM retriever training**: add `--lora`, LLM pooling/prefix options, PEFT dependency notes, and usually DeepSpeed or gradient checkpointing.
- **Teacher distillation**: use `tevatron.retriever.driver.train_distil`; verify every positive and negative passage carries a numeric teacher `score`.
- **Sparse retriever training**: use the SPLADE/UniCOIL patterns in the workflow reference; SPLADE has current package model support, while UniCOIL requires an adapted driver in this package version.
- **JAX/TPU training**: use `tevatron.retriever.driver.jax_train` for the current HF-style driver or `tevatron.tevax.experimental.mp.train_lora` for the experimental Tevax LoRA route.

## Required Checks

Before handing a command to a user, confirm:

- `--do_train` is present for PyTorch/Transformers-style drivers.
- `--output_dir` is new, intentionally resumable, or paired with `--overwrite_output_dir`.
- The data route matches the schema: inline `positive_passages`/`negative_passages`, or ID lists with `--corpus_name`/`--corpus_path`.
- Optional dependencies are explicit: `torch`, `peft`, `deepspeed`, `grad_cache`, `flash-attn`, `jax`, `flax`, `optax`, and `magix` are not installed by Tevatron's core package.
- Long-running GPU/TPU commands are presented as plans unless the user explicitly asks to run training.
