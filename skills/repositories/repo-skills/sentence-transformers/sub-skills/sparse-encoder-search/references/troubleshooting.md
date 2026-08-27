# Sparse Encoder Troubleshooting

## Install and Import Problems

### `ImportError: No module named sentence_transformers`

Install the package in the active Python environment:

```bash
pip install -U sentence-transformers
```

Sentence Transformers requires Python 3.10 or newer. Verify the active environment before debugging model code.

### Torch, Transformers, or Hub compatibility errors

The base package depends on PyTorch, Transformers, Hugging Face Hub, NumPy, scikit-learn, SciPy, tqdm, and typing extensions. Upgrade the package first, then pin only if a deployment requires it:

```bash
pip install -U sentence-transformers torch transformers huggingface-hub
```

If CUDA is involved, install a PyTorch build that matches the driver/CUDA runtime instead of relying on a generic CPU wheel.

### Offline or private model loading fails

Use constructor controls deliberately:

- `local_files_only=True` prevents network calls but requires cached/local model files.
- `token=...` is required for private Hub models.
- `revision=...` pins a branch, tag, or commit for reproducibility.
- `trust_remote_code=True` should only be set for reviewed model repositories.

## Optional Service Dependencies

Sparse service helpers import optional packages at call time:

- Qdrant helper: `pip install qdrant-client`.
- Elasticsearch helper: `pip install elasticsearch`.
- OpenSearch helper: `pip install opensearch-py`.
- Seismic helper: `pip install pyseismic-lsr`.

Installing the client library does not start the service. Also verify host, port, credentials, index permissions, TLS settings, and version compatibility.

## API Misuse

### Dense arrays appear where sparse tensors were expected

`SparseEncoder.encode` defaults to `convert_to_tensor=True` and `convert_to_sparse_tensor=True`. If code sets `convert_to_sparse_tensor=False`, downstream Qdrant sparse helpers will reject the output. For Qdrant, pass sparse COO tensors.

### `ValueError: Query embeddings must be a sparse COO tensor`

The Qdrant helper expects torch sparse COO tensors:

```python
embeddings = model.encode(texts, convert_to_tensor=True, convert_to_sparse_tensor=True)
```

If the tensor was transformed, convert it back with `.to_sparse()` when safe.

### `ValueError: Query embeddings must be a list of lists...`

Elasticsearch, OpenSearch, and Seismic helpers expect decoded token-weight lists, not tensors:

```python
embeddings = model.encode(texts)
decoded = model.decode(embeddings, top_k=128)
```

For one input, normalize output shape if your code expects a batch of lists.

### Unsupported keyword arguments to `encode`

`SparseEncoder.encode` rejects kwargs that the model does not use, except `task` and `processing_kwargs`. Remove dense-only parameters or inspect `model.get_model_kwargs()` before forwarding user-supplied options.

### Wrong method for IR prompts or routers

If the model defines query/document prompts or an inference-free router, use `encode_query` and `encode_document`. Plain `encode` can route all inputs through the default path and produce misleading retrieval scores.

## Sparsity and Ranking Failures

### Too many active dimensions

Symptoms: high memory use, slow service indexing, large rank-feature payloads, or low `sparsity_ratio`.

Fixes:

1. Measure with `model.sparsity(embeddings)`.
2. Decode top tokens with `model.decode(embeddings, top_k=20)` to verify meaningful terms.
3. Try `max_active_dims` at encode time before changing the model.
4. For trained models, increase SPLADE regularization gradually and monitor IR metrics.

### Collapsed sparse output

Symptoms: nearly all outputs have zero or very few active dimensions, scores are all zero or tied, decoded token lists are empty, or recall drops sharply.

Fixes:

1. Remove or relax `max_active_dims` to check whether the cap caused collapse.
2. Verify inputs are non-empty and not all truncated by `processing_kwargs` or `max_seq_length`.
3. For training, reduce sparsity regularizer weights and confirm the inner loss receives correct columns/labels.
4. Compare against a known pretrained SPLADE model to separate data problems from architecture/training problems.

### Unexpected lexical matches

SPLADE sparse models can expand terms but remain more lexical/interpretable than dense encoders. Decode top tokens for query and documents. If important semantic paraphrases are missed, combine with dense retrieval and fuse results rather than forcing sparse retrieval to behave like a dense model.

### Scores look different from dense similarity scores

Dot product is the default sparse score and can be much larger than cosine values. Do not compare sparse dot scores directly with dense cosine scores without normalization or rank-based fusion.

## Training-Specific Problems

### `SpladeLoss` rejects the inner loss

`SpladeLoss` requires an inner loss with `compute_loss_from_embeddings`. Use sparse losses from `sentence_transformers.sparse_encoder.losses`, not arbitrary PyTorch losses.

### Query/document regularization behaves oddly

`SpladeLoss` regularizes query and document embeddings separately unless `use_document_regularizer_only=True`. If `query_regularizer_weight=None`, query regularization is skipped. This can be valid for inference-free setups but is risky for standard SPLADE query encoders.

### Dataset columns train the wrong pairs

Sentence Transformers training uses non-label columns as inputs in order. Remove metadata columns and reorder data before training. For router models, set `router_mapping` so query and document columns use the intended route.

### Evaluation is too slow during training

Use a small eval slice, larger `eval_steps`, and `corpus_chunk_size` appropriate to memory. Track `SparseInformationRetrievalEvaluator` metrics periodically, but avoid full-corpus evaluation every few steps.

## Backend and Service Limits

- Backend export and quantization details belong in `../backend-export-optimization/SKILL.md`; sparse models can be constructed with `backend="onnx"` or `backend="openvino"`, but optional backend dependencies and exported filenames must be handled there.
- Elasticsearch/OpenSearch `rank_features` mappings can grow large with too many decoded tokens; cap active dimensions or decode top-k only after validating ranking quality.
- Default service helper URLs are local defaults; production code should pass explicit client configuration and handle authentication.
- Temporary helper-created index names are useful for demos. Production systems should create stable indexes, mappings, lifecycle policy, and rollback behavior outside request-time code.

## Smoke Script Problems

### `--help` fails

The script should not import or load a model before argparse help completes. If `--help` fails, check the Python file syntax and standard-library imports first.

### Model load fails with `--local-files-only`

The model is not cached locally or the path is wrong. Remove `--local-files-only` only if downloads are allowed, or pass a local model directory.

### CUDA out of memory or CPU is slow

Use smaller batches, shorter sentences, `max_active_dims`, or CPU-safe tiny/local models for smoke tests. For production, benchmark query and document paths separately because document encoding can often run offline.
