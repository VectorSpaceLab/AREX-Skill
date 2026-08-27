# PaliGemma 2 API reference

This reference covers Maestro's PaliGemma 2 model route only. For dataset schemas and metric internals, use [datasets-and-metrics](../../datasets-and-metrics/).

## CLI route

Command name and options use underscores as exposed by the current Typer CLI:

```bash
maestro paligemma_2 train \
  --dataset ./dataset \
  --model_id google/paligemma2-3b-pt-224 \
  --revision refs/heads/main \
  --device auto \
  --optimization_strategy lora \
  --epochs 10 \
  --lr 1e-5 \
  --batch_size 4 \
  --accumulate_grad_batches 8 \
  --num_workers 0 \
  --output_dir ./training/paligemma_2 \
  --metrics edit_distance \
  --max_new_tokens 512 \
  --peft_advanced_params '{}'
```

Important CLI options:

| Option | Default | Meaning |
| --- | --- | --- |
| `--dataset` | required | Local JSONL dataset directory or resolvable dataset identifier. |
| `--model_id` | `google/paligemma2-3b-pt-224` | Hugging Face model id or local checkpoint/model directory. |
| `--revision` | `refs/heads/main` | Model revision passed to `from_pretrained`. |
| `--device` | `auto` | Parsed by Maestro's device helper; common values are `auto`, `cpu`, `cuda`, and `mps`. |
| `--optimization_strategy` | `lora` | One of `lora`, `qlora`, `freeze`, `none`. |
| `--cache_dir` | unset | Optional model-weight cache directory. |
| `--epochs` | `10` | Lightning training epochs. |
| `--lr` | `1e-5` | AdamW learning rate. |
| `--batch_size` | `4` | Train batch size. Lower this first on CUDA OOM. |
| `--accumulate_grad_batches` | `8` | Gradient accumulation steps. |
| `--val_batch_size` | train batch size | Validation batch size if set. |
| `--num_workers` | `0` | Train DataLoader workers. |
| `--val_num_workers` | train workers | Validation DataLoader workers if set. |
| `--output_dir` | `./training/paligemma_2` | Base output directory. A numbered run directory is created inside it. |
| `--metrics` | none | Repeat for each metric, e.g. `--metrics edit_distance --metrics bleu`. Text metrics are the normal PaliGemma choice. |
| `--max_new_tokens` | `512` | Generation length used in validation and as the training collate `max_length`. |
| `--random_seed` | unset | Optional reproducibility seed. |
| `--peft_advanced_params` | unset | JSON object string merged into default LoRA params; pass `'{}'` when using the CLI without custom PEFT params if the CLI reports an unbound local variable. |

The bundled helper can print a matching command without running it:

```bash
python scripts/build_paligemma_config.py --dataset ./dataset --metric edit_distance --emit cli
```

## Python training API

```python
from maestro.trainer.models.paligemma_2.core import PaliGemma2Configuration, train

config = PaliGemma2Configuration(
    dataset="./dataset",
    model_id="google/paligemma2-3b-pt-224",
    revision="refs/heads/main",
    device="auto",
    optimization_strategy="lora",
    epochs=10,
    lr=1e-5,
    batch_size=4,
    accumulate_grad_batches=8,
    output_dir="./training/paligemma_2",
    metrics=["edit_distance", "bleu"],
    max_new_tokens=512,
)
train(config)
```

`train(config)` also accepts a `dict` and converts it to `PaliGemma2Configuration`.

### `PaliGemma2Configuration` fields

| Field | Default | Notes |
| --- | --- | --- |
| `dataset: str` | required | Local dataset path or resolvable identifier. If no dataset is resolved, training returns without fitting. |
| `model_id: str` | `google/paligemma2-3b-pt-224` | Model id or local path passed to `load_model`. |
| `revision: str` | `refs/heads/main` | Passed to processor/model loading. |
| `device: str | torch.device` | `auto` | Parsed and checked for availability during configuration initialization. |
| `optimization_strategy` | `lora` | Literal: `lora`, `qlora`, `freeze`, or `none`. |
| `cache_dir: str | None` | `None` | Optional cache for model weights. |
| `epochs: int` | `10` | Lightning `max_epochs`. |
| `lr: float` | `1e-5` | AdamW learning rate. |
| `batch_size: int` | `4` | Training DataLoader batch size. |
| `accumulate_grad_batches: int` | `8` | Lightning gradient accumulation. |
| `val_batch_size: int | None` | `batch_size` | Filled in during `__post_init__` when omitted. |
| `num_workers: int` | `0` | Training DataLoader workers. |
| `val_num_workers: int | None` | `num_workers` | Filled in during `__post_init__` when omitted. |
| `output_dir: str` | `./training/paligemma_2` | Base directory; `train` replaces it with a new numbered run directory. |
| `metrics: list[BaseMetric] | list[str]` | `[]` | String names are parsed through the common metric registry. Use text metrics such as `edit_distance` and `bleu` for JSON/VQA/OCR text outputs. |
| `max_new_tokens: int` | `512` | Used in validation generation and train collate truncation. Increase for long JSON suffixes. |
| `random_seed: int | None` | `None` | Seeds reproducibility helpers when set. |
| `peft_advanced_params: dict | None` | `None` | Custom LoRA config overrides. |

## Optimization strategies

Use `OptimizationStrategy` from `maestro.trainer.models.paligemma_2.checkpoints` when calling `load_model` directly.

| Strategy | Value | Behavior |
| --- | --- | --- |
| `OptimizationStrategy.LORA` | `"lora"` | Loads the base PaliGemma model, applies PEFT LoRA, and prints trainable parameter counts. |
| `OptimizationStrategy.QLORA` | `"qlora"` | Same LoRA adapter path plus 4-bit `BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4", bnb_4bit_compute_type=torch.bfloat16)`. Requires bitsandbytes support and normally a CUDA-capable setup. |
| `OptimizationStrategy.FREEZE` | `"freeze"` | Loads the model to the selected device and freezes `vision_tower` and `multi_modal_projector`; the language model remains trainable. |
| `OptimizationStrategy.NONE` | `"none"` | Loads the model without adapters or freezing. This is the usual choice for simple checkpoint inference examples. |

Default LoRA parameters merged with `peft_advanced_params` when LoRA/QLoRA is selected:

```python
{
    "r": 8,
    "lora_alpha": 16,
    "lora_dropout": 0.05,
    "bias": "none",
    "target_modules": [
        "q_proj", "o_proj", "k_proj", "v_proj",
        "gate_proj", "up_proj", "down_proj",
    ],
    "task_type": "CAUSAL_LM",
}
```

## Checkpoint API

```python
from maestro.trainer.models.paligemma_2.checkpoints import (
    OptimizationStrategy,
    load_model,
    save_model,
)

processor, model = load_model(
    model_id_or_path="google/paligemma2-3b-pt-224",
    revision="refs/heads/main",
    device="auto",
    optimization_strategy=OptimizationStrategy.NONE,
    cache_dir=None,
)

save_model("./my-paligemma-checkpoint", processor=processor, model=model)
```

`load_model(...)` returns `(processor, model)`, not `(model, processor)`. During training, Maestro's checkpoint callback overwrites `checkpoints/latest` at the end of each epoch by calling `save_model`. The current callback does not implement a separate `best` checkpoint selector, so `latest` is the built-in checkpoint path to look for after a normal run.

## Inference API

```python
from maestro.trainer.common.datasets.jsonl import JSONLDataset
from maestro.trainer.models.paligemma_2.checkpoints import OptimizationStrategy, load_model
from maestro.trainer.models.paligemma_2.inference import predict

processor, model = load_model(
    model_id_or_path="./training/paligemma_2/1/checkpoints/latest",
    optimization_strategy=OptimizationStrategy.NONE,
)

ds = JSONLDataset(
    annotations_path="./dataset/test/annotations.jsonl",
    images_directory_path="./dataset/test",
)
image, entry = ds[0]
text = predict(model=model, processor=processor, image=image, prefix=entry["prefix"])
```

`predict(model, processor, image, prefix, device="auto", max_new_tokens=1024) -> str` accepts an image path, bytes, or a PIL image. It prepends `<image>` to the supplied `prefix`, preprocesses with the processor, calls `model.generate`, removes the prompt tokens from generated ids, and decodes the remaining text.

`predict_with_inputs(model, processor, input_ids, attention_mask, pixel_values, device, max_new_tokens=1024) -> list[str]` is the lower-level batched helper used by validation. It expects already-processed tensors and moves them to `device` before generation.

## Collate behavior

- `train_collate_fn(batch, processor, max_length=512)` reads `(image, entry)` pairs, builds `"<image>" + entry["prefix"]`, supplies `entry["suffix"]` as the processor suffix, pads, truncates only the suffix side, and returns `(input_ids, attention_mask, token_type_ids, pixel_values, labels)`.
- `evaluation_collate_fn(batch, processor)` also prepends `<image>`, pads prompts, and returns `(input_ids, attention_mask, pixel_values, prefixes, suffixes)` for validation generation/metric comparison.

Do not add `<image>` into dataset `prefix` fields unless you deliberately want duplicated image tokens for a custom experiment.
