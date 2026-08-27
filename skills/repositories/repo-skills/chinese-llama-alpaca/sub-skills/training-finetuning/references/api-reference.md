# Training Script API Reference

This reference summarizes the public dataclasses, helper functions, and output conventions in the bundled training scripts. For command planning, keep option names exactly as shown.

## Shared Model Arguments

Both [`scripts/run_clm_pt_with_peft.py`](../scripts/run_clm_pt_with_peft.py) and [`scripts/run_clm_sft_with_peft.py`](../scripts/run_clm_sft_with_peft.py) parse `ModelArguments` with `HfArgumentParser`.

| Option | PT | SFT | Default | Meaning |
| --- | --- | --- | --- | --- |
| `--model_name_or_path` | yes | yes | `None` | Model checkpoint/path/model id for weight initialization. |
| `--tokenizer_name_or_path` | yes | yes | `None` | Tokenizer path/model id loaded as `LlamaTokenizer`. |
| `--model_type` | yes | no | `None` | PT-only scratch model type. Not used for normal LoRA continuation. |
| `--config_overrides` | yes | yes | `None` | Scratch config overrides; incompatible with `--config_name` or `--model_name_or_path`. |
| `--config_name` | yes | yes | `None` | Config path/id when different from model. |
| `--tokenizer_name` | yes | yes | `None` | Alternative tokenizer name loaded with `AutoTokenizer`. |
| `--cache_dir` | yes | yes | `None` | Cache for model/config/tokenizer downloads. |
| `--use_fast_tokenizer` | yes | yes | `True` | Use fast tokenizer when available. |
| `--model_revision` | yes | yes | `main` | Branch/tag/commit for model assets. |
| `--use_auth_token` | yes | yes | `False` | Use logged-in HF token for private assets. |
| `--torch_dtype` | yes | yes | `None` | One of `auto`, `bfloat16`, `float16`, `float32`. |

## PT DataTrainingArguments

[`scripts/run_clm_pt_with_peft.py`](../scripts/run_clm_pt_with_peft.py) reads raw `.txt` files from `--dataset_dir`.

| Option | Default | Meaning |
| --- | --- | --- |
| `--dataset_dir` | `None` | Directory scanned for `*.txt`. |
| `--dataset_config_name` | `None` | Datasets configuration name; present but not used by the local text-file path. |
| `--train_file` | `None` | Present from the base CLM example; not used by the directory scanner. |
| `--validation_file` | `None` | Present from the base CLM example; not used by the directory scanner. |
| `--max_train_samples` | `None` | Optional truncation after train split. |
| `--max_eval_samples` | `None` | Optional truncation after eval split. |
| `--streaming` | `False` | Requires `datasets>=2.0.0`; the directory cache path still dominates this script. |
| `--block_size` | `None` | CLM chunk length; if `None`, derived from tokenizer max length and capped at 1024 when necessary. |
| `--overwrite_cache` | `False` | Parsed, but the script primarily refreshes by cache path; use a new `--data_cache_dir` or remove stale caches. |
| `--validation_split_percentage` | `0.05` | Fraction reserved for test/eval split. |
| `--preprocessing_num_workers` | `None` | Datasets map worker count. |
| `--keep_linebreaks` | `True` | Text loader linebreak behavior. |
| `--data_cache_dir` | `./` | Root for filename-derived processed caches. |

## SFT DataTrainingArguments

[`scripts/run_clm_sft_with_peft.py`](../scripts/run_clm_sft_with_peft.py) reads instruction `.json` files from `--dataset_dir`.

| Option | Default | Meaning |
| --- | --- | --- |
| `--dataset_dir` | `None` | Directory scanned for `*.json`. |
| `--train_file` | `None` | Present but not used by the directory scanner. |
| `--validation_file` | `None` | JSON file used only when `--do_eval` is set. |
| `--overwrite_cache` | `False` | Parsed; refresh by removing filename-derived SFT cache directories. |
| `--validation_split_percentage` | `0.05` | Parsed; the SFT script uses explicit `--validation_file` for eval. |
| `--preprocessing_num_workers` | `None` | Worker count for SFT tokenization. |
| `--keep_linebreaks` | `True` | Parsed compatibility field. |
| `--data_cache_dir` | `None` | Parsed; current SFT call passes `None` to `build_instruction_dataset`. |
| `--max_seq_length` | `512` | Prompt+answer maximum token length. |

## PEFT and Training Arguments

Both scripts extend Hugging Face `TrainingArguments`, so standard options such as `--deepspeed`, `--output_dir`, `--do_train`, `--do_eval`, `--per_device_train_batch_size`, `--gradient_accumulation_steps`, `--learning_rate`, `--fp16`, `--save_steps`, `--resume_from_checkpoint`, and `--overwrite_output_dir` are also accepted.

Custom PEFT fields:

| Option | PT default | SFT default | Meaning |
| --- | --- | --- | --- |
| `--trainable` | `q_proj,v_proj` | `q_proj,v_proj` | Comma-separated LoRA target module names. Shell templates expand this to attention+MLP projections. |
| `--lora_rank` | `8` | `8` | LoRA rank `r`. |
| `--lora_dropout` | `0.1` | `0.1` | LoRA dropout in Python defaults; templates use `0.05`. |
| `--lora_alpha` | `32.0` | `32.0` | LoRA alpha scaling. |
| `--modules_to_save` | `None` | `None` | Comma-separated non-LoRA modules to store; templates use `embed_tokens,lm_head`. |
| `--debug_mode` | `False` | no | PT-only: limits PT file list to the first file. |
| `--peft_path` | `None` | `None` | Existing PEFT adapter loaded with `PeftModel.from_pretrained`. |
| `--force_resize_embeddings` | no | `False` | Parsed by SFT. In this script version, embeddings are resized automatically when tokenizer length differs from model embedding size; the flag is available for compatibility but is not the controlling branch. |

## LoRAConfig Construction

When `--peft_path` is absent, both scripts build:

```text
LoraConfig(
  task_type=TaskType.CAUSAL_LM,
  target_modules=<--trainable split by comma>,
  inference_mode=False,
  r=<--lora_rank>,
  lora_alpha=<--lora_alpha>,
  lora_dropout=<--lora_dropout>,
  modules_to_save=<--modules_to_save split by comma or None>,
)
```

Then `get_peft_model` wraps the model and the scripts replace `model.state_dict` with `get_peft_model_state_dict(...)` so saved checkpoints contain PEFT state rather than full base model weights.

## Tokenizer and Embedding Checks

- PT checks output embedding vocab size and tokenizer length. Valid combinations are `32000/32000`, `32000/49953`, `49953/49953`, and `49954/49954`; all other combinations raise a `ValueError`.
- PT always calls `model.resize_token_embeddings(len(tokenizer))` after the compatibility check.
- SFT requires tokenizer length `49954`; otherwise it raises `ValueError: The vocab size of the tokenizer must be 49954`.
- SFT adds `[PAD]` if `tokenizer.pad_token is None` and then resizes embeddings when `len(tokenizer)` differs from the model input embedding size.
- Both scripts rely on tokenizer EOS. SFT appends `tokenizer.eos_token` to each answer in `build_instruction_dataset`.

## `build_instruction_dataset` and Collator

[`scripts/build_dataset.py`](../scripts/build_dataset.py) exposes:

```text
build_instruction_dataset(data_path, tokenizer, max_seq_length, data_cache_dir=None, preprocessing_num_workers=None)
DataCollatorForSupervisedDataset(tokenizer)
```

Important behavior:

- `data_path` may be a string or list of JSON files.
- Cache path defaults to each file's directory plus the filename stem.
- The prompt source is masked with `IGNORE_INDEX=-100`; target answer tokens are supervised.
- The collator pads `input_ids` with `tokenizer.pad_token_id`, pads labels with `-100`, and creates `attention_mask=input_ids.ne(tokenizer.pad_token_id)`.

## `SavePeftModelCallback`

Both scripts register a callback that saves adapter and tokenizer files on `Trainer` save and at train end.

| Script | Periodic save location | Final save location |
| --- | --- | --- |
| PT | checkpoint folder plus nested `pt_lora_model` | `OUTPUT_DIR/pt_lora_model` |
| SFT | checkpoint folder plus nested `sft_lora_model` | `OUTPUT_DIR/sft_lora_model` |

Because this callback saves PEFT adapters/tokenizers, do not expect a full original LLaMA model in the training output. Merge or load adapters using the model-reconstruction or inference guidance after training.
