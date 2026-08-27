# Qwen2.5-VL workflows

This file distills the two supported Qwen flows in Maestro: JSON extraction and COCO object detection.

## Conversation template behavior

The Qwen helpers build a chat conversation rather than a raw prompt string.

- `format_conversation(...)` inserts an optional `system_message` as the first turn.
- The user turn always contains the image plus the textual prefix.
- Training-only supervision adds an assistant suffix as the final turn.
- `processor.apply_chat_template(...)` renders that message list into the Qwen prompt text.
- `predict(...)` adds `add_generation_prompt=True`, which opens the assistant turn for generation.

Practical rule: if you want stable output shape, keep the same `system_message` and prompt wording in training and inference. If you are already using the provided collators and `predict(...)`, do not hand-build the chat string yourself.

## Workflow 1: JSON extraction

Use this path when the target output is structured JSON rather than boxes.

### Data assumptions

- The dataset is accessible locally or through a resolvable Roboflow identifier.
- Each example pairs an image with a JSON target string in the suffix.
- The target JSON should be valid and parseable with `json.loads(...)`.

### Suggested prompt

A task-specific system message should explicitly tell the model to emit only JSON. The cookbook recipe uses a prompt that asks for structured extraction from palette-manifest imagery and forbids extra prose.

### Train

```bash
maestro qwen_2_5_vl train \
  --dataset /path/to/jsonl_dataset \
  --model_id Qwen/Qwen2.5-VL-3B-Instruct \
  --revision refs/heads/main \
  --optimization_strategy qlora \
  --epochs 10 \
  --batch_size 4 \
  --lr 2e-4 \
  --metrics edit_distance \
  --metrics bleu \
  --system_message "You are a Vision Language Model specialized in extracting structured data from images. Provide only the JSON output based on the extracted information."
```

Python equivalent:

```python
from maestro.trainer.models.qwen_2_5_vl.core import train

config = {
    "model_id": "Qwen/Qwen2.5-VL-3B-Instruct",
    "revision": "refs/heads/main",
    "dataset": dataset.location,
    "system_message": SYSTEM_MESSAGE,
    "epochs": 10,
    "batch_size": 4,
    "num_workers": 10,
    "optimization_strategy": "qlora",
    "metrics": ["edit_distance", "bleu"],
}

train(config)
```

### Validate

- Load the latest checkpoint with `load_model(...)`.
- Call `predict(...)` on a sample image and prefix.
- Parse the generated suffix with `json.loads(...)`.
- Inspect the saved metric plots for loss and text metrics.

### Notes

- `max_new_tokens` defaults to 1024; reduce it if outputs are clipped or increase it if the model cuts off long JSON.
- If you change the system message, keep the same wording at inference time unless you have a specific reason to vary it.

## Workflow 2: COCO object detection

Use this path when the target output is a Qwen detection JSON array derived from COCO annotations.

### Data assumptions

- The dataset is COCO-shaped and can be represented with `COCODataset` plus `COCOVLMAdapter`.
- The dataset skill owns the split and annotation validation; this sub-skill only owns the Qwen-specific prompt and suffix format.
- The class names in the dataset should match the class names you want in the Qwen labels.

### Suggested pixel bounds

The source default is `min_pixels=256*28*28` and `max_pixels=1280*28*28`.
The object-detection cookbook overrides `min_pixels` to `512*28*28` for its recipe.

Keep the same pixel bounds in:

- `load_model(...)`
- `train(...)`
- `detections_to_suffix_formatter(...)`
- any parsing path that uses `smart_resize(...)` or `sv.Detections.from_vlm(...)`

### Train

```bash
maestro qwen_2_5_vl train \
  --dataset /path/to/coco_dataset \
  --model_id Qwen/Qwen2.5-VL-3B-Instruct \
  --revision refs/heads/main \
  --optimization_strategy qlora \
  --epochs 20 \
  --batch_size 2 \
  --lr 2e-4 \
  --metrics edit_distance \
  --metrics mean_average_precision \
  --system_message "You are a helpful assistant." \
  --min_pixels 401408 \
  --max_pixels 1003520
```

Python equivalent:

```python
from functools import partial

from maestro.trainer.common.datasets.coco import COCODataset, COCOVLMAdapter
from maestro.trainer.models.qwen_2_5_vl.core import train
from maestro.trainer.models.qwen_2_5_vl.detection import (
    detections_to_prefix_formatter,
    detections_to_suffix_formatter,
)

coco_dataset = COCODataset(
    annotations_path=f"{dataset.location}/test/_annotations.coco.json",
    images_directory_path=f"{dataset.location}/test",
)

qwen_dataset = COCOVLMAdapter(
    coco_dataset=coco_dataset,
    prefix_formatter=detections_to_prefix_formatter,
    suffix_formatter=partial(
        detections_to_suffix_formatter,
        min_pixels=512 * 28 * 28,
        max_pixels=1280 * 28 * 28,
    ),
)

config = {
    "dataset": dataset.location,
    "system_message": "You are a helpful assistant.",
    "min_pixels": 512 * 28 * 28,
    "max_pixels": 1280 * 28 * 28,
    "epochs": 20,
    "batch_size": 2,
    "optimization_strategy": "qlora",
    "metrics": ["edit_distance", "mean_average_precision"],
}

train(config)
```

### Validate

- Load the saved checkpoint with the same `min_pixels` / `max_pixels` pair.
- Generate one image with `predict(...)`.
- Parse both the target and prediction with `sv.Detections.from_vlm(...)` using `sv.VLM.QWEN_2_5_VL`.
- Compare predictions and targets with `mean_average_precision` or your own post-processing.

### Notes

- `system_message` can be a short generic assistant message or a task-specific instruction.
- If the model emits extra prose around the JSON array, tighten the system prompt and keep `add_generation_prompt=True` through `predict(...)`.
- For visual inspection, annotate predictions and targets with a comparison annotator after parsing.

## LoRA / QLoRA / none summary

- `lora`: apply PEFT adapters only.
- `qlora`: apply PEFT adapters plus 4-bit quantization through BitsAndBytes.
- `none`: load the base model without PEFT wrapping.

Use `qlora` when you want the memory-efficient training path shown in the cookbook; use `none` when you only want a plain checkpoint load or CPU-side inspection.
