# Training API Reference

This reference covers BEIR's training-facing APIs. It assumes `corpus`, `queries`, and `qrels` are already loaded in BEIR shape. Route file format and loader questions to `../data-loading/SKILL.md`.

## Core Class: `TrainRetriever`

Import:

```python
from beir.retrieval.train import TrainRetriever

retriever = TrainRetriever(model=sentence_transformer_model, batch_size=64)
```

Constructor:

| Argument | Default | Notes |
| --- | --- | --- |
| `model` | required | A `sentence_transformers.SentenceTransformer` instance or compatible object for loader/evaluator construction. Full training calls `model.fit(...)`. |
| `batch_size` | `64` | Used by pair/triplet loading loops and default training dataloaders. Larger triplet batches improve in-batch negatives but increase memory. |

## Training Pair Loading

```python
train_samples = retriever.load_train(corpus, queries, qrels)
```

Input shape:

- `corpus`: `{doc_id: {"title": str, "text": str}}`
- `queries`: `{query_id: query_text}`
- `qrels`: `{query_id: {doc_id: relevance_int}}`

Behavior:

- Creates one `sentence_transformers.readers.InputExample` per positive `qrels` entry where score is `>= 1`.
- Each example has `texts=[query_text, title + " " + text]` and `label=1`.
- Relevance `0` entries are ignored.
- Missing corpus ids are logged and skipped by `load_train`; do not rely on this during expensive runs. Preflight the ids first.
- Missing query ids referenced by `qrels` can raise `KeyError`.

Use pair samples with SentenceTransformers losses such as `losses.MultipleNegativesRankingLoss(model=retriever.model)`.

## Triplet Loading

```python
triplets = [(query_text, positive_text, negative_text)]
train_samples = retriever.load_train_triplets(triplets)
train_dataloader = retriever.prepare_train_triplets(train_samples)
```

Behavior:

- Each triplet is wrapped as `InputExample(guid=None, texts=triplet)`.
- BEIR does not validate tuple length in `load_train_triplets`; validate that each item has exactly three strings before calling it.
- `prepare_train_triplets()` returns SentenceTransformers `datasets.NoDuplicatesDataLoader`, which is suited to in-batch-negative training.

Triplets are used by the BEIR examples for mined BM25/dense hard negatives and for MS MARCO-style hard-negative files.

## Dataloader Preparation

```python
train_dataloader = retriever.prepare_train(train_samples, shuffle=True)
```

Arguments:

| Argument | Default | Notes |
| --- | --- | --- |
| `train_dataset` | required | Usually a list of `InputExample`; can also be a ready PyTorch dataset. |
| `shuffle` | `True` | Passed to `torch.utils.data.DataLoader`. |
| `dataset_present` | `False` | If `False`, wraps examples in `SentencesDataset(train_dataset, model=retriever.model)`. If `True`, uses the dataset object directly. |

Use `dataset_present=True` for custom datasets that yield `InputExample` instances dynamically, such as MS MARCO hard-negative datasets.

## Training Evaluators

```python
ir_evaluator = retriever.load_ir_evaluator(dev_corpus, dev_queries, dev_qrels, name="dev")
```

Behavior:

- Raises `ValueError("Dev Set Empty!, Cannot evaluate on Dev set.")` when `dev_queries` is empty.
- Converts corpus docs to `title + " " + text` strings.
- Converts qrels to `{query_id: set(relevant_doc_ids)}` for `InformationRetrievalEvaluator`.
- Optional `max_corpus_size` keeps all relevant corpus ids and samples extra non-relevant docs.
- If `max_corpus_size` is smaller than the number of unique relevant ids, raises `ValueError("Your maximum corpus size should atleast contain N corpus ids")`.
- Relevant ids missing from `dev_corpus` can raise `KeyError` during evaluator corpus selection.

Use a dummy evaluator only when the user accepts that no dev metric will select checkpoints:

```python
ir_evaluator = retriever.load_dummy_evaluator()
```

`load_dummy_evaluator()` returns an empty `SequentialEvaluator` whose score is time-based. It prevents evaluator plumbing failures but does not measure retrieval quality.

## Training Invocation

```python
retriever.fit(
    train_objectives=[(train_dataloader, train_loss)],
    evaluator=ir_evaluator,
    epochs=1,
    warmup_steps=1000,
    evaluation_steps=10000,
    output_path="checkpoints/my-beir-model",
    use_amp=True,
)
```

`TrainRetriever.fit()` forwards to `SentenceTransformer.fit()` with these BEIR defaults:

| Parameter | Default | Notes |
| --- | --- | --- |
| `epochs` | `1` | Keep small for smoke runs; production training often needs more. |
| `scheduler` | `"WarmupLinear"` | SentenceTransformers scheduler name. |
| `warmup_steps` | `10000` | Examples often use `int(len(train_samples) * epochs / batch_size * 0.1)` for pair training or fixed `1000` for MS MARCO-style training. |
| `optimizer_class` | `transformers.AdamW` | Version-sensitive import; newer Transformers may deprecate this path. |
| `optimizer_params` | `{"lr": 2e-5, "eps": 1e-6, "correct_bias": False}` | Standard transformer fine-tuning defaults. |
| `weight_decay` | `0.01` | Passed to SentenceTransformers. |
| `evaluation_steps` | `0` | Set nonzero for periodic evaluator calls. |
| `output_path` | `None` | Set to a user-owned checkpoint directory outside source/package directories. |
| `save_best_model` | `True` | Requires meaningful evaluator if checkpoint selection matters. |
| `max_grad_norm` | `1` | Gradient clipping. |
| `use_amp` | `False` | Mixed precision; use only when compatible with device and model. |

## Loss Selection

### SentenceTransformers Multiple Negatives

```python
from sentence_transformers import losses
train_loss = losses.MultipleNegativesRankingLoss(model=retriever.model)
```

Use for:

- Pair examples from qrels where in-batch positives serve as negatives.
- Triplets with hard negatives when using SentenceTransformers' compatible data loaders.

For dot-product models, pass the SentenceTransformers utility function appropriate for the installed version, for example `similarity_fct=util.dot_score`.

### BEIR `MarginMSELoss`

```python
from beir.losses import MarginMSELoss
train_loss = MarginMSELoss(model=retriever.model, scale=1.0, similarity_fct="dot")
```

Use for cross-architecture distillation with triplets where the label is:

```python
label = positive_teacher_score - negative_teacher_score
```

Forward inputs are query, positive passage, and negative passage sentence features. The implementation computes dot-product margins and applies MSE against the label.

### BEIR `BPRLoss`

```python
from beir.losses import BPRLoss
train_loss = BPRLoss(model=retriever.model)
```

Use for binary-code retriever training with triplets. It combines:

- Dense multiple-negatives cross entropy over query/document scores.
- Binary margin ranking loss over tanh-scaled binary-like representations.

Important parameters:

| Parameter | Default | Notes |
| --- | --- | --- |
| `scale` | `1.0` | Multiplies similarity scores. |
| `similarity_fct` | `sentence_transformers.util.dot_score` | Similarity between dense embeddings. |
| `binary_ranking_loss_margin` | `2.0` | Margin for binary ranking loss. |
| `hashnet_gamma` | `0.1` | Controls tanh scaling growth with `global_step`. |

## Evidence Paths

This API summary is grounded in BEIR package sources and examples:

- `beir/retrieval/train.py`
- `beir/losses/bpr_loss.py`
- `beir/losses/margin_mse_loss.py`
- `examples/retrieval/training/train_sbert.py`
- `examples/retrieval/training/train_sbert_BM25_hardnegs.py`
- `examples/retrieval/training/train_msmarco_v2.py`
- `examples/retrieval/training/train_msmarco_v3.py`
- `examples/retrieval/training/train_msmarco_v3_bpr.py`
- `examples/retrieval/training/train_msmarco_v3_margin_MSE.py`
- `pyproject.toml`
