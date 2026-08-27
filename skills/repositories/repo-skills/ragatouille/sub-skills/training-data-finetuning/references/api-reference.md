# API Reference

This reference records the RAGatouille `0.0.9post2` training APIs verified from repository code and package inspection.

## `RAGTrainer`

Import:

```python
from ragatouille import RAGTrainer
```

Constructor:

```python
RAGTrainer(
    model_name: str,
    pretrained_model_name: str,
    language_code: str = "en",
    n_usable_gpus: int = -1,
)
```

Behavior:
- Initializes a ColBERT-backed trainer in training mode immediately; this can load local checkpoints or download Hugging Face assets depending on `pretrained_model_name`.
- `pretrained_model_name` can be an existing ColBERT checkpoint for fine-tuning or a BERT/RoBERTa-like base model for new ColBERT training.
- `language_code` is also passed to `SimpleMiner` during hard-negative mining.
- `n_usable_gpus=-1` means use all visible GPUs if available; CPU-only environments are not suitable for full training.

Methods:

```python
add_documents(documents: list[str])
```

Adds strings to `trainer.collection` and shuffles deterministically with RAGatouille's seeded shuffle.

```python
export_training_data(path: str | pathlib.Path)
```

Exports the data already processed by `prepare_training_data` through the attached `TrainingDataProcessor`.

```python
prepare_training_data(
    raw_data: list[tuple] | list[list],
    all_documents: list[str] | None = None,
    data_out_path: str | pathlib.Path = "./data/",
    num_new_negatives: int = 10,
    hard_negative_minimum_rank: int = 10,
    mine_hard_negatives: bool = True,
    hard_negative_model_size: str = "small",
    pairs_with_labels: bool = False,
    positive_label: int | str = 1,
    negative_label: int | str = 0,
) -> str
```

Behavior:
- Determines `data_type` from the first raw item: arity 2 means `pairs`; arity 3 means `labeled_pairs` only when `pairs_with_labels=True`, otherwise `triplets`.
- Adds `all_documents` strings to the collection before generating negatives.
- Accepts query strings only; non-string query values raise `ValueError("Queries must be a strings.")`.
- For labeled pairs, the sample label and later labels must match `positive_label` or `negative_label`.
- When `mine_hard_negatives=True`, constructs `SimpleMiner(language_code, hard_negative_model_size)`, builds an embedding index over the collection, and mines negatives.
- If no triplets are produced with hard negatives, it prints a warning and retries with `mine_hard_negatives=False` for random negatives.
- If no triplets are produced without hard negatives, it raises `ValueError("No training triplets were generated.")`.
- Returns the `data_out_path` argument.

```python
train(
    batch_size: int = 32,
    nbits: int = 2,
    maxsteps: int = 500000,
    use_ib_negatives: bool = True,
    learning_rate: float = 5e-6,
    dim: int = 128,
    doc_maxlen: int = 256,
    use_relu: bool = False,
    warmup_steps: int | Literal["auto"] = "auto",
    accumsteps: int = 1,
) -> str
```

Behavior:
- Requires `prepare_training_data` to have populated `trainer.data_dir` and either in-memory `training_triplets` or an existing `triples.train.colbert.jsonl` under `data_dir`.
- Builds a `ColBERTConfig` with `bsize=batch_size`, `checkpoint=pretrained_model_name`, `maxsteps`, `nbits`, `lr=learning_rate`, `dim`, `doc_maxlen`, `relu=use_relu`, and `accumsteps`.
- `warmup_steps="auto"` becomes roughly 10% of `total_triplets // batch_size`.
- Delegates actual training to the underlying ColBERT model and returns the trained model path.

## `TrainingDataProcessor`

Import:

```python
from ragatouille.data import TrainingDataProcessor
```

Constructor:

```python
TrainingDataProcessor(
    collection: list[str],
    queries: list[str],
    negative_miner=None,
)
```

Method:

```python
process_raw_data(
    raw_data,
    data_type: Literal["pairs", "triplets", "labeled_pairs"],
    data_dir: str | pathlib.Path,
    export: bool = True,
    mine_hard_negatives: bool = True,
    num_new_negatives: int = 10,
    positive_label: int = 1,
    negative_label: int = 0,
    hard_negative_minimum_rank: int = 10,
)
```

Behavior:
- Use `mine_hard_negatives=False` when no `negative_miner` was supplied; otherwise it raises `ValueError("mine_hard_negatives is True but no negative miner was provided!")`.
- Converts raw examples into integer ColBERT triplets `[query_id, positive_passage_id, negative_passage_id]`.
- With `export=True`, writes the three training files to `data_dir`.
- Random negative sampling is seeded and excludes known positives and negatives for the query.

## `CorpusProcessor`

Imports:

```python
from ragatouille.data import CorpusProcessor, llama_index_sentence_splitter
```

Constructor:

```python
CorpusProcessor(
    document_splitter_fn: Callable | None = llama_index_sentence_splitter,
    preprocessing_fn: Callable | list[Callable] | None = None,
)
```

Method:

```python
process_corpus(
    documents: list[str],
    document_ids: list[str] | None = None,
    **splitter_kwargs,
) -> list[dict]
```

Behavior:
- Generates UUID document IDs if `document_ids` is omitted.
- The default splitter returns chunks shaped as `{"document_id": <id>, "content": <chunk_text>}`.
- `llama_index_sentence_splitter(documents, document_ids, chunk_size=256)` uses sentence-aware chunks with overlap derived from `chunk_size`.

## `SimpleMiner`

Import:

```python
from ragatouille.negative_miners import SimpleMiner
```

Constructor:

```python
SimpleMiner(
    language_code: str,
    model_size: Literal["small", "base", "large"] = "small",
)
```

Important behavior:
- Loads a `sentence-transformers` model during construction, so it can download model weights.
- Language mapping uses `en`, `zh`, `fr`, or `other` for unsupported language codes.
- Model choices include English BGE, Chinese GTE, French OrdalieTech Solon, and multilingual E5 variants by size.
- `build_index(collection, batch_size=128, save_index=False, save_path=None, force_fp32=True)` embeds the collection and builds a Voyager cosine index.
- `mine_hard_negatives(queries, collection=None, save_index=False, save_path=None, force_fp32=True)` mines from the existing index or builds one when a collection is supplied.
