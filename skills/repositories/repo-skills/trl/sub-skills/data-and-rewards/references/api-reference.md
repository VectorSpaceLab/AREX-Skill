# API Reference

This reference summarizes the TRL data and chat-template helpers most often needed before trainer construction.

## Data helpers

### `prepare_multimodal_messages(messages, images=None)`

Converts messages into structured multimodal content blocks and injects provided image objects.

- String user content becomes image placeholders followed by one text block on the first user turn when `images` is provided.
- String system, assistant, and tool content becomes `[{"type": "text", "text": ...}]`.
- Existing image blocks with an `image` payload are preserved.
- Raises when the number of unfilled image placeholders does not match `len(images)`.

### `is_conversational(example)`

Returns `True` when one of `prompt`, `chosen`, `rejected`, `completion`, or `messages` contains a list whose first item is a dict with a `role` key. Use this before applying chat templates.

### `apply_chat_template(example, processing_class, tools=None, **template_kwargs)`

Applies a tokenizer or processor chat template to a conversational example. Supported key sets are:

- `messages`
- `prompt`
- `prompt`, `completion`
- `prompt`, `chosen`, `rejected`
- `chosen`, `rejected`
- `prompt`, `completion`, `label`

For prompt rows, TRL adds a generation prompt when the last prompt role is `user` or `tool`; it continues the final message when the last prompt role is `assistant`. Pass `tools` only for templates that support tool calling.

### `maybe_apply_chat_template(example, processing_class, tools=None, **template_kwargs)`

Applies `apply_chat_template` only to conversational examples. Standard string examples are returned unchanged. Prefer this in preprocessing code that may receive either plain-text or chat rows.

### `extract_prompt(example)` and `maybe_extract_prompt(example)`

Extract a shared prompt from implicit preference rows where `chosen` and `rejected` contain the prompt prefix. `maybe_extract_prompt` is safer for mixed datasets because it leaves explicit rows unchanged.

Use this for the hard case where a conversational preference row has only `chosen` and `rejected`; after extraction it should have `prompt`, `chosen`, and `rejected`, with `chosen`/`rejected` reduced to the divergent assistant completions.

### `unpair_preference_dataset(dataset, **map_kwargs)` and `maybe_unpair_preference_dataset(dataset, **map_kwargs)`

Converts paired preference rows into unpaired rows with `completion` and boolean `label`. Use when a trainer or preprocessing step expects unpaired preference examples. Preserve the original `prompt` where present.

### `pack_dataset(dataset, seq_length, strategy="bfd", map_kwargs=None)`

Packs sequences into fixed-length examples. `strategy="bfd"` uses a best-fit decreasing style and is the default. Validate that text/token columns exist and have the expected type before packing.

### `maybe_convert_to_chatml(example)`

Converts OpenAI-style records to TRL message keys. It maps `conversations` to `messages`, `from` to `role`, and `value` to `content` where present.

## Chat-template helpers

### `clone_chat_template(model, tokenizer, source_tokenizer_path, resize_to_multiple_of=64)`

Clones a chat template and special tokens from a source tokenizer to a target tokenizer/model pair, resizing embeddings to the requested multiple. Use when a base model lacks a suitable chat template.

### `get_training_chat_template(...)`

Returns a patched training template for supported model families when TRL needs features such as assistant-generation masks or prefix-preserving tool-call rendering. Use this instead of hand-editing a bundled model family template.

### `supports_tool_calling(processing_class)`

Checks whether the tokenizer or processor can render tool-calling conversations. If false, do not pass `tools` into preprocessing or GRPO tool-call flows for that processing class.

### `parse_response(tokenizer, ids)`

Parses generated token ids into a response structure when the tokenizer has an attached response schema. This is most relevant for tool-call responses. If parsing fails, first check that the chat template family is supported and the response schema was added.

## Recommended preprocessing order

1. Convert OpenAI-style records with `maybe_convert_to_chatml`.
2. For preference data, call `maybe_extract_prompt` if implicit prompts are possible.
3. For multimodal rows, call `prepare_multimodal_messages` with the exact image list for each row.
4. Check `is_conversational`; call `maybe_apply_chat_template` with the tokenizer/processor and row-level tools when needed.
5. Pack only after examples are in the representation expected by the target trainer.
