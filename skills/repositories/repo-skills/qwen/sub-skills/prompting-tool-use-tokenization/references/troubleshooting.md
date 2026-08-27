# Prompting, Tool-use, and Tokenizer Troubleshooting

## Function calling

- Function calling requested with `stream=True`: unsupported by the repository API server; use non-streaming requests.
- `function` role before an assistant call: reorder the messages so a function observation follows the assistant's tool call.
- Tool arguments are not JSON: put a clear formatting rule in `description_for_model` and validate the generated `Action Input`.
- Model stops at `Observation:` unexpectedly: the API server adds `Observation:` as a stop word when functions are present.

## System prompts

- System prompt ignored: check that a chat checkpoint is loaded, `history` is preserved correctly, and the prompt is passed through the `system` parameter rather than embedded ambiguously in the user message.
- Behavior drifts across turns: shorten and clarify the system rule, then test with a two-turn local chat before deploying through the API.

## Tokenizer and ChatML

- User text containing `<|endoftext|>` is treated as control: use `allowed_special=set()` or configure `disallowed_special` for untrusted text.
- Replacement characters appear in decoded output: Qwen regular tokens can represent partial UTF-8 bytes; decode complete token sequences or choose `errors='ignore'` only when acceptable.
- Batch inference gives malformed responses: check pad token, left padding, prompt slicing, and ChatML context construction.
- Fine-tuning data with `function` role fails: convert function-call examples into user/assistant ReAct text samples.
