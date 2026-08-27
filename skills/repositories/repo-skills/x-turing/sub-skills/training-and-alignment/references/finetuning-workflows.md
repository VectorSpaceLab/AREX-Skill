# Finetuning workflows

## What this workflow covers

Use `model.finetune(...)` for supervised adaptation of causal language models.
The supported training inputs are:

- `TextDataset` for plain text continuation data
- `InstructionDataset` for instruction / response pairs
- LoRA variants when you want adapter-based training with lower memory use
- int8 and k-bit variants when the selected backend supports quantization

`model.finetune(...)` builds a `LightningTrainer` under the hood.

## Typical supervised fine-tuning flow

1. Load a dataset with the expected schema.
2. Create a model with the matching xTuring model key or class.
3. Inspect and edit the finetuning config.
4. Start training with `model.finetune(dataset=...)`.
5. Save the result with `model.save(...)` and run a short generation sanity check.

```python
from xturing.datasets import InstructionDataset
from xturing.models import BaseModel

instruction_dataset = InstructionDataset("/path/to/instruction_dataset")
model = BaseModel.create("qwen3_0_6b_lora")
model.finetune(dataset=instruction_dataset)
output = model.generate(texts=["Why are smaller language models popular?"])
model.save("/path/to/output_dir")
```

### Text fine-tuning

For continuation-style tasks, swap in `TextDataset` and a matching model key:

```python
from xturing.datasets import TextDataset
from xturing.models import BaseModel

text_dataset = TextDataset("/path/to/text_dataset")
model = BaseModel.create("gpt2")
model.finetune(dataset=text_dataset)
```

## Finetuning config

`model.finetuning_config()` returns the resolved config object loaded from the package defaults plus the selected model preset. The most common fields to adjust are:

- `learning_rate`
- `gradient_accumulation_steps`
- `batch_size`
- `weight_decay`
- `warmup_steps`
- `max_length`
- `num_train_epochs`
- `logging_steps`
- `max_grad_norm`
- `save_total_limit`
- `optimizer_name`
- `output_dir`
- `use_deepspeed`
- `deepspeed_config_path`

Optimizer choices are intentionally narrow:

- `adamw`
- `adam`
- `cpu_adam` `# requires DeepSpeed`

## Trainer behavior

`LightningTrainer` handles supervised runs and shares the same config object used by the model.

- On CPU, training stays on the CPU accelerator path.
- On GPU without LoRA / explicit DeepSpeed, the trainer uses the standard Lightning GPU path.
- On LoRA variants, the trainer is configured for DeepSpeed automatically.
- When `use_deepspeed=True`, a custom DeepSpeed config can be supplied with `deepspeed_config_path`.
- If `optimizer_name` is `cpu_adam`, DeepSpeed must be available.

## Choosing a training variant

### Full supervised fine-tuning

Use a non-LoRA model key or a direct model class when you want the whole backbone updated and you have enough memory.

### LoRA supervised fine-tuning

Use adapter training when you want the best balance of memory and quality.

Recommended presets:

- `qwen3_0_6b_lora` for Qwen3 0.6B
- `generic_lora` / `GenericLoraModel` for arbitrary base checkpoints

Generic LoRA is useful when you want to attach an adapter to your own base model id:

```python
from xturing.datasets import InstructionDataset
from xturing.models import GenericLoraModel

instruction_dataset = InstructionDataset("/path/to/instruction_dataset")
model = GenericLoraModel("facebook/opt-1.3b", target_modules=["q_proj", "v_proj"])
model.finetune(dataset=instruction_dataset)
```

If your backbone uses GPT-2 style naming, `c_attn` is the common default target module. If the model uses different projection names, override `target_modules` so the adapter actually matches modules in the backbone.

### int8 and k-bit choices

Use quantized training only when the hardware and backend are already ready.

- `*_int8`: 8-bit loading / training path. Treat this as backend-sensitive and do not assume it works on CPU.
- `*_lora_int8`: LoRA plus 8-bit loading. Requires CUDA-capable quantization support and bitsandbytes.
- `*_lora_kbit`: 4-bit / k-bit training prep with gradient checkpointing. Requires CUDA-capable quantization support.

For Qwen3, the ready-made LoRA preset is usually the simplest starting point:

```python
from xturing.datasets import InstructionDataset
from xturing.models import BaseModel

instruction_dataset = InstructionDataset("/path/to/instruction_dataset")
model = BaseModel.create("qwen3_0_6b_lora")
model.finetune(dataset=instruction_dataset)
```

## Save and reload after training

`model.save(output_dir)` writes the trained xTuring artifacts, tokenizer files, and the model metadata file that makes reload possible.

Reloading is straightforward when the output directory came from xTuring:

```python
from xturing.models import BaseModel

model = BaseModel.load("/path/to/output_dir")
```

If the directory is a plain external checkpoint without xTuring metadata, use the appropriate model class or the generic model path instead of assuming `BaseModel.load(...)` will infer everything.

## Safe preflight before training

Use the bundled preflight script to validate a dataset schema and inspect the resolved finetuning config without starting training. That keeps expensive jobs from launching on malformed data.
