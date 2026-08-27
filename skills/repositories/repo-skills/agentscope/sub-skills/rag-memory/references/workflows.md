# Workflows

## Purpose

Read this for the concrete flows that connect parsing, chunking, embedding, vector search, and agent-side memory.

## 1) Standalone RAG indexing and search

This is the simplest path:

1. Choose an embedding model.
2. Create a parser and chunker.
3. Create a `KnowledgeBase` with a vector store.
4. Parse bytes into sections.
5. Chunk the sections.
6. Insert the chunks.
7. Search the knowledge base.

The bundled `scripts/index_and_search.py` follows that shape with an in-memory Qdrant store and a DashScope embedding model.

## 2) Attach RAG to an agent

`RAGMiddleware` adds the retrieval step to an `Agent`:

- `static` mode injects search results automatically.
- `agentic` mode exposes a `search_knowledge` tool and lets the agent decide when to search.

The bundled `scripts/integrate_with_agent.py` shows both modes against the same knowledge base.

## 3) Filesystem memory

`AgenticMemoryMiddleware` stores durable memory in a workspace directory. The workflow is:

1. Create or reuse a workspace directory.
2. Let the agent read/write Markdown memory files under `Memory/`.
3. Reuse the same workspace for later turns.

The bundled `scripts/agentic_memory_demo.py` uses a fresh workspace, shows the saved Markdown files, and demonstrates recall in a later turn.

## 4) mem0 memory

`Mem0Middleware` is the AgentScope adapter around mem0.

Key choices:

- `mode='static_control'` for automatic memory injection and write-back.
- `mode='agent_control'` when the agent should call `search_memory` / `add_memory` itself.
- `mode='both'` when you want both behaviors.
- `client` wins over `mem0_config`, and the tests assert that a warning is logged if other backend kwargs are ignored.

Important notes:

- The `user_id` is required.
- The `embedding_model` and `chat_model` path is useful when you want AgentScope to drive mem0.
- Qdrant path locking matters if you build multiple local mem0 clients from the same store.

## 5) ReMe memory

`ReMeMiddleware` is the embedded ReMe app integration.

Key choices:

- `workspace_dir` selects where the memory cards live.
- `parameters.chat_model` and `parameters.embedding_model` drive the embedded app.
- `mode='static_control'`, `mode='agent_control'`, or `mode='both'` decides how retrieval is exposed.
- `session_id` is read from the agent state and scopes write-back.
- Reindexing matters when you need fresh cards to be searchable immediately.

The tests and demo confirm that one middleware instance can be shared across agents because ReMe reads the session id at hook time.

## Flow selection guide

| Need | Best flow |
| --- | --- |
| Index and search a local corpus | standalone RAG indexing/search |
| Use retrieval inside an agent turn | agent-attached RAG |
| Save simple durable notes in a workspace | filesystem memory |
| Use a hosted or OSS memory service | mem0 |
| Use the embedded ReMe memory app | ReMe |

## When to read this vs the vector-store reference

- Read `vector-stores.md` when the problem is the backend store or dimension choice.
- Read this file when the problem is the retrieval or memory workflow itself.
