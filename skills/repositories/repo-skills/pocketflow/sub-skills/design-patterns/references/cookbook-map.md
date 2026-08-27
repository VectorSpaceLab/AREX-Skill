# PocketFlow cookbook map

This page maps common user intents to PocketFlow recipe families and notes the usual optional dependencies or service assumptions.

## Chat and conversation memory

- **Intent**: build a simple terminal chat bot or memory-augmented assistant.
- **Pattern**: workflow or a short self-looping agent.
- **Typical extras**: an LLM provider SDK and API key.
- **Notes**: keep conversation history in shared state and keep the chat transport thin.

## Workflow writing

- **Intent**: outline, draft, rewrite, and style text in stages.
- **Pattern**: fixed workflow.
- **Typical extras**: an LLM provider SDK and API key.
- **Notes**: stage boundaries should be explicit and easy to validate.

## Agent research

- **Intent**: decide whether to search or answer based on gathered context.
- **Pattern**: agent decision loop.
- **Typical extras**: LLM provider SDK, search API or web-search wrapper.
- **Notes**: action names should be small and unambiguous.

## RAG

- **Intent**: retrieve relevant document chunks and answer from them.
- **Pattern**: offline indexing plus online retrieval.
- **Typical extras**: embedding provider, vector index or search backend, LLM provider.
- **Notes**: keep chunking, embedding, and retrieval as separately testable steps.

## Map-reduce

- **Intent**: process many files, items, or records and combine the results.
- **Pattern**: BatchNode map followed by reduce.
- **Typical extras**: usually just the LLM provider if the map step is generative.
- **Notes**: design the reduce node to handle empty inputs and partial results.

## Streaming chat

- **Intent**: show partial responses and support interruption.
- **Pattern**: async flow plus transport loop.
- **Typical extras**: LLM streaming support.
- **Notes**: keep interrupt handling outside the core graph if possible.

## Agent skills

- **Intent**: select reusable instruction files and inject them into a graph.
- **Pattern**: workflow or agent with skill selection.
- **Typical extras**: local Markdown skill files, LLM provider.
- **Notes**: this is a routing problem; keep the skill loader small and explicit.

## Coding agent

- **Intent**: read files, patch code, run commands, and loop until tests pass.
- **Pattern**: tool-routing agent with self-loop.
- **Typical extras**: LLM provider and shell access.
- **Notes**: keep patching logic separate from command execution.

## Text-to-SQL

- **Intent**: turn a question into SQL, run it, and debug errors.
- **Pattern**: workflow with validation/debug loop.
- **Typical extras**: LLM provider and SQLite or another database.
- **Notes**: schema retrieval and SQL validation are separate concerns.

## Deep research

- **Intent**: plan queries, search in parallel, synthesize, and iterate when gaps remain.
- **Pattern**: planner + batch research + review loop.
- **Typical extras**: LLM provider and search API.
- **Notes**: keep the final synthesis node responsible for deciding whether to loop again.

## FastAPI / background job apps

- **Intent**: expose a graph through a web app with progress updates.
- **Pattern**: service wrapper around a workflow.
- **Typical extras**: web framework, background job or queue abstraction, optional SSE/WebSocket.
- **Notes**: the graph should remain transport-agnostic.

## Voice chat

- **Intent**: record speech, transcribe it, answer, and synthesize speech.
- **Pattern**: async service workflow.
- **Typical extras**: audio device support, speech provider APIs, and usually an LLM provider.
- **Notes**: separate audio capture/playback from graph logic.
