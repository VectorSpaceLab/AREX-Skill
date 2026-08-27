# Florence-2 workflows

Use these recipes to construct Maestro Florence-2 fine-tuning, load/save, and inference workflows. They are distilled from the package docs, model source, CLI help, and the object-detection cookbook, but they are self-contained and do not depend on the original notebook.

## Workflow 1: choose data and task shape

Florence-2 training consumes entries with a text `prefix`, a text `suffix`, and an image.

- JSONL datasets already provide `prefix`/`suffix` pairs. Route exact JSONL file names, split rules, and validation to [datasets-and-metrics data formats](../../datasets-and-metrics/references/data-formats.md).
- COCO object-detection datasets need model-specific formatter callbacks. Maestro's Florence train path supplies `detections_to_prefix_formatter` and `detections_to_suffix_formatter` automatically; manual DataLoader construction must pass those functions explicitly.
- Roboflow identifiers can be resolved by Maestro, but that path requires `ROBOFLOW_API_KEY` and may download data. Prefer a local dataset root for reproducible runs.

For object detection, the target prompt is always `<OD>` and the target suffix is Florence's normalized `<loc_*>` text. See [detection formats](detection-formats.md).

## Workflow 2: choose an optimization strategy

| Strategy | Use when | Notes |
| --- | --- | --- |
| `lora` | Default efficient fine-tuning. | Uses PEFT LoRA with Maestro's default target modules unless `peft_advanced_params` overrides them. |
| `freeze` | You want to tune while freezing the vision tower. | The loader marks `model.vision_tower` parameters as not trainable. |
| `none` | Full model load, inference from an exported checkpoint, or a baseline run. | Highest trainable-parameter footprint if used for training. |

Do **not** select `qlora` for Florence-2. QLoRA is used by other Maestro model families, not this one.

## Workflow 3: CLI fine-tuning command

This command starts training; it is not a dry run.

```bash
maestro florence_2 train \
  --dataset ./datasets/cards-coco \
  --model_id microsoft/Florence-2-base-ft \
  --revision refs/pr/20 \
  --device auto \
  --optimization_strategy lora \
  --epochs 10 \
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

Adjust for hardware:

- Reduce `--batch_size` and `--val_batch_size` first when memory is tight.
- Keep `--optimization_strategy lora` for the lowest typical fine-tuning footprint available in this Florence path.
- Use `--device cuda` only when CUDA is available; otherwise prefer `--device auto` or `--device cpu` for tiny smoke experiments.
- Use `--cache_dir` when model files should be stored in a specific cache location.

When using a custom LoRA configuration, pass a JSON object:

```bash
maestro florence_2 train \
  --dataset ./datasets/cards-coco \
  --optimization_strategy lora \
  --peft_advanced_params '{"r": 16, "lora_alpha": 32, "lora_dropout": 0.05}'
```

The JSON must be accepted by `peft.LoraConfig` after Maestro merges it with its default Florence LoRA parameters.

## Workflow 4: Python fine-tuning API

```python
from maestro.trainer.models.florence_2.core import Florence2Configuration, train

config = Florence2Configuration(
    dataset="./datasets/cards-coco",
    model_id="microsoft/Florence-2-base-ft",
    revision="refs/pr/20",
    device="auto",
    optimization_strategy="lora",
    epochs=10,
    batch_size=4,
    accumulate_grad_batches=8,
    metrics=["edit_distance", "mean_average_precision"],
    output_dir="./training/florence_2",
    random_seed=42,
)
train(config)
```

Dictionary style is also valid:

```python
from maestro.trainer.models.florence_2.core import train

train({
    "dataset": "./datasets/cards-coco",
    "model_id": "microsoft/Florence-2-base-ft",
    "revision": "refs/pr/20",
    "device": "auto",
    "optimization_strategy": "lora",
    "epochs": 10,
    "batch_size": 4,
    "metrics": ["edit_distance", "mean_average_precision"],
    "output_dir": "./training/florence_2",
})
```

What the training API does:

1. Converts dictionaries to `Florence2Configuration`.
2. Seeds reproducibility if `random_seed` is set.
3. Creates a new numbered run directory under `output_dir`.
4. Loads the processor and model using `load_model`.
5. Resolves the dataset as a local path or Roboflow identifier.
6. Creates JSONL or COCO DataLoaders; for COCO it attaches Florence `<OD>` prefix and suffix formatters.
7. Runs a Lightning trainer and saves checkpoints under the run directory's `checkpoints` subdirectory.
8. Saves metric plots under the run directory's `metrics` subdirectory.

## Workflow 5: load a model or checkpoint

For the default model:

```python
from maestro.trainer.models.florence_2.checkpoints import OptimizationStrategy, load_model

processor, model = load_model(
    model_id_or_path="microsoft/Florence-2-base-ft",
    revision="refs/pr/20",
    device="auto",
    optimization_strategy=OptimizationStrategy.NONE,
)
```

For a fine-tuned checkpoint exported by Maestro:

```python
from maestro.trainer.models.florence_2.checkpoints import OptimizationStrategy, load_model

processor, model = load_model(
    model_id_or_path="./training/florence_2/1/checkpoints/latest",
    optimization_strategy=OptimizationStrategy.NONE,
    device="auto",
)
```

Use `OptimizationStrategy.NONE` for ordinary inference from a saved checkpoint unless you intentionally need to rebuild a LoRA-wrapped model for further training.

To save a model/processor pair:

```python
from maestro.trainer.models.florence_2.checkpoints import save_model

save_model(target_dir="./exported-florence-2", processor=processor, model=model)
```

## Workflow 6: run inference

For object detection, pass `<OD>` as the prefix.

```python
from PIL import Image
from maestro.trainer.models.florence_2.inference import predict

image = Image.open("./datasets/cards-coco/test/example.jpg").convert("RGB")
generated_text = predict(
    model=model,
    processor=processor,
    image=image,
    prefix="<OD>",
    device="auto",
    max_new_tokens=1024,
)
```

You can parse the generated text with Maestro's formatter if the output uses the Florence training suffix grammar:

```python
from maestro.trainer.models.florence_2.detection import result_to_detections_formatter

boxes, class_ids = result_to_detections_formatter(
    text=generated_text,
    resolution_wh=image.size,
    classes=["card", "chip", "dealer button"],
)
```

If you are using the Hugging Face Florence processor's task post-processing, keep the same task and image size:

```python
result = processor.post_process_generation(
    text=generated_text,
    task="<OD>",
    image_size=(image.width, image.height),
)
```

Use one post-processing path consistently in a project. Maestro's formatter is deterministic and is also what its COCO training adapter uses; processor post-processing may return a task-specific dictionary suitable for downstream visualization libraries.

## Workflow 7: validate before expensive runs

Run these checks before launching a long training job:

```bash
maestro florence_2 train --help
python sub-skills/florence-2/scripts/smoke_florence_detection_format.py --json
```

Then verify dataset and metrics separately with [datasets-and-metrics](../../datasets-and-metrics/SKILL.md). The safe checks do not prove that Hugging Face downloads, Roboflow downloads, GPU memory, or full training will succeed; they only reduce avoidable command/API/formatter mistakes.
