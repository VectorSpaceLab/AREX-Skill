# Data Formats

This repo uses JSON arrays for all training workflows.

## Shared media rules

- Images and videos may be strings or lists of strings.
- Relative media paths are resolved against `--image_folder` / `--eval_image_folder` when the path does not already exist.
- Video inputs are processed through the multimodal utilities and may carry per-video metadata depending on the Qwen family.
- For video workflows, keep `fps` and `nframes` mutually exclusive.

## SFT / GRPO format

Each sample contains `conversations` with alternating human and assistant turns.

```json
{
  "id": "sample_001",
  "image": "image.jpg",
  "conversations": [
    {"from": "human", "value": "<image>\nWhat is shown here?"},
    {"from": "gpt", "value": "A cat sitting on a sofa."}
  ]
}
```

Reasoning-aware samples use a separate `reasoning` field on the assistant turn:

```json
{
  "from": "gpt",
  "reasoning": "The object has whiskers and a curled tail, so it is likely a cat.",
  "value": "A cat sitting on a sofa."
}
```

Rules:

- Do not manually write `<think>...</think>` into `value` when the repo’s reasoning mode is enabled.
- `Qwen3-VL-*-Thinking` requires a non-empty `reasoning` field on every assistant turn when reasoning is enabled.
- `Qwen3.5` may mix reasoning and non-reasoning samples.

## DPO format

Each record contains a prompt and paired answers:

```json
{
  "id": "sample_dpo_001",
  "image": "image.jpg",
  "prompt": "<image>\nDescribe the scene.",
  "chosen": "A damaged car is half submerged in a pool.",
  "rejected": "A car is parked beside water."
}
```

Reasoning-aware DPO adds paired reasoning fields:

- `chosen_reasoning`
- `rejected_reasoning`

Rules:

- If one reasoning field is present, the other must be present too.
- `Qwen3-VL-*-Thinking` requires both reasoning fields when reasoning is enabled.
- `Qwen3.5` may omit both reasoning fields even when reasoning mode is enabled.

## Classification format

Each record contains a media item, an optional prompt, and a label string:

```json
{
  "id": "sample_cls_001",
  "image": "image.jpg",
  "prompt": "Question: What is in the image? Options: A, B",
  "label": "A"
}
```

Rules:

- The repo’s default label map is `A -> 0`, `B -> 1`.
- If `prompt` is absent, the dataset code inserts a default user message.
- Image or video data may be single-item or list-valued.

## Validation checklist

- The dataset type matches the workflow you plan to run.
- Media paths resolve correctly from the declared folder.
- Reasoning fields follow the model-family rules.
- Classification labels are valid for the expected class map.
