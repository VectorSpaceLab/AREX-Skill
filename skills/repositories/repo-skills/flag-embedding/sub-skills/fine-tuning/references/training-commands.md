# Training Commands

Build commands in two phases: validate data first, then construct a `torchrun` command that names the correct module entry point. Do not launch full training until the user confirms devices, model/cache availability, data paths, output directory, and runtime budget.

## Installation and Backend Caveats

Base package requirements include PyTorch, Transformers, Datasets, Accelerate, Sentence Transformers, PEFT, IR Datasets, SentencePiece, and Protobuf. The optional finetune extra adds DeepSpeed and flash-attn:

```bash
pip install -U "FlagEmbedding[finetune]"
```

Treat that install as a dependency plan, not proof of a working GPU stack. DeepSpeed, flash-attn, BF16/FP16, CUDA versions, compiler availability, model size, and tokenizer/model downloads must be checked in the target runtime.

## Module Entry Points

Embedder modules:

- `FlagEmbedding.finetune.embedder.encoder_only.base`: standard encoder-only embedding models.
- `FlagEmbedding.finetune.embedder.encoder_only.m3`: bge-m3, including unified fine-tuning and self-distillation flags.
- `FlagEmbedding.finetune.embedder.decoder_only.base`: decoder-only embedding models, usually with LoRA and `last_token` pooling.
- `FlagEmbedding.finetune.embedder.decoder_only.icl`: decoder-only ICL embedder, including example length and suffix flags.

Reranker modules:

- `FlagEmbedding.finetune.reranker.encoder_only.base`: standard encoder-only rerankers.
- `FlagEmbedding.finetune.reranker.decoder_only.base`: decoder-only rerankers, usually with LoRA and optional flash-attn.
- `FlagEmbedding.finetune.reranker.decoder_only.layerwise`: decoder-only layerwise rerankers with `start_layer`, `head_multi`, and `head_type`.

Each module is a Python module entry point. Use it with `torchrun -m`, not as a filesystem script.

## Common Embedder Arguments

Model arguments:

- `model_name_or_path`, `config_name`, `tokenizer_name`, `cache_dir`, `trust_remote_code`, `use_fast_tokenizer`, `token`.

Data arguments:

- `train_data`: one or more JSONL files or directories containing JSONL/JSON files.
- `cache_path`: dataset cache path.
- `train_group_size`: total group size per query, including one positive.
- `query_max_len`, `passage_max_len`, `pad_to_multiple_of`.
- `max_example_num_per_dataset`.
- `query_instruction_for_retrieval`, `query_instruction_format`.
- `knowledge_distillation`.
- `passage_instruction_for_retrieval`, `passage_instruction_format`.
- `shuffle_ratio`.
- `same_dataset_within_batch`, `small_threshold`, `drop_threshold`.

Training tail arguments added by FlagEmbedding:

- `negatives_cross_device`: share negatives across devices.
- `temperature`: similarity temperature.
- `fix_position_embedding`: freeze position embeddings.
- `sentence_pooling_method`: `cls`, `mean`, or `last_token`.
- `normalize_embeddings`: normalize embeddings before loss.
- `sub_batch_size`: split large batches inside the collator/trainer.
- `kd_loss_type`: `kl_div` or `m3_kd_loss`.
- `use_mrl`, `mrl_dims`: Matryoshka representation learning controls.

Standard Transformers training arguments are also accepted, including `output_dir`, `overwrite_output_dir`, `learning_rate`, `fp16`, `bf16`, `num_train_epochs`, `per_device_train_batch_size`, `gradient_accumulation_steps`, `dataloader_drop_last`, `warmup_ratio`, `gradient_checkpointing`, `weight_decay`, `deepspeed`, `logging_steps`, and `save_steps`.

## Common Reranker Arguments

Model arguments:

- `model_name_or_path`, `config_name`, `tokenizer_name`, `cache_dir`, `trust_remote_code`, `model_type`, `use_fast_tokenizer`, `token`.

Data arguments:

- `train_data`, `cache_path`, `train_group_size`.
- `query_max_len`, `passage_max_len`, `max_len`, `pad_to_multiple_of`.
- `max_example_num_per_dataset`.
- `query_instruction_for_rerank`, `query_instruction_format`.
- `knowledge_distillation`.
- `passage_instruction_for_rerank`, `passage_instruction_format`.
- `shuffle_ratio`.
- `sep_token`: separator token for decoder-only rerankers.

Reranker training adds `sub_batch_size`, but source metadata notes that it is not implemented yet for reranker training.

## DeepSpeed Config Shapes

The examples use two small DeepSpeed config shapes. Create the JSON in the run directory and pass it with `--deepspeed`.

Stage 0 shape:

```json
{
  "zero_optimization": {"stage": 0},
  "fp16": {"enabled": "auto", "loss_scale": 0, "loss_scale_window": 1000, "initial_scale_power": 12, "hysteresis": 2, "min_loss_scale": 1},
  "bf16": {"enabled": "auto"},
  "optimizer": {"type": "AdamW", "params": {"lr": "auto", "betas": "auto", "eps": "auto", "weight_decay": "auto"}},
  "scheduler": {"type": "WarmupDecayLR", "params": {"warmup_min_lr": "auto", "warmup_max_lr": "auto", "warmup_num_steps": "auto", "total_num_steps": "auto"}},
  "gradient_accumulation_steps": "auto",
  "gradient_clipping": "auto",
  "steps_per_print": 100,
  "train_batch_size": "auto",
  "train_micro_batch_size_per_gpu": "auto",
  "wall_clock_breakdown": false
}
```

Stage 1 shape adds ZeRO stage 1 and a reduce bucket:

```json
{
  "zero_optimization": {"stage": 1, "reduce_bucket_size": 500000000.0},
  "fp16": {"enabled": "auto", "loss_scale": 0, "initial_scale_power": 10, "loss_scale_window": 1000, "hysteresis": 2, "min_loss_scale": 1},
  "bf16": {"enabled": "auto", "loss_scale": 0, "initial_scale_power": 10, "loss_scale_window": 1000, "hysteresis": 2, "min_loss_scale": 1},
  "optimizer": {"type": "AdamW", "params": {"lr": "auto", "betas": "auto", "eps": "auto", "weight_decay": "auto", "torch_adam": true}},
  "scheduler": {"type": "WarmupDecayLR", "params": {"warmup_min_lr": "auto", "warmup_max_lr": "auto", "warmup_num_steps": "auto", "total_num_steps": "auto"}},
  "gradient_accumulation_steps": "auto",
  "gradient_clipping": "auto",
  "steps_per_print": 1000,
  "train_batch_size": "auto",
  "train_micro_batch_size_per_gpu": "auto",
  "wall_clock_breakdown": false
}
```

Use stage 0 for smaller encoder-only jobs unless memory requires more. Decoder-only LoRA examples often used stage 1, but the right choice is hardware and model dependent.

## Command Patterns

Before any command, validate data:

```bash
python scripts/validate_train_jsonl.py --task embedder --knowledge-distillation data/train.scored.jsonl
```

Standard encoder-only embedder:

```bash
torchrun --nproc_per_node 2 \
  -m FlagEmbedding.finetune.embedder.encoder_only.base \
  --model_name_or_path BAAI/bge-large-en-v1.5 \
  --cache_dir ./cache/model \
  --train_data data/retrieval data/sts.jsonl data/classification-no_in_batch_neg \
  --cache_path ./cache/data \
  --train_group_size 8 \
  --query_max_len 512 \
  --passage_max_len 512 \
  --pad_to_multiple_of 8 \
  --query_instruction_for_retrieval "Represent this sentence for searching relevant passages: " \
  --query_instruction_format "{}{}" \
  --knowledge_distillation False \
  --output_dir outputs/embedder-base \
  --overwrite_output_dir \
  --learning_rate 1e-5 \
  --fp16 \
  --num_train_epochs 2 \
  --per_device_train_batch_size 2 \
  --dataloader_drop_last True \
  --warmup_ratio 0.1 \
  --gradient_checkpointing \
  --deepspeed ds_stage0.json \
  --logging_steps 1 \
  --save_steps 1000 \
  --negatives_cross_device \
  --temperature 0.02 \
  --sentence_pooling_method cls \
  --normalize_embeddings True \
  --kd_loss_type kl_div
```

bge-m3 unified embedder fine-tuning with same-dataset batching:

```bash
torchrun --nproc_per_node 2 \
  -m FlagEmbedding.finetune.embedder.encoder_only.m3 \
  --model_name_or_path BAAI/bge-m3 \
  --cache_dir ./cache/model \
  --train_data data/retrieval data/sts.jsonl data/classification-no_in_batch_neg data/clustering-no_in_batch_neg \
  --cache_path ./cache/data \
  --train_group_size 8 \
  --query_max_len 512 \
  --passage_max_len 512 \
  --pad_to_multiple_of 8 \
  --knowledge_distillation True \
  --same_dataset_within_batch True \
  --small_threshold 0 \
  --drop_threshold 0 \
  --output_dir outputs/bge-m3-unified \
  --overwrite_output_dir \
  --learning_rate 1e-5 \
  --fp16 \
  --num_train_epochs 2 \
  --per_device_train_batch_size 1 \
  --dataloader_drop_last True \
  --dataloader_num_workers 0 \
  --warmup_ratio 0.1 \
  --gradient_checkpointing \
  --deepspeed ds_stage0.json \
  --logging_steps 1 \
  --save_steps 1000 \
  --negatives_cross_device \
  --temperature 0.02 \
  --sentence_pooling_method cls \
  --normalize_embeddings True \
  --kd_loss_type m3_kd_loss \
  --unified_finetuning True \
  --use_self_distill True \
  --fix_encoder False \
  --self_distill_start_step 0
```

Notes for bge-m3:

- `--knowledge_distillation True` requires valid score arrays. Run the validator with `--knowledge-distillation`.
- With `same_dataset_within_batch`, the collator expects `per_device_train_batch_size 1` and no dataloader multiprocessing in the source comments. Keep data grouped by compatible task type and prompt.
- Route final benchmark or retrieval-quality checks to sibling `evaluation` after training.

Decoder-only embedder with LoRA:

```bash
torchrun --nproc_per_node 2 \
  -m FlagEmbedding.finetune.embedder.decoder_only.base \
  --model_name_or_path BAAI/bge-multilingual-gemma2 \
  --cache_dir ./cache/model \
  --use_lora True \
  --lora_rank 32 \
  --lora_alpha 64 \
  --target_modules q_proj k_proj v_proj o_proj gate_proj down_proj up_proj \
  --additional_special_tokens "<instruct>" "<query>" \
  --save_merged_lora_model True \
  --train_data data/retrieval data/sts.jsonl \
  --cache_path ./cache/data \
  --train_group_size 8 \
  --query_max_len 512 \
  --passage_max_len 512 \
  --pad_to_multiple_of 8 \
  --query_instruction_for_retrieval "Given a query, retrieve passages that are relevant to the query." \
  --query_instruction_format "<instruct>{}\n<query>{}" \
  --knowledge_distillation True \
  --same_dataset_within_batch True \
  --small_threshold 0 \
  --drop_threshold 0 \
  --output_dir outputs/decoder-embedder-lora \
  --overwrite_output_dir \
  --learning_rate 1e-4 \
  --fp16 \
  --num_train_epochs 1 \
  --per_device_train_batch_size 1 \
  --dataloader_drop_last True \
  --dataloader_num_workers 0 \
  --warmup_ratio 0.1 \
  --gradient_checkpointing \
  --deepspeed ds_stage1.json \
  --logging_steps 1 \
  --save_steps 1000 \
  --negatives_cross_device \
  --temperature 0.02 \
  --sentence_pooling_method last_token \
  --normalize_embeddings True \
  --kd_loss_type m3_kd_loss
```

Add `--use_flash_attn True` only after flash-attn imports successfully with the installed PyTorch/CUDA stack.

Decoder-only ICL embedder:

```bash
torchrun --nproc_per_node 2 \
  -m FlagEmbedding.finetune.embedder.decoder_only.icl \
  --model_name_or_path BAAI/bge-en-icl \
  --cache_dir ./cache/model \
  --use_lora True \
  --lora_rank 32 \
  --lora_alpha 64 \
  --target_modules q_proj k_proj v_proj o_proj gate_proj down_proj up_proj \
  --additional_special_tokens "<instruct>" "<query>" "<response>" \
  --save_merged_lora_model True \
  --train_data data/retrieval data/classification-no_in_batch_neg \
  --cache_path ./cache/data \
  --train_group_size 8 \
  --query_max_len 2048 \
  --passage_max_len 512 \
  --pad_to_multiple_of 8 \
  --query_instruction_for_retrieval "Given a query, retrieve passages that are relevant to the query." \
  --query_instruction_format "<instruct>{}\n<query>{}" \
  --knowledge_distillation True \
  --same_dataset_within_batch True \
  --small_threshold 0 \
  --drop_threshold 0 \
  --example_query_max_len 256 \
  --example_passage_max_len 256 \
  --retrieval_use_examples True \
  --icl_suffix_str "\n<response>" \
  --output_dir outputs/icl-embedder \
  --overwrite_output_dir \
  --learning_rate 1e-4 \
  --fp16 \
  --num_train_epochs 1 \
  --per_device_train_batch_size 1 \
  --dataloader_drop_last True \
  --dataloader_num_workers 0 \
  --warmup_ratio 0.1 \
  --gradient_checkpointing \
  --deepspeed ds_stage1.json \
  --logging_steps 1 \
  --save_steps 1000 \
  --negatives_cross_device \
  --temperature 0.02 \
  --sentence_pooling_method last_token \
  --normalize_embeddings True \
  --kd_loss_type kl_div
```

Encoder-only reranker:

```bash
torchrun --nproc_per_node 2 \
  -m FlagEmbedding.finetune.reranker.encoder_only.base \
  --model_name_or_path BAAI/bge-reranker-base \
  --cache_dir ./cache/model \
  --train_data data/reranker.scored.jsonl \
  --cache_path ./cache/data \
  --train_group_size 8 \
  --query_max_len 256 \
  --passage_max_len 256 \
  --pad_to_multiple_of 8 \
  --knowledge_distillation True \
  --output_dir outputs/reranker-base \
  --overwrite_output_dir \
  --learning_rate 6e-5 \
  --fp16 \
  --num_train_epochs 2 \
  --per_device_train_batch_size 2 \
  --gradient_accumulation_steps 1 \
  --dataloader_drop_last True \
  --warmup_ratio 0.1 \
  --gradient_checkpointing \
  --weight_decay 0.01 \
  --deepspeed ds_stage0.json \
  --logging_steps 1 \
  --save_steps 1000
```

Decoder-only reranker:

```bash
torchrun --nproc_per_node 2 \
  -m FlagEmbedding.finetune.reranker.decoder_only.base \
  --model_name_or_path BAAI/bge-reranker-v2-gemma \
  --cache_dir ./cache/model \
  --use_lora True \
  --lora_rank 32 \
  --lora_alpha 64 \
  --target_modules q_proj k_proj v_proj o_proj \
  --save_merged_lora_model True \
  --model_type decoder \
  --train_data data/reranker-prompt.scored.jsonl \
  --cache_path ./cache/data \
  --train_group_size 8 \
  --query_max_len 512 \
  --passage_max_len 512 \
  --pad_to_multiple_of 8 \
  --knowledge_distillation True \
  --query_instruction_for_rerank "A: " \
  --query_instruction_format "{}{}" \
  --passage_instruction_for_rerank "B: " \
  --passage_instruction_format "{}{}" \
  --output_dir outputs/reranker-decoder-lora \
  --overwrite_output_dir \
  --learning_rate 2e-4 \
  --bf16 \
  --num_train_epochs 1 \
  --per_device_train_batch_size 2 \
  --gradient_accumulation_steps 1 \
  --dataloader_drop_last True \
  --warmup_ratio 0.1 \
  --gradient_checkpointing \
  --weight_decay 0.01 \
  --deepspeed ds_stage0.json \
  --logging_steps 1 \
  --save_steps 1000
```

Layerwise decoder-only reranker:

```bash
torchrun --nproc_per_node 2 \
  -m FlagEmbedding.finetune.reranker.decoder_only.layerwise \
  --model_name_or_path BAAI/bge-reranker-v2-minicpm-layerwise \
  --cache_dir ./cache/model \
  --use_lora True \
  --lora_rank 32 \
  --lora_alpha 64 \
  --target_modules q_proj k_proj v_proj o_proj \
  --save_merged_lora_model True \
  --model_type from_finetuned_model \
  --start_layer 8 \
  --head_multi True \
  --head_type simple \
  --trust_remote_code True \
  --train_data data/reranker-prompt.scored.jsonl \
  --cache_path ./cache/data \
  --train_group_size 8 \
  --query_max_len 512 \
  --passage_max_len 512 \
  --pad_to_multiple_of 8 \
  --knowledge_distillation True \
  --query_instruction_for_rerank "A: " \
  --query_instruction_format "{}{}" \
  --passage_instruction_for_rerank "B: " \
  --passage_instruction_format "{}{}" \
  --output_dir outputs/reranker-layerwise \
  --overwrite_output_dir \
  --learning_rate 2e-4 \
  --bf16 \
  --num_train_epochs 1 \
  --per_device_train_batch_size 2 \
  --gradient_accumulation_steps 1 \
  --dataloader_drop_last True \
  --warmup_ratio 0.1 \
  --gradient_checkpointing \
  --weight_decay 0.01 \
  --deepspeed ds_stage0.json \
  --logging_steps 1 \
  --save_steps 1000
```

The layerwise source example repeated `--model_type`; use one value. For the layerwise module, `from_raw_model` or `from_finetuned_model` is the model-type context expected by its arguments.

## Command Safety Checklist

- Run the validator against every `train_data` file. For KD, include `--knowledge-distillation`.
- Confirm `torchrun` sees the intended number of devices and set `--nproc_per_node` accordingly.
- Use separate output directories per experiment. Keep `--overwrite_output_dir` only when overwrite is intentional.
- Keep cache paths writable and large enough for model and dataset caches.
- Omit `--use_flash_attn True` until flash-attn import and CUDA compatibility are proven.
- For same-dataset batching, use one sample per device at the outer Trainer batch level unless you have verified a different setting.
- After training, route evaluation and benchmark decisions to sibling `evaluation`.
