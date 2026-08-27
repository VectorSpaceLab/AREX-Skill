# Data Formats

TRL separates dataset **format** from dataset **type**:

- **Standard format** stores plain strings, booleans, token ids, or scalar metadata.
- **Conversational format** stores messages as lists of dictionaries with at least `role` and usually `content`.
- **Type** describes the trainer objective: language modeling, prompt-only, prompt-completion, paired preference, unpaired preference, stepwise supervision, or reward-function inputs.

## Column checklist

| Task | Standard columns | Conversational columns | Notes |
| --- | --- | --- | --- |
| Language modeling / SFT | `text` | `messages` | Use `messages` for chat fine-tuning; use `text` for already-rendered strings. |
| Prompt-only / GRPO prompts | `prompt` | `prompt` | `prompt` is a string in standard format or a message list in conversational format. |
| Prompt-completion / SFT | `prompt`, `completion` | `prompt`, `completion` | Conversational `prompt` is usually user/tool turns; `completion` is assistant turns. |
| Paired preference / DPO-style | `prompt`, `chosen`, `rejected` or `chosen`, `rejected` | same keys with message lists | Missing `prompt` means an implicit prompt must be extracted from shared prefixes. |
| Unpaired preference | `prompt`, `completion`, `label` | same keys with message lists | `label` is boolean-like and marks preferred vs rejected completion. |
| Stepwise supervision | `prompt`, `completions`, `labels` | usually standard | `completions` and `labels` must have matching lengths. |
| Tool-calling SFT | `messages`, `tools` | `messages`, `tools` | `tools` is a list of JSON-schema tool definitions or a JSON string for older dataset stacks. |
| Multimodal chat | `messages`, optional `images` | `messages`, optional `images` | Message `content` may be structured blocks with `type: text` or `type: image`. |

## Message schema

A conversational row uses message objects such as:

```json
{"role": "user", "content": "What color is the sky?"}
{"role": "assistant", "content": "It is blue."}
```

Valid roles in TRL message preparation are `system`, `user`, `assistant`, and `tool`. Assistant messages may omit text content when they carry `tool_calls` instead. Tool responses use role `tool`, a tool `name`, and response `content`.

For multimodal rows, `content` can already be structured:

```json
{"role": "user", "content": [{"type": "image"}, {"type": "text", "text": "Describe this."}]}
```

`prepare_multimodal_messages(messages, images=...)` fills unpopulated `image` blocks from the supplied images and wraps string content into text blocks. The number of unfilled image placeholders must equal the number of provided images.

## Preference datasets

Paired preference rows can be explicit or implicit:

```json
{"prompt": "The sky is", "chosen": " blue.", "rejected": " green."}
```

```json
{"chosen": "The sky is blue.", "rejected": "The sky is green."}
```

Conversational implicit preference rows put the shared prompt turns inside both `chosen` and `rejected`:

```json
{"chosen": [{"role": "user", "content": "What color is the sky?"}, {"role": "assistant", "content": "Blue."}], "rejected": [{"role": "user", "content": "What color is the sky?"}, {"role": "assistant", "content": "Green."}]}
```

Use `maybe_extract_prompt` when rows may mix explicit and implicit prompts. It leaves explicit rows unchanged and extracts a shared prompt from implicit rows when possible.

## ChatML conversion

Use `maybe_convert_to_chatml` for datasets using OpenAI-style keys:

- `from` becomes `role`.
- `value` becomes `content`.
- `conversations` becomes `messages`.

Run conversion before `maybe_apply_chat_template` so downstream helpers see TRL's expected message keys.

## Tool-call data

A tool-calling message sequence can contain:

```json
{"role": "assistant", "tool_calls": [{"type": "function", "function": {"name": "lookup", "arguments": {"key": "x"}}}]}
{"role": "tool", "name": "lookup", "content": "result"}
```

Keep tool definitions in a row-level `tools` column for SFT datasets. Prefer JSON-schema-like tool dictionaries. If a dataset backend cannot preserve arbitrary JSON objects, store `tools` as a JSON string and decode it before applying chat templates.

## Packing

Use `pack_dataset(dataset, seq_length, strategy="bfd", map_kwargs=None)` only after text/tokenized sequences are ready to concatenate. Packing changes example boundaries and is not a substitute for fixing missing columns or invalid chat message shapes.
