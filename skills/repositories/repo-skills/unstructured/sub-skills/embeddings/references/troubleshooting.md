# Embedding Troubleshooting

## Missing SDK or Optional Dependency

Symptoms:
- `ImportError` or dependency-guard messages when `get_client()` runs.
- Provider imports succeed only until a concrete SDK class is needed.

Fixes:
- Install only the provider SDK needed for the chosen encoder.
- For OpenAI, install `langchain_openai`.
- For OctoAI, install `openai` and `tiktoken`.
- For Mixedbread AI, install `mixedbread_ai`.
- For VoyageAI, install `voyageai`; install `tqdm` only if `show_progress_bar=True`.
- For Vertex AI, install `langchain` and `langchain_google_vertexai`.
- For Bedrock, install `boto3` and `langchain_community`.
- For HuggingFace, expect heavier local ML dependencies such as `torch`, `transformers`, and model download support.

Use `scripts/embedding_config_check.py` for import checks that do not contact providers.

## Missing or Unsafe Credentials

Symptoms:
- Pydantic validation errors for required key fields.
- Provider authentication failures.
- Vertex AI credential JSON parsing or Google application credential issues.
- Mixedbread `initialize()` complaining that no API key was provided.

Fixes:
- Read secrets from runtime environment variables or secret managers, not source files.
- Pass only the value into the config; never print `SecretStr.get_secret_value()`.
- For Mixedbread, set `MXBAI_API_KEY` or pass `api_key` explicitly.
- For OpenAI, OctoAI, VoyageAI, Vertex AI, and Bedrock, build configs from approved runtime secrets.
- For Vertex AI, remember `get_client()` writes service-account JSON to a temporary credentials file and sets `GOOGLE_APPLICATION_CREDENTIALS`; avoid calling it in dry-run checks.

Do not serialize credentials into element metadata, test cases, vector-store payloads, logs, exception wrappers, or generated examples.

## Provider Rate Limits or Network Failures

Symptoms:
- Timeout, retry, quota, or HTTP 429/5xx errors.
- Large `embed_documents()` calls fail partway through.
- OctoAI appears slow because it embeds one element at a time.

Fixes:
- Batch deliberately before calling providers, especially for providers without built-in batching.
- For VoyageAI, rely on its token-aware batching and known model token limits, but still handle provider errors around each batch.
- For Mixedbread, note the implementation uses batch size 128, timeout 60 seconds, and 3 retries once initialized.
- Add application-level retry/backoff and idempotent persistence so partial embedding runs can resume safely.
- Keep raw text and element IDs available for re-embedding after transient provider failures.

## Empty Texts and Bad Inputs

Symptoms:
- Empty vectors, provider validation errors, or low-quality retrieval results.
- Assertion errors because the provider returned fewer vectors than input elements.

Fixes:
- Filter or mark elements where `str(element).strip()` is empty before embedding.
- Avoid embedding image-only, formula-only, checkbox-only, or structural elements unless their text representation is useful.
- Preserve original element order if you filter, then reattach vectors only to the corresponding elements.
- Keep a skipped-elements report in the application layer rather than creating fake vectors.

## Dimension Mismatches

Symptoms:
- Vector-store insert errors because vector length differs from index dimension.
- Query vectors cannot search an existing index.
- Mixed provider/model results appear in the same collection.

Fixes:
- Record provider, model name, and optional output dimension with each index configuration.
- Validate one query vector and one document vector before bulk insertion.
- Do not mix OpenAI, VoyageAI, HuggingFace, Bedrock, Vertex AI, OctoAI, or Mixedbread vectors in the same vector space unless the store separates them.
- For VoyageAI, keep `output_dimension` identical for documents and queries.

## Metadata Loss After Embedding

Symptoms:
- `element_id`, `metadata.page_number`, table metadata, coordinates, or data-source metadata disappear after enrichment.
- Serialized JSON contains only text and embeddings.

Fixes:
- Pass existing `Element` objects to `embed_documents()` and persist those same objects.
- Do not rebuild elements from strings after embedding.
- Assert before/after metadata snapshots in tests for important fields.
- If embedding chunks, decide whether `metadata.orig_elements` should be kept using the `chunking` sub-skill before embedding.
- Keep enrichment provenance non-secret: provider name, model name, vector dimension, and application run ID are acceptable; API keys and provider request payloads are not.

## HuggingFace Heavy Dependency Problems

Symptoms:
- Long installs, `torch` import errors, model download failures, CPU memory pressure, or GPU device selection errors.
- Slow first embedding call because the model is being downloaded or loaded.

Fixes:
- Prefer `model_kwargs={"device": "cpu"}` unless a GPU runtime is known to exist.
- Pre-warm or cache models in controlled environments; set `cache_folder` when the deployment requires an explicit cache location.
- Avoid claiming offline execution unless the model files already exist in the environment.
- For lightweight CI checks, mock `HuggingFaceEmbeddingConfig.get_client()` rather than loading a real model.

## Secret-Safe Logging

Never log:
- API keys, service-account JSON, AWS secret keys, bearer tokens, or provider client objects.
- Full provider request payloads if they may include sensitive document text.
- Serialized element JSON containing confidential text or embeddings unless the destination is approved.

Safe to log:
- Provider name, model name, count of elements embedded, skipped empty count, vector dimension, elapsed time, and exception class.
- Whether a required environment variable is present, but not its value.

## Testing Without Real Providers

Use mocked clients like the repository tests:
- Patch each config's `get_client()` to return a fake client.
- Return predictable embeddings with the same count as input elements.
- Assert original text and metadata remain present after `embed_documents()`.
- Assert `embed_query()` passes provider-specific query mode when applicable, such as VoyageAI `input_type="query"`.

This is safer than live provider tests for generated skills because it avoids credentials, network variability, rate limits, and cost.
