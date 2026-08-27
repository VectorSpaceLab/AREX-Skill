# Workflows

These recipes separate safe offline data preparation from model initialization, downloads, and GPU training.

## Safe Data-Prep Checklist

1. Pick one raw-data mode: pairs, labeled pairs, or triplets.
2. Ensure every query is a string and every passage is a string, list of strings, or supported `{"content": ...}` dict.
3. For pairs, provide enough candidate negatives through `all_documents`, `add_documents`, or hard-negative mining.
4. For labeled pairs, ensure each query has at least one positive and one negative after label mapping, or enable negative sampling/mining.
5. For explicit triplets, set `num_new_negatives=0` and `mine_hard_negatives=False` if the negative column is already complete.
6. Write processed files to a stable `data_out_path` and version the three ColBERT output files.

## Offline Conversion Without Model Downloads

When model downloads are unsafe, bypass `RAGTrainer` construction and use `TrainingDataProcessor` directly:

```python
from ragatouille.data import TrainingDataProcessor

raw_data = [
    ("what is ragatouille?", "RAGatouille wraps ColBERT.", "A cooking dish is unrelated."),
]
queries = sorted({row[0] for row in raw_data})
collection = sorted({text for _, positive, negative in raw_data for text in [positive, negative]})

processor = TrainingDataProcessor(collection=collection, queries=queries, negative_miner=None)
processor.process_raw_data(
    raw_data=raw_data,
    data_type="triplets",
    data_dir="data",
    export=True,
    mine_hard_negatives=False,
    num_new_negatives=0,
)
```

Use this for validation, CI, or constrained environments. It creates the same output file names without loading the ColBERT model or `SimpleMiner`.

## Corpus Chunking

Use `CorpusProcessor` to split long documents before creating pairs or candidate negatives:

```python
from ragatouille.data import CorpusProcessor, llama_index_sentence_splitter

processor = CorpusProcessor(document_splitter_fn=llama_index_sentence_splitter)
chunks = processor.process_corpus(long_documents, document_ids=document_ids, chunk_size=256)
chunk_texts = [chunk["content"] for chunk in chunks]
```

Guidance:
- Use chunk sizes around 128-256 for ColBERT-style passage retrieval.
- Keep `document_id` values if you need to trace chunks back to source documents outside the training file.
- Pass `chunk_texts` as `all_documents`; raw examples may use chunk dicts because `RAGTrainer._add_to_collection` reads their `content` field.

## Prepare Pairs With Random Negatives

This is the safest RAGTrainer data-prep mode when model initialization is allowed but dense-miner downloads are not:

```python
from ragatouille import RAGTrainer

trainer = RAGTrainer(
    model_name="domain-colbert",
    pretrained_model_name="colbert-ir/colbertv2.0",
    language_code="en",
)
trainer.prepare_training_data(
    raw_data=pairs,
    all_documents=all_candidate_passages,
    data_out_path="data",
    num_new_negatives=10,
    mine_hard_negatives=False,
)
```

Notes:
- Random negatives are sampled from the deduplicated collection and exclude known positives/negatives for the query.
- If the corpus is too small or every candidate is already positive, this can still produce zero triplets.
- Increase corpus breadth or provide explicit triplets when preparing a tiny dataset.

## Prepare With Hard Negatives

Use hard negatives when the environment may download and run `sentence-transformers` and Voyager indexing:

```python
trainer.prepare_training_data(
    raw_data=pairs,
    all_documents=all_candidate_passages,
    data_out_path="data",
    num_new_negatives=10,
    hard_negative_minimum_rank=10,
    mine_hard_negatives=True,
    hard_negative_model_size="small",
)
```

Guidance:
- `hard_negative_model_size` accepts `"small"`, `"base"`, or `"large"`; start with `"small"` for cost and memory.
- `language_code` from `RAGTrainer` chooses English, Chinese, French, or multilingual fallback miner models.
- `hard_negative_minimum_rank=10` skips the nearest hits before sampling, reducing accidental positives.
- If hard mining yields zero triplets, RAGatouille retries random negatives and prints a warning.

## Labeled Pair Recipe

```python
trainer.prepare_training_data(
    raw_data=labeled_pairs,
    pairs_with_labels=True,
    positive_label="positive",
    negative_label="negative",
    data_out_path="data",
    mine_hard_negatives=False,
    num_new_negatives=0,
)
```

Use `num_new_negatives > 0` only if you want extra sampled/mined negatives in addition to labeled negatives.

## Explicit Triplet Recipe

```python
trainer.prepare_training_data(
    raw_data=triplets,
    pairs_with_labels=False,
    data_out_path="data",
    mine_hard_negatives=False,
    num_new_negatives=0,
)
```

This is the most deterministic mode for CI and hand-curated datasets.

## Training/Fine-Tuning

Only train after data files exist and the runtime is allowed to perform expensive model work:

```python
model_path = trainer.train(
    batch_size=32,
    nbits=2,
    maxsteps=500000,
    use_ib_negatives=True,
    learning_rate=5e-6,
    dim=128,
    doc_maxlen=256,
    use_relu=False,
    warmup_steps="auto",
    accumsteps=1,
)
```

Operational guidance:
- Use a ColBERT checkpoint such as `colbert-ir/colbertv2.0` for fine-tuning, or a transformer base model for new ColBERT training.
- Start with a very small `maxsteps` only for smoke testing on suitable GPU hardware.
- `batch_size` is total batch size; account for the number of usable GPUs.
- `doc_maxlen` should match the passage chunking strategy.
- Persist and inspect the returned model path before routing to indexing/search workflows.

## Script Entrypoint Note

When turning training code into a standalone script, guard execution with:

```python
if __name__ == "__main__":
    main()
```

ColBERT training and multiprocessing dependencies behave more reliably when script side effects are not executed at import time.
