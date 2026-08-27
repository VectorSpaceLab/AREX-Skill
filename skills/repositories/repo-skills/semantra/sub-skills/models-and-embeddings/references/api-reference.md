# Models API Reference

## Purpose

Read this when a task needs verified Semantra model classes, method signatures,
registry defaults, or behavior that is not visible from the CLI alone.

## Base model contract

All Semantra model backends inherit the same conceptual interface:

| Method | Purpose |
| --- | --- |
| `get_num_dimensions()` | Return embedding width. |
| `get_tokens(text)` | Convert raw text to backend token representation. |
| `get_token_length(tokens)` | Count backend tokens. |
| `get_text_chunks(text, tokens)` | Convert token offsets back to text chunks. |
| `get_config()` | Return JSON-serializable model config used in cache hashing. |
| `embed(tokens, offsets, is_query=False)` | Embed token ranges. |
| `embed_document(document)` | Embed one document string by tokenizing and embedding its full token span. |
| `embed_query(query)` | Embed one query string. |
| `embed_queries(queries)` | Sum weighted query embeddings. |
| `embed_queries_and_preferences(queries, preferences, documents)` | Combine query embeddings with positively/negatively tagged result embeddings. |
| `is_asymmetric()` | Return whether query and document tokenization differ. |

`queries` are dictionaries with `query` and `weight`. `preferences` point at
stored document embeddings and carry `weight` values from the web UI.

## Verified constructors and functions

Installed inspection verified these signatures for Semantra 0.1.12:

```python
OpenAIModel(model_name='text-embedding-ada-002', num_dimensions=1536, tokenizer_name='cl100k_base')
TransformerModel(model_name, doc_token_pre=None, doc_token_post=None, query_token_pre=None, query_token_post=None, asymmetric=False, cuda=None)
mean_pooling(model_output, attention_mask)
as_numpy(x)
```

`TransformerModel(..., cuda=None)` uses `torch.cuda.is_available()`. If CUDA is
true, the model and tensors are moved to CUDA. Use `cuda=False` only in custom
Python code when CPU behavior is required despite visible CUDA.

## OpenAI model behavior

`OpenAIModel`:

- requires `OPENAI_API_KEY` in the environment when constructed;
- sets `openai.api_key` from that environment variable;
- uses a `tiktoken` tokenizer named `cl100k_base` by default;
- reports config fields `model_type='openai'`, `model_name`, and
  `tokenizer_name`;
- embeds by calling the legacy `openai.Embedding.create(model=..., input=...)`
  API.

Because current OpenAI SDKs removed that legacy call path, inspect SDK
compatibility before relying on OpenAI mode.

## Transformer model behavior

`TransformerModel`:

- loads `AutoTokenizer.from_pretrained(model_name)`;
- loads `AutoModel.from_pretrained(model_name)`;
- optionally encodes query/document pre/post tokens;
- returns mean-pooled token embeddings;
- reports config fields `model_type='transformers'`, `model_name`, all
  pre/post token strings, and `asymmetric`;
- returns model dimension from `model.config.hidden_size`.

The first construction of a model can download files from Hugging Face. The
registry inspection helper intentionally avoids calling `get_model` factories so
it does not instantiate these objects.

## Preset registry shape

The `models` registry maps preset names to dictionaries containing static
metadata and a `get_model` factory. Verified static defaults:

```json
{
  "openai": {"cost_per_token": 0.0000004, "pool_size": 50000, "pool_count": 2000},
  "minilm": {"cost_per_token": null, "pool_size": 50000},
  "mpnet": {"cost_per_token": null, "pool_size": 15000},
  "sgpt": {"cost_per_token": null, "pool_size": 10000},
  "sgpt-1.3B": {"cost_per_token": null, "pool_size": 1000}
}
```

Semantra's CLI resolves the registry like this:

1. If `--transformer-model` is provided, construct `TransformerModel` for that
   model name and use default transformer pool size `15000` unless overridden.
2. Otherwise, look up the selected `--model` preset.
3. Fill `--pool-size` and `--pool-count` from the selected preset when omitted.
4. Reject `--svm` if the selected model reports `is_asymmetric()`.

## Query/preference embedding combination

The browser normalizes query and preference weights before sending them to the
server. The server calls `embed_queries_and_preferences`, which sums:

- weighted embeddings for typed query phrases; and
- weighted stored embeddings for selected search-result preferences.

This means preferences operate directly in the same embedding vector space as
query text. For parser and normalization details, use
[interactive query semantics](../../interactive-search/references/query-semantics.md).
