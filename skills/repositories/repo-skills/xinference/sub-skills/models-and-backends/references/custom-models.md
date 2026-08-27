# Custom Models

This skill validates direct custom-registration JSON. It does not fetch models or resolve model hubs.

## Offline validation rules

- Validate a single JSON object, not a model hub catalog list.
- `model_name` must be unique and syntactically valid.
- A custom config should normally have either `model_id` or `model_uri`.
- `model_uri` must be absolute when it is a local file path; relative file paths are rejected.
- Unknown fields are tolerated by Xinference, but this helper reports them so they are visible before registration.
- If the payload only looks like a hub catalog entry with `model_src`, it is the wrong shape for direct registration.
- `video` is recognized as a model family, but custom video registration is not supported.

## LLM custom models

Required top-level fields:

- `version` `= 2`
- `model_name`
- `model_lang`
- `model_ability`
- `model_family`
- `model_specs`

Spec fields that must be present:

- `model_format`
- `model_size_in_billions`
- `quantization`

Common optional fields:

- `model_description`
- `context_length`
- `chat_template`
- `stop_token_ids`
- `stop`
- `reasoning_start_tag`
- `reasoning_end_tag`
- `architectures`
- `tool_parser`
- `cache_config`
- `virtualenv`
- `is_builtin`

Notes:

- `model_family` is mandatory for custom LLMs.
- `chat_template` is recommended whenever `chat` is part of `model_ability`.
- Tool and vision abilities have extra family constraints; the checker can only flag the shape, not claim a backend match.
- `model_size_in_billions` may be an integer, a float, or a radix string such as `1_8`.
- Legacy payloads may still show `quantizations`; the v2 shape prefers `quantization`.
- GGUF specs also need `model_file_name_template`; the split template and quantization parts are optional.
- `model_hub` defaults to `huggingface`.

## Embedding custom models

Required top-level fields:

- `version` `= 2`
- `model_name`
- `dimensions`
- `max_tokens`
- `language`
- `model_specs`

Spec fields that must be present:

- `model_format`
- `quantization`

Common optional fields:

- `cache_config`
- `virtualenv`
- `is_builtin`

Notes:

- `model_family` is not part of the embedding schema.
- A local `model_uri` is fine when it points to an absolute path that already exists.
- GGUF specs also need `model_file_name_template`.

## Rerank custom models

Required top-level fields:

- `version` `= 2`
- `model_name`
- `language`
- `model_specs`

Common optional fields:

- `type`
- `max_tokens`
- `cache_config`
- `virtualenv`
- `is_builtin`

Spec fields that must be present:

- `model_format`
- `quantization`

Notes:

- `type` defaults to `unknown` if omitted.
- The same `model_uri` and GGUF rules as embedding models apply.

## Image custom models

Required top-level fields:

- `version` `= 2`
- `model_name`
- `model_family`

Common optional fields:

- `model_id`
- `model_revision`
- `model_hub`
- `model_ability`
- `controlnet`
- `default_model_config`
- `default_generate_config`
- `gguf_model_id`
- `gguf_quantizations`
- `gguf_model_file_name_template`
- `lightning_model_id`
- `lightning_versions`
- `lightning_model_file_name_template`
- `cache_config`
- `virtualenv`
- `is_builtin`
- `model_uri`

Notes:

- `controlnet` is a nested list of image-family objects and should be validated recursively.
- The checker should treat a missing source path as an error unless the payload clearly points at a local or hub-backed model.

## Audio custom models

Required top-level fields:

- `version` `= 2`
- `model_name`
- `model_family`
- `multilingual`

Common optional fields:

- `model_id`
- `model_revision`
- `model_hub`
- `language`
- `model_ability`
- `default_model_config`
- `default_transcription_config`
- `engine`
- `cache_config`
- `virtualenv`
- `is_builtin`
- `model_uri`

Notes:

- `engine` is optional but useful for audio families with multiple backends.
- A missing source path is usually a registration problem for custom audio configs.

## Flexible custom models

Required top-level fields:

- `model_name`
- `launcher`

Common optional fields:

- `version`
- `model_id`
- `model_description`
- `model_uri`
- `launcher_args`
- `cache_config`
- `virtualenv`
- `is_builtin`

Notes:

- `launcher_args` must be valid JSON text.
- Flexible models are launcher-driven, so backend fit comes from the launcher rather than a fixed family list.

## Registration boundary

- This checker prints a register-command template, but actual registration still happens through the serving surface.
- Use the sibling sub-skill for service orchestration when the problem is not the JSON itself.
