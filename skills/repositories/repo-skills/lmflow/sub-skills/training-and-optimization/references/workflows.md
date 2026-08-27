# LMFlow Training Workflows

## Full Fine-Tuning

Full fine-tuning updates all parameters of the base model.

Typical inputs:

- `model_name_or_path`
- `dataset_path`
- `output_dir`
- `conversation_template` for chat-style data
- `num_train_epochs`
- `learning_rate`
- `per_device_train_batch_size`
- `gradient_accumulation_steps`

Use full fine-tuning when the user wants the simplest baseline and has enough memory.

## LoRA

LoRA fine-tuning adds low-rank adapters and is usually the first efficient adaptation choice.

Typical additions:

- `use_lora=1`
- `lora_r`
- `lora_alpha`
- `lora_dropout`

## QLoRA

QLoRA combines adapters with quantized weights.

Typical additions:

- `use_qlora=1`
- `quant_bit=4` or `quant_bit=8`
- LoRA adapter parameters

Use this when memory is tighter than the LoRA path can handle.

## LISA

LISA activates a limited number of layers at a time.

Typical additions:

- `use_lisa=1`
- `lisa_activated_layers`
- `lisa_interval_steps`

Use this only when the user explicitly wants LISA or memory-efficient layer switching.

## Custom Optimizers

LMFlow exposes a long list of optimizer names in `OptimizerNames`. A custom optimizer run may need extra fields such as beta, momentum, or weight-decay settings.

Common custom names include:

- `adabelief`
- `adabound`
- `lars`
- `lamb`
- `adamax`
- `nadam`
- `radam`
- `adamp`
- `sgdp`
- `yogi`
- `sophia`
- `adan`
- `adam`
- `novograd`
- `adadelta`
- `adagrad`
- `muon`
- `adamw_schedule_free`
- `sgd_schedule_free`

## Launch Planning

LMFlow examples show Accelerate/FSDP and DeepSpeed launcher patterns. For a future agent, the safe default is to render a command first, then decide whether the run should be wrapped in an accelerator launcher.

## Output Safety

Always decide one of these before a run:

- a fresh `output_dir`;
- deliberate overwrite;
- resume from checkpoint.

The skill does not hide those choices.
