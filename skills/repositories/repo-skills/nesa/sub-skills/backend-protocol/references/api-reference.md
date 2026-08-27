# Backend API Reference

This reference distills the Nesa backend helper APIs verified during inspection.

## Settings

Runtime settings are loaded with Pydantic settings and dotenv support. Important
fields:

- `project_name`: defaults to `default-service`.
- `version`: defaults to `0.0.1` in the inspected source settings.
- `stream_url`: defaults to `https://eegent.dev.nesa.ai/request`.
- `publish_configs` and `consume_configs`: populated from environment variables
  with `PUBLISH_` and `CONSUME_` prefixes.

Do not hard-code local `.env` values in generated outputs. Treat `stream_url` as
configurable.

## Protocol structs

The source uses `msgspec.Struct` classes.

### `Message`

Fields:

- `content: str`
- `role: Optional[str]`

### `Role`

String enum values are lower-case enum names generated from:

- `ASSISTANT`
- `USER`
- `AI`
- `SYSTEM`

### `LLMParams`

Important defaults:

- `n=1`
- penalties: presence/frequency `0.0`, repetition `1.0`
- `temperature=1.0`
- `top_p=1.0`, `top_k=-1`, `min_p=0.0`
- `max_tokens=16`, `min_tokens=0`
- `skip_special_tokens=True`
- `detokenize=True`
- `stop_token_ids` normalizes to an empty list when omitted

Validation highlights:

- `n` must be an integer and at least 1.
- presence and frequency penalties must be in `[-2, 2]`.
- repetition penalty must be in `(0, 2]`.
- temperature must be non-negative.
- top-p must be in `(0, 1]`.
- top-k must be `-1` or at least 1, and it must be an integer.
- min-p must be in `[0, 1]`.
- max tokens must be at least 1 when set.
- min tokens must be non-negative and at most max tokens.
- near-zero temperature uses greedy sampling and requires `n == 1`.

Use `LLMParams.from_optional(...)` to coerce optional API values to defaults.

### `SessionID`

Fields:

- `ee: bool`
- `session_id: Optional[str]`
- `user_id: Optional[str]`

Use `ee=True` for Nesa encrypted-session requests.

### `LLMInference`

Fields:

- `stream: bool`
- `correlation_id: str`
- `messages: List[Message]`
- `model: str`
- `model_params: Optional[LLMParams | dict]`
- `session_id: Optional[SessionID]`

### Streaming response structs

- `DeltaMessage`: optional role plus `content`, which can be an integer token or
  a string.
- `Choice`: index, delta, and optional finish reason.
- `InferenceResponse`: correlation id, model, choices, object type
  `chat.completion.chunk`, and optional session.

## Registry

`ModelRegistry.register(key, is_model_specific=False)` stores a class in either
`model_specific` or `task_type`. `ModelRegistry.get_model(base_id, task_type)`
returns:

1. model-specific handler for `base_id`, if present;
2. task-type handler for `task_type`, if present;
3. otherwise raises `ValueError`.

Known source handlers include encrypted DistilBERT local classification and an
encrypted Llama remote streaming handler.

## Utility helpers

`sanitize_subject_token` lowercases strings and replaces `.`, `>`, `*`, and
space with placeholder markers. `desanitize_subject_token` reverses those
markers. Use these helpers only for subject-token-safe routing strings; do not
confuse them with encryption/decryption.

`clean_string` decodes HTML entities, strips non-ASCII printable characters, and
normalizes with Unicode NFKC before trimming. This is used in prompt/history
construction.
