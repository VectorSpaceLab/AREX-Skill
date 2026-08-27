# Florence-2 API reference

This reference captures the Maestro Florence-2 surfaces needed to construct commands and Python calls from the generated skill alone.

## CLI surface

The installed CLI exposes the model group and one training command:

```bash
maestro florence_2 --help
maestro florence_2 train --help
```

Use the exact option names shown here; the current CLI exposes underscore option spellings.

```bash
maestro florence_2 train \
  --dataset ./dataset \
  --model_id microsoft/Florence-2-base-ft \
  --revision refs/pr/20 \
  --device auto \
  --optimization_strategy lora \
  --cache_dir ./model-cache \
  --epochs 10 \
  --lr 1e-5 \
  --batch_size 4 \
  --accumulate_grad_batches 8 \
  --val_batch_size 4 \
  --num_workers 0 \
  --val_num_workers 0 \
  --output_dir ./training/florence_2 \
  --metrics edit_distance \
  --metrics mean_average_precision \
  --max_new_tokens 1024 \
  --random_seed 42 \
  --peft_advanced_params '{}'
```

Notes:

- `--dataset` may be a local dataset root or a Roboflow identifier. Route layout and credential details to [datasets-and-metrics](../../datasets-and-metrics/SKILL.md).
- `--optimization_strategy` must be one of `lora`, `freeze`, or `none`.
- `--metrics` can be repeated. Useful names include `edit_distance`, `bleu`, and `mean_average_precision`; route metric behavior to [datasets-and-metrics](../../datasets-and-metrics/references/metrics-and-utilities.md).
- `--peft_advanced_params` is a JSON dictionary for LoRA parameters. Passing `'{}'` is a safe no-op override when using default LoRA settings and also works around a current CLI edge case where the omitted argument may leave the parsed variable undefined.
- There is no dry-run flag; the command starts training after printing the parsed configuration.

## Training API

```python
from maestro.trainer.models.florence_2.core import Florence2Configuration, train

config = Florence2Configuration(
    dataset="./dataset",
    model_id="microsoft/Florence-2-base-ft",
    revision="refs/pr/20",
    device="auto",
    optimization_strategy="lora",
    cache_dir="./model-cache",
    epochs=10,
    lr=1e-5,
    batch_size=4,
    accumulate_grad_batches=8,
    val_batch_size=None,
    num_workers=0,
    val_num_workers=None,
    output_dir="./training/florence_2",
    metrics=["edit_distance", "mean_average_precision"],
    max_new_tokens=1024,
    random_seed=42,
    peft_advanced_params=None,
)
train(config)
```

Equivalent dictionary style:

```python
from maestro.trainer.models.florence_2.core import train

train({
    "dataset": "./dataset",
    "model_id": "microsoft/Florence-2-base-ft",
    "revision": "refs/pr/20",
    "device": "auto",
    "optimization_strategy": "lora",
    "epochs": 10,
    "batch_size": 4,
    "metrics": ["edit_distance", "mean_average_precision"],
})
```

`Florence2Configuration` validates the device during initialization, resolves metric strings through Maestro's metric registry, and fills `val_batch_size` and `val_num_workers` from their training counterparts when omitted.

## Configuration fields

| Field | Default | Use |
| --- | --- | --- |
| `dataset` | required | Local dataset root or Roboflow identifier. |
| `model_id` | `microsoft/Florence-2-base-ft` | Hugging Face id or local checkpoint/model directory. |
| `revision` | `refs/pr/20` | Model revision passed to Hugging Face loaders. |
| `device` | `auto` | `auto`, `cpu`, `cuda`, `mps`, or a `torch.device`. |
| `optimization_strategy` | `lora` | `lora`, `freeze`, or `none`; Florence-2 does not support QLoRA in Maestro. |
| `cache_dir` | `None` | Optional model cache directory. |
| `epochs` | `10` | Training epochs. |
| `lr` | `1e-5` | AdamW learning rate. |
| `batch_size` | `4` | Train batch size. |
| `accumulate_grad_batches` | `8` | Lightning gradient accumulation steps. |
| `val_batch_size` | `None` | Validation/test batch size; defaults to `batch_size`. |
| `num_workers` | `0` | Train DataLoader workers. |
| `val_num_workers` | `None` | Validation/test workers; defaults to `num_workers`. |
| `output_dir` | `./training/florence_2` | Base directory; Maestro creates numbered run directories under it. |
| `metrics` | `[]` | Metric names or metric objects. |
| `max_new_tokens` | `1024` | Generation length used during validation and inference helpers. |
| `random_seed` | `None` | Optional reproducibility seed. |
| `peft_advanced_params` | `None` | Optional dict merged into default LoRA PEFT parameters when `lora` is selected. |

## Model checkpoint API

```python
from maestro.trainer.models.florence_2.checkpoints import (
    OptimizationStrategy,
    load_model,
    save_model,
)

processor, model = load_model(
    model_id_or_path="microsoft/Florence-2-base-ft",
    revision="refs/pr/20",
    device="auto",
    optimization_strategy=OptimizationStrategy.NONE,
    peft_advanced_params=None,
    cache_dir="./model-cache",
)

save_model(target_dir="./training/florence_2/export", processor=processor, model=model)
```

Exact callable shapes:

```text
load_model(model_id_or_path='microsoft/Florence-2-base-ft', revision='refs/pr/20', device='auto', optimization_strategy=OptimizationStrategy.NONE, peft_advanced_params=None, cache_dir=None) -> (processor, model)
save_model(target_dir, processor, model) -> None
```

`load_model` always uses Hugging Face `AutoProcessor` and `AutoModelForCausalLM` with `trust_remote_code=True`. When `OptimizationStrategy.LORA` is selected it builds a PEFT LoRA model; otherwise it loads the base model and optionally freezes the vision tower for `FREEZE`.

## Optimization strategies

```python
from maestro.trainer.models.florence_2.checkpoints import OptimizationStrategy

OptimizationStrategy.LORA.value    # "lora"
OptimizationStrategy.FREEZE.value  # "freeze"
OptimizationStrategy.NONE.value    # "none"
```

Default LoRA parameters used by Maestro:

```python
{
    "r": 8,
    "lora_alpha": 16,
    "lora_dropout": 0.05,
    "bias": "none",
    "target_modules": ["q_proj", "o_proj", "k_proj", "v_proj", "linear", "Conv2d", "lm_head", "fc2"],
    "task_type": "CAUSAL_LM",
}
```

Use `peft_advanced_params` only for LoRA. Keep it a JSON/dict accepted by `peft.LoraConfig`.

## Inference API

```python
from maestro.trainer.models.florence_2.inference import predict, predict_with_inputs

text = predict(
    model=model,
    processor=processor,
    image=image,              # PIL.Image.Image
    prefix="<OD>",
    device="auto",
    max_new_tokens=1024,
)
```

Exact callable shapes:

```text
predict(model, processor, image, prefix, device='auto', max_new_tokens=1024) -> str
predict_with_inputs(model, processor, input_ids, pixel_values, device, max_new_tokens=1024) -> list[str]
```

`predict` preprocesses one PIL image and text prefix, then calls `model.generate(do_sample=False, num_beams=3)`. It returns the generated text string; post-processing depends on the task prefix and is covered in [workflows](workflows.md) and [detection formats](detection-formats.md).

## Object-detection formatter API

```python
from maestro.trainer.models.florence_2.detection import (
    detections_to_prefix_formatter,
    detections_to_suffix_formatter,
    result_to_detections_formatter,
)

prefix = detections_to_prefix_formatter(xyxy, class_id, classes, resolution_wh)
suffix = detections_to_suffix_formatter(xyxy, class_id, classes, resolution_wh)
boxes, class_ids = result_to_detections_formatter(suffix, resolution_wh, classes)
```

Exact callable shapes:

```text
detections_to_prefix_formatter(xyxy, class_id, classes, resolution_wh) -> str
# Always returns "<OD>".

detections_to_suffix_formatter(xyxy, class_id, classes, resolution_wh) -> str
# Converts pixel xyxy boxes to normalized <loc_*> text.

result_to_detections_formatter(text, resolution_wh, classes=None) -> (boxes, class_ids)
# Converts Florence text back to pixel xyxy boxes and int class ids.
```

See [detection formats](detection-formats.md) for the exact text grammar, round-trip behavior, and smoke checks.

## Collate functions used by training

```python
from maestro.trainer.models.florence_2.loaders import train_collate_fn, evaluation_collate_fn
```

- `train_collate_fn(batch, processor)` reads each entry's `prefix` and `suffix`, processes images and prefixes together, and tokenizes suffixes as labels.
- `evaluation_collate_fn(batch, processor)` returns input tensors plus original images, prefixes, and suffixes so validation can generate predictions and compute metrics.

Most users do not call these directly; Maestro wires them into `create_data_loaders` during `train`.
