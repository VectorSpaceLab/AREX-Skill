# Qwen-VL finetuning data format

The official finetuning script expects a JSON file containing a list of samples.
Each sample is a dictionary with at least:

- `id`: a unique sample identifier.
- `conversations`: a list of conversation turns.

Each turn has:

- `from`: either `user` or `assistant`.
- `value`: the text content.

## Minimal example

```json
[
  {
    "id": "identity_0",
    "conversations": [
      {"from": "user", "value": "你好"},
      {"from": "assistant", "value": "我是Qwen-VL，一个支持视觉输入的大模型。"}
    ]
  }
]
```

## Multimodal example

```json
[
  {
    "id": "identity_1",
    "conversations": [
      {
        "from": "user",
        "value": "Picture 1: <img>image.jpg</img>\n图中的狗是什么品种？"
      },
      {
        "from": "assistant",
        "value": "图中是一只拉布拉多犬。"
      }
    ]
  }
]
```

## Grounding example

```json
[
  {
    "id": "identity_2",
    "conversations": [
      {
        "from": "user",
        "value": "Picture 1: <img>image.jpg</img>\n请给我框出左边的人"
      },
      {
        "from": "assistant",
        "value": "<ref>左边的人</ref><box>(123,456),(234,789)</box>"
      }
    ]
  }
]
```

## Important constraints

- Preserve the `Picture n:` prefix exactly when multiple images appear in one conversation turn.
- Use normalized box coordinates in `[0, 1000)`.
- Keep `<ref>...</ref>` paired with `<box>...</box>` for grounding labels.
- The finetuning code treats the conversation as alternating user/assistant turns; malformed alternation should be rejected by the validator.
- For LoRA on the base model, the docs note that embedding and output layers may need to be trainable because the base model does not already understand the chat special tokens.
- For Q-LoRA, the source docs warn that the Int4 chat model is the safer choice and that BF16 is not the intended precision.

## When to validate

Run the bundled validator before a launch whenever the data is new, hand-edited, or derived from another dataset:

```bash
python scripts/validate_finetune_data.py --data path/to/data.json
```

The validator checks the list shape, required keys, turn alternation, and basic multimodal markup expectations.
