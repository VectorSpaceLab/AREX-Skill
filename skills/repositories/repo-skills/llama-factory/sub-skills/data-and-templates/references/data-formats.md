# Data Formats And Registry Entries

LlamaFactory v0 discovers datasets from `dataset_info.json` in `dataset_dir` unless `dataset_dir: ONLINE` is used. The registry entry tells LlamaFactory where to load rows from and how to convert each row to the internal aligned fields: `_prompt`, `_response`, `_system`, `_tools`, `_images`, `_videos`, and `_audios`.

## Registry Entry Shape

A dataset entry is a top-level object keyed by the dataset name used in `dataset:` or `eval_dataset:`:

```json
{
  "my_dataset": {
    "file_name": "my_data.json",
    "formatting": "alpaca",
    "ranking": false,
    "split": "train",
    "columns": {
      "prompt": "instruction",
      "query": "input",
      "response": "output",
      "system": "system",
      "tools": "tools",
      "images": "images",
      "videos": "videos",
      "audios": "audios",
      "chosen": "chosen",
      "rejected": "rejected",
      "kto_tag": "kto_tag"
    }
  }
}
```

Common top-level keys:

- Source keys: `hf_hub_url`, `ms_hub_url`, `om_hub_url`, `script_url`, `cloud_file_name`, or `file_name`.
- Load metadata: `subset`, `split`, `folder`, and `num_samples`.
- Conversion metadata: `formatting`, `ranking`, `columns`, and `tags`.

Source precedence is hub URL first, then script, then cloud file, then local file. If both Hugging Face and ModelScope/OpenMind URLs are present, runtime environment helpers choose the remote hub preference; if no remote/source key is present, local `file_name` is required.

## Alpaca Format

Default `formatting` is `alpaca`. Defaults are `prompt: instruction`, `query: input`, and `response: output`.

```json
[
  {
    "instruction": "Summarize the note.",
    "input": "The server was patched on Friday.",
    "output": "The server patch happened Friday.",
    "system": "Be concise.",
    "history": [["Hi", "Hello"]]
  }
]
```

Conversion behavior:

- `history` is a list of prior user/assistant string pairs and is prepended as earlier turns.
- `instruction` and `input` are joined with a newline to form the current user message.
- `output` becomes the single assistant response for SFT.
- For pretraining, map `prompt` to the text column and omit a response column.

Minimal registry:

```json
{
  "my_alpaca": {
    "file_name": "my_alpaca.json",
    "columns": {
      "prompt": "instruction",
      "query": "input",
      "response": "output",
      "system": "system",
      "history": "history"
    }
  }
}
```

## ShareGPT Format

Use `formatting: sharegpt` when rows contain a list of role/content messages. Defaults are `messages: conversations`, `role_tag: from`, `content_tag: value`, `user_tag: human`, `assistant_tag: gpt`, `observation_tag: observation`, `function_tag: function_call`, and `system_tag: system`.

```json
[
  {
    "conversations": [
      {"from": "system", "value": "You are helpful."},
      {"from": "human", "value": "Use the weather tool for Paris."},
      {"from": "function_call", "value": "{\"name\": \"weather\", \"arguments\": {\"city\": \"Paris\"}}"},
      {"from": "observation", "value": "Sunny, 21C"},
      {"from": "gpt", "value": "It is sunny and 21C in Paris."}
    ],
    "tools": "[{\"name\": \"weather\", \"description\": \"Get weather\"}]"
  }
]
```

Important ordering rule:

- User-like turns are odd-position inputs after removing an optional initial system message: `human` and `observation`.
- Assistant-like turns are even-position outputs: `gpt` and `function_call`.
- Non-ranking SFT examples need an even number of aligned messages after optional system removal so the final message is the response.
- Ranking examples need an odd number of aligned prompt messages plus separate `chosen` and `rejected` assistant-like messages.

## OpenAI Format

The code includes an `openai` converter. Use it when rows already look like OpenAI chat messages and may include `tool_calls`.

```json
[
  {
    "messages": [
      {"role": "system", "content": "You are brief."},
      {"role": "user", "content": "Call the search tool."},
      {
        "role": "assistant",
        "content": "",
        "tool_calls": [{"function": {"name": "search", "arguments": "{\"q\": \"llama\"}"}}]
      },
      {"role": "tool", "content": "LlamaFactory is a fine-tuning framework."},
      {"role": "assistant", "content": "LlamaFactory is a fine-tuning framework."}
    ],
    "tools": [{"type": "function", "function": {"name": "search", "description": "Search docs"}}]
  }
]
```

Registry for OpenAI-like roles:

```json
{
  "my_openai": {
    "file_name": "my_openai.jsonl",
    "formatting": "openai",
    "columns": {"messages": "messages", "tools": "tools"},
    "tags": {
      "role_tag": "role",
      "content_tag": "content",
      "user_tag": "user",
      "assistant_tag": "assistant",
      "observation_tag": "tool",
      "function_tag": "assistant",
      "system_tag": "system"
    }
  }
}
```

The OpenAI converter serializes assistant `tool_calls[*].function` values as a function-role content string, joins consecutive tool/observation messages inside `<tool_response>` blocks, and stringifies `tools` when it is a dict or list. It also injects or appends a short `detailed thinking off` system hint when no tools are present.

## Preference And KTO Rows

For Alpaca ranking, set `ranking: true` and provide string `chosen` and `rejected` columns:

```json
{
  "instruction": "Give one safety rule.",
  "input": "",
  "chosen": "Wear eye protection.",
  "rejected": "Ignore safety equipment."
}
```

For ShareGPT/OpenAI ranking, `chosen` and `rejected` are message objects using the same role/content tags and must be assistant-like:

```json
{
  "conversations": [{"from": "human", "value": "Give one safety rule."}],
  "chosen": {"from": "gpt", "value": "Wear eye protection."},
  "rejected": {"from": "gpt", "value": "Ignore safety equipment."}
}
```

For KTO, map `kto_tag` to a boolean column. Conversion creates two responses by pairing the real response with an empty response; the feedback processor warns if all rows have only one preference type.

## Multimodal Columns

Map `images`, `videos`, or `audios` in `columns` when messages contain `<image>`, `<video>`, or `<audio>` placeholders.

```json
{
  "messages": [
    {"role": "user", "content": "<image>Describe the label."},
    {"role": "assistant", "content": "The label says fragile."}
  ],
  "images": ["images/box.jpg"]
}
```

Rules:

- The number of media paths must match the number of placeholders in message content.
- Local media paths are resolved relative to `media_dir`, which defaults to `dataset_dir`.
- Video rows may use a list of frame paths for pre-extracted frames.
- Media columns are only useful with a model/template whose multimodal plugin supports that modality; otherwise preprocessing raises a template/processor support error.

## File Types And Loading

Local `file_name` may point to a file or directory. Allowed local file types are JSON, JSONL, CSV, Parquet, and Arrow. A directory must contain files of the same type. Missing local files fail before conversion.
