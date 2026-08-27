# PEFT Training Recipes

This reference is for placing PEFT correctly inside training workflows. It intentionally avoids method-specific hyperparameter tables; route those to the method sub-skills.

## Generic Preflight

Before wiring a training run:

- Install runtime packages generically with `pip install peft`, or use an editable source install only when contributing to PEFT itself.
- Verify `import peft`, `import torch`, `import transformers`, and `import accelerate`; add `trl`, `diffusers`, `bitsandbytes`, `deepspeed`, or `gptqmodel` only for workflows that actually need them.
- Choose the training framework first, then choose backend launch settings, then choose adapter method parameters.
- Confirm `model.print_trainable_parameters()` or equivalent trainable-parameter inspection before spending GPU time.
- Keep `output_dir` for adapters separate from downloaded base model caches and from merged/full-model export directories.

## Transformers Trainer

Use this pattern when the base model is a Transformers model and the training loop is ordinary supervised fine-tuning, sequence classification, token classification, seq2seq, or causal LM training.

1. Load the base model and tokenizer with the dtype/device map appropriate for the backend.
2. If using k-bit bitsandbytes training, call `prepare_model_for_kbit_training(base_model)` before PEFT wrapping.
3. Construct the PEFT config, usually from `LoraConfig`, IA3, prompt tuning, or another method-specific config.
4. Call `get_peft_model(base_model, peft_config)` before creating `Trainer`, unless the selected trainer accepts `peft_config` directly.
5. Set `model.config.use_cache = False` when using gradient checkpointing for causal LM training.
6. Build `TrainingArguments` with precision and distributed settings consistent with the launcher.
7. Call `trainer.train(...)` and `trainer.save_model()` or `model.save_pretrained(...)` through the framework's main-process save path.

Minimal shape:

```python
from peft import LoraConfig, get_peft_model
from transformers import Trainer, TrainingArguments

base_model = ...
peft_config = LoraConfig(task_type="CAUSAL_LM", target_modules="all-linear")
model = get_peft_model(base_model, peft_config)
model.print_trainable_parameters()

training_args = TrainingArguments(output_dir="adapter-out", bf16=True)
trainer = Trainer(model=model, args=training_args, train_dataset=train_dataset)
trainer.train()
trainer.save_model()
```

Use `Seq2SeqTrainer` the same way, but keep generation/evaluation settings on the trainer side and adapter settings on the PEFT side.

## TRL SFTTrainer

Use TRL `SFTTrainer` when the task is instruction/chat supervised fine-tuning and TRL owns dataset formatting, packing, and chat templates.

Typical pattern:

- Create a tokenizer and dataset with the expected text field or chat template.
- Create `peft_config` separately and pass it to `SFTTrainer(peft_config=peft_config, ...)`.
- Let `SFTTrainer`/Accelerate prepare the model; do not also wrap the same model manually unless the trainer version explicitly expects a pre-wrapped model.
- Keep `packing`, `max_seq_length`/`max_length`, `gradient_checkpointing`, and `gradient_checkpointing_kwargs` explicit because they strongly affect memory.
- Save with `trainer.save_model()` so distributed wrappers and adapter-only save semantics are respected.

For QLoRA-style SFT, check the reentrant checkpointing rule for the selected setup. PEFT examples use `use_reentrant=True` for single-GPU QLoRA and `use_reentrant=False` for multi-GPU QLoRA in some workflows; treat this as a backend-specific compatibility choice, not a universal constant.

## Raw Accelerate Loop

Use raw `Accelerate` when custom training logic matters more than trainer convenience.

Recommended order:

1. Create `Accelerator(...)` with the desired mixed precision and project config.
2. Load model/tokenizer/dataloaders.
3. Apply quantized-preparation helpers if needed.
4. Wrap the model with PEFT.
5. Build optimizer only over trainable parameters.
6. Call `accelerator.prepare(model, optimizer, train_dataloader, scheduler)`.
7. Train with `accelerator.backward(loss)`.
8. Save only on `accelerator.is_main_process`, using `accelerator.unwrap_model(model).save_pretrained(output_dir)`.

Avoid calling `save_pretrained` on each distributed rank. For ZeRO/FSDP, use the trainer/accelerator state-dict helpers required by that backend before final save.

## Diffusers Training

Use this for DreamBooth, Stable Diffusion, ControlNet, Flux, or other diffusion examples that inject adapters into UNet/text encoder modules.

Checklist:

- Install `diffusers` and any example-specific optional packages only when the workflow needs them.
- Identify which components receive adapters: commonly UNet attention processors, text encoder layers, or both.
- Freeze all non-adapter parameters explicitly and verify trainable names before training.
- Keep latent caching, VAE dtype, mixed precision, gradient accumulation, and optimizer settings in the Diffusers script; keep adapter method parameters in PEFT config objects.
- Save adapters in a PEFT-compatible format and document any conversion needed for non-PEFT ecosystems.
- Treat conversion scripts between PEFT and third-party Stable Diffusion LoRA formats as save/load concerns and route to `save-load-merge`.

Diffusers examples often change with upstream APIs. When an example fails, first verify the installed `diffusers`, `transformers`, `accelerate`, and `peft` versions and inspect renamed pipeline arguments before changing adapter code.

## Memory-Efficient Training Choices

PEFT reduces trainable optimizer and gradient memory, but the base model, activations, and loss tensors can still dominate. Use this order before adding complex distributed machinery:

1. Smaller model, smaller batch, shorter sequence/resolution, or gradient accumulation.
2. Mixed precision with `bf16` where hardware supports it; use `fp16` carefully with adapter trainable dtype.
3. Gradient checkpointing, with backend-specific `use_reentrant` settings.
4. Quantized base model plus PEFT adapters, using `prepare_model_for_kbit_training` for k-bit bitsandbytes workflows.
5. FSDP or DeepSpeed for multi-GPU sharding/offload.
6. TRL memory features such as chunked language-modeling loss or Liger kernels when using compatible TRL versions.
7. `torch.compile` only after correctness is established.

## torch.compile Placement

PEFT supports `torch.compile` for several training and inference paths, including Transformers `Trainer`, custom PyTorch loops, inference, generation, LoRA/DoRA, IA3, BOFT/OFT, LoHa/LoKr, VeRA, HRA, modules-to-save, quantization, adapter disabling, merging, and mixed adapter batches in tested scenarios.

Practical rules:

- Compile after loading and adding all adapters needed for the run.
- Avoid dynamic adapter loading/switching after compilation unless you have a specific tested pattern.
- Validate numerics on a tiny batch before trusting speedups; a compile run can succeed but still produce incorrect outputs for unsupported dynamic behavior.
- Expect graph breaks or modest speedups when adapter operations remain dynamic.
