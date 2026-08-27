# CLI Reference

The training surface in DeTikZify is organized around Python entrypoints and `torchrun`-style launches rather than a single package CLI.

## Common argument groups

### Standard fine-tuning

- `--base_model`
- `--projector`
- `--datikz`
- `--sketch_ratio`
- `--output`
- `--deepspeed`
- `--gradient_checkpointing`

### Projection pretraining

- `--base_model`
- `--size`
- `--output`
- `--deepspeed`
- `--gradient_checkpointing`

### Refinement / GRPO

- `--base_model`
- `--datikz`
- `--sketch_ratio`
- `--output`
- `--num_compile_workers`
- `--deepspeed`
- `--gradient_checkpointing`
- `--strict`
- `--batch_size`
- `--num_train_steps`

### TikZero adapter pretraining

- `--base_model`
- `--embedding_model`
- `--output`
- `--deepspeed`
- `--gradient_checkpointing`
- `--mse_loss`

### TikZero end-to-end fine-tuning

- `--base_model`
- `--embedding_model`
- `--adapter_model`
- `--datikz`
- `--caption_condition`
- `--output`
- `--deepspeed`
- `--gradient_checkpointing`

## Output and launch semantics

- Most training flows write checkpoints and final weights into a chosen output directory.
- Distributed runs use the standard `torchrun` / process-group environment variables.
- Some workflows resume from an existing checkpoint unless told to overwrite or start from scratch.
- `bf16` and `tf32` are common defaults in the repo's training code paths.
