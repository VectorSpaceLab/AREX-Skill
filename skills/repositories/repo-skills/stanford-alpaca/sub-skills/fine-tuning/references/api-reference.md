# Fine-tuning API reference

The adapted trainer in `scripts/train_alpaca_sft.py` preserves the public logic of the repository `train.py` while inlining the JSON loader so the generated skill is self-contained. The exact prompt/schema details are owned by `dataset-and-prompts`; this reference documents how the trainer consumes already-prepared data.

## Argument parser

The trainer parses three dataclasses with `transformers.HfArgumentParser`:

```python
parser = transformers.HfArgumentParser((ModelArguments, DataArguments, TrainingArguments))
model_args, data_args, training_args = parser.parse_args_into_dataclasses()
```

### `ModelArguments`

| Field | Default | Meaning |
| --- | --- | --- |
| `model_name_or_path` | `facebook/opt-125m` | Hugging Face model/checkpoint directory or model id. Must include a compatible causal LM config and tokenizer assets. README recipes replace the default with a converted LLaMA checkpoint or `facebook/opt-6.7b`. |

### `DataArguments`

| Field | Default | Meaning |
| --- | --- | --- |
| `data_path` | `None` | Path to the Alpaca-style supervised fine-tuning JSON file. Validate schema and prompt-source expectations with `dataset-and-prompts` before using this sub-skill. |

### `TrainingArguments`

The repo subclass extends `transformers.TrainingArguments` with these direct fields:

| Field | Default | Meaning |
| --- | --- | --- |
| `cache_dir` | `None` | Optional model/tokenizer cache directory passed to `from_pretrained`. |
| `optim` | `adamw_torch` | Optimizer name used by Hugging Face Trainer. |
| `model_max_length` | `512` | Maximum sequence length; tokenizer right-pads and truncates to this length. |

The parser also exposes the standard Hugging Face `TrainingArguments` surface. The training recipes in this skill rely especially on:

| Field / CLI flag | Typical value in README recipes | Purpose |
| --- | --- | --- |
| `output_dir` / `--output_dir` | required | Directory for checkpoints, final model, and trainer state. |
| `num_train_epochs` | `3` for LLaMA-7B; `5` for LLaMA-13B | Full training epochs. |
| `per_device_train_batch_size` | `4` | Micro-batch per GPU/process. |
| `per_device_eval_batch_size` | `4` | Eval micro-batch; README disables eval but keeps the flag. |
| `gradient_accumulation_steps` | `8` on 4 GPUs | Multiplies the micro-batch to reach global batch 128. |
| `evaluation_strategy` | `no` | No eval dataset is returned by `make_supervised_data_module`. |
| `save_strategy` | `steps` | Save checkpoint periodically. |
| `save_steps` | `2000` | Checkpoint interval used in README. |
| `save_total_limit` | `1` | Keep only one checkpoint to limit storage. |
| `learning_rate` | `2e-5` or `1e-5` | Initial AdamW learning rate. |
| `weight_decay` | `0.` | README uses no weight decay. |
| `warmup_ratio` | `0.03` | Warmup ratio. |
| `lr_scheduler_type` | `cosine` in FSDP examples | Scheduler used in documented FSDP commands. |
| `logging_steps` | `1` in FSDP examples | Log interval. |
| `bf16` | `True` | Enable bfloat16 on compatible hardware. |
| `tf32` | `True` | Enable TF32 matmul on supported NVIDIA GPUs. |
| `fsdp` | `full_shard auto_wrap` or `full_shard auto_wrap offload` | FSDP sharding/offload mode. |
| `fsdp_transformer_layer_cls_to_wrap` | `LlamaDecoderLayer` or `OPTDecoderLayer` | Transformer block class for FSDP auto-wrap. |
| `deepspeed` | `scripts/default_offload_opt_param.json` | DeepSpeed config path for ZeRO-3 offload. |
| `report_to` | optional | Controls integrations such as Weights & Biases. Use this to disable unwanted reporting. |
| `resume_from_checkpoint` | optional | Resume an interrupted Trainer run from a checkpoint. |
| `no_cuda` / `use_mps_device` | optional | Device selection flags; avoid accidental CPU-only launches for full training. |

## Trainer constants

| Name | Value | Use |
| --- | --- | --- |
| `IGNORE_INDEX` | `-100` | Label value ignored by PyTorch cross-entropy; used to mask source/prompt tokens and padded label positions. |
| `DEFAULT_PAD_TOKEN` | `[PAD]` | Added if the tokenizer lacks a pad token. |
| `DEFAULT_EOS_TOKEN` | `</s>` | Added if the tokenizer lacks an EOS token. |
| `DEFAULT_BOS_TOKEN` | `<s>` | Added if the tokenizer lacks a BOS token. |
| `DEFAULT_UNK_TOKEN` | `<unk>` | Added if the tokenizer lacks an unknown token. |

## Function and class contracts

### `smart_tokenizer_and_embedding_resize(special_tokens_dict, tokenizer, model)`

Adds missing special tokens to the tokenizer and resizes the model token embeddings to the new tokenizer length. If tokens are added, the new input and output embedding rows are initialized to the mean of existing embeddings. The source docstring notes this is not optimized and may make the embedding size not divisible by 64.

Use this when a LLaMA/OPT tokenizer lacks `pad`, `eos`, `bos`, or `unk` tokens. Do not skip the resize after adding tokens; otherwise token ids can exceed embedding rows.

### `_tokenize_fn(strings, tokenizer)`

Tokenizes a sequence of strings with:

- `return_tensors="pt"`
- `padding="longest"`
- `max_length=tokenizer.model_max_length`
- `truncation=True`

Returns `input_ids`, `labels`, `input_ids_lens`, and `labels_lens`. Lengths count non-pad token ids.

### `preprocess(sources, targets, tokenizer) -> Dict`

Concatenates each source string with its target string, tokenizes full examples and source-only strings, deep-copies full-example `input_ids` into labels, then masks the source span for each label with `IGNORE_INDEX`.

Result:

```python
{
    "input_ids": list[torch.Tensor],
    "labels": list[torch.Tensor],
}
```

This is the key supervised fine-tuning behavior: loss is computed only on response/target tokens, not on prompt/source tokens.

### `SupervisedDataset(data_path, tokenizer)`

Loads the JSON dataset, formats each example with the appropriate Alpaca prompt template, appends the tokenizer EOS token to each target, calls `preprocess`, and stores `self.input_ids` and `self.labels`.

Boundary note: exact dataset keys and prompt wording belong to `dataset-and-prompts`. This class is documented here only to explain the training data consumption path.

### `DataCollatorForSupervisedDataset(tokenizer)`

Callable collator for a batch of dataset items:

- Pads `input_ids` with `tokenizer.pad_token_id`.
- Pads `labels` with `IGNORE_INDEX`.
- Builds `attention_mask = input_ids.ne(tokenizer.pad_token_id)`.

This preserves ignored labels across padding and gives Trainer the causal LM inputs expected by `AutoModelForCausalLM`.

### `make_supervised_data_module(tokenizer, data_args) -> Dict`

Creates:

```python
{
    "train_dataset": SupervisedDataset(...),
    "eval_dataset": None,
    "data_collator": DataCollatorForSupervisedDataset(...),
}
```

Because `eval_dataset` is `None`, the README commands set `--evaluation_strategy "no"`.

### `train()`

Execution order:

1. Parse model, data, and training arguments.
2. Load `AutoModelForCausalLM.from_pretrained(model_name_or_path, cache_dir=...)`.
3. Load `AutoTokenizer.from_pretrained(..., model_max_length=..., padding_side="right", use_fast=False)`.
4. Add missing special tokens and resize embeddings.
5. Build the supervised data module.
6. Construct `Trainer(model=model, tokenizer=tokenizer, args=training_args, **data_module)`.
7. Run `trainer.train()`.
8. Save trainer state and the final model to `output_dir`.
