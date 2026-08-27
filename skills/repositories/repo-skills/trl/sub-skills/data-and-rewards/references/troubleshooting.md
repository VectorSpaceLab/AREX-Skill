# Troubleshooting

## Missing columns

Symptom: preprocessing or trainer setup raises a key error for columns such as `messages`, `prompt`, `chosen`, `rejected`, `completion`, `label`, `solution`, or `tools`.

Fix:

1. Identify the dataset type before choosing a trainer.
2. Compare the row against the column checklist in [Data Formats](data-formats.md).
3. For preference rows with only `chosen` and `rejected`, decide whether this is an implicit prompt dataset and run prompt extraction before requiring a `prompt` column.
4. For GRPO reward functions, keep task-specific metadata such as `solution` in the dataset so reward functions receive it.

## Implicit vs explicit prompt confusion

Symptom: a preference dataset has `chosen` and `rejected` but no `prompt`, or conversion duplicates the prompt inside both completions.

Fix:

- Explicit preference rows already have `prompt`, `chosen`, and `rejected`; do not extract again.
- Implicit preference rows include the shared prompt prefix inside both `chosen` and `rejected`.
- Use `maybe_extract_prompt` on mixed data so explicit rows stay unchanged.
- After extraction, verify that `chosen` and `rejected` contain only the divergent completions.

## Conversational vs standard mismatch

Symptom: `apply_chat_template` fails on strings, or a trainer receives message lists when it expected rendered text.

Fix:

- Use `is_conversational` to detect message-list examples.
- Use `maybe_apply_chat_template` when batches can contain standard and conversational rows.
- Use `apply_chat_template` only when the row is definitely conversational and has one of the supported key sets.
- Do not apply a chat template twice; rendered strings should stay strings.

## Invalid message roles or content

Symptom: multimodal preparation raises invalid-role errors or chat template rendering fails.

Fix:

- Restrict roles to `system`, `user`, `assistant`, and `tool` for TRL message preparation.
- Keep assistant tool calls in `tool_calls`; a tool response should have role `tool`, a `name`, and `content`.
- For multimodal rows, string content is acceptable before preparation; structured content must be a list of blocks such as `{"type": "text", "text": ...}` or `{"type": "image"}`.

## Multimodal image mismatch

Symptom: `prepare_multimodal_messages` raises that provided images do not match image placeholders.

Fix:

- Count unfilled `{"type": "image"}` blocks without an `image` payload across non-tool messages.
- Pass exactly that many image objects for the row.
- If messages have plain string user content and `images` is non-empty, TRL inserts all image placeholders before the first user text message.
- Existing image blocks with an `image` payload do not require another image object.

## Tool-call template or parsing failure

Symptom: tool definitions render incorrectly, `parse_response` fails, or GRPO tool-call loops cannot extract tool suffix tokens.

Fix:

- Check `supports_tool_calling(processing_class)` before passing `tools`.
- Use row-level `tools` as JSON-schema-like dictionaries; avoid arbitrary Python objects in persisted datasets.
- Use supported training chat templates when GRPO tool calling needs prefix preservation.
- For SFT assistant-only loss, ensure the template has generation markers around assistant output.
- When the dataset backend cannot store arbitrary JSON, serialize `tools` as JSON strings and decode before preprocessing.

## Rewards return `None`

Symptom: a reward result contains `None` values or aggregate reward counts look lower than the batch size.

Fix:

- `accuracy_reward` and `reasoning_accuracy_reward` return `None` when the gold solution is unparseable; this means skip, not wrong.
- Return `None` from custom rewards for rows the reward cannot judge, especially in mixed math/coding datasets.
- Return `0.0` when the row is judgeable and the model should be penalized, such as incomplete reasoning for `reasoning_accuracy_reward`.
- Keep reward lists aligned with the completion batch length even when some entries are `None`.

## Missing `math_verify`

Symptom: importing or calling math accuracy rewards raises an optional dependency error.

Fix:

- Install the optional math verification dependency in the training environment before using `accuracy_reward` or `reasoning_accuracy_reward`.
- If the task is not math verification, use non-math rewards such as `think_format_reward`, repetition penalties, overlong punishment, or a custom reward.
- For mixed datasets, guard custom reward code so non-math rows return `None` rather than requiring math parsing.
