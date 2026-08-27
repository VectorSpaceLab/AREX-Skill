# Data formats

This sub-skill covers the JSONL shape the trainer consumes before it builds prompts and reward inputs. Keep the authored JSON compact: the current loader reads only the first two conversation turns.

## Required shape

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `conversations` | list | yes | Use at least two turns. The first turn is the user prompt, and the second turn is the target answer. Extra turns are ignored by the current loader. |
| `image` | string or list[string] | no | Relative path(s) to image file(s). A list means multi-image input and preserves order. |
| `accu_reward_method` | string | no | Row-level override for the accuracy scorer. If omitted, the file-level default is used. |
| `id` | scalar | no | Bookkeeping only. |

## Single-image row

```json
{
  "id": 1,
  "image": "set_a/sample_001.png",
  "conversations": [
    {"from": "human", "value": "<image>What number of purple metallic balls are there?"},
    {"from": "gpt", "value": "0"}
  ]
}
```

Notes:
- Keep the image path relative.
- If you include a literal `<image>` placeholder, use one token for one image.
- Zero literal `<image>` placeholders is also valid because the loader rebuilds image content from the `image` field.
- Put the final answer only in the second turn.

## Multi-image row

```json
{
  "id": 2,
  "image": ["gui/before.png", "gui/after.png"],
  "conversations": [
    {"from": "human", "value": "<image><image>Did the UI change as expected?"},
    {"from": "gpt", "value": "Operation No Response"}
  ]
}
```

Notes:
- Keep the image order stable.
- If you include literal `<image>` placeholders, use one token per image.
- Zero literal `<image>` placeholders is also valid; the GUI multi-image pattern relies on the image list order.
- Mixed single-image and multi-image rows are allowed in the same file as long as each row stays internally consistent.

## Text-only row

```json
{
  "id": 3,
  "conversations": [
    {"from": "human", "value": "Solve the problem."},
    {"from": "gpt", "value": "42"}
  ]
}
```

Notes:
- If a row has no `image`, avoid `<image>` placeholders; the loader strips them but they are usually misleading.
- The validator treats a missing answer turn as a hard failure.

## Image-root mapping

- `data_file_paths`, `image_folders`, and `reward_method` are colon-separated lists.
- The nth JSONL file is paired with the nth image root and the nth file-level reward method.
- The loader joins each relative image path with its paired root.
- Keep absolute paths out of the JSONL. Use relative paths only.
- If a row stores a list of images, each list element is joined separately and the order is preserved.

## Answer conventions

- Store the final answer only in `conversations[1].value`.
- The loader strips literal `<answer>` tags if present, but authors should not add commentary around the final answer.
- For label datasets, the answer is usually a short string such as `No Defect` or `Operation No Response`.
- For math and MCQ tasks, keep the final answer compact so the default scorer can normalize it cleanly.
- For bbox tasks, keep the answer shape aligned with the selected reward method: a plain box list, a JSON array of box objects, or `None` for empty detections.
- The current loader only uses the first two conversation turns.

## Mixed-schema checklist

Use this quick check before validation:
- every row has a usable second conversation turn
- single-image rows have one relative `image` string
- multi-image rows have a list of relative image strings
- the prompt contains either zero `<image>` placeholders or the same number of placeholders as images
- the paired image root actually contains the referenced files when existence checks are enabled
