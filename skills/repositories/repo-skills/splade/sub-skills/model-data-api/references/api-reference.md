# SPLADE API Reference

This reference summarizes the programmatic APIs future agents most often need for SPLADE inspection and small integrations. It is intentionally runtime-oriented and does not require access to the source checkout.

## Classic Representation Models

Import path: `splade.models.transformer_rep`.

| Class | Constructor | Main behavior | Forward inputs | Forward outputs |
| --- | --- | --- | --- | --- |
| `Splade` | `Splade(model_type_or_dir, model_type_or_dir_q=None, freeze_d_model=False, agg="max", fp16=True)` | Masked-LM SPLADE encoder. Applies `log(1 + relu(logits))` then `max` or `sum` aggregation over sequence length into vocab-size sparse vectors. | `d_kwargs=<tokenizer dict>`, `q_kwargs=<tokenizer dict>`, or both. Optional `score_batch=True`; optional `nb_negatives=<int>`. | `d_rep`, `q_rep`, and when both sides are present, `score`. |
| `SpladeDoc` | `SpladeDoc(model_type_or_dir, model_type_or_dir_q=None, freeze_d_model=False, agg="sum", fp16=True)` | Document expansion model with lexical bag-of-words query encoder. Query side is `generate_bow` over input token ids after clearing pad/CLS/SEP. | Same `d_kwargs`/`q_kwargs` convention. `model_type_or_dir_q` must be `None`. | Vocab-size sparse vectors and optional dot-product `score`. |
| `SpladeTopK` | `SpladeTopK(model_type_or_dir, model_type_or_dir_q=None, freeze_d_model=False, agg="max", fp16=False, output="MLM", top_d=32, top_q=5, **kwargs)` | SPLADE encoder that prunes representations to top-k dimensions. `top_d` applies to document encodings and `top_q` to query encodings. Use `-1` to disable thresholding. | Same `d_kwargs`/`q_kwargs` convention. | Top-k-pruned `d_rep`/`q_rep` and optional `score`. |
| `SpladeLexical` | `SpladeLexical(model_type_or_dir, model_type_or_dir_q=None, freeze_d_model=False, lexical_type="query", agg="sum", fp16=False)` | Combines SPLADE activation with a cleaned lexical bow mask. `lexical_type` is `query`, `document`, or `both`. | Same `d_kwargs`/`q_kwargs` convention. | Lexically masked sparse vectors and optional `score`. |
| `TransformerRep` | `TransformerRep(model_type_or_dir, output, fp16=False)` | Thin wrapper around HF `AutoModel` or `AutoModelForMaskedLM`; `output` is `mean`, `cls`, `hidden_states`, or `MLM`. | Tokenizer keyword dict. | Dense pooled tensor, hidden states plus mask, or MLM output. |

The classic `SiameseBase.forward` contract is:

- `model(d_kwargs=tokens)` returns only document representations.
- `model(q_kwargs=tokens)` returns only query representations.
- `model(d_kwargs=d_tokens, q_kwargs=q_tokens)` returns both plus a dot-product score.
- `score_batch=True` computes a query-by-document matrix with `q_rep @ d_rep.T`.
- `nb_negatives=N` reshapes documents as `(batch_size, N, output_dim)` and returns one score per negative.

## Model Factory

Import path: `splade.models.models_utils.get_model`.

`get_model(config, init_dict)` maps `config["matching_type"]` to a classic representation class and calls it with `**init_dict`:

| `matching_type` | Class |
| --- | --- |
| `splade` | `Splade` |
| `splade_doc` | `SpladeDoc` |
| `splade_topk` | `SpladeTopK` |
| `splade_lexical` | `SpladeLexical` |

Any other value raises `NotImplementedError`. In Hydra flows, `init_dict.model_type_or_dir` typically points to a pretrained model id or checkpoint model directory. When `hf_training` appears in config restoration, SPLADE rewrites model paths under the checkpoint model folder.

## HuggingFace Trainer Models

Import path: `splade.hf.models`.

| Class | Constructor | Behavior |
| --- | --- | --- |
| `SPLADE` | `SPLADE(model_type_or_dir, tokenizer=None, shared_weights=True, n_negatives=-1, splade_doc=False, model_q=None, **kwargs)` | Trainer-oriented SPLADE model. Returns `(queries_result, docs_result)`, where docs include positive plus negatives. Uses a shared masked-LM encoder by default; can use a separate query encoder with `shared_weights=False`; with `splade_doc=True`, query vectors are cleaned bag-of-words. |
| `DPR` | `DPR(model_type_or_dir, shared_weights=True, n_negatives=-1, tokenizer=None, model_q=None, pooling="cls")` | Dense dual encoder using `AutoModel`; returns `(queries_result, docs_result)` with `cls` or `mean` pooling. |
| `SpladeDoc` | `SpladeDoc(tokenizer, output_dim)` | HF-side lexical query/document helper that returns cleaned bag-of-words vectors from token ids. |

Important HF model shape rule: the input batch is arranged as query, positive document, then `n_negatives` negatives. The HF wrappers reshape `input_ids` and `attention_mask` to `(-1, n_negatives + 2, sequence_length)` and return query vectors with shape `(batch, 1, dim)` and document vectors with shape `(batch, n_negatives + 1, dim)`.

## HF Dataclasses

Import path: `splade.hf.args`.

| Dataclass | Key fields |
| --- | --- |
| `ModelArguments` | `model_name_or_path`, `max_length=128`, `shared_weights=True`, `splade_doc=False`, `model_q=None`, `dense_pooling="cls"`, `dense=False`. |
| `DataTrainingArguments` | `training_data_type`, `training_data_path`, `document_dir`, `query_dir`, `qrels_path`, `n_negatives=4`, `n_queries=-1`. |
| `LocalTrainingArguments` | Extends HF `TrainingArguments`; SPLADE-specific fields include `training_loss`, `l0d`, `l0q`, `T_d`, `T_q`, `top_d`, `top_q`, and `lexical_type`. |

HF training/reranking commands belong to the `hf-training-reranking` sub-skill; this reference exists to explain what the dataclasses mean when debugging config or scripts.

## Datasets and Data Loaders

Classic datasets import path: `splade.datasets.datasets`.

| Class | Expected input | Item output |
| --- | --- | --- |
| `CollectionDatasetPreLoad(data_dir, id_style)` | Directory containing `raw.tsv` with `id<TAB>text`. `id_style` is `row_id` or `content_id`. | For `row_id`: `(original_id, text)` by integer row. For `content_id`: `(str(id), text)` by content id lookup. |
| `PairsDatasetPreLoad(data_dir)` | Directory containing `raw.tsv` with `query<TAB>positive<TAB>negative`. | `(query, positive, negative)`. |
| `DistilPairsDatasetPreLoad(data_dir)` | Directory containing `raw.tsv` with `query<TAB>positive<TAB>negative<TAB>positive_score<TAB>negative_score`. | `(query, positive, negative, positive_score, negative_score)`. |
| `MsMarcoHardNegatives(dataset_path, document_dir, query_dir, qrels_path)` | pkl-gz score dictionary plus collection/query raw.tsv directories and qrel JSON. | `(query_text, positive_doc_text, negative_doc_text, positive_score, negative_score)`. |
| `BeirDataset(value_dictionary, information_type)` | BEIR-like dictionaries for documents or queries. | `(idx, text)`. |
| `IR_Dataset(ir_dataset, information_type, sequential_idx=True, all_docs=None)` | `ir_datasets` object. | `(idx, text)` with optional original ids. |

HF datasets import path: `splade.hf.datasets`.

| Class | Expected input | Item output |
| --- | --- | --- |
| `DatasetPreLoad(data_dir, id_style)` | A raw TSV file path, not a directory. | Similar row/content-id behavior to classic collection preload. |
| `L2I_Dataset(document_dir, query_dir, qrels_path, n_negatives=2, nqueries=-1, training_file_path=None, training_data_type=None)` | Content-id document/query raw TSV files, qrel JSON, and one hard-negative score source. | `([query, positive_doc, negative_doc...], scores_tensor)`. |
| `RerankingDataset(...)` | Same as `L2I_Dataset`. | `([query repeated...], [positive_doc, negative_doc...], scores_tensor)`. |
| `TRIPLET_Dataset(data_dir)` | Raw triplet TSV file path with `query<TAB>positive<TAB>negative`. | `([query, positive, negative], zeros_score_tensor)`. |

Data loaders import path: `splade.datasets.dataloaders`.

| Class | Batch convention |
| --- | --- |
| `SiamesePairsDataLoader` | Tokenizes triplets into prefixed keys such as `q_input_ids`, `pos_input_ids`, `neg_input_ids`. |
| `DistilSiamesePairsDataLoader` | Same as pairs, plus `teacher_p_score` and `teacher_n_score`. |
| `CollectionDataLoader` | Tokenizes `(id, text)` pairs and returns tensors plus integer `id`. |
| `TextCollectionDataLoader` | Like collection loader, but preserves original text for Anserini JSONL export. |
| `EvalDataLoader` | Tokenizes query-document pairs and preserves `q_id`/`d_id`. |

## Reranking Datasets

Import path: `splade.datasets.rerank`.

| Class | Use |
| --- | --- |
| `EvalDatasetRerank` | Builds `(q_id, d_id, query_text, doc_text)` records from a run file plus content-id query/document collections. Accepts JSON run dictionaries and TREC-style text. |
| `EvalDatasetMonoT5` | Produces pygaggle-style grouped query/text objects for monoT5-style reranking. Optional dependency may be absent. |
| `EvalDatasetRerankPairwise` | Builds pairwise document comparisons for a query from an existing run. |

## Inverted Index and Evaluator APIs

Import path: `splade.indexing.inverted_index.IndexDictOfArray`.

| Method | Behavior |
| --- | --- |
| `IndexDictOfArray(index_path=None, force_new=False, filename="array_index.h5py", dim_voc=None)` | Loads an existing HDF5 inverted index if available, otherwise initializes posting-list dictionaries. Without `index_path`, keeps everything in memory. |
| `add_batch_document(row, col, data, n_docs=-1)` | Adds sparse coordinate triples. `row` is row-local document id, `col` is vocab dimension, and `data` is weight. |
| `nb_docs()` | Returns number of indexed documents tracked by the index. |
| `save(dim=None)` | Writes HDF5 posting lists plus `index_dist.json`. `doc_ids.pkl` is written by `SparseIndexing`, not by this object. |

Import path: `splade.tasks.transformer_evaluator`.

| Class | Behavior |
| --- | --- |
| `SparseIndexing` | Iterates a collection loader, calls model `d_kwargs` or `q_kwargs`, stores nonzero coordinates in `IndexDictOfArray`, and writes `doc_ids.pkl` when `index_dir` is set. |
| `SparseRetrieval` | Loads an index or accepts an in-memory index dictionary, encodes one query per batch with `q_kwargs`, scores posting lists with numba, and writes `run.json`. |
| `EncodeAnserini` | Converts sparse representations to Anserini JSONL documents or expanded query TSV. Empty vectors are filled with a fallback unused token to avoid invalid Anserini output. |

Full indexing/retrieval/export commands belong to `hydra-pipelines` or `pruning-export-evaluation`.

## Utility Helpers

Import path: `splade.utils.utils`.

| Function | Behavior |
| --- | --- |
| `generate_bow(input_ids, output_dim, device, values=None)` | Creates a dense bag-of-token-ids tensor of shape `(batch, output_dim)`. If `values` is provided, uses those per-token weights. |
| `clean_bow(bow, pad_id=None, cls_id=None, sep_id=None, mask_id=None)` | Clears selected special-token columns. Note that the implementation checks `if pad_id:` so id `0` will not be cleared unless handled separately by the caller. |
| `pruning(output, k, dim)` | Keeps top `k` values along a dimension and zeros the rest. |
| `normalize(tensor, eps=1e-9)` | L2-normalizes on the final dimension. |
| `rename_keys(d, prefix)` | Adds a prefix plus underscore to every key. |
| `parse(d, name)` | Extracts keys containing `name` and strips the prefix. |
| `get_loss(config)` | Maps loss names such as `PairwiseNLL`, `DistilMarginMSE`, `KlDiv`, `InBatchPairwiseNLL`, and `BCE` to loss objects. |
