# Model Overview

Xinference groups model support into a small set of family types. The registry key is `model_name`; the rest of the family payload narrows the backend, format, and launch rules.

## Family types at a glance

| Type | Core fields | Shape notes |
| --- | --- | --- |
| LLM | `version`, `model_name`, `model_lang`, `model_ability`, `model_family`, `model_specs` | `model_engine` is explicit at launch time. `chat_template` and stop fields shape chat behavior. |
| embedding | `version`, `model_name`, `dimensions`, `max_tokens`, `language`, `model_specs` | Defaults to `sentence_transformers` when no engine is supplied. |
| rerank | `version`, `model_name`, `language`, `model_specs`, optional `type`/`max_tokens` | Also defaults to `sentence_transformers` when no engine is supplied. |
| image | `version`, `model_name`, `model_family`, `model_id`/`model_uri`, `model_revision` | Defaults to `diffusers` when no engine is supplied. |
| audio | `version`, `model_name`, `model_family`, `model_id`/`model_uri`, `multilingual`, optional `language`/`engine` | Engine choice is family-specific. |
| video | `version`, `model_name`, `model_family`, `model_id`, `model_ability`, optional config blocks | Built-in catalog only; custom video registration is not supported. |
| flexible | `version`, `model_name`, `launcher`, optional `launcher_args`, `model_uri` | Launcher-driven, not a fixed model-engine family. |

## Selection cues

- `model_name` picks the family.
- `model_format` and `quantization` narrow a spec within a family.
- `model_engine` narrows the runtime backend where the family supports multiple engines.
- LLM launches require an explicit `model_engine`; embedding, rerank, and image can fall back to a default engine when one is not supplied.
- `model_uri` can point at an existing local directory or file, so no download is needed when the family already supports a local path.
- `virtualenv.packages` can advertise engines through `#engine#` markers, but hardware and OS checks still apply.
- Custom `model_name` values must be unique and should stay within the legal name pattern.

## Safe reading order

1. Confirm the family type.
2. Confirm the JSON has the right required fields for that type.
3. Match the format and quantization to the intended backend.
4. Only then check virtualenv, LoRA, and memory-planning details.
