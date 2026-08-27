---
name: training-and-integrations
description: "Use PEFT with Transformers Trainer, Accelerate, FSDP, DeepSpeed,
  TRL SFT, Diffusers training examples, memory-efficient training,
  torch.compile, and backend-specific training caveats."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Training and Integrations

Use this sub-skill when the task is about fitting PEFT into a training workflow rather than choosing adapter method parameters. It covers `Trainer`, `Seq2SeqTrainer`, `SFTTrainer`, raw `Accelerate`, FSDP, DeepSpeed, Diffusers DreamBooth/ControlNet-style scripts, memory-reduction choices, quantized training backends, and adapting PEFT example workflows safely.

## Route Here For

- Converting a single-GPU PEFT training script to `accelerate launch`, FSDP, DeepSpeed, or multi-GPU SFT.
- Deciding where PEFT wrapping belongs in `Trainer`, `SFTTrainer`, custom training loops, or Diffusers pipelines.
- Troubleshooting distributed save behavior, mixed precision gradient errors, gradient checkpointing/offload interactions, optional backend dependencies, or example scripts that drift with upstream APIs.
- Building a training readiness checklist without downloading data/models or running training.
- Deciding whether `torch.compile`, quantized loading, CPU/GPU offload, or gradient checkpointing is safe for a PEFT workflow.

## Route Elsewhere

- Core `LoraConfig`, `PeftConfig`, `get_peft_model`, adapter lifecycle, target module discovery, and `modules_to_save`: use `../adapter-core/SKILL.md`.
- LoRA variants, QLoRA configuration, LoftQ, QALoRA, DoRA, quantization parameter choices, and trainable tokens: use `../lora-and-quantization/SKILL.md`.
- Prompt tuning, prefix tuning, p-tuning, and soft prompt method behavior: use `../prompt-and-soft-methods/SKILL.md`.
- Non-LoRA tuner families such as IA3, BOFT/OFT, LoHa/LoKr, VeRA, HRA, RandLoRA, and similar method-specific choices: use `../specialized-tuners/SKILL.md`.
- Saving, loading, merging, conversion, deployment packaging, or checkpoint format questions after training: use `../save-load-merge/SKILL.md`.

## Start Fast

1. Run the bundled no-training checklist builder from this sub-skill directory:

   ```bash
   python scripts/build_training_checklist.py --workflow trainer --backend single-gpu
   python scripts/build_training_checklist.py --workflow trainer --backend fsdp --quantized
   python scripts/build_training_checklist.py --workflow diffusers --backend deepspeed
   ```

2. Read `references/training-recipes.md` for PEFT placement in `Trainer`, `SFTTrainer`, `Accelerate`, and Diffusers-style scripts.
3. Read `references/distributed-and-backends.md` before changing FSDP, DeepSpeed, quantization, offload, or `torch.compile` settings.
4. Read `references/troubleshooting.md` when failures mention FP16 gradient unscale, gradient checkpointing, optional packages, FSDP/DeepSpeed save behavior, stale examples, or backend-specific dtype limitations.

## Core Workflow Pattern

- Prepare the base model/tokenizer/dataset exactly as the training framework expects, then apply PEFT before the trainer or accelerator prepares the model.
- For Transformers `Trainer`, pass a `PeftModel` as `model`, or use a trainer integration such as TRL `SFTTrainer(peft_config=...)` when that trainer is responsible for wrapping.
- For raw `Accelerate`, build the PEFT model before `accelerator.prepare(...)`; after preparation, save adapters with the unwrapped model on the main process.
- For FSDP, set PEFT-aware wrapping through `peft.utils.other.fsdp_auto_wrap_policy`, keep `fsdp_use_orig_params: false` when memory savings matter, and switch to a full state dict before final adapter save when using trainer-managed FSDP.
- For DeepSpeed ZeRO-3, align `accelerate` config and training arguments, keep gradient accumulation consistent across both, and use trainer/accelerator save helpers rather than rank-local saves.
- For quantized PEFT training, route method/backend parameters to `lora-and-quantization`, but keep integration checks here: installed optional backend, `prepare_model_for_kbit_training`, compatible gradient checkpointing mode, and compatible distributed backend.

## Safety Rules For Adapting Examples

- Treat examples as patterns, not stable APIs: re-check current `transformers`, `accelerate`, `trl`, `diffusers`, `bitsandbytes`, and `torch` versions when adapting.
- Do not run example training as a smoke test unless the user explicitly wants downloads, GPU time, and dataset access; use parser/help checks or dry configuration review first.
- Replace hard-coded model IDs, dataset names, hub push flags, precision flags, and output directories with user-controlled arguments.
- Preserve the final adapter save path and distributed save semantics when porting examples to FSDP or DeepSpeed.
- Keep PEFT adapter configuration decisions separate from launcher/backend decisions so changes are reviewable.

## Bundled Materials

- `references/training-recipes.md`: framework-specific recipes for `Trainer`, `Accelerate`, TRL SFT, Diffusers training, memory-efficient training, and `torch.compile` placement.
- `references/distributed-and-backends.md`: FSDP, DeepSpeed, quantization, offload, precision, and backend compatibility guidance.
- `references/troubleshooting.md`: diagnosis paths for stale examples, dtype unscale errors, checkpointing/offload issues, optional packages, distributed saves, and compile limitations.
- `scripts/build_training_checklist.py`: parser-only checklist generator for `trainer`, `accelerate`, and `diffusers` workflows across `single-gpu`, `fsdp`, `deepspeed`, and `cpu` backends.
