# Embedding Training Configuration

RAG-Retrieval embedding training is configured by passing `--config` to `train_embedding.py`. This skill bundles the inspected training snapshot under `scripts/training_bundle/`; the parser defines defaults and then overwrites them with keys from YAML. Unknown YAML keys are not rejected by the parser, so validate carefully before launch.

## Source-Checkout Boundary

Treat `train_embedding.py`, `data.py`, `model.py`, `model_distill.py`, and their config examples as bundled source-code snapshots, not installed package APIs. A future agent should default to the bundled snapshot and ask for a checkout path only when the user wants current repository code.

Do not embed local machine paths into reusable docs or committed configs. In working YAML files, replace example-relative values such as `../../../example_data/...` with user-controlled dataset, teacher-array, and output paths.

## `training_embedding.yaml`

Typical keys for standard fine-tuning:

```yaml
model_name_or_path: "BAAI/bge-base-zh-v1.5"
train_type: "train"
train_dataset: "/path/to/train.jsonl"
neg_nums: 5
query_max_len: 128
passage_max_len: 512
shuffle: true
output_dir: "/path/to/output"
save_on_epoch_end: 1
num_max_checkpoints: 5
temperature: 0.02
epochs: 2
lr: 2e-5
batch_size: 8
seed: 666
warmup_proportion: 0.1
gradient_accumulation_steps: 3
mixed_precision: "bf16"
all_gather: true
gradient_checkpointing: true
use_mrl: false
mrl_dims: "128, 256, 512, 768, 1024, 1280, 1536, 1792"
log_interval: 10
log_with: "wandb"
```

Key notes:

- `train_type` must be `train` for pair, triplet, and pair-score JSONL.
- `train_dataset` points to JSONL with one of the supported schemas.
- `neg_nums` affects only triplet records with `neg`.
- `all_gather` gathers positives/negatives across distributed processes for more in-batch negatives.
- `temperature` controls softmax sharpness for pair/triplet and pair-score losses.
- `passage_max_len` is not used by distillation text data, but matters for pair/triplet/pair-score training.

## `distill_embedding.yaml`

Typical keys for teacher-embedding distillation:

```yaml
model_name_or_path: "BAAI/bge-base-zh-v1.5"
train_type: "distill"
train_dataset: "/path/to/distill_text.jsonl"
train_dataset_vec: "/path/to/teacher_embeddings.mmap"
query_max_len: 512
teacher_embedding_dim: 3584
shuffle: false
output_dir: "/path/to/output_distill"
save_on_epoch_end: 1
num_max_checkpoints: 5
epochs: 2
lr: 1e-4
batch_size: 128
seed: 666
warmup_proportion: 0.05
gradient_accumulation_steps: 1
mixed_precision: "bf16"
gradient_checkpointing: true
use_mrl: true
mrl_dims: "256,512,1024,1536,2048,2560,3072,3584"
log_interval: 10
log_with: "wandb"
```

Key notes:

- `train_type` must be `distill`.
- `train_dataset` is text JSONL with `query` rows.
- `train_dataset_vec` is the teacher embedding array/memmap in the same row order.
- `teacher_embedding_dim` must match the teacher vector width. The source parser also accepts the misspelled compatibility key `teacher_emebedding_dim` when `teacher_embedding_dim` is absent.
- `shuffle: false` is a safer default for distillation because row order must match teacher embeddings. Shuffling in the DataLoader happens after the dataset pairs each query with its embedding by index, so it is not necessarily invalid, but it makes debugging order issues harder.

## MRL Options

MRL means Matryoshka Representation Learning. In this source workflow:

- Standard training with `use_mrl: true` may remove a final normalize module and add or reuse a `Dense` layer whose output width is at least `max(mrl_dims)`.
- Distillation adds a dense projection to `teacher_embedding_dim` and computes losses across each listed `mrl_dims` slice.
- `mrl_dims` is parsed from a comma-separated string of integers.
- Dimensions should be positive, unique, increasing for readability, and no larger than the output dimension being trained.
- For distillation, `max(mrl_dims)` should be less than or equal to `teacher_embedding_dim`.

Use validation to catch malformed MRL strings before model construction:

```bash
python skills/rag-retrieval/sub-skills/embedding-training/scripts/validate_embedding_training_config.py --config /path/to/config.yaml
```

## Logging

The source parser default for `log_with` is `wandb`. YAML examples also use `wandb`.

Practical guidance:

- Use `log_with: "tensorboard"` when Weights & Biases is unavailable or should not be contacted.
- Use a local/no-network logging setup for offline or restricted environments.
- Keep `log_interval` positive; the trainer logs when `batch_index % log_interval == 0`.
- The trainer writes run/checkpoint files under `output_dir`.

## FSDP vs DeepSpeed

Use the bundled Accelerate config snapshots under the root `scripts/accelerate_configs/` by default, or pass an explicit external config when the user is maintaining a current checkout.

Choose:

- **FSDP/default DDP-like config** for BERT-like sentence-transformer embedding models such as BGE base models.
- **DeepSpeed ZeRO config** for LLM-like embedding models such as GTE Qwen-style models, especially when model size stresses memory.

Before launch:

- Match `num_processes` to the intended number of GPUs.
- Set `CUDA_VISIBLE_DEVICES` consistently with `num_processes`.
- Confirm the FSDP transformer layer class fits the model family; a BERT layer wrapper is not necessarily correct for every architecture.
- Confirm the environment already has compatible `torch`, `accelerate`, `transformers`, and `sentence-transformers` versions.

## Validation Scope

The bundled validator is intentionally safe and local. It does not import the RAG-Retrieval training modules, instantiate tokenizers, download models, import torch, or run Accelerate. It checks the config/data shape and reports warnings for risky but source-compatible behavior.
