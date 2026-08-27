# Modeling and Tokenization Guide

## Mental Model

ColBERT represents queries and passages as matrices of contextual token embeddings. It does not collapse each text into one pooled vector. At scoring time, each query token finds its best matching document token, and ColBERT sums those per-query-token maxima. This is the MaxSim/late-interaction design that separates model/tokenizer behavior from indexing and retrieval orchestration.

The modeling path is:

1. `ColBERTConfig` supplies checkpoint, model, tokenizer, max-length, marker-token, dimension, device, and scoring fields.
2. `Checkpoint(name, colbert_config=None, verbose=3)` loads checkpoint metadata, merges explicit config overrides, initializes a Hugging Face-backed ColBERT model, and creates query/document tokenizers.
3. `QueryTokenizer.tensorize()` and `DocTokenizer.tensorize()` convert lists of strings into token IDs and masks with ColBERT marker tokens inserted.
4. `Checkpoint.queryFromText()` and `Checkpoint.docFromText()` encode tokenized text through the backbone model and ColBERT projection.
5. Scoring helpers use late interaction over query and document embedding matrices.

## Checkpoint Loading

`Checkpoint` accepts:

- A local ColBERT checkpoint directory containing model/tokenizer files and usually `artifact.metadata`.
- A legacy `.dnn` file.
- A Hugging Face model or repo name when remote/cache access is intentional.

The constructor calls `ColBERTConfig.from_existing(ColBERTConfig.load_from_checkpoint(name), colbert_config)`. This means saved checkpoint metadata is loaded first, then assigned fields from the explicit `colbert_config` override it.

If `ColBERTConfig.load_from_checkpoint(name)` returns `None`, the path/name likely does not contain ColBERT metadata. This can happen for generic backbones such as `bert-base-uncased` or checkpoint directories missing `artifact.metadata`. In that case, pass an explicit `ColBERTConfig(checkpoint=name, ...)` and verify that the resulting model weights are compatible.

Hugging Face-backed loading can access the network or local cache through `hf_hub_download()`, `from_pretrained()`, and `AutoTokenizer.from_pretrained()`. For offline or reproducible work, use local checkpoint directories and the bundled scripts without `--allow-remote`.

## Marker Tokens

ColBERT uses logical marker labels but stores marker IDs through tokenizer vocabulary tokens:

- Query label: `config.query_token='[Q]'`.
- Query vocabulary token: `config.query_token_id='[unused0]'`.
- Document label: `config.doc_token='[D]'`.
- Document vocabulary token: `config.doc_token_id='[unused1]'`.

Both tokenizers insert the marker ID at column `1`, immediately after the first special token from the backbone tokenizer. With BERT-style tokenizers, this means `[CLS]` at column `0`, `[unused0]` or `[unused1]` at column `1`, text tokens after that, and `[SEP]` before padding/masks.

Do not pass text that already includes marker tokens expecting ColBERT to preserve them as structural markers. Let `QueryTokenizer` or `DocTokenizer` insert markers exactly once.

## Query Tokenization

`QueryTokenizer(config, verbose=3)` loads the raw tokenizer from `config.checkpoint` and records `query_maxlen`, marker IDs, special token IDs, and `background_maxlen`.

`tensorize(batch_text, bsize=None, context=None, full_length_search=False)` behavior:

- `batch_text` must be a list or tuple.
- Normal output width is `config.query_maxlen`.
- The raw tokenizer uses `max_length=query_maxlen - 1`; ColBERT then inserts the query marker at column `1`.
- Pad token IDs are replaced with `[MASK]` token IDs.
- The attention mask keeps normal padding semantics unless `attend_to_mask_tokens=True`.
- `context` appends background tokens after the query, with one context entry per query.
- `full_length_search=True` is valid only for a single query in a list and expands width up to `min(500, max(query_maxlen, observed_length))`.

Unexpected `[MASK]` tokens in decoded query output are usually normal query padding, not necessarily model corruption.

## Document Tokenization

`DocTokenizer(config)` loads the raw tokenizer from `config.checkpoint` and records `doc_maxlen`, marker IDs, and special token IDs.

`tensorize(batch_text, bsize=None)` behavior:

- `batch_text` must be a list or tuple.
- The raw tokenizer uses `max_length=doc_maxlen - 1`; ColBERT then inserts the document marker at column `1`.
- Padding is `longest`, so short batches may produce widths below `doc_maxlen`.
- With `bsize`, tokenized documents are sorted by length for efficient batching and returned with `reverse_indices`.

Document truncation surprises are usually caused by `doc_maxlen`, not by indexing. Lowering `doc_maxlen` can silently remove passage tail tokens before embedding.

## Punctuation Masking

When `config.mask_punctuation=True`, `ColBERT` builds a skiplist for punctuation strings and their token IDs from the raw tokenizer. `ColBERT.doc()` uses this skiplist to zero/remove punctuation document embeddings along with pad tokens. Queries do not use the punctuation skiplist in the same way; query masking only removes pad tokens.

If punctuation appears in decoded tokenizer output but seems absent from document embeddings, check `mask_punctuation` before changing the tokenizer.

## Encoding Outputs

`Checkpoint.queryFromText(queries, ...)` returns normalized query embeddings. Default shape is `(num_queries, query_maxlen, dim)`.

`Checkpoint.docFromText(docs, ...)` supports several output modes:

- `keep_dims=True`: padded 3-D tensor shaped like `(num_docs, observed_doc_width, dim)`.
- `keep_dims=False`: list of unpadded per-document tensors.
- `keep_dims='flatten'`: packed 2-D embeddings plus `doclens`; useful for packed scoring or indexing-style flows.
- `return_tokens=True`: includes tokenized text from the batched tokenizer path.
- `to_cpu=True`: returns CPU tensors for inspection and downstream CPU consumers.

On GPU, document embeddings are half precision; on CPU, they stay CPU tensors. Always inspect `.shape`, `.device`, and `.dtype` before mixing outputs with custom scoring code.

## Native Validation Anchors

The repository tokenizer tests validate these invariants:

- `QueryTokenizer.tensorize()` returns IDs/masks shaped `(num_queries, config.query_maxlen)` for normal query batches.
- Query marker IDs occupy `ids[:, 1]`.
- Document marker IDs occupy `ids[:, 1]`.
- ColBERTv2 known examples have stable IDs/masks when the Hugging Face checkpoint is available.

Use those invariants when adapting tokenization behavior or building smoke tests. Skip network-dependent checks unless the user explicitly allows Hugging Face access.
