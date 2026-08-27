# TypeScript OSS Providers

TypeScript OSS usage imports `Memory` from `mem0ai/oss`. The current package metadata inspected in the repository reports `mem0ai` version `3.0.9` for the TypeScript package.

## Config Shape

```ts
import { Memory } from "mem0ai/oss";

const memory = new Memory({
  embedder: {
    provider: "openai",
    config: { apiKey: process.env.OPENAI_API_KEY, model: "text-embedding-3-small" },
  },
  vectorStore: {
    provider: "memory",
    config: { collectionName: "memories", dimension: 1536 },
  },
  llm: {
    provider: "openai",
    config: { apiKey: process.env.OPENAI_API_KEY, model: "gpt-5-mini" },
  },
  historyStore: {
    provider: "sqlite",
    config: { historyDbPath: "memory.db" },
  },
});
```

The TypeScript config manager merges user config with defaults and validates with a Zod schema. Defaults are OpenAI embedder/LLM, in-memory vector store, SQLite history, `version: "v1.1"`, and `disableHistory: false`.

## Provider Names

TypeScript OSS factories support these provider strings:

- Embedders: `openai`, `ollama`, `lmstudio`, `google`, `gemini`, `azure_openai`, `langchain`
- LLMs: `openai`, `openai_structured`, `anthropic`, `groq`, `ollama`, `lmstudio`, `google`, `gemini`, `azure_openai`, `mistral`, `langchain`, `deepseek`
- Vector stores: `memory`, `qdrant`, `redis`, `supabase`, `langchain`, `vectorize`, `azure-ai-search`, `pgvector`
- History stores: `sqlite`, `supabase`, `memory`

The docs may describe a smaller TypeScript provider set; prefer the installed factory when resolving an actual project.

## Dimension Behavior

TypeScript differs from Python in dimension naming and startup behavior:

- Vector store config uses `dimension`, not Python's `embedding_model_dims`.
- Embedder config uses `embeddingDims`, but the config manager also normalizes Python-style `embedding_dims` for LM Studio/OpenClaw compatibility.
- If no explicit `dimension` or `embeddingDims` is supplied, `Memory` auto-detects dimension by running a probe embedding before creating the vector store.
- If dimension auto-detection fails, set either `vectorStore.config.dimension` or `embedder.config.embeddingDims` explicitly.
- Explicit `vectorStore.config.dimension` wins over `embedder.config.embeddingDims`.

## Naming and Casing Differences

- Python top-level keys are snake_case: `vector_store`, `history_db_path`, `custom_instructions`.
- TypeScript top-level keys are camelCase: `vectorStore`, `historyDbPath`, `customInstructions`.
- Python entity filters use `user_id`, `agent_id`, `run_id`. TypeScript accepts camelCase in add options, but search/getAll validation expects entity scope inside `filters`; normalize to snake_case in persisted filters when debugging cross-SDK behavior.
- TypeScript vector provider `azure-ai-search` uses hyphens; Python uses `azure_ai_search`.

## Peer Dependencies

Core TypeScript dependencies include `axios`, `openai`, `uuid`, and `zod`. Provider-specific packages are peer dependencies, so install only what your selected provider needs:

- Qdrant: `@qdrant/js-client-rest`
- Redis: `redis`
- Supabase vector/history: `@supabase/supabase-js`
- SQLite history: `better-sqlite3`
- Anthropic: `@anthropic-ai/sdk`
- Google/Gemini: `@google/genai`
- Groq: `groq-sdk`
- Ollama: `ollama`
- Mistral: `@mistralai/mistralai`
- Azure Search/identity: `@azure/search-documents`, `@azure/identity`
- PGVector: `pg` and `@types/pg` for TypeScript builds
- LangChain adapters: `@langchain/core`
- BM25/entity utilities can use `natural` and `compromise` when installed.

## Search and Validation Boundaries

- Search rejects top-level entity parameters; pass scope inside `filters`.
- `threshold` must be a number from 0 to 1; `topK` must be a non-negative integer.
- `referenceDate` and `decay` are not supported by OSS TypeScript Memory; they produce explicit feature errors/notices.
- `disableHistory: true` swaps in an in-memory/dummy history manager and avoids SQLite history writes.
- For basic add/search/get/update/delete workflows after provider setup, switch to `../sdk-memory/SKILL.md`.
