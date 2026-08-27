# verl Data Formats

## Post-training parquet rows

verl post-training datasets are commonly written as parquet files. The RL dataset loader reads parquet or JSON/JSONL files, concatenates them, optionally filters overlong prompts, and returns non-tensor fields through `DataProto.non_tensor_batch` after collation.

Recommended row fields:

| Field | Required | Expected shape | Purpose |
| --- | --- | --- | --- |
| `data_source` | Yes | non-empty string | Selects the default reward scorer and appears in reward diagnostics. |
| `prompt` | Yes, unless config uses another `prompt_key` | list of chat messages | Passed to tokenizer or processor chat templates. |
| `ability` | Recommended | string such as `math`, `toolcall`, `qa` | Task grouping metadata used by examples and diagnostics. |
| `reward_model` | Yes for rule rewards and validation | dict | Carries reward metadata, especially `ground_truth`. |
| `extra_info` | Recommended | dict or null | Stores `split`, `index`, raw question/answer, tool settings, and interaction settings. |

A minimal math row follows this shape:

```json
{
  "data_source": "openai/gsm8k",
  "prompt": [{"role": "user", "content": "Question text. Let's think step by step and output the final answer after \"####\"."}],
  "ability": "math",
  "reward_model": {"style": "rule", "ground_truth": "72"},
  "extra_info": {"split": "train", "index": 0}
}
```

## Prompt message rules

`RLHFDataset` defaults to `prompt_key: prompt`. Each prompt should be a non-empty list of dictionaries compatible with Hugging Face chat templates:

- `role` should usually be `system`, `user`, `assistant`, or `tool`.
- `content` may be a string for text-only rows.
- For already-structured multimodal rows, `content` may be a list of content parts such as `{"type": "image", "image": ...}` or `{"type": "text", "text": ...}`.
- A plain string prompt is not equivalent to chat messages; tokenizer `apply_chat_template` expects the list-of-message shape.

## Multimodal rows

For multimodal RL data, `RLHFDataset._build_messages` replaces placeholders in string content when matching modality columns are present:

- `<image>` consumes entries from the configured `image_key`, default `images`.
- `<video>` consumes entries from the configured `video_key`, default `videos`.
- `<audio>` consumes entries from the configured `audio_key`, default `audios`.

Each placeholder must have exactly one corresponding modality entry. The loader removes raw `images`, `videos`, and `audios` from the returned sample after building `raw_prompt`, so reward code should rely on `extra_info` or `raw_prompt` rather than those original columns.

## Dataset loader behavior to remember

- Supported file extensions are parquet, JSON, and JSONL.
- `filter_overlong_prompts` applies the chat template while measuring prompt length; malformed prompts are skipped as overlong after printing a traceback.
- `extra_info` is normalized to `{}` when missing or null at item access time.
- `extra_info.index` becomes the sample `index`; missing index defaults to `0`.
- `extra_info.tools_kwargs`, `extra_info.interaction_kwargs`, and `extra_info.need_tools_kwargs` are surfaced for tool/agent workflows.
- `collate_fn` stacks tensor fields and converts non-tensor fields, including `reward_model`, `data_source`, and `extra_info`, into object arrays for `DataProto.from_dict`.

## DataProto facts for downstream agents

Verified `DataProto` API facts recorded during skill generation:

- `DataProto(...)` accepts tensor batch, non-tensor batch, metadata, and related protocol fields; prefer factory helpers where possible.
- `DataProto.from_single_dict(...)` builds a one-sample protocol object from a mixed dictionary.
- `DataProto.from_dict(tensors=..., non_tensors=..., meta_info=...)` is the common bridge from `collate_fn` output.
- `DataProto.concat(...)`, `chunk(...)`, `reorder(...)`, `repeat(...)`, `to(...)`, and `select(...)` are used to reshape, shard, move, and slice data during trainer and reward flows.

Use these as orientation, not as a replacement for checking the active installed API when editing protocol-heavy code.

## Safe preprocessing guidance

The bundled examples in verl load public Hugging Face datasets, so generated skills should not require running them in offline environments. When adapting them, preserve the output schema and replace network access with an already-available local dataset or a caller-provided raw-data source.
