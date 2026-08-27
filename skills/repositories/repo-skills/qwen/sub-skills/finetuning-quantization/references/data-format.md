# Qwen Fine-tuning Data Format

## When to read

Read this before editing a training dataset or choosing a fine-tuning script.

## Core schema

The repository documents supervised fine-tuning data as JSON containing a list of samples. Each sample has a `conversations` list, and each conversation item uses at least:

- `from`: `user` or `assistant`
- `value`: message text

A practical sample looks like:

```json
[
  {
    "id": "identity_0",
    "conversations": [
      {"from": "user", "value": "你好"},
      {"from": "assistant", "value": "我是一个语言模型，我叫通义千问。"}
    ]
  }
]
```

## Loading behavior

The historical `finetune.py`:

- Uses dataclasses for model, data, training, and LoRA arguments.
- Reads `data_path` and optional `eval_data_path` as JSON.
- Builds ChatML-style inputs with the checkpoint tokenizer.
- Masks user turns and padding with `IGNORE_TOKEN_ID`.
- Supports `lazy_preprocess` to delay formatting until item access.

## Data checks to perform before training

1. Confirm JSON parses as a list.
2. Confirm every sample has a `conversations` list.
3. Confirm turn roles are only `user` and `assistant` for the training schema.
4. Confirm the first turn is appropriate for the selected model and script.
5. Confirm the total tokenized sequence length fits the chosen `model_max_length` and hardware budget.
6. Confirm the data is compatible with the selected precision and quantization path.

## Common mistakes

- Missing `conversations` or using a flat prompt/response schema.
- Providing a chat-style dataset to a script that expects plain continuation text.
- Using a base model for a chat-style SFT recipe without understanding the special-token side effects.
- Forgetting that Q-LoRA uses an Int4 chat checkpoint and fp16.
