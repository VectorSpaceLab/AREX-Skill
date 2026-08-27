# Data Formats

## `test_cases.jsonl`

The batch scripts read one JSON object per line.

Required and optional fields:

| Field | Type | Meaning |
| --- | --- | --- |
| `question` | string | The user question to send to the model. |
| `image` | string | Optional image path. May be empty for text-only cases. |

Example lines:

```json
{"image": "./demo_image/demo_1.png", "question": "右边第二个小孩子的裙子是什么颜色？"}
{"image": "", "question": "英雄联盟历史上最成功的选手是谁？为什么？"}
```

Image-path handling rules for the validator and payload builder:

1. An absolute path is used as-is.
2. A relative path is first resolved against the input file directory.
3. If still unresolved, the current working directory is checked.
4. Empty strings mean text-only records and are valid.

## OpenAI-compatible request body

The bundled payload builder emits a JSON request body with these fields:

| Field | Type | Meaning |
| --- | --- | --- |
| `messages` | array | One `user` message containing content blocks. |
| `model` | string | `skywork/r1v4-lite` or `skywork/r1v4-vl-planner-lite`. |
| `stream` | boolean | `false` for non-stream, `true` for SSE. |
| `enable_search` | boolean | `false` in the regular model scripts; planner variants keep the source behavior. |

Message content order:

1. `image_url` block when an image is present.
2. `text` block with the question.

Example content block order:

```json
[
  {"type": "image_url", "image_url": {"url": "data:image/png;base64,..."}},
  {"type": "text", "text": "问题内容"}
]
```

## Result JSONL from the batch scripts

Each line is a record with the original input and a response block.

Typical fields:

| Field | Type | Meaning |
| --- | --- | --- |
| `image` | string | Original image path or empty string. |
| `question` | string | The original question. |
| `response.full_response` | string | Concatenated model output or full message text. |
| `response.raw_response` | object | Non-stream raw API JSON response. |
| `response.raw_events` | string | Stream mode SSE lines joined with newlines. |
| `response.error` | string | Error text when the request failed. |

## Tagged response grammar

The parser expects the common tagged format used by the source helper:

```text
<think>...</think>
<tool_call>{...}</tool_call>
<observation>{...}</observation>
<answer>...</answer>
```

Parser behavior in the bundled CLI:

- `think` and `answer` text are preserved as raw strings.
- `tool_call` and `observation` are parsed as JSON when possible.
- Malformed JSON stays available as the raw string plus a parse-error field.
- The parser keeps per-round raw blocks so future agents can inspect the original text without re-reading source code.

## Parsed response shape

A parsed response returned by `parse_full_response()` contains:

- `rounds`: ordered rounds with `think_raw`, `tool_call_raw`, `observation_raw`, and parse error fields.
- `final_round`: the final `think` plus `answer`.
- `tag_sequence`: ordered raw tag blocks for debugging.
- `tag_counts`: counts for `<think>`, `<tool_call>`, `<observation>`, and `<answer>` tags.

This shape is designed to survive malformed tool JSON while keeping the original content visible.
