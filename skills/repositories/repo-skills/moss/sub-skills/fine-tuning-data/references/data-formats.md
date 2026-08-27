# MOSS SFT data formats

## Purpose

Read this before validating or preparing MOSS supervised fine-tuning data. It
summarizes the record structure used by `SFTDataset` and the released sample
conversation files.

## Dataset categories

The public SFT data documentation describes no-plugin categories:

- Brainstorming
- Complex Instruction
- Code
- Role Playing
- Writing
- Harmless
- Others (`Continue` and `Switching`)

Honesty data was removed because it contained private information. Plugin data
contains conversations using web search, calculator, equation solver,
text-to-image, and mixed tools.

## Conversation record schema

A conversation JSON object has:

```json
{
  "conversation_id": "1",
  "meta_instruction": "You are an AI assistant whose name is MOSS...",
  "num_turns": 2,
  "chat": {
    "turn_1": {
      "Human": "<|Human|>: ...<eoh>\n",
      "Inner Thoughts": "<|Inner Thoughts|>: None<eot>\n",
      "Commands": "<|Commands|>: None<eoc>\n",
      "Tool Responses": "<|Results|>: None<eor>\n",
      "MOSS": "<|MOSS|>: ...<eom>\n"
    }
  },
  "category": "code"
}
```

`conversation_id` may be a string or number in samples. `num_turns` may also be
string-like; the training loader coerces it with `int()`.

## Required turn markers

| Turn field | Required start | Required end | Training note |
| --- | --- | --- | --- |
| `Human` | `<|Human|>:` | `<eoh>` | User input. |
| `Inner Thoughts` | `<|Inner Thoughts|>:` | `<eot>` | `None` for no-plugin data. |
| `Commands` | `<|Commands|>:` | `<eoc>` | `None` or tool call. |
| `Tool Responses` | `<|Results|>:` | `<eor>` | Tool output; payload spans are masked for loss. |
| `MOSS` | `<|MOSS|>:` | `<eom>` | Assistant target text. |

## Plugin commands

Observed plugin command families include:

- `Search("query")`
- `Calculate("expression")`
- `Solve("equation")`
- `Text2Image("description")`

Plugin tool responses appear between `<|Results|>:` and `<eor>`. The loader masks
the inner content of tool responses with `-100` labels while keeping surrounding
format tokens trainable.

## Loader cache files

`SFTDataset(data_dir, tokenizer, data_type="train")` looks for cached tensors:

- `train_data` and `train_no_loss_spans`
- `val_data` and `val_no_loss_spans`

If the cache files do not exist, it reads `train.jsonl` or `val.jsonl`, encodes
the meta instruction and turns, skips samples with no usable turns, drops turns
that would push a sample over 2048 tokens, and writes cache files with
`torch.save`.

## User prompt files

The released user-prompt seed samples use JSONL lines such as:

```json
{"user_prompt": "Write a function in Python that takes an integer as input and returns the factorial of the number."}
```

These are seed prompts, not direct `SFTDataset` training records. Convert them
into full conversation records before running tokenizer-based SFT preprocessing
or the bundled fine-tuning command planner.

## Safe validation

Use the bundled validator to check structure and markers before tokenization:

```bash
python sub-skills/fine-tuning-data/scripts/validate_sft_json.py sample.json --json
python sub-skills/fine-tuning-data/scripts/validate_sft_json.py plugin.json --expect-plugin
```

The validator intentionally does not enforce token length; use the real tokenizer
when you need exact 2048-token behavior.
