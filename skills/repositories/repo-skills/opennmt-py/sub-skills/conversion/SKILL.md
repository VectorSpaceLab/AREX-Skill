---
name: conversion
description: "Routes OpenNMT-py checkpoint averaging, release, CTranslate2,
  external-family conversion, vocabulary or embedding extraction, and LoRA merge
  workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Conversion

Use this sub-skill when the task is about OpenNMT-py checkpoint maintenance or model-format conversion rather than training or translation.

## Use this route when

- The request says average checkpoints, strip optimizer state, release a model, convert to CTranslate2, quantize for CT2, or inspect a saved checkpoint.
- The user needs to convert a LLaMA, Mistral, Mixtral, Phi, T5, MPT, Falcon, RedPajama, XGen, or Hugging Face-style checkpoint into OpenNMT-py format.
- The user needs to extract source/target vocabularies, inspect or export embeddings, convert pretrained embeddings to tensors, or check vocab availability.
- The user needs to merge or concatenate LoRA weights into a compatible base OpenNMT-py model.

## Do not use this route when

- The main work is building corpora or tokenizers before training; use the data-preparation route.
- The main work is choosing architecture, optimizer, LoRA training options, or checkpoint continuation; use the training route.
- The main work is running inference or serving an already released model; use the inference route.

## Start here

1. Read `references/checkpoint-tools.md` to identify the exact checkpoint family, expected files, command/API surface, validation checks, and output format.
2. Before changing a checkpoint, inspect the input with `scripts/check_checkpoint_file.py`:

   ```bash
   python scripts/check_checkpoint_file.py path/to/model.pt --json
   ```

   The helper maps tensors to CPU or fake tensors and reports top-level keys, option fields, vocab sides, tensor counts, and conversion-readiness hints.
3. Read `references/troubleshooting.md` before running weight-heavy conversion, CTranslate2 release, external/Hugging Face conversion, or LoRA merge.
4. Prefer package console commands for installed OpenNMT-py entry points: `onmt_average_models` and `onmt_release_model`. For utilities that were only source-tree tools, use the distilled contracts in `references/checkpoint-tools.md` and create a task-local reviewed helper instead of depending on any particular checkout path.

## Primary workflows

- **Average compatible checkpoints**: check all inputs, confirm identical vocabulary and architecture options, then run `onmt_average_models -models ... -output averaged.pt`; add `-fp32` when the release target must not preserve half precision.
- **Release PyTorch or CTranslate2 models**: use `onmt_release_model --format pytorch` to drop optimizer state, or `--format ctranslate2` with an optional quantization mode to create a CT2 model directory.
- **Convert external model families**: use the family matrix and option contracts in `references/checkpoint-tools.md`; validate that the output checkpoint has `model`, `generator`, `vocab`, and `opt` sections before training or release.
- **Extract vocabularies or embeddings**: confirm `vocab.src`/`vocab.tgt` first, then use the reference recipes to write vocab text files or embedding tensors without relying on source checkout scripts.
- **Merge LoRA weights**: verify the base and LoRA checkpoints share architecture/vocab assumptions, merge for inference or concatenate for resumed training, then inspect the output and release it if needed.

## Safety and validation rules

- Treat `torch.load` checkpoints as trusted pickle files; do not inspect arbitrary untrusted checkpoints without an isolation plan.
- Conversion and inspection should not place tensors on GPU. Use CPU/fake-tensor loading for checks, and only select GPU for downstream inference/training if the owning route requires it.
- Never average checkpoints from different vocabularies, architectures, model tasks, or incompatible LoRA/base states.
- For CT2, validate that the output is a directory with CT2 files such as `model.bin`, `config.json`, and `vocabulary.json`, not a `.pt` checkpoint.
- Keep real model paths, Hugging Face tokens, cache directories, and machine-specific paths out of skill notes and reusable scripts.

## Bundled files

- `references/checkpoint-tools.md` — workflows, command/API contracts, external family matrix, vocab/embedding and LoRA guidance.
- `references/troubleshooting.md` — symptoms, likely causes, and recovery steps for conversion-specific failures.
- `scripts/check_checkpoint_file.py` — safe checkpoint inventory helper for OpenNMT-py `.pt` metadata and tensor summaries.
