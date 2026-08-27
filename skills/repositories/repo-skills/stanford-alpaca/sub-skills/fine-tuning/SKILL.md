---
name: fine-tuning
description: "Supervised fine-tuning of LLaMA/OPT-style causal LMs with Alpaca
  data using Hugging Face Trainer, FSDP, and optional DeepSpeed offload."
metadata:
  disco-role: operating
disable-model-invocation: true
license: NOASSERTION
---

# Fine-tuning

Use this sub-skill when a task is about supervised fine-tuning an Alpaca-style causal language model with the Stanford Alpaca training flow: Hugging Face `AutoModelForCausalLM`, `AutoTokenizer`, `Trainer`, tokenizer special-token resizing, source-token label masking, FSDP recipes, or optional DeepSpeed ZeRO-3 CPU offload.

Do **not** use this sub-skill as the owner for data schema, prompt wording, OpenAI instruction generation, or weight-diff recovery. Route those parts to sibling sub-skills by id:

- `dataset-and-prompts`: Alpaca JSON schema, prompt text, prompt/schema validation, and training-data quality checks.
- `instruction-generation`: OpenAI/Self-Instruct style instruction generation.
- `weight-diff-recovery`: recovering Alpaca weights from released weight diffs.

## Evidence baseline

This sub-skill is grounded in the repository's fine-tuning and OOM README sections, `train.py`, `configs/default_offload_opt_param.json`, and the prepared environment report signatures. Verified facts include:

- `train.py` uses `transformers.HfArgumentParser((ModelArguments, DataArguments, TrainingArguments))`.
- Help exposes `--model_name_or_path`, `--data_path`, `--output_dir`, `--fsdp`, `--fsdp_transformer_layer_cls_to_wrap`, `--deepspeed`, `--model_max_length`, `--bf16`, `--tf32`, and standard Hugging Face `TrainingArguments` fields.
- `preprocess(sources, targets, tokenizer)` concatenates prompt sources and targets, then masks source-token labels with `IGNORE_INDEX = -100`.
- The DeepSpeed offload config uses ZeRO stage 3 with CPU parameter and optimizer offload.

## Fast routing

1. If the user needs the training logic, dataclass fields, function signatures, token resizing, or collator behavior, read [`references/api-reference.md`](references/api-reference.md).
2. If the user needs an end-to-end plan or documented `torchrun` recipes, read [`references/workflows.md`](references/workflows.md).
3. If the user needs hyperparameters, batch-size math, FSDP/DeepSpeed flags, or config-key interpretation, read [`references/configuration.md`](references/configuration.md).
4. If the user reports OOM, missing special tokens, path errors, missing optional packages, CUDA confusion, or full-scale training failures, read [`references/troubleshooting.md`](references/troubleshooting.md).
5. If the task is only to assemble a launch command safely, use [`scripts/build_training_command.py`](scripts/build_training_command.py). It prints command text and never launches training.
6. If the user wants a self-contained Stanford Alpaca trainer script, use [`scripts/train_alpaca_sft.py`](scripts/train_alpaca_sft.py) instead of depending on the original repository checkout.
7. For DeepSpeed ZeRO-3 CPU offload, use the bundled [`scripts/default_offload_opt_param.json`](scripts/default_offload_opt_param.json) config.

## Operating workflow

- Start with the `dataset-and-prompts` handoff: the training `data_path` must already point to a validated Alpaca-style JSON dataset. This sub-skill can explain how the trainer consumes that dataset, but not the full schema or prompt text.
- Use the command builder when planning, reviewing, or pasting commands. Do not launch training during command planning.
- Use the adapted trainer when the user explicitly wants to run the Stanford Alpaca SFT logic from a self-contained skill tree.
- For LLaMA-style FSDP, set `--fsdp "full_shard auto_wrap"` and `--fsdp_transformer_layer_cls_to_wrap LlamaDecoderLayer`.
- For OPT-style FSDP, use `OPTDecoderLayer` for `--fsdp_transformer_layer_cls_to_wrap`.
- To reduce VRAM beyond FSDP full shard, first try `--fsdp "full_shard auto_wrap offload"`; if that is still unsuitable, use the DeepSpeed ZeRO-3 offload recipe and bundled JSON config.

## Key defaults to preserve

- Original documented LLaMA-7B recipe: global batch size 128, learning rate `2e-5`, 3 epochs, max length 512, weight decay 0.
- Original documented LLaMA-13B recipe: global batch size 128, learning rate `1e-5`, 5 epochs, max length 512, weight decay 0.
- The README examples use 4 GPUs, `per_device_train_batch_size=4`, and `gradient_accumulation_steps=8`: `4 GPUs * 4 micro-batch * 8 accumulation = 128`.
- `TrainingArguments.model_max_length` defaults to 512; tokenization right-pads and truncates to that length.
- Missing `pad`, `eos`, `bos`, or `unk` tokenizer tokens are added before training and the model embeddings are resized.

## Verification posture

Full LLaMA/OPT training is expensive and GPU-dependent. A CPU-side check can validate imports, argument parsing, data loading, tokenization, command construction, and help surfaces, but it is **not** proof that a multi-GPU FSDP or DeepSpeed job will fit or converge. Treat GPU recipes as documented launch templates unless final verification explicitly runs them on suitable hardware.
