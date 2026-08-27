# Data Formats

ms-swift accepts direct files through `--dataset`, dataset metadata through `--custom_dataset_info`, and plugin-registered datasets through `--external_plugins`. Direct file loading is the best first choice for new data because `AutoPreprocessor` can map common formats into standard `messages` rows.

## Standard Row Keys

`messages` is the central key for LLM, multimodal, agent, SFT, PT, and most RLHF data. Common optional keys are:

| Key | Use |
| --- | --- |
| `messages` | Conversation list. Each item needs `role` and non-null `content`. |
| `rejected_response` | DPO/ORPO/CPO/SimPO/RM rejected answer appended after the last user turn. |
| `rejected_messages` | Full rejected conversation branch; use when the rejected side has different multimodal or tool context. |
| `label` | KTO boolean labels, sequence classification labels, or regression targets. |
| `images`, `videos`, `audios` | Multimodal paths, URLs, base64 data URIs, or model-supported video-frame lists. |
| `tools` | Agent tool schema. ms-swift expects a JSON string or list describing tools. |
| `objects` | Grounding refs and boxes for tasks that use `<ref-object>` and `<bbox>` placeholders. |
| `loss`, `loss_scale` | Assistant-message-level loss control; these belong inside individual `messages` entries. |
| `chat_template_kwargs` | Per-sample template options such as `max_pixels`, `fps`, `enable_thinking`, or response-prefix controls. |
| `channel` | Channel-loss label when training with channel loss enabled. |

Message roles accepted by ms-swift preprocessing include `system`, `user`, `assistant`, `tool_call`, `tool_response`, and `tool`. `tool` and `tool_response` are equivalent. `tool_call` and `tool_response` contents should be JSON strings when using agent templates.

## AutoPreprocessor Selection

`AutoPreprocessor` chooses a row preprocessor from dataset features:

- `messages`, `conversation`, or `conversations` → `MessagesPreprocessor`.
- `instruction` plus `input` → `AlpacaPreprocessor`; the query becomes `instruction + "\n" + input` when both are non-empty.
- Otherwise → `ResponsePreprocessor`, which maps query/response style fields.

Automatic query/response aliases include:

- System: `system`, `system_prompt`.
- Query: `query`, `prompt`, `input`, `instruction`, `question`, `problem`.
- Response: `response`, `answer`, `output`, `targets`, `target`, `answer_key`, `answers`, `solution`, `text`, `completion`, `content`.

`image`/`images`, `video`/`videos`, and `audio`/`audios` are normalized to plural multimodal keys. Explicit `--columns` mappings run before preprocessing and should map source column names to ms-swift field names.

## Column Mapping

Use `--columns source=target source2=target2` to rename dataset columns before preprocessing. Typical examples:

```bash
swift sft --dataset train.jsonl --columns prompt=query answer=response
swift rlhf --dataset pref.jsonl --columns chosen=response rejected=rejected_response
```

For metadata-driven loading, put the same mapping in a `columns` object inside `dataset_info.json` or a subset entry. If multiple source columns map to the same target, ms-swift keeps only safe, unambiguous renames. If auto mapping surprises you, explicitly preserve the desired field with a direct mapping such as `query=query` and validate with the bundled row checker.

## Direct Dataset Files

Direct `--dataset` can point at `jsonl`, `json`, `csv`, `txt`, or folders. Recommended workflow:

1. Convert rows to one of the standard or auto-detected shapes.
2. Run `scripts/validate_dataset_rows.py` on the file.
3. Start a small ms-swift run with `--dataset_sample` or equivalent sampling before full training.

For JSON arrays, each object is a row. For JSONL, each non-empty line is one row. For CSV, fields that contain `messages`, `tools`, `objects`, `images`, `videos`, `audios`, or rejected variants may need JSON strings so they parse into structured values.

## SFT and Pretraining Rows

SFT rows use alternating `user` and `assistant` messages, optionally preceded by `system`. Pretraining rows may be a single `assistant` message containing raw text. A row-level `system` in the dataset has priority over a command-line `--system`, and both override only when the template supports system prompts.

Assistant messages may include:

- `loss: false` to suppress loss for that assistant span.
- `loss: true` to force loss for that assistant span under the selected strategy.
- `loss_scale: <number>` to weight that assistant span. If values greater than `1` occur, configure binary-loss behavior appropriately in the training command.

These fields take effect on assistant content; they are not general row-level fields.

## RLHF and Preference Rows

DPO/ORPO/CPO/SimPO/RM rows require a chosen side in `messages` plus a rejected side. Provide at least one of:

- `rejected_response`: a rejected assistant answer or list of rejected assistant messages.
- `rejected_messages`: a full rejected branch.
- `rejected_images`, `rejected_videos`, `rejected_audios`, or `rejected_tools` when the rejected branch needs different multimodal/tool context.

If `rejected_response` is identical to the final chosen assistant content, ms-swift rejects the row. If using `rejected_messages` for multimodal or agent samples, also provide the rejected media/tool fields when they differ from the chosen side.

KTO rows use `label` as a boolean-like preference label. PPO/GRPO rows can be prompt-only `messages`; GRPO passes extra row fields through to custom reward/ORM code, so avoid accidental large or private columns.

## Multimodal Rows

Use `<image>`, `<video>`, and `<audio>` placeholders in message content where features should be inserted. The number of placeholders should match the corresponding media list unless the chosen model/template documents a different behavior.

Valid media values include:

- Local paths or URLs.
- Base64 data URIs such as `data:image/jpg;base64,...`.
- Video frame lists for models that support frame-list videos.
- Image dictionaries with `path` and `bytes` fields after ms-swift casting.

Prefer paths that are valid in the runtime environment. Absolute paths can work in a training job, but do not bake local machine paths into reusable datasets or public skill content.

## Grounding Rows

For ms-swift grounding format, provide `objects` with:

- `ref`: labels that replace `<ref-object>` placeholders.
- `bbox`: boxes that replace `<bbox>` placeholders; each box has length `2` or `4`.
- `bbox_type`: optional, commonly `real` or `norm1`.
- `image_id`: optional image indices for multi-image samples; length should match `bbox` when used.

The count of `<ref-object>` placeholders should match `len(objects.ref)`. The count of `<bbox>` placeholders should match `len(objects.bbox)`. Some model families normalize boxes differently, so use the intended model/template when checking final encodings.

## Agent Rows

Agent rows combine `tools` with messages containing tool calls and responses. Practical rules:

- `tools` should be a list or a JSON string representing a list of function schemas.
- `tool_call` content should be a JSON string with the call name and arguments.
- `tool_response` or `tool` content should be a JSON string response.
- Parallel tool calls can appear as consecutive `tool_call` messages.
- Multimodal agent rows still need placeholder/media consistency.

When `agent_template` is set, ms-swift formats tools into the system section and maps tool roles into model-specific assistant/tool text.

## Validation Checklist

Before training or RLHF execution:

- `messages` exists after column mapping and is a non-empty list.
- Each message has a valid `role` and non-null `content`.
- `rejected_response` is not empty and not identical to the chosen final assistant answer.
- Multimodal placeholders match `images`, `videos`, and `audios` counts.
- `objects.ref` and `objects.bbox` counts match placeholders.
- `loss` is boolean and `loss_scale` is numeric when present.
- `chat_template_kwargs` is an object, not an arbitrary string.
- Extra fields are intentional, especially for GRPO or custom preprocessors.
