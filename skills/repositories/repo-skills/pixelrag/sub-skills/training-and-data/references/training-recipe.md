# Training Recipe

## Released adapter path

Most users do not need to retrain. The published adapter is:

- Base model: `Qwen/Qwen3-VL-Embedding-2B`
- Adapter repo: `Chrisyichuan/wiki-screenshot-embedding-lora`
- Best checkpoint: `lora_vit/ckpt200`

Example pattern:

```python
from peft import PeftModel
from transformers import AutoModel

base = AutoModel.from_pretrained("Qwen/Qwen3-VL-Embedding-2B")
model = PeftModel.from_pretrained(
    base,
    "Chrisyichuan/wiki-screenshot-embedding-lora",
    subfolder="lora_vit/ckpt200",
)
```

Use the same adapter/index condition when comparing retrieval results.

## Separate uv project

Training lives in a separate project:

```bash
cd train
uv sync
```

Pinned expectations from the training project include:

- Python `>=3.12,<3.14`
- PyTorch `2.9.1` from CUDA 12.9 wheel source
- `transformers==4.57.1`
- `nvidia-cudnn-cu12==9.20.0.48`
- PEFT, Accelerate, FAISS CPU, W&B, HF Hub, Qwen VL utils, datasets, OpenAI

Always run training/eval commands with `uv run` from inside `train/`.

## Resource requirements

Full reproduction can require:

- One GPU with about 40GB VRAM for training.
- A separate GPU for vLLM reader during QA eval.
- About 95GB free disk for image data and larger scratch during extraction.
- OpenAI key for QA grading.
- W&B key or `WANDB_MODE=offline`.
- Optional HF token for large dataset downloads.

## Data needed for the documented run

- `screenshot-training-natural-filtered-v2`: training/eval/test query-image pairs with hard negatives and image shards.
- `screenshot-training/test_miniv8`: 400 SimpleQA questions and candidate tiles.
- `text-qa-pair`: text warmup data.

Images must be extracted so JSONL relative paths resolve, typically under each dataset directory's `images/` or `tiles/` layout.

## Training command shape

The full command is intentionally not bundled as a one-line script because it depends on data roots, GPUs, W&B policy, eval cadence, and reader endpoint. Before launching:

1. Verify `uv sync` completed in `train/`.
2. Verify dataset files and image paths with the bundled checker or a small Python sample.
3. Start the vLLM reader if QA eval is enabled.
4. Verify OpenAI key/base URL with a tiny eval or disabled/offline eval plan.
5. Launch with explicit `CUDA_VISIBLE_DEVICES`, output directory, data roots, and logging mode.

## Evaluation during training

QA score around the documented run depends on retrieval plus reader plus OpenAI grading. If OpenAI grading fails, the training loop may continue but QA score can appear as zero. Always inspect eval JSONL/logs before concluding the model is bad.
