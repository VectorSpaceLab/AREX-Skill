# Integrations and Storage Troubleshooting

## `ModuleNotFoundError: llama_index.llms.openai`

Likely cause: only `llama-index-core` is installed. Core imports use `llama_index.core...`; OpenAI LLM support is an integration package.

Check first:

```bash
python sub-skills/integrations-and-storage/scripts/check_integration_imports.py \
  --dist llama-index-core --module llama_index.core \
  --dist llama-index-llms-openai --module llama_index.llms.openai
```

Fix narrowly:

```bash
pip install llama-index-llms-openai
```

If the user wants the starter install instead, `pip install llama-index` includes core plus default OpenAI-oriented integrations, but it is broader than necessary for a customized environment.

## Import Path Mismatch

Symptoms:

- `pip show llama-index-vector-stores-qdrant` succeeds, but `from llama_index.vectorstores.qdrant import ...` fails.
- Code imports from `llama_index.core.llms.openai` or another provider under `core`.
- A hyphenated provider distribution is transformed incorrectly into a module path.

Fixes:

- Use `llama_index.vector_stores.<provider>`, not `llama_index.vectorstores.<provider>`.
- Use `llama_index.llms.<provider>` and `llama_index.embeddings.<provider>` for integrations.
- Read the package's `tool.llamahub.import_path` metadata when available.
- Use the bundled checker with both `--dist` and `--module` so distribution and namespace are verified separately.

## Missing Optional Provider Package

If a class imports but a provider dependency fails, install the integration package that owns the provider instead of manually installing random transitive dependencies.

Examples:

- OpenAI LLM: `llama-index-llms-openai` owns the OpenAI client dependency.
- HuggingFace embeddings: `llama-index-embeddings-huggingface` owns sentence-transformer/HuggingFace dependencies.
- Qdrant vector store: `llama-index-vector-stores-qdrant` owns `qdrant-client` and compatible core bounds.
- File readers: `llama-index-readers-file` owns common file parser dependencies, with some extra parser backends remaining optional.

When a package defines extras, install the specific extra only when the requested feature needs it.

## Credentials and Environment Variables

If imports pass but provider calls fail, check credentials and endpoint setup before changing LlamaIndex code.

Common checks:

- API key variable exists, is non-empty, and matches the provider expected by the integration.
- Base URL, region, deployment name, project ID, and organization/account values match the provider account.
- Local services such as Ollama, Qdrant, Chroma server, Milvus, Redis, Elasticsearch, or Postgres are running and reachable.
- Cloud services allow the current network, IP, VPC, or firewall policy.
- Model name and embedding dimension match the provider collection/index configuration.

Do not place secrets in generated skill content or example files. Prefer placeholders and environment-variable names.

## Service Unavailable or Network-Skipped Environments

Some failures are environmental rather than code defects:

- No outbound network access in CI or sandbox.
- Local daemon not started.
- Provider rate limit, quota, billing, or region outage.
- TLS/proxy configuration blocks SDK calls.
- Model download blocked for local embedding providers.

For a safe offline check, run `check_integration_imports.py`; it only imports modules and reads metadata. For actual provider smoke tests, ask the user before running networked or credentialed calls.

## Vector Store Persistence Surprises

Symptoms:

- Code calls `persist()` but no local files appear.
- Reloading from `persist_dir` does not find vectors stored in a provider service.
- Data disappears after restart when an in-memory backend was used.
- Querying an existing vector database returns IDs but no text nodes.

Diagnosis:

- Core/simple stores persist to `persist_dir`; provider-backed vector stores usually persist in the provider backend.
- Recreate `StorageContext` with the same provider client, collection/index name, and embedding model configuration on reload.
- For local directories with multiple indexes, set and reuse stable index IDs.
- Confirm whether the vector store stores text/documents. If not, pair it with a docstore or configure node storage in the index path.
- Verify collection/index dimensions match the embedding model; dimension mismatches are provider errors, not LlamaIndex persistence errors.

## Core and Plugin Version Compatibility

For this skill, live verified core is `llama-index-core==0.14.22`; compatible integrations in this repo generally declare upper bounds such as `<0.15`.

If imports break after upgrades:

1. Check installed versions with the bundled script or `pip show`.
2. Upgrade the specific integration package that owns the failing import.
3. Keep core and integrations on the same minor line when possible.
4. Remove stale editable/source installs that shadow site-packages.
5. Avoid mixing old monolithic `llama-index` expectations with modern split integration packages.

## When to Route Away

- If package and provider setup are correct but retrieval is empty or synthesis is wrong, use `../indexing-and-querying/SKILL.md`.
- If the failure is file discovery, parsing, chunk overlap, ingestion cache, or reader arguments, use `../ingestion-and-loading/SKILL.md`.
- If model-specific prompts, structured outputs, JSON schemas, or tool-calling parameters are the issue, use `../customization-and-structured-outputs/SKILL.md`.
