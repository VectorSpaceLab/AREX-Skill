# Training Workflows

Full training is expensive and may download model weights or datasets. For custom data, validate files first with the bundled scripts, then run a bounded smoke or a real training job only when hardware and cache constraints are explicit.

## Choose the training path

| Need | Use | Data |
|---|---|---|
| Score/rank sentence similarity and produce an embedding model | `CosentModel` | Pair TSV/JSONL; labels can be binary or similarity scores. |
| Supervised pair classification while keeping an embedding encoder | `SentenceBertModel` | Pair TSV/JSONL; labels are class ids. |
| Cross-encoder pair classification/reranking | `BertMatchModel` | Pair TSV/JSONL; labels are class ids; no standalone sentence embedding output. |
| Dense retrieval fine-tuning with positives and negatives | `BgeModel` | BGE JSONL triples with `query`, `pos`, `neg`. |

## Supervised text-matching recipe

Use this template for CoSENT, Sentence-BERT, or BERT-match with local TSV/JSONL data:

```python
from text2vec import CosentModel, SentenceBertModel, BertMatchModel

model = CosentModel(  # or SentenceBertModel(...), BertMatchModel(...)
    model_name_or_path="hfl/chinese-macbert-base",  # local model dir or HF id
    encoder_type="MEAN",
    max_seq_length=128,
)

global_step, training_details = model.train_model(
    train_file="train.jsonl",
    eval_file="valid.jsonl",
    output_dir="outputs/my-text2vec-run",
    num_epochs=10,
    batch_size=64,
    lr=2e-5,
    save_model_every_epoch=True,
    bf16=False,
    data_parallel=False,
)
```

Recipe notes distilled from the supervised examples:
- `model_arch=cosent` maps to `CosentModel`; `model_arch=sentencebert` maps to `SentenceBertModel`; `model_arch=bert` maps to `BertMatchModel`.
- Built-in Chinese dataset names include `ATEC`, `STS-B`, `BQ`, `LCQMC`, and `PAWSX` when using the Hugging Face dataset path.
- For `use_hf_dataset=True`, pass `hf_dataset_name="STS-B"` or another supported dataset name and omit local `train_file`.
- For local custom files, pass `train_file`, `eval_file`, and usually a separate test file for post-training metric computation.
- If labels are not binary, ensure the model constructor has a matching `num_classes` for `SentenceBertModel`/`BertMatchModel`, or use `CosentModel` for score/ranking labels.

## Hugging Face dataset recipe

```python
from text2vec import CosentModel

model = CosentModel(
    model_name_or_path="hfl/chinese-macbert-base",
    encoder_type="FIRST_LAST_AVG",
    max_seq_length=128,
)
model.train_model(
    output_dir="outputs/sts-b-cosent",
    num_epochs=10,
    batch_size=64,
    lr=2e-5,
    use_hf_dataset=True,
    hf_dataset_name="STS-B",
)
```

This requires the Hugging Face dataset package and network access or a populated dataset cache. For deterministic offline work, prefer local TSV/JSONL files and `use_hf_dataset=False`.

## English STS-B / NLI recipe

The English STS recipe loads `stsbenchmark.tsv.gz` into train/dev/test splits. It converts train scores to binary with `score > 2.5`, keeps dev/test scores for metrics, and builds one of these datasets:
- CoSENT: flatten pair rows to `(sentence, score)` records.
- Sentence-BERT: keep `(sentence1, sentence2, label)` pairs.
- BERT-match: keep pair rows but tokenize them as a cross-encoder input.

The English NLI pretraining recipe downloads or reuses `AllNLI.tsv.gz`, maps labels to `contradiction=0`, `entailment=1`, `neutral=2`, and caps training rows with an `nli_limit_size`-style limit. Use `num_classes=3` for `SentenceBertModel` and `BertMatchModel` on this data.

## BGE fine-tuning recipe

Validate BGE triples first:

```bash
python scripts/validate_bge_jsonl.py --input-file bge_train.jsonl --train-group-size 4
```

Then train with explicit query/passage lengths and group size:

```python
from text2vec import BgeModel

model = BgeModel(
    model_name_or_path="BAAI/bge-large-zh-noinstruct",  # local model dir or HF id
    encoder_type="MEAN",
    max_seq_length=32,      # query max length
    passage_max_len=64,     # positive/negative passage max length
)
model.train_model(
    train_file="bge_train.jsonl",
    eval_file="valid_pairs.jsonl",
    output_dir="outputs/bge-finetune",
    num_epochs=3,
    batch_size=4,
    lr=1e-5,
    train_group_size=4,
    temperature=1.0,
    normalize_embeddings=False,
    save_model_every_epoch=True,
    bf16=False,
    data_parallel=False,
)
```

BGE recipe notes:
- Each training row forms one query group: one random positive plus `train_group_size - 1` negatives.
- If `temperature < 1.0`, prefer `normalize_embeddings=True` so dot-product scores remain well-scaled.
- `eval_file` is a text-matching pair file, not BGE triples; it is used for Spearman/Pearson-style evaluation if provided.
- The source data-building recipe constructs triples by keeping positive STS-style pairs and adding random negatives; optional hard-negative mining requires FAISS and an embedding model.

## Multi-GPU, `data_parallel`, and `bf16`

The package exposes `bf16` and `data_parallel` flags in the training methods.

Use multi-card training only when multiple CUDA devices and a matching PyTorch build are available:

```bash
CUDA_VISIBLE_DEVICES=0,1 torchrun --nproc_per_node 2 YOUR_TRAINING_DRIVER.py \
  --do_train --output_dir outputs/multigpu-run --batch_size 64 --bf16 --data_parallel
```

Operational boundaries:
- `data_parallel=True` is not useful on CPU, MPS, or a single CUDA device.
- The training code reads `LOCAL_RANK` and uses a distributed sampler; launch through `torchrun` or disable `data_parallel`.
- Treat `batch_size` as the per-process batch size in multi-process launches; effective throughput can be larger than a single-process run.
- `bf16=True` uses `torch.bfloat16` autocast and should be disabled on unsupported GPUs or CPU-only training.
- Reduce `batch_size`, `max_seq_length`, `query_max_len`, or `passage_max_len` before assuming model-code failure on OOM.

## `output_dir` and checkpoint behavior

- Training creates `output_dir` if it does not exist.
- Per-epoch checkpoints are saved under `output_dir/checkpoint-<global_step>-epoch-<epoch>` when `save_model_every_epoch=True`.
- The best evaluation checkpoint is saved at the root of `output_dir`.
- `training_progress_scores.csv` is written to `output_dir` after evaluations.
- Reusing an old checkpoint-like `model_name_or_path` can trigger resume logic; use a fresh output directory for clean experiments.

## Download and cache planning

- `model_name_or_path` can be a local Transformers-compatible directory or a Hugging Face model id. HF ids download at model construction time if not cached.
- `use_hf_dataset=True` and BGE dataset-name loading call Hugging Face `load_dataset`; use local files for offline or reproducible runs.
- Hard-negative mining can add FAISS dependency, sentence-model downloads, and large embedding-memory requirements; treat it as optional preprocessing, not a required validator.
