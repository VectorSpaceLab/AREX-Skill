---
name: checkpoint-conversion
description: "Download, validate, convert, classify, and merge LitGPT
  checkpoints while diagnosing model config, tokenizer, LoRA metadata, and
  checkpoint layout issues."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# LitGPT Checkpoint Conversion

Use this sub-skill when the task involves checkpoint acquisition, LitGPT/Hugging Face format decisions, model configuration support, tokenizer/config layout, pre-flight validation, or LoRA merge readiness.

## Route here when

- A checkpoint must be downloaded with `litgpt download`, including gated Hub access, tokenizer-only downloads, or `--model_name` overrides for alternative weights.
- A directory must be classified as LitGPT format, Hugging Face format, full/pretraining output, or LoRA output.
- A Hugging Face checkpoint needs `litgpt convert_to_litgpt`, a LitGPT checkpoint needs `litgpt convert_from_litgpt`, or a pretraining checkpoint needs `litgpt convert_pretrained_checkpoint`.
- A LoRA output must be checked or merged with `litgpt merge_lora` before normal inference/evaluation/export.
- `Config.from_name`, `Config.from_file`, `Config.from_checkpoint`, or `GPT(config)` behavior matters for support triage.

Route generation/chat with a ready checkpoint to `../inference-chat/SKILL.md`, training and LoRA creation to `../training-data/SKILL.md`, and evaluation/serving flows to `../evaluation-serving/SKILL.md` after using this sub-skill for layout checks.

## Fast workflow

1. Classify the directory with `python scripts/check_checkpoint_layout.py CHECKPOINT_DIR --json`.
2. If it is Hugging Face format and lacks `lit_model.pth`, convert it with `litgpt convert_to_litgpt CHECKPOINT_DIR --model_name MODEL_NAME` when the directory name is not a supported LitGPT config name.
3. If it is LitGPT format, run `litgpt validate CHECKPOINT_DIR --dtype float32` before inference, training continuation, or evaluation.
4. If it is LoRA output, run `python scripts/check_lora_metadata.py CHECKPOINT_DIR --json`; then run `litgpt merge_lora CHECKPOINT_DIR` or add `--pretrained_checkpoint_dir BASE_CHECKPOINT_DIR` when metadata points to a moved base checkpoint.
5. If it is a LitGPT training/pretraining checkpoint with optimizer metadata, export model-only weights with `litgpt convert_pretrained_checkpoint CHECKPOINT_DIR OUTPUT_DIR` before downstream loading.
6. If it must become Hugging Face-style output, ensure it has merged non-adapter weights, then run `litgpt convert_from_litgpt CHECKPOINT_DIR OUTPUT_DIR`.

## Bundled references

- `references/cli-reference.md` lists supported checkpoint subcommands, arguments, and safe sequencing.
- `references/checkpoint-layout.md` explains required files and classification signals.
- `references/model-configs.md` explains LitGPT model config lookup, support checks, and `--model_name` overrides.
- `references/troubleshooting.md` maps common errors to fixes.

## Bundled scripts

- `scripts/check_checkpoint_layout.py` inspects files only; it does not load model weights, download files, or write outputs.
- `scripts/check_lora_metadata.py` reads `hyperparameters.yaml` only; it does not load LoRA/base weights or merge files.

## Safety notes

- Treat downloads, conversions, and merges as potentially large I/O operations; ask before running them when runtime, network, or disk cost matters.
- Never expose access tokens in commands or notes; prefer `HF_TOKEN` or a secured environment mechanism.
- Do not use `convert_from_litgpt` on LoRA or adapter checkpoints directly. Merge LoRA first; adapter checkpoint export is not supported by the converter.
