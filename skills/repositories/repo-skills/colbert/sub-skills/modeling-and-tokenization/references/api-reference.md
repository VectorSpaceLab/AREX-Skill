# Modeling and Tokenization API Reference

## Verified Imports

```python
from colbert.infra import ColBERTConfig
from colbert.modeling.checkpoint import Checkpoint
from colbert.modeling.tokenization import QueryTokenizer, DocTokenizer
from colbert.modeling.colbert import colbert_score, colbert_score_packed
```

The package is distributed as `colbert-ai` and imported as `colbert`. Verified imports include `colbert`, `colbert.infra`, `colbert.data`, `colbert.modeling.checkpoint`, `utility`, and `baleen`.

## Core Constructors

### `Checkpoint(name, colbert_config=None, verbose=3)`

Loads a ColBERT model for inference and creates:

- `checkpoint.colbert_config`
- `checkpoint.query_tokenizer`
- `checkpoint.doc_tokenizer`
- `checkpoint.amp_manager`

`name` can be a local ColBERT checkpoint directory, a legacy `.dnn` file, or an intentional Hugging Face model/repo name. Remote model names can trigger Hugging Face Hub or Transformers cache/network behavior.

Internally the constructor merges `ColBERTConfig.load_from_checkpoint(name)` with any caller-supplied `colbert_config`, then loads the Hugging Face model/tokenizer and moves the model to `colbert.parameters.DEVICE`.

### `ColBERTConfig(...)`

`ColBERTConfig` is a dataclass-style config composed from run, resource, document, query, training, indexing, search, and tokenizer settings. For modeling/tokenization tasks, the most important fields are `checkpoint`, `model_name`, `dim`, `query_maxlen`, `doc_maxlen`, `mask_punctuation`, `attend_to_mask_tokens`, `query_token_id`, and `doc_token_id`.

Common patterns:

```python
config = ColBERTConfig.load_from_checkpoint("/path/to/checkpoint")
config = ColBERTConfig(checkpoint="bert-base-uncased", query_maxlen=32, doc_maxlen=180)
merged = ColBERTConfig.from_existing(config, ColBERTConfig(doc_maxlen=220))
```

`load_from_checkpoint()` can return `None` when the checkpoint has no ColBERT metadata. In that case, construct an explicit config before loading a model or tokenizer.

## Checkpoint Encoding Methods

### `query(input_ids, attention_mask, to_cpu=False)`

Encodes already-tokenized queries under `torch.no_grad()` and ColBERT's mixed precision context. Returns normalized query embeddings. With `to_cpu=True`, returns CPU tensors.

### `doc(input_ids, attention_mask, keep_dims=True, to_cpu=False)`

Encodes already-tokenized documents. `keep_dims` must be `True`, `False`, or `'return_mask'` at this lower-level method.

- `True`: padded 3-D tensor of document embeddings.
- `False`: list of unpadded per-document tensors.
- `'return_mask'`: tuple `(D, mask)` for padded embeddings and boolean document mask.

On GPU, document embeddings are converted to half precision. With `to_cpu=True`, returned tensors are moved to CPU.

### `queryFromText(queries, bsize=None, to_cpu=False, context=None, full_length_search=False)`

Tokenizes query strings and encodes them.

- `queries` must be a list or tuple of strings.
- `bsize` returns mini-batches internally and concatenates encoded results.
- `context` appends background text, one context string per query.
- `full_length_search=True` is valid only for a single query in a list and expands width up to `min(500, max(query_maxlen, observed_length))`.

Typical default output shape is `(len(queries), query_maxlen, dim)`.

### `docFromText(docs, bsize=None, keep_dims=True, to_cpu=False, showprogress=False, return_tokens=False, pool_factor=1, protected_tokens=0, clustering_mode='hierarchical')`

Tokenizes document strings and encodes them.

- `docs` must be a list or tuple of strings.
- `keep_dims=True` returns a padded 3-D tensor.
- `keep_dims=False` returns a list of per-document tensors.
- `keep_dims='flatten'` returns packed embeddings and `doclens`; with `return_tokens=True`, tokenized text is also included.
- `pool_factor > 1` only applies to the flattened path and uses hierarchical token pooling.
- `clustering_mode` is currently asserted as `'hierarchical'`.

With batching, documents are sorted by length and then restored to original order.

## QueryTokenizer

### `QueryTokenizer(config, verbose=3)`

Loads the raw tokenizer from `config.checkpoint` through ColBERT's Hugging Face wrapper. It records:

- `query_maxlen`
- `background_maxlen = 512 - query_maxlen + 1`
- `Q_marker_token_id` from `config.query_token_id`
- backbone `[CLS]`, `[SEP]`, `[MASK]`, and pad token IDs

### `tokenize(batch_text, add_special_tokens=False)`

Returns token strings. With `add_special_tokens=True`, it prepends `[CLS]` and the query marker, appends `[SEP]`, then fills the remaining query length with `[MASK]` tokens. Very long input can produce a negative mask-fill count; prefer `tensorize()` for truncation-aware behavior.

### `encode(batch_text, add_special_tokens=False)`

Returns token IDs. With `add_special_tokens=True`, it inserts the query marker and mask IDs like `tokenize()`.

### `tensorize(batch_text, bsize=None, context=None, full_length_search=False)`

Returns query IDs and attention masks, or a list of `(ids, mask)` mini-batches when `bsize` is set.

Important invariants:

- `batch_text` must be a list or tuple.
- The query marker is inserted at `ids[:, 1]`.
- Without context/full-length search, output width is `config.query_maxlen`.
- Pad IDs are replaced with mask token IDs after tokenization.
- If `config.attend_to_mask_tokens=True`, mask positions for `[MASK]` IDs are set to `1`.

## DocTokenizer

### `DocTokenizer(config)`

Loads the raw tokenizer from `config.checkpoint` and records `doc_maxlen`, `D_marker_token_id`, `[CLS]`, and `[SEP]` token IDs.

### `tokenize(batch_text, add_special_tokens=False)`

Returns token strings. With `add_special_tokens=True`, it prepends `[CLS]` and the document marker, then appends `[SEP]`.

### `encode(batch_text, add_special_tokens=False)`

Returns token IDs. With `add_special_tokens=True`, it inserts the document marker ID similarly.

### `tensorize(batch_text, bsize=None)`

Returns document IDs and attention masks, or `(batches, reverse_indices)` when `bsize` is set.

Important invariants:

- `batch_text` must be a list or tuple.
- The document marker is inserted at `ids[:, 1]`.
- Tokenization truncates at `doc_maxlen - 1`, then inserts the marker to produce width at most `doc_maxlen`.
- Padding is `longest`, so the output width may be shorter than `doc_maxlen` for short batches.

## Scoring Helpers

### `colbert_score(Q, D_padded, D_mask, config=ColBERTConfig())`

Scores query/document matrices with ColBERT late interaction. `Q` must be 3-D with first dimension `1` or `num_docs`; `D_padded` must be 3-D; `D_mask` masks padded document positions.

### `colbert_score_packed(Q, D_packed, D_lengths, config=ColBERTConfig())`

Scores one query against packed document embeddings and lengths. GPU and CPU paths differ; CPU may rely on the segmented MaxSim extension loaded by ColBERT modeling code.
