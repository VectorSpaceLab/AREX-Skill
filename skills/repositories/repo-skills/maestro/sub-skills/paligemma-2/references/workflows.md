# PaliGemma 2 workflows

These workflows are distilled into safe operating guidance. They are not notebook links. Full fine-tuning still requires the user's own dataset, model access, storage, and suitable hardware.

## 1. Choose task framing

PaliGemma 2 in Maestro is a text-generation VLM recipe. Put the task instruction in each JSONL entry's `prefix` and the expected answer in `suffix`.

Good PaliGemma 2 task fits:

- **JSON extraction**: `prefix`: `extract document data in JSON format`; `suffix`: a serialized JSON object string.
- **VQA**: `prefix`: a natural language question; `suffix`: a concise answer string.
- **OCR-style extraction**: `prefix`: `read equation in LATEX` or another extraction instruction; `suffix`: the target transcription.

PaliGemma 2 can generate detection-like text if the dataset is authored that way, but Maestro does not provide PaliGemma-specific detection formatter/parsing APIs. If the user needs source-backed COCO/detection formatter helpers, route to Florence-2 or Qwen2.5-VL sibling skills.

## 2. Prepare and validate data

Expected local layout:

```text
dataset/
  train/
    annotations.jsonl
    image1.jpg
  valid/
    annotations.jsonl
    image2.jpg
  test/
    annotations.jsonl
    image3.jpg
```

Each JSONL line needs at least:

```json
{"image":"image1.jpg","prefix":"extract document data in JSON format","suffix":"{\"invoice_id\":\"A-42\",\"total\":\"19.99\"}"}
```

For JSON extraction, validate `suffix` strings before training:

```python
import json

suffix = entry["suffix"]
json.loads(suffix)  # should succeed for structured JSON targets
```

Use [datasets-and-metrics](../../datasets-and-metrics/) for full JSONL validation, Roboflow identifier handling, image existence checks, and metric availability. PaliGemma-specific training only consumes the dataset after it has been resolved by Maestro's common dataset utilities.

Important prompt rule: do **not** put `<image>` in normal dataset prefixes. Maestro prepends `<image>` internally in training collate, evaluation collate, and direct prediction.

## 3. Generate a safe config without training

From this sub-skill directory, generate a Python config JSON:

```bash
python scripts/build_paligemma_config.py \
  --dataset ./dataset \
  --optimization-strategy lora \
  --metric edit_distance \
  --metric bleu \
  --max-new-tokens 512 \
  --emit json > paligemma_config.json
```

Or generate a CLI command string:

```bash
python scripts/build_paligemma_config.py \
  --dataset ./dataset \
  --optimization-strategy qlora \
  --batch-size 1 \
  --accumulate-grad-batches 8 \
  --metric edit_distance \
  --emit cli
```

The helper only prints text. It does not import Maestro, download models, read credentials, or start training.

## 4. Fine-tune with the Python API

Use Python when you need explicit config control or want to avoid CLI argument parsing edge cases:

```python
from maestro.trainer.models.paligemma_2.core import train

config = {
    "dataset": "./dataset",
    "model_id": "google/paligemma2-3b-pt-224",
    "revision": "refs/heads/main",
    "device": "auto",
    "optimization_strategy": "lora",
    "epochs": 10,
    "lr": 1e-5,
    "batch_size": 4,
    "accumulate_grad_batches": 8,
    "output_dir": "./training/paligemma_2",
    "metrics": ["edit_distance", "bleu"],
    "max_new_tokens": 512,
}

train(config)
```

Runtime expectations:

1. `PaliGemma2Configuration` checks the requested device and parses metric strings.
2. `train` creates a new numbered run directory under `output_dir`.
3. `load_model` loads processor/model and applies the selected optimization strategy.
4. Maestro resolves the dataset, builds train/valid/test loaders, logs one sample prefix/suffix, and starts Lightning training.
5. At each epoch end, `checkpoints/latest` is refreshed.
6. On fit end, metric plots are saved under the run's `metrics/` directory.

## 5. Fine-tune with the CLI

Use the CLI when command-line reproducibility is more important than Python integration:

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
  --output_dir ./training/paligemma_2 \
  --metrics edit_distance \
  --metrics bleu \
  --max_new_tokens 512 \
  --peft_advanced_params '{}'
```

Notes:

- Use the CLI option names exposed by `maestro paligemma_2 train --help`; the current route uses underscore option names such as `--batch_size` and `--optimization_strategy`.
- Repeat `--metrics` for multiple metrics.
- Passing `--peft_advanced_params '{}'` is harmless for default LoRA/QLoRA and avoids a current CLI edge case where the parsed PEFT dict may be undefined when the option is omitted.

## 6. Select an optimization strategy

| User situation | Strategy | Practical guidance |
| --- | --- | --- |
| Default efficient fine-tuning | `lora` | Use first unless the user specifically wants quantization or full/freeze behavior. Works with PEFT LoRA defaults. |
| Large model memory pressure on CUDA | `qlora` | Requires bitsandbytes support and normally CUDA. Start with `batch_size=1`, keep accumulation, and monitor memory. |
| Freeze visual front-end | `freeze` | Freezes `vision_tower` and `multi_modal_projector`; useful when adapting language-side behavior while preserving image features. |
| Full model load/no adapters | `none` | Use for simple inference/loading or intentional full-parameter training experiments; memory requirements are higher for training. |

## 7. Load a checkpoint and predict

After a run, look for the latest checkpoint under the numbered run directory:

```text
./training/paligemma_2/1/checkpoints/latest
```

Load and predict:

```python
import json

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

generated_suffix = predict(
    model=model,
    processor=processor,
    image=image,
    prefix=entry["prefix"],
    max_new_tokens=1024,
)

# For JSON extraction tasks only:
parsed = json.loads(generated_suffix)
```

`predict` prepends `<image>` internally. Pass the same natural-language prefix shape used during training.

## 8. Validate training outputs

Minimum post-run checks:

1. Confirm a numbered run directory was created under `./training/paligemma_2` or the configured `output_dir`.
2. Confirm `checkpoints/latest` exists.
3. Confirm metric plots exist for tracked metrics under `metrics/`.
4. For JSON extraction, run a few `predict` calls and `json.loads` the generated text.
5. Compare generated strings against `entry["suffix"]`; for text extraction use `edit_distance`, and for longer text use `bleu` if available.

If outputs are truncated or invalid JSON, increase `max_new_tokens`, reduce prompt/suffix length, and inspect the first logged train/validation examples for unintended placeholder text or duplicated `<image>` tokens.
