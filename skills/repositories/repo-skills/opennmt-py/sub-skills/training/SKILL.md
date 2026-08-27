---
name: training
description: "Routes OpenNMT-py training, checkpoint continuation, distributed
  layout, alignment, LoRA, and quantized fine-tuning workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Training

Use this sub-skill when the task is to run or debug OpenNMT-py model training with `onmt_train`, including model architecture choices, optimizer schedules, GPU layout, checkpoint continuation, vocabulary update, alignment training, pretrained embeddings, LoRA, gradient checkpointing, or 4/8-bit fine-tuning.

## Use this route when

- The request mentions `onmt_train`, a training YAML, `train_steps`, `valid_steps`, `save_model`, `train_from`, `reset_optim`, or `update_vocab`.
- The user needs to choose or debug RNN, Transformer, language-model, summarization, or fine-tuning options.
- The task involves `world_size`, `gpu_ranks`, `CUDA_VISIBLE_DEVICES`, multi-node rank slices, or training throughput.
- The task involves pretrained embeddings, frozen word vectors, supervised alignment loss, copy-attention summarization, LoRA adapters, gradient checkpointing, or quantized layers.

## Do not use this route when

- The task is only corpus discovery, tokenizer transforms, or vocabulary building before training; use `../data-preparation/` first.
- The task is translation, scoring, server deployment, decoding, or CTranslate2 inference; use `../inference/`.
- The task is checkpoint averaging, release conversion, external checkpoint conversion, or LoRA merge after training; use `../conversion/`.

## Start here

1. Read `references/training-configs.md` to select the smallest valid training pattern and understand the parser constraints.
2. Run the bundled inspector before launching a long job:

   ```bash
   python scripts/inspect_train_config.py train.yaml
   ```

3. For real training, run:

   ```bash
   onmt_train -config train.yaml
   ```

4. If the inspector reports data or vocabulary failures, fix them with `../data-preparation/` before retrying training.
5. If the training job fails after launch, use `references/troubleshooting.md` to map the failure to config validation, distributed runtime, checkpoint, alignment, embedding, LoRA, quantization, or memory causes.

## Operating rules

- Treat YAML config checks as a safety gate, not as proof that the model will fit memory or converge.
- Prefer explicit YAML over long command lines for training because configargparse merges nested data, vocab, model, optimizer, and distributed options in one place.
- When continuing from a checkpoint, decide whether the goal is exact resume, new optimizer states, changed model options, or vocabulary update before setting `reset_optim` and `override_opts`.
- Do not claim 4/8-bit or LoRA viability without the required optional packages and GPU memory checks; CPU-only checks only validate config shape.
- Keep source-data paths, checkpoint paths, and private environment details in the user's config or logs, not in reusable instructions.
