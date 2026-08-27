# MiniMind training data formats

MiniMind uses a compact tokenizer and two core JSONL schemas for the training stages owned by this sub-skill.

## Tokenizer contract

MiniMind's main tokenizer is a custom BPE tokenizer with ByteLevel pre-tokenization and a compact vocabulary of `6400`. Keep this tokenizer for normal training: changing the vocabulary changes model weight compatibility, token-level metrics, prompt formatting, and inference behavior.

Core token facts:

| Purpose | Token | Id / setting | Notes |
|---|---:|---:|---|
| Padding and unknown | `<|endoftext|>` | `0` | Used as `pad_token` and `unk_token`. |
| Message start / BOS | `<|im_start|>` | `1` | Used as `bos_token`; datasets add it explicitly for pretraining. |
| Message end / EOS | `<|im_end|>` | `2` | Used as `eos_token`; datasets add it explicitly for pretraining. |
| Tool call block | `<tool_call>`, `</tool_call>` | added tokens | Kept as ordinary added tokens, not marked as tokenizer special tokens. |
| Tool response block | `<tool_response>`, `</tool_response>` | added tokens | Used by the chat template for `tool` role messages. |
| Thinking block | `<think>`, `</think>` | added tokens | Used for explicit or empty reasoning spans. |
| Reserved future tokens | `<|buffer1|>` ... `<|buffer9|>` | added tokens | Reserved buffer tokens; do not repurpose casually. |

Other tokenizer settings that affect training:

- `add_bos_token=false` and `add_eos_token=false`; datasets add MiniMind BOS/EOS markers where needed.
- `clean_up_tokenization_spaces=false` and `spaces_between_special_tokens=false`; avoid extra whitespace cleanup in fixture comparisons.
- `model_max_length=131072`; this is tokenizer capacity, not the same as training `max_seq_len`.
- Main training uses token lengths. Approximate compression from project evidence: Chinese text is often `1.5-1.7` characters per token; pure English can be `4-5` characters per token.

## Chat template behavior used by SFT

SFT and LoRA samples are converted through the tokenizer chat template before labels are created.

Important behavior:

1. If a system message contains `tools`, the template emits a system tool preamble and serializes tool signatures inside `<tools>...</tools>`.
2. `system`, `user`, and later non-initial `system` messages are rendered as `<|im_start|>{role}\n{content}<|im_end|>\n`.
3. Each assistant message is rendered as an assistant block with a thinking section first:
   - If `reasoning_content` is a string, it becomes the content inside `<think>...</think>`.
   - If `reasoning_content` is absent and `content` already contains `</think>`, the template extracts the thinking text from `content`.
   - Otherwise the assistant block contains an empty thinking section before the assistant content.
4. Assistant `tool_calls` are rendered as one or more `<tool_call>...</tool_call>` JSON objects after assistant content.
5. Consecutive `tool` role messages are grouped into a synthetic user block containing `<tool_response>...</tool_response>` segments.
6. With `add_generation_prompt=true`, the template opens an assistant block and either opens thinking (`open_thinking=true`) or inserts an empty thinking block.

MiniMind SFT label creation trains only assistant spans. Labels outside assistant spans are `-100`. The assistant span begins after tokenizing `<|im_start|>assistant\n` and ends at `<|im_end|>\n`.

## Pretraining JSONL schema

Each non-empty line must be a standalone JSON object with a string `text` field:

```jsonl
{"text": "如何才能摆脱拖延症？治愈拖延症并不容易，但以下建议可能有所帮助。"}
{"text": "Transformer 通过自注意力机制建模上下文关系，是现代大语言模型的重要基础结构。"}
```

Training behavior:

- The pretraining dataset reads `sample["text"]`.
- It tokenizes the text with `add_special_tokens=false` and truncates to `max_seq_len - 2`.
- It prepends `<|im_start|>` and appends `<|im_end|>`.
- It pads to `max_seq_len` with `<|endoftext|>` and sets pad labels to `-100`.

Practical guidance:

- Use `pretrain_t2t_mini.jsonl` for quick reproduction and `pretrain_t2t.jsonl` for full main-branch pretraining.
- README evidence recommends roughly `max_seq_len≈768` for the mini pretrain file and `max_seq_len≈380` for the full pretrain file; the native pretraining script default is more conservative.
- Empty, non-string, or missing `text` fields should be rejected before training.

## SFT and LoRA JSONL schema

Full SFT and LoRA use the same conversation schema. Each line is a standalone JSON object:

```jsonl
{"conversations":[{"role":"user","content":"你好"},{"role":"assistant","content":"你好！"},{"role":"user","content":"再见"},{"role":"assistant","content":"再见！"}]}
```

Message object fields:

| Field | Required | Type used by MiniMind training | Applies to | Notes |
|---|---:|---|---|---|
| `role` | yes | string | all messages | Expected roles: `system`, `user`, `assistant`, `tool`. |
| `content` | yes | string | all messages | Assistant content may be empty when `tool_calls` is present. |
| `reasoning_content` | optional | string | assistant | Preferred way to provide explicit thinking text. |
| `tools` | optional | JSON-encoded string | system | Parsed with `json.loads` before `apply_chat_template`. |
| `tool_calls` | optional | JSON-encoded string | assistant | Parsed with `json.loads`; each call should name a function and arguments. |

Tool-call example:

```jsonl
{"conversations":[{"role":"system","content":"# Tools ...","tools":"[{\"type\":\"function\",\"function\":{\"name\":\"calculate_math\",\"description\":\"Calculate an expression\",\"parameters\":{\"type\":\"object\",\"properties\":{\"expression\":{\"type\":\"string\"}},\"required\":[\"expression\"]}}}]"},{"role":"user","content":"帮我算一下 256 乘以 37 等于多少"},{"role":"assistant","content":"","tool_calls":"[{\"name\":\"calculate_math\",\"arguments\":{\"expression\":\"256 * 37\"}}]"},{"role":"tool","content":"{\"result\":\"9472\"}"},{"role":"assistant","content":"256 乘以 37 等于 9472。"}]}
```

Reasoning example:

```jsonl
{"conversations":[{"role":"user","content":"9 和 13 哪个更大？"},{"role":"assistant","reasoning_content":"比较两个整数：13 大于 9。","content":"13 更大。"}]}
```

Training behavior:

- Non-tool conversations may receive a random system prompt before templating.
- Empty thinking blocks may be removed probabilistically during post-processing.
- SFT labels supervise only assistant response/tool-call spans; user/system/tool context is input-only.
- LoRA uses this same SFT dataset format but freezes non-LoRA model parameters.

Cautions:

- Keep `tools` on a system message and `tool_calls` on assistant messages.
- Keep `tools` and `tool_calls` as JSON-encoded strings for compatibility with the native dataset feature schema.
- `tool` role `content` should be a string, commonly a JSON string returned by the tool.
- Tool calling and explicit thinking can both be represented by the template, but project evidence notes limited joint training data where tool calls and visible reasoning coexist. Avoid treating joint tool+thinking behavior as robust without targeted validation.

## Safe validation helper

Use the bundled validator before launching any full training route:

```bash
python scripts/validate_minimind_jsonl.py --schema pretrain <pretrain.jsonl>
python scripts/validate_minimind_jsonl.py --schema sft <sft-or-lora.jsonl>
python scripts/validate_minimind_jsonl.py --schema sft --tokenizer-dir <local-tokenizer-dir> --max-seq-len 768 <sft-or-lora.jsonl>
```

The validator checks JSONL syntax, schema, tool-call JSON strings, reasoning fields, and optional local tokenizer/chat-template compatibility without downloading data or writing outputs.
