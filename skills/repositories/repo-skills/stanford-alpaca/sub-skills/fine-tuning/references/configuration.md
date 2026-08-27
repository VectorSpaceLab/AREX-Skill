# Fine-tuning configuration reference

This reference collects the training flags, hyperparameters, batch-size math, and offload config facts needed to adapt the Stanford Alpaca supervised fine-tuning recipe.

## Package/runtime assumptions

- The repository documents Python 3.10 for reproducing the LLaMA recipe, while the project metadata also advertises Python 3.9+.
- Core training packages are `torch`, `transformers>=4.28.1`, `sentencepiece`, and `tokenizers>=0.13.3`.
- `wandb` is listed in requirements but is not required for argument parsing; it can be disabled with `--report_to none`/empty reporting depending on the local Transformers version or by setting the relevant W&B environment variables.
- `deepspeed` is optional and required only when using `--deepspeed scripts/default_offload_opt_param.json`.

## README hyperparameter table

| Hyperparameter | LLaMA-7B | LLaMA-13B |
| --- | ---: | ---: |
| Global batch size | 128 | 128 |
| Learning rate | `2e-5` | `1e-5` |
| Epochs | 3 | 5 |
| Max length | 512 | 512 |
| Weight decay | 0 | 0 |

The OPT-6.7B README command demonstrates that the same trainer works for OPT-style causal LMs, but it is not an optimality claim for every OPT size or downstream dataset.

## Batch-size math

For single-node `torchrun`, compute global batch as:

```text
global_batch_size = nproc_per_node * per_device_train_batch_size * gradient_accumulation_steps
```

Documented default:

```text
4 GPUs * 4 examples per GPU * 8 accumulation steps = 128
```

If the user changes GPU count:

| GPUs | Per-device batch | Accumulation for global batch 128 |
| ---: | ---: | ---: |
| 1 | 4 | 32 |
| 2 | 4 | 16 |
| 4 | 4 | 8 |
| 8 | 4 | 4 |

If OOM forces `per_device_train_batch_size=2`, double accumulation to preserve the same global batch. The README explicitly says global batch size has not been optimized; preserve it for reproduction-oriented runs, but do not present it as universally best.

## Tokenizer and sequence configuration

The trainer uses:

```python
AutoTokenizer.from_pretrained(
    model_name_or_path,
    cache_dir=training_args.cache_dir,
    model_max_length=training_args.model_max_length,
    padding_side="right",
    use_fast=False,
)
```

Special-token defaults added when missing:

| Token slot | Value |
| --- | --- |
| `pad_token` | `[PAD]` |
| `eos_token` | `</s>` |
| `bos_token` | `<s>` |
| `unk_token` | `<unk>` |

After adding any token, the script calls `model.resize_token_embeddings(len(tokenizer))` and initializes new input/output embedding rows to the average of existing rows.

`model_max_length=512` drives right padding and truncation in tokenization. Raising it increases memory usage; lowering it can truncate useful target tokens.

## FSDP settings

| Model family | `--fsdp` | `--fsdp_transformer_layer_cls_to_wrap` |
| --- | --- | --- |
| LLaMA | `full_shard auto_wrap` | `LlamaDecoderLayer` |
| OPT | `full_shard auto_wrap` | `OPTDecoderLayer` |
| LLaMA/OPT with CPU offload | `full_shard auto_wrap offload` | matching layer class |

Notes:

- Full shard avoids redundant full model copies on every GPU.
- CPU offload reduces VRAM pressure but slows training and increases host-memory and host-device-transfer demands.
- Do not set FSDP and DeepSpeed in the same command.

## DeepSpeed ZeRO-3 offload settings

Use `scripts/default_offload_opt_param.json` with `--deepspeed` for the documented DeepSpeed offload recipe. The bundled config contains these important key families:

| Key path | Value / shape | Meaning |
| --- | --- | --- |
| `bf16.enabled` | `auto` | Let Trainer/DeepSpeed coordinate bfloat16 behavior. |
| `optimizer.type` | `AdamW` | DeepSpeed optimizer wrapper. |
| `optimizer.params.lr` / `betas` / `eps` / `weight_decay` | `auto` | Trainer-provided values are propagated. |
| `scheduler.type` | `WarmupDecayLR` | DeepSpeed scheduler with auto-derived schedule params. |
| `scheduler.params.total_num_steps` | `auto` | Derived from training plan. |
| `zero_optimization.stage` | `3` | ZeRO stage 3 partitions optimizer states, gradients, and parameters. |
| `zero_optimization.offload_optimizer.device` | `cpu` | Offload optimizer state to CPU. |
| `zero_optimization.offload_optimizer.pin_memory` | `true` | Use pinned host memory for optimizer offload. |
| `zero_optimization.offload_param.device` | `cpu` | Offload parameters to CPU. |
| `zero_optimization.offload_param.pin_memory` | `true` | Use pinned host memory for parameter offload. |
| `zero_optimization.overlap_comm` | `true` | Overlap communication where possible. |
| `zero_optimization.contiguous_gradients` | `true` | Store gradients contiguously to reduce fragmentation. |
| `zero_optimization.reduce_bucket_size` | `auto` | Let DeepSpeed set bucket size. |
| `zero_optimization.stage3_prefetch_bucket_size` | `auto` | Let DeepSpeed set prefetch bucket size. |
| `zero_optimization.stage3_param_persistence_threshold` | `auto` | Auto-tune stage-3 persistence threshold. |
| `zero_optimization.stage3_gather_16bit_weights_on_model_save` | `false` | Do not gather 16-bit weights automatically on model save. |
| `gradient_accumulation_steps` | `auto` | Trainer-provided accumulation. |
| `gradient_clipping` | `auto` | Trainer-provided gradient clipping. |
| `train_batch_size` | `auto` | Trainer-derived global batch size. |
| `train_micro_batch_size_per_gpu` | `auto` | Trainer-derived micro-batch size. |
| `steps_per_print` | `5` | DeepSpeed log interval. |
| `wall_clock_breakdown` | `false` | Disable detailed timing breakdown. |

DeepSpeed can be more memory-efficient than FSDP offload in some setups, but it adds another dependency, additional config interactions, and slower CPU-offloaded training.

## Recommended launch flag groups

### FSDP full shard

```text
--bf16 True
--per_device_train_batch_size 4
--gradient_accumulation_steps 8
--evaluation_strategy no
--save_strategy steps
--save_steps 2000
--save_total_limit 1
--warmup_ratio 0.03
--lr_scheduler_type cosine
--logging_steps 1
--fsdp "full_shard auto_wrap"
--fsdp_transformer_layer_cls_to_wrap <LlamaDecoderLayer-or-OPTDecoderLayer>
--tf32 True
```

### FSDP offload

Use the same group, but set:

```text
--fsdp "full_shard auto_wrap offload"
```

### DeepSpeed offload

Use the same optimizer/batch/save flags, omit FSDP flags, and set:

```text
--deepspeed scripts/default_offload_opt_param.json
```

## Path fields

| Field | Guidance |
| --- | --- |
| `model_name_or_path` | Use a model id or local checkpoint directory with matching tokenizer assets. LLaMA must be converted to Hugging Face format before use. |
| `data_path` | Use the validated dataset produced or checked by `dataset-and-prompts`. |
| `output_dir` | Must be writable and large enough for checkpoints/final weights. Avoid reusing a non-empty directory unless resuming intentionally. |
| `cache_dir` | Optional cache location; do not hard-code private cache paths into reusable commands. |
