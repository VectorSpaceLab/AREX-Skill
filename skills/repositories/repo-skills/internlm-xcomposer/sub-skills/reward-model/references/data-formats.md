# Reward Preference Data Formats

IXC-2.5-Reward training consumes preference pairs: a chosen answer in `conversations_a` and a rejected answer in `conversations_b`. The source loader is `InternLM-XComposer-2.5-Reward/training/data_mix.py`; this reference preserves its schema and the additional guidance from `training/README.md`.

## File-level shape

A reward training JSON file must be a JSON list. Each element is one preference example.

Plain text example keys:

```json
{
  "id": 0,
  "conversations_a": [
    {"from": "human", "value": "Question"},
    {"from": "bot", "value": "Chosen answer"}
  ],
  "conversations_b": [
    {"from": "human", "value": "Question"},
    {"from": "bot", "value": "Rejected answer"}
  ]
}
```

Image-text example keys add `image`:

```json
{
  "id": "receipt-001",
  "conversations_a": [
    {"from": "human", "value": "Parse receipt to JSON."},
    {"from": "bot", "value": "{\"items\": [...]}"}
  ],
  "conversations_b": [
    {"from": "human", "value": "Parse receipt to JSON."},
    {"from": "bot", "value": "I need an image before I can answer."}
  ],
  "image": "/data/receipts/receipt-001.png"
}
```

Extra metadata keys such as `turn`, `language`, `model_a`, or `model_b` are tolerated by the source example and can be preserved for audit, but the trainer only consumes the required conversation and image fields.

## Conversation rules

Each `conversations_a` or `conversations_b` value must be a non-empty list of messages with `from` and `value` string keys.

The source `conv2text` role mapping is:

| `from` value | Rendered role |
| --- | --- |
| `system` | system |
| `human` or `user` | user |
| anything else, including `bot` or `assistant` | assistant |

Recommended preference-pair practice:

- Keep user/system turns identical between `conversations_a` and `conversations_b` so the pair compares answer quality for the same prompt.
- End both conversations with the assistant/bot response being judged.
- Avoid leaking chat template tokens such as `<|im_start|>` or `<|im_end|>` into responses.
- Keep final responses non-empty. The training code filters examples whose final chosen or rejected response is empty, only whitespace, contains those chat-template tokens, or is a very long response with extremely long unbroken tokens.

## Image field rules

`image` is optional for text-only preference data. When present, it must be either:

- a string path for one image or video; or
- a list of string paths for multiple images.

Single image preference examples do not require `<ImageHere>` placeholders. Multi-image examples should use ordered placeholders in the human instruction, for example:

```json
{"from": "human", "value": "Image1 <ImageHere>; Image2 <ImageHere>; Which answer is more grounded?"}
```

Path caveat: the source loader calls `Image.open(image_path)` on the raw string. Relative image paths are resolved by the Python process current working directory, not by the JSON file directory. Use absolute paths in production manifests, or run from a working directory where the JSON image paths resolve.

## `data.txt` manifest semantics

The source training scripts pass `--data_path data.txt --given_num True`. A manifest line has:

```text
<json path> <sample number in thousands>
```

Example:

```text
./data/example.json 1
```

With `--given_num True`, the second field is multiplied by 1000, so `1` means sample 1,000 examples per epoch from that JSON file. The loader samples down if the file is larger or upsamples with replacement if it is smaller.

If `--given_num False`, the optional second field is treated as a ratio against the JSON file length instead. For example, `0.5` means sample half of the examples, while `2` means upsample to twice the file length.

## Validation helper

Use the bundled stdlib-only validator before training:

```bash
# Validate a JSON list schema only.
python scripts/validate_reward_data.py /data/preferences.json

# Validate a source-style manifest and parse the count as thousands.
python scripts/validate_reward_data.py /data/data.txt --given-num

# Also check image paths as the source loader would resolve them from cwd.
python scripts/validate_reward_data.py /data/data.txt --given-num --check-images --image-base cwd

# For tiny fixtures whose image paths live beside the JSON file.
python scripts/validate_reward_data.py fixtures/preference_fixture.json --check-images --image-base json
```

The helper never imports PIL, torch, or the original repo. It checks JSON shape, message keys, final-response filter rules, image value types, optional image path existence, multi-image placeholder counts, and manifest sample-count parsing.

## Common schema mistakes

| Mistake | Why it matters | Fix |
| --- | --- | --- |
| Passing API-style `role`/`content` messages to training | The training loader expects `from`/`value`. | Convert messages to `from`/`value`; reserve `role`/`content` for inference APIs. |
| Swapping chosen/rejected | `conversations_a` is chosen and `conversations_b` is rejected. | Verify source labels before training. |
| Multi-image list without placeholders | The model cannot reliably align image order and text. | Add ordered `Image1 <ImageHere>; Image2 <ImageHere>; ...` text in the user prompt. |
| Relative image paths valid only from the JSON directory | Source loader resolves from the process cwd. | Use absolute paths or set the training cwd to match the image paths. |
| Empty or templated final responses | Source `filter_data` silently drops those examples. | Run the validator and clean failed rows before training. |
