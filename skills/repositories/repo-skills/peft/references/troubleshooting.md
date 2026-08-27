# PEFT Troubleshooting

## Imports And Backend Packages

- PEFT user workflows normally need `peft`, `torch`, `transformers`, and `accelerate`; quantization or distributed backends add packages such as bitsandbytes, DeepSpeed, or FSDP-compatible PyTorch.
- Do not diagnose PEFT behavior from a base Python environment that cannot import `peft`.

## Adapter Setup

- Missing target-module errors usually require explicit `target_modules` or a different method for the architecture.
- Unexpected trainable parameters should be checked with `print_trainable_parameters()`, `get_model_status()`, and `get_layer_status()`.
- Use `modules_to_save` for heads or other non-adapter layers that must remain trainable and be saved.

## LoRA, Quantization, And Training

- For QLoRA-style training, prepare the k-bit base model before applying PEFT and prefer `target_modules="all-linear"` when appropriate.
- FSDP, DeepSpeed, offload, gradient checkpointing, and `torch.compile` can change save and dtype behavior; route those to `training-and-integrations`.

## Checkpoints And Merge

- A loadable adapter directory needs `adapter_config.json` and adapter weights.
- Adapter checkpoints do not contain the full base model unless explicitly saved elsewhere.
- Merge is not reversible after saving a merged full model and is unsupported for some adapter families.
