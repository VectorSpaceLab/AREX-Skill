---
name: finetuning
description: "Prepare and run Qwen-VL supervised finetuning, LoRA, and Q-LoRA workflows."
metadata:
  disco-role: operating
disable-model-invocation: true
license: NOASSERTION
---

# Qwen-VL Finetuning

Use this sub-skill when the user wants to adapt Qwen-VL or Qwen-VL-Chat for a downstream instruction-tuning task, a domain-specific adapter, or a memory-constrained Q-LoRA run. It covers the official training script, launch templates, data layout, checkpoint handling, and the most common configuration and dependency failures.

## Read first

- [Data format](references/data-format.md) for the conversation JSON schema, multimodal markup, and adapter-related constraints.
- [Launch reference](references/launch-reference.md) for the official full-parameter, LoRA, and Q-LoRA launch templates.
- [Troubleshooting](references/troubleshooting.md) for peft/transformers compatibility, DeepSpeed, CUDA, memory, and special-token issues.
- [Bundled finetune validator](scripts/validate_finetune_data.py) for a quick schema check before launching a training job.
- [Bundled training script](scripts/finetune.py) and the shell templates in the same directory are copied/adapted runtime entrypoints from the source repo.

## Choose this sub-skill for

- Building a training command from a JSON conversation dataset.
- Choosing between full-parameter finetuning, LoRA, and Q-LoRA.
- Preparing a DeepSpeed launch, single-GPU launch, or multi-GPU launch.
- Validating that the data has the right conversation structure, image markup, and box format.
- Loading a LoRA adapter for inference after training or merging a LoRA adapter into a standalone checkpoint.
- Diagnosing OOM, missing CUDA tooling, wrong model type, or adapter/token compatibility failures.

## Route elsewhere

- One-off multimodal chat, grounding, quantization-aware inference, or box rendering belong in [../inference/SKILL.md](../inference/SKILL.md).
- Serving a trained checkpoint behind a Gradio or FastAPI listener belongs in [../serving/SKILL.md](../serving/SKILL.md).
- Benchmark scoring and submission formatting belong in [../evaluation/SKILL.md](../evaluation/SKILL.md).

## Operating rules

1. Use `Qwen/Qwen-VL-Chat` for instruction-style finetuning unless the user explicitly wants base-model behavior; the chat model already carries the chat-token conventions expected by the examples.
2. Keep the data in the documented list-of-conversations JSON form. Each sample needs an `id` and a `conversations` array with alternating `user` and `assistant` messages.
3. For multimodal messages, keep the `Picture n: <img>...</img>` prefix and the `<ref>`/`<box>` markup exactly as documented. The box coordinates are normalized values in `[0, 1000)`.
4. Full finetuning, LoRA, and Q-LoRA are separate choices. Do not mix the launch flags casually:
   - full finetuning uses the base training script with `--use_lora` off;
   - LoRA uses `--use_lora` and usually `--bf16`;
   - Q-LoRA adds `--q_lora` and uses `--fp16` rather than `--bf16`.
5. For Q-LoRA, prefer the Int4 chat model. The repo docs warn against using BF16 for that path.
6. The prepared inspection environment verified a compatible combination of `transformers==4.32.0`, `peft==0.5.0`, `deepspeed`, and CUDA torch wheels. If a different environment is used, re-check those versions before trusting the launch templates.
7. `CUDA_HOME` is not required to read the help text, but it matters if you want to compile or use optional DeepSpeed CUDA extensions. The troubleshooting reference explains the warning.

## Typical workflow

1. Validate the dataset with `python scripts/validate_finetune_data.py --data DATA.json`.
2. Pick the launch template that matches the task size and adapter strategy.
3. Replace the placeholder `MODEL`, `DATA`, and `OUTPUT_DIR` values.
4. Run the shell template explicitly; do not infer defaults from the source repo.
5. After training, load the adapter with the inference sub-skill or merge it only when the docs say the adapter type supports merging.

## Quick launch map

- Full finetuning: [scripts/finetune_full_ds.sh](scripts/finetune_full_ds.sh)
- LoRA single GPU: [scripts/finetune_lora_single_gpu.sh](scripts/finetune_lora_single_gpu.sh)
- LoRA DeepSpeed: [scripts/finetune_lora_ds.sh](scripts/finetune_lora_ds.sh)
- Q-LoRA single GPU: [scripts/finetune_qlora_single_gpu.sh](scripts/finetune_qlora_single_gpu.sh)
- Q-LoRA DeepSpeed: [scripts/finetune_qlora_ds.sh](scripts/finetune_qlora_ds.sh)

## What this sub-skill does not do

- It does not run a long training job on your behalf.
- It does not download data or checkpoints automatically.
- It does not merge Q-LoRA adapters, because the source docs say that merge path is not supported.

If the user already has a trained adapter and wants to use it for multimodal chat, route to the inference sub-skill for adapter-loading guidance.
