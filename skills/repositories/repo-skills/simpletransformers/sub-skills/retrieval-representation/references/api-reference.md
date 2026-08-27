# Retrieval and Representation API Reference

## Public imports and constructors

```python
from simpletransformers.language_representation import RepresentationModel
from simpletransformers.retrieval import RetrievalArgs, RetrievalModel
from simpletransformers.pretrain_retrieval import PretrainRetrievalModel
```

```python
RepresentationModel(model_type, model_name, args=None, use_cuda=True, cuda_device=-1, **kwargs)

RetrievalModel(
    model_type=None,
    model_name=None,
    context_encoder_name=None,
    query_encoder_name=None,
    context_encoder_tokenizer=None,
    query_encoder_tokenizer=None,
    reranking_model_name=None,
    prediction_passages=None,
    teacher_model_name=None,
    teacher_tokenizer_name=None,
    autoencoder_model=None,
    clustering_model=None,
    args=None,
    use_cuda=True,
    cuda_device=-1,
    **kwargs,
)
```

## Main methods

| API | Methods | Notes |
|---|---|---|
| `RepresentationModel` | `encode_sentences(sentences, combine_strategy=...)` | Returns representation arrays/tensors depending on strategy and args. |
| `RetrievalModel` | `train_model`, `eval_model`, `predict`, `retrieve_docs_from_query_embeddings` | Dense retrieval training, evaluation, and prediction. |
| `RetrievalModel` | `build_hard_negatives`, `get_hard_negatives`, `add_hard_negatives_for_ance` | Advanced training-data construction. |
| `RetrievalModel` | `evaluate_beir` | Requires optional BEIR dependencies and dataset layout. |
| `PretrainRetrievalModel` | train/eval/predict style methods | Advanced pretraining; use only when user explicitly needs it. |

## RetrievalArgs highlights

High-impact fields include `data_format`, `use_hf_datasets`, `include_title`, `include_hard_negatives`, `hard_negatives`, `n_hard_negatives`, `faiss_index_type`, `faiss_d`, `faiss_m`, `retrieve_n_docs`, `pytrec_eval_metrics`, `evaluate_with_beir`, `external_embeddings`, `prediction_passages`, `include_nll_loss`, `include_triplet_loss`, `include_kl_div_loss`, `multi_head_vectors`, `teacher_type`, `reranking_model_name`, `query_config`, and `context_config`.

## Optional dependencies

- `faiss`: required when building/loading FAISS indexes.
- `pytrec_eval`: required for TREC-style metrics.
- `beir`: required for `evaluate_beir` and BEIR loaders/evaluators.
- CUDA-capable PyTorch: optional acceleration for training/inference; not needed for schema validators.

## Compatibility note

Retrieval imports share custom model modules with classification. If `SequenceSummary` import errors appear, resolve Transformers/Simple Transformers compatibility before debugging retrieval data.
