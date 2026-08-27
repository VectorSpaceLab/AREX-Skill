# Fine-tuning troubleshooting

Use this file when a Stanford Alpaca supervised fine-tuning task fails during command planning, tokenizer/model loading, data consumption, distributed launch, sharding/offload setup, or full-scale training.

## OOM or CUDA memory fragmentation

**Symptoms**

- `torch.cuda.OutOfMemoryError`
- process killed during model load or first backward pass
- NCCL/FSDP failure after one rank OOMs
- GPU memory nearly full before the first optimizer step

**Likely causes**

- A 7B model in naive full fine-tuning can require roughly `7B params * 4 bytes * 4 optimizer/gradient/state copies ~= 112 GB` VRAM.
- `per_device_train_batch_size` or `model_max_length` is too high.
- FSDP auto-wrap layer class is wrong, so the intended blocks are not sharded.
- DeepSpeed/FSDP offload was requested but dependency/config/device setup did not activate.

**Recovery ladder**

1. Confirm the recipe uses FSDP full shard:
   ```text
   --fsdp "full_shard auto_wrap"
   --fsdp_transformer_layer_cls_to_wrap LlamaDecoderLayer   # for LLaMA
   --fsdp_transformer_layer_cls_to_wrap OPTDecoderLayer     # for OPT
   ```
2. If still OOM, lower `--per_device_train_batch_size` and raise `--gradient_accumulation_steps` to preserve the desired global batch.
3. Try FSDP CPU offload:
   ```text
   --fsdp "full_shard auto_wrap offload"
   ```
4. Try DeepSpeed ZeRO-3 CPU offload with `scripts/default_offload_opt_param.json`.
5. Reduce `--model_max_length` only after accepting additional truncation.
6. Avoid presenting a CPU import or parser check as proof that GPU memory will fit.

## Missing pad/eos/bos/unk tokens

**Symptoms**

- tokenizer has no `pad_token_id`
- batching fails during padding
- model embedding/tokenizer length mismatch after adding tokens
- loss behaves strangely because EOS is absent from targets

**Expected trainer behavior**

The trainer checks `tokenizer.pad_token`, `eos_token`, `bos_token`, and `unk_token`. Missing slots are filled with `[PAD]`, `</s>`, `<s>`, and `<unk>` respectively. It then calls `model.resize_token_embeddings(len(tokenizer))` and initializes new embedding rows from the mean of existing rows.

**Recovery**

- Do not remove the special-token resize step from the adapted trainer.
- If using a custom tokenizer, inspect token ids before training and confirm the tokenizer can right-pad.
- If a saved checkpoint later reloads with mismatched embeddings, save and reload tokenizer artifacts alongside the final model.

## Tokenizer/model mismatch

**Symptoms**

- `size mismatch` during model load
- tokenizer files load but model config is from a different family
- FSDP wrapper class is not found or does not match the model blocks
- generated command uses LLaMA layer class for OPT or vice versa

**Recovery**

- Ensure `--model_name_or_path` points to a compatible model and tokenizer pair.
- For converted LLaMA checkpoints, verify both the checkpoint and tokenizer are in Hugging Face format before launch.
- Use `LlamaDecoderLayer` for LLaMA-style models and `OPTDecoderLayer` for OPT-style models.
- If the model is neither LLaMA nor OPT, identify the actual decoder block class before using FSDP auto-wrap.
- Keep `use_fast=False` unless you have validated fast-tokenizer behavior for the chosen model family.

## Invalid or stale `data_path`

**Symptoms**

- `FileNotFoundError`
- JSON decode error
- `KeyError` during `SupervisedDataset` construction
- training hangs or spends a long time in `Tokenizing inputs...`

**Recovery**

- Confirm the path exists from the process working directory used by `torchrun`.
- Validate data schema and prompt-related assumptions through `dataset-and-prompts`; do not debug prompt text inside this sub-skill.
- Use a small fixture first if you only need to verify parser/data-loading behavior.
- Remember that `SupervisedDataset` reads and tokenizes the full dataset eagerly at construction time.

## Missing `accelerate`, `deepspeed`, or `wandb`

**Symptoms**

- Hugging Face Trainer complains that `accelerate` is missing or too old.
- `--deepspeed ...` fails with `ModuleNotFoundError: deepspeed`.
- training attempts to initialize Weights & Biases unexpectedly or errors because `wandb` is missing.

**Recovery**

- Install a Transformers-compatible `accelerate` package in the training environment if Trainer/distributed setup requires it.
- Install DeepSpeed only for the DeepSpeed recipe:
  ```bash
  pip install deepspeed
  ```
- If W&B logging is not desired, disable reporting with the local Transformers-supported `--report_to` value or environment variables such as W&B disabled/offline mode. If W&B is desired, install and authenticate it before a long run.
- Keep optional training dependencies out of command-planning checks unless the user is actually launching the corresponding recipe.

## CPU vs CUDA confusion

**Symptoms**

- parser/help works, but full training is extremely slow or impossible
- `torch.cuda.is_available()` is false in the selected environment
- `torchrun --nproc_per_node=4` launches processes that all run on CPU
- only one GPU is visible despite a 4-GPU command

**Recovery**

- Treat CPU checks as validation of code paths, not proof of GPU training readiness.
- Verify the training environment has a CUDA-enabled PyTorch build when launching the README GPU recipes.
- Check GPU visibility before launch with the system's GPU probe and `python -c "import torch; print(torch.cuda.is_available(), torch.cuda.device_count())"`.
- Ensure `CUDA_VISIBLE_DEVICES` exposes at least `nproc_per_node` devices.
- Do not pass `--no_cuda` for a full-scale CUDA run.
- Match `--nproc_per_node` to visible devices; wrong world size can produce NCCL/rendezvous errors.

## DeepSpeed config path or key errors

**Symptoms**

- `--deepspeed` path not found
- DeepSpeed rejects config keys
- ZeRO stage/offload does not activate

**Recovery**

- Use the bundled path from this sub-skill when launching from the `fine-tuning` directory:
  ```text
  --deepspeed scripts/default_offload_opt_param.json
  ```
- Confirm the config still contains `zero_optimization.stage: 3`, `offload_optimizer.device: cpu`, and `offload_param.device: cpu`.
- Do not mix `--fsdp` and `--deepspeed` in the same command.
- Keep Trainer batch/optimizer fields consistent with DeepSpeed `auto` fields.

## Full-scale training caveats

**Caveats to communicate**

- The repository training script is intentionally simple and not heavily optimized.
- The README documented a 4x A100 80GB FSDP recipe; smaller or different hardware may need offload, smaller micro-batches, or a different recipe.
- The global batch size of 128 is a documented reproduction setting, not a proven optimum.
- DeepSpeed and FSDP offload can fit runs that otherwise OOM, but usually increase wall-clock time.
- Full runs require model weights, tokenizer assets, output storage, and license/usage compliance; this sub-skill does not recover LLaMA/Alpaca weights.

Route weight recovery questions to `weight-diff-recovery` and dataset/prompt validation questions to `dataset-and-prompts`.
