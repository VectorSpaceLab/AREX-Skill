---
name: embeddings-and-generative
description: "Select Chonkie embedding models, provider embeddings, and
  generative chunking workflows without hidden network assumptions."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Chonkie embeddings and generative workflows

Use this sub-skill when a task depends on embedding vectors, semantic/late/neural/LLM chunking, embedding-based refinement, or provider-backed generation inside Chonkie.

## Route here for

- Selecting or wiring `AutoEmbeddings`, `BaseEmbeddings`, `Model2VecEmbeddings`, `SentenceTransformerEmbeddings`, `CatsuEmbeddings`, provider embedding wrappers, or `LiteLLMEmbeddings`.
- Adding chunk embeddings with `EmbeddingsRefinery` before retrieval, export, or vector storage.
- Operating `SemanticChunker`, `LateChunker`, `NeuralChunker`, or `SlumberChunker` with explicit optional dependencies, model cache/download, credential, batching, and timeout decisions.
- Debugging provider `Genie` classes used by `SlumberChunker`: OpenAI, Azure OpenAI, Gemini, Groq, and Cerebras.

## Route elsewhere first

- Deterministic token/sentence/recursive/table/code chunking and `Chunk`/tokenizer contracts: `../chunking-and-types/`.
- Pipeline placement, CHOMP ordering, file processing, chefs, and refinery orchestration: `../pipelines-and-processing/`.
- Chonkie Cloud, local FastAPI/API schemas, and CLI deployment: `../interfaces-and-deployment/`.
- Vector DB handshakes and chunk/document storage targets: `../integrations-and-storage/`.

## Operating procedure

1. Identify whether the user needs **local embeddings**, **third-party provider embeddings**, **model-dependent chunking**, or **generative LLM chunking**.
2. Read `references/embeddings-reference.md` for embedding/provider selection, constructor arguments, extras, credentials, and batching/timeout notes.
3. Read `references/model-dependent-chunking.md` before using `EmbeddingsRefinery`, `SemanticChunker`, `LateChunker`, `NeuralChunker`, or `SlumberChunker`.
4. Run `scripts/optional_dependency_probe.py` to inspect installed optional modules without making network calls. Use `--instantiate-safe` only for the script's safe no-network checks.
5. If optional dependencies, credentials, models, or services are missing, read `references/troubleshooting.md` and select a deterministic fallback or ask the user to authorize the required install/network/API-key path.

## Verification boundary

The Chonkie skill's required environment only verified CPU-local core package behavior. Model downloads, accelerator use, third-party provider APIs, provider credentials, and live generative calls are optional and must be treated as unverified unless the current user explicitly supplies and authorizes those resources.
