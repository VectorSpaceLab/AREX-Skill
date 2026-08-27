# Embeddings and Semantic Search

## Purpose

Read this when the task is to enable semantic search, inspect embedding providers, or troubleshoot optional vector search behavior.

## Verified provider surface

The package supports a provider-aware embedding store and `get_provider()` routing for:

- local sentence-transformers embeddings,
- OpenAI-compatible endpoints,
- Google Gemini,
- MiniMax,
- and Voyage.

The default package install is enough for the CLI and graph workflows, but local embeddings require the optional `embeddings` extra.

## Typical workflow

1. Install the needed extra only when semantic search is actually required:
   ```bash
   pip install "code-review-graph[embeddings]"
   ```
2. Build or update the graph.
3. Run the embedding workflow.
4. Use semantic search when keyword search is insufficient.

## Provider notes

- Local embeddings use sentence-transformers and a configurable model name.
- Cloud providers are opt-in and should only be used when the user has explicitly accepted external egress.
- `get_provider()` validates provider names instead of silently falling back.
- The embedding store can refresh only when the requested provider/model identity matches the stored embeddings.

## What to expect

- Local embeddings may need an initial model download.
- Semantic search can fall back to keyword/FTS search when embeddings are unavailable.
- Embedding refresh should purge orphan vectors and preserve the active provider/model identity.

## Troubleshooting cues

- Missing local embedding dependency: install the embeddings extra.
- Unknown provider name: check the exact provider spelling.
- Cloud provider warnings: confirm the needed environment variables and that the user accepted external egress.
- Refresh refuses to migrate: the requested provider/model does not match existing stored embeddings.

## Native evidence

Relevant tests cover provider validation, local initialization, concurrency behavior, refresh/purge behavior, docstring text used for embeddings, and fallback behavior when optional dependencies are absent.
