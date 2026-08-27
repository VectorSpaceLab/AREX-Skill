# MOSS fine-tuning and data summary

## Purpose

Read this for the root-level summary of MOSS SFT data and fine-tuning planning.
For detailed schema validation and command planning, route to
[../sub-skills/fine-tuning-data/SKILL.md](../sub-skills/fine-tuning-data/SKILL.md).

## Data surfaces

MOSS SFT data has two major shapes:

| Surface | Content | Operational note |
| --- | --- | --- |
| No-plugin conversations | Multi-turn helpful, harmless, writing, code, role-play, brainstorming, complex-instruction, continue/switching examples. | `Inner Thoughts`, `Commands`, and `Tool Responses` are present but usually `None`. |
| Plugin conversations | Tool-use transcripts for web search, calculator, equation solver, text-to-image, and mixed workflows. | Turns include inner thoughts, tool commands, tool results, and MOSS responses. |
| User-prompt seed JSONL | Lines with a `user_prompt` field. | Seed prompts are not directly accepted by the SFT loader; convert to full conversation records. |

The public documentation states honesty data was removed because it contained
private information.

## Required record fields

Training conversations include:

- `conversation_id`
- `meta_instruction`
- `num_turns`
- `chat.turn_N.Human`
- `chat.turn_N.Inner Thoughts`
- `chat.turn_N.Commands`
- `chat.turn_N.Tool Responses`
- `chat.turn_N.MOSS`

Each turn field should preserve MOSS markers such as `<|Human|>:`, `<eoh>`,
`<|MOSS|>:`, and `<eom>`. Plugin records also use `<|Inner Thoughts|>:`,
`<|Commands|>:`, `<|Results|>:`, and their end markers.

## Safe validation and command planning

Schema validation:

```bash
python sub-skills/fine-tuning-data/scripts/validate_sft_json.py train.jsonl --sample-limit 100 --json
python sub-skills/fine-tuning-data/scripts/validate_sft_json.py plugin_sample.json --expect-plugin --json
```

Training command planning:

```bash
python sub-skills/fine-tuning-data/scripts/plan_finetune_command.py \
  --model-name-or-path OpenMOSS-Team/moss-moon-003-base \
  --data-dir /path/to/sft-data \
  --output-dir /path/to/output \
  --log-dir /path/to/logs \
  --write-config /path/to/moss_sft_accelerate.yaml \
  --json
```

The planner may write an Accelerate/DeepSpeed YAML file when requested. It does
not run tokenizer preprocessing, load a model, or train.

## Full training cautions

- Full SFT is a distributed GPU job, not a smoke test.
- It requires a base checkpoint, tokenizer, training and validation data,
  adequate GPU memory, output/log directories, and compatible Accelerate plus
  DeepSpeed setup.
- Tokenizer-based length behavior requires the real MOSS tokenizer; schema
  validation alone cannot prove that records fit 2048 tokens.
- Tool-result inner payload spans are intentionally masked with `-100` labels by
  the loader; preserve tool markers exactly.
