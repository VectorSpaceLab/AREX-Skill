# Arguments Reference

This reference summarizes Tevatron training arguments that are easy to confuse across dense, distillation, sparse, DeepSpeed, GradCache, LoRA, and JAX routes.

## Installed Package Baseline

The public package metadata identifies `tevatron` version `0.0.1` and only installs these core dependencies:

- `transformers>=4.10.0`
- `datasets>=1.1.3`

Training commands often also need optional packages such as `torch`, `peft`, `deepspeed`, `grad_cache`, `flash-attn`, `jax`, `flax`, `optax`, `magix`, `xformers`, or sparse retrieval evaluation packages. Do not assume they are present merely because `tevatron` imports.

## ModelArguments

| Argument | Default | Use |
| --- | --- | --- |
| `--model_name_or_path` | required | Hugging Face model id or local pretrained directory. |
| `--config_name` | `None` | Override config path/name when different from model. |
| `--tokenizer_name` | `None` | Override tokenizer path/name when different from model. |
| `--cache_dir` | `None` | Model/dataset cache used by Transformers/Datasets. |
| `--pooling` | `cls` | Dense pooling method; use `eos`/`last` for many decoder-only retrievers. |
| `--normalize` | `False` | L2-normalize representations after pooling. |
| `--temperature` | `1.0` | Contrastive loss temperature. |
| `--lora` | `False` | Enable PEFT LoRA construction. |
| `--lora_name_or_path` | `None` | Load an existing LoRA adapter. |
| `--lora_r` | `16` | LoRA rank for new adapters. |
| `--lora_alpha` | `64` | LoRA alpha for new adapters. |
| `--lora_dropout` | `0.1` | LoRA dropout for new adapters. |
| `--lora_target_modules` | `q_proj,k_proj,v_proj,o_proj,down_proj,up_proj,gate_proj` | Comma-separated modules to wrap; must match the backbone. |
| `--dtype` | `float32` | JAX training dtype; choose from `float32`, `float16`, `bfloat16`. |
| `--attn_implementation` | `flash_attention_2` | Transformers attention backend, such as `eager`, `sdpa`, or `flash_attention_2`. |
| `--untie_encoder` | `False` | JAX dual-encoder route with separate query and passage params. |

## DataArguments

| Argument | Default | Use |
| --- | --- | --- |
| `--dataset_name` | `json` | Hugging Face dataset name or loader. Set `json` for local JSON/JSONL. |
| `--dataset_config` | `None` | Dataset config/subset. |
| `--dataset_path` | `None` | Local train file(s), often JSONL. |
| `--dataset_split` | `train` | Dataset split to load. |
| `--dataset_cache_dir` | `None` | Dataset cache. |
| `--corpus_name` | `None` | Hugging Face corpus dataset for ID-to-corpus training. |
| `--corpus_config` | `None` | Corpus config/subset. |
| `--corpus_path` | `None` | Local corpus file for ID-to-corpus training. |
| `--corpus_split` | `train` | Corpus split. |
| `--train_yaml` | `None` | YAML for multiple training datasets; present in args but not used by the main dense driver path. |
| `--assets_path` | `None` | Asset root for multimodal corpora; multimodal training is outside this sub-skill. |
| `--train_group_size` | `8` | Total passages per query: one positive plus negatives. |
| `--positive_passage_no_shuffle` | `False` | Always choose first positive. |
| `--negative_passage_no_shuffle` | `False` | Use first negatives instead of epoch-shuffled negatives. |
| `--query_max_len` | `32` | Query token length. |
| `--passage_max_len` | `128` | Passage token length. |
| `--query_prefix` | empty | Text prepended to every query before tokenization. |
| `--passage_prefix` | empty | Text prepended to every passage before tokenization. |
| `--passage_field_separator` | space | Separator between passage title and body when present. |
| `--append_eos_token` | `False` | Append EOS after tokenization; useful for decoder-only retrievers. |
| `--pad_to_multiple_of` | `16` | Padding multiple for tensor-core-friendly batches. |
| `--num_proc` | `1` | Datasets tokenization/loading process count. |
| `--padding_side` | `right` | Tokenizer padding side; accepted values are interpreted as right vs left. |

The `DataArguments` class also contains encoding and multimodal switches. Keep those out of pure text training unless the user is intentionally preparing an encode or multimodal workflow.

## TevatronTrainingArguments Additions

Tevatron extends Hugging Face `TrainingArguments` with:

| Argument | Default | Use |
| --- | --- | --- |
| `--warmup_ratio` | `0.1` | Linear warmup ratio unless explicit warmup steps override it through Hugging Face args. |
| `--grad_cache` | `False` | Switch dense PyTorch training to `GradCacheTrainer`; also used by JAX routes. |
| `--gc_q_chunk_size` | `4` | GradCache query chunk size. |
| `--gc_p_chunk_size` | `32` | GradCache passage chunk size. |
| `--distil_temperature` | `0.02` | Teacher-distillation KL temperature. |

All standard Hugging Face `TrainingArguments` still apply, including `--do_train`, `--output_dir`, `--overwrite_output_dir`, `--per_device_train_batch_size`, `--gradient_accumulation_steps`, `--gradient_checkpointing`, `--learning_rate`, `--num_train_epochs`, `--logging_steps`, `--save_steps`, `--fp16`, `--bf16`, `--deepspeed`, and distributed-launch settings.

## Dense Driver Argument Groups

Minimum viable dense command:

- Required model: `--model_name_or_path`.
- Required training intent: `--do_train`.
- Required output: `--output_dir`.
- Required data: `--dataset_name` plus optional `--dataset_path`, or the defaults for local JSON when the path is supplied.
- Strongly recommended: `--train_group_size`, `--query_max_len`, `--passage_max_len`, batch size, learning rate, epochs, precision, and logging/save intervals.

Model-shape choices:

- BERT-like dense models: default `--pooling cls`, no `--append_eos_token` usually needed.
- Mean-pooling embedding models: `--pooling mean --normalize` is common.
- Decoder-only LLM retrievers: `--pooling eos --append_eos_token --normalize`, usually with LoRA, BF16/FP16, gradient checkpointing, and DeepSpeed or GradCache.

## Distillation-Specific Arguments

The distillation driver uses the same shared dataclasses but changes dataset, collator, and trainer behavior:

- Driver: `tevatron.retriever.driver.train_distil`.
- Required score field: every selected positive/negative passage or corpus document needs `score`.
- Teacher temperature: `--distil_temperature`; default `0.02`.
- Student similarity temperature: `--temperature`; default `1.0`, examples often use `0.01`.
- Long query/passage lengths such as `350` appear in E5 teacher-distillation examples, so memory planning matters.

## Sparse Arguments

SPLADE adds two driver-local arguments:

| Argument | Example | Use |
| --- | --- | --- |
| `--q_flops_loss_factor` | `0.01` | Query FLOPS regularization multiplier. |
| `--p_flops_loss_factor` | `0.01` | Passage FLOPS regularization multiplier. |

SPLADE's model aggregates masked-language-model logits with `max(log(1 + relu(logits)))` over sequence positions. Use `--attn_implementation sdpa` if FlashAttention is unavailable or inappropriate.

UniCOIL evidence uses older names:

| Example name | Current shared equivalent |
| --- | --- |
| `--train_n_passages` | `--train_group_size` |
| `--q_max_len` | `--query_max_len` |
| `--p_max_len` | `--passage_max_len` |
| `--dataset_proc_num` | `--num_proc` |

Do not blindly pass old names to the current shared drivers.

## JAX and Tevax Names

HF-style JAX driver `tevatron.retriever.driver.jax_train` uses the same `ModelArguments`, `DataArguments`, and `TevatronTrainingArguments` names as dense PyTorch, including `--output_dir`, `--dataset_name`, `--per_device_train_batch_size`, `--train_group_size`, `--query_max_len`, and `--passage_max_len`.

Experimental Tevax MP drivers use `simple_parsing` dataclasses and different names:

| Tevax MP argument | Meaning |
| --- | --- |
| `--train_file` | HF dataset name or local `.jsonl` file. |
| `--checkpoint_dir` | Checkpoint output directory. |
| `--model_name` | Model id/path. |
| `--model_type` | Magix model family key, such as `mistral` or `llama` when supported. |
| `--mesh_shape` | Device mesh shape; README pattern uses `1 -1`. |
| `--batch_size` | Global batch size used by the MP training loop. |
| `--num_target_passages` | Passages per query. |
| `--max_query_length` | Query length. |
| `--max_passage_length` | Passage length. |
| `--query_num_chunks` | Tevax GradCache query chunk count. |
| `--passage_num_chunks` | Tevax GradCache passage chunk count. |
| `--fully_shard_params` | LoRA MP route sharding toggle. |

## Output Artifacts

Dense and distillation PyTorch training save:

- Model weights via the underlying encoder `save_pretrained` behavior.
- Tokenizer files in `--output_dir` on world process zero.
- Hugging Face `training_args.bin` through the trainer save path.

JAX HF-style training saves:

- One model directory for tied encoders.
- `query_encoder/` and `passage_encoder/` subdirectories when `--untie_encoder` is set.
- Tokenizer files in `--output_dir`.

Tevax MP training saves checkpoints under `--checkpoint_dir`, with LoRA-specific runs saving LoRA and optimizer items.

## Command Builder Mapping

The bundled `scripts/build_training_command.py` emits command strings only. It supports these route names:

- `dense`: main PyTorch dense driver.
- `distil`: teacher-distillation driver.
- `lora`: dense driver with LoRA-oriented defaults.
- `gradcache`: dense driver with GradCache flags.
- `deepspeed-lora`: DeepSpeed launcher plus LoRA defaults.
- `jax`: HF-style JAX driver.
- `tevax-lora`: experimental Tevax MP LoRA driver.
- `splade`: SPLADE example-driver pattern with FLOPS regularization flags.
- `unicoil`: translated UniCOIL example-driver skeleton using current shared argument names.

Use the printed command as a starting point and then adjust hardware launchers, precision, lengths, batch sizes, data paths, and any copied/adapted sparse driver code.
