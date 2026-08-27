# Models and Encoders Troubleshooting

## Import and Install Issues

Symptoms:

- `ModuleNotFoundError` when loading a provider model.
- `ImportError` from wrappers for OpenAI, Voyage, Jina, Cohere, Bedrock, Gemini, vLLM, BM25, FAISS, audio, image, or video models.
- `pip check` reports incompatible optional dependencies.

Fixes:

1. Confirm base import: `python -c "import mteb; print(mteb.__version__)"`.
2. Install only the extra required by the model family, for example `pip install "mteb[bm25s]"` for BM25 baselines or the provider extra documented for an API wrapper.
3. Re-run `pip check` after installing extras.
4. For contributed wrappers, move optional imports inside `__init__`, `encode`, `predict`, `index`, or `search` so `import mteb` works without provider extras.

Expected signal: base `import mteb` works even if optional model families are unavailable; loading an optional model should fail with a clear missing-extra message.

## Unknown Model or Revision

Symptoms:

- `KeyError: Model '<name>' not found in MTEB registry`.
- Close-match suggestions are printed.
- `ValueError` says a requested revision does not match the registered revision.

Fixes:

- Check spelling and canonical organization/model name.
- Use `mteb.get_model_metas(model_names=[...])` or list/filter model metadata before loading.
- If intentionally loading a Hugging Face model not registered in MTEB, use APIs that fetch metadata from the Hub where appropriate, or instantiate `SentenceTransformer`/`CrossEncoder` directly.
- If reproducing benchmark results, use the exact `revision` recorded in `ModelMeta`.

## Prompt or Performance Regressions

Symptoms:

- Results are far below a published model card.
- Warnings mention ignored prompt keys or missing `query`/`document` prompts.
- Retrieval results look asymmetric or poor only for query/corpus tasks.

Fixes:

- Prefer `mteb.get_model(...)` for registered models because MTEB loaders often include required instructions/prefixes.
- Validate `model_prompts` keys against the priority scheme: `<task-name>-query`, `<task-name>`, `<task-type>-document`, `<task-type>`, then `query`/`document`.
- Confirm `prompt_type` is accepted and used in custom `encode(...)` methods.
- Keep prompt templates versioned with result directories and embedding caches.

## Custom Encoder Signature Mismatch

Symptoms:

- `TypeError: encode() got an unexpected keyword argument 'task_metadata'`.
- `TypeError: encode() got an unexpected keyword argument 'prompt_type'`.
- `TypeError: __init__() got an unexpected keyword argument 'device'` when loading from `ModelMeta` or CLI.
- Evaluation fails only when `encode_kwargs` are supplied.

Fixes:

1. Run `python sub-skills/models-and-encoders/scripts/validate_encoder_protocol.py module:object`.
2. Add keyword-only parameters `task_metadata`, `hf_split`, `hf_subset`, `prompt_type=None`, and `**kwargs` to `encode` or `predict`.
3. Add constructor support for `model_name`, `revision=None`, `device=None`, and `**kwargs` when the object is a loader target.
4. Remove unsupported values from `encode_kwargs`, or pass them through only to the underlying library methods that accept them.

Expected signal: the validator reports `encoder-like`, `cross-encoder-like`, or `search-like`, and warnings are limited to optional features.

## Bad Embedding Shapes, NaNs, or Dtypes

Symptoms:

- Similarity computation fails.
- Search wrapper reports NaN similarity scores.
- Downstream metrics fail on ragged arrays.
- Compression wrapper warns about unstable quantization thresholds.

Fixes:

- Ensure `encode(...)` returns a 2D numeric array shaped `(n_inputs, embed_dim)`.
- Convert GPU tensors to CPU tensors/arrays before returning if downstream code expects CPU-safe objects.
- Preserve input order exactly.
- Implement `similarity` and `similarity_pairwise`, or use a wrapper/base class that provides them.
- For `CompressionWrapper`, use enough embeddings to estimate quantization thresholds and validate `clipping_margin` as `0 < lower < upper < 1`.

## Search and Reranking Errors

Symptoms:

- `ValueError: Corpus must be indexed before searching.`
- `ValueError: CrossEncoder search requires top_ranked documents for reranking.`
- Retrieval output keys are missing or are numeric positions instead of task IDs.

Fixes:

- Call `index(corpus, ...)` before `search(queries, ...)` on `SearchProtocol` objects.
- Use a dense encoder or search model to generate first-stage candidates before a CrossEncoder reranker.
- In custom search implementations, return `{query_id: {corpus_id: score}}` with IDs from the task datasets.
- Do not reuse stateful search wrapper instances across unrelated corpora unless they explicitly support reset/re-indexing.

## Cache and Result Path Mistakes

Symptoms:

- Cached embeddings are reused after changing prompts, model revision, tokenizer, `embed_dim`, quantization, or modality options.
- Result files do not update after reruns.
- Cache files become very large or contain zero placeholders.

Fixes:

- Keep embedding cache directories separate from evaluation result directories.
- Version cache directories by model name, revision, prompt config, task, split, and key encode kwargs.
- Use `mteb.evaluate(..., cache=..., overwrite_strategy=...)` for result caching behavior and `CachedEmbeddingWrapper(..., cache_path=...)` for embedding caching; these are different cache layers.
- Choose a deliberate `overwrite_strategy`, such as the default `only-missing`, when rerunning partial results.
- Delete or archive stale embedding caches when changing model behavior.

## Dataset, Private Access, and Task Filters

Symptoms:

- Dataset download fails or asks for authentication.
- Expected tasks are missing from `get_tasks(...)`.
- A benchmark includes fewer tasks than expected.

Fixes:

- Use public tasks first unless credentials and licenses are configured.
- Remember that `get_tasks(...)` defaults include filters such as `exclude_superseded=True`, `exclude_private=True`, and `exclude_beta=True`.
- Set `exclude_private=False`, `exclude_beta=False`, or `exclude_superseded=False` only when the user intentionally wants those tasks and has access.
- Check `languages`, `modalities`, `exclusive_language_filter`, and `exclusive_modality_filter` when filtering multilingual or multimodal tasks.

## CLI and API Misuse

Symptoms:

- `mteb run` cannot load a custom class.
- CLI model kwargs are ignored or parsed unexpectedly.
- API examples work but CLI runs fail.

Fixes:

- For Python API workflows, pass an instantiated model object or `ModelMeta` directly into `mteb.evaluate`.
- For CLI workflows, make sure the model loader is importable and constructor-compatible with `model_name`, `revision`, `device`, and additional kwargs.
- Confirm the CLI command group exists with `mteb --help`; available command families include `run`, `available-tasks`, `available-benchmarks`, `create-model-results`, and `leaderboard`.
- Use the evaluation sub-skill for full run orchestration and this sub-skill only for model object/protocol preparation.

## Optional Provider Extra Missing Case

For OpenAI/Voyage/Jina/vLLM-style wrappers, a good debug sequence is:

```bash
python -c "import mteb; print('mteb import ok')"
python -m pip check
python -c "import importlib; importlib.import_module('provider_package_name')"
python sub-skills/models-and-encoders/scripts/validate_encoder_protocol.py your_module:your_model_object
```

If the provider package import fails, install the matching extra or dependency group before changing MTEB code. If the protocol validator fails after the provider import succeeds, fix the wrapper method names/signatures.
