---
name: brain-qa
description: "Ask a Quivr brain questions, stream answers, inspect retrieval
  metadata, and route web search when needed."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Brain QA

Use this sub-skill when the brain already exists and the task is about asking
questions, streaming answers, inspecting search results, or tuning retrieval and
tool routing.

## Start here

- For live API signatures and object names, read `../../references/api-reference.md`.
- For the canonical QA workflow, read `references/workflows.md`.
- For failure modes and stale-example warnings, read `references/troubleshooting.md`.
- For a safe executable smoke path, run `../../scripts/text_brain_smoke.py --phase qa`.

## What this sub-skill owns

- `Brain.aask`
- `Brain.ask_streaming`
- `Brain.asearch`
- `ChatHistory`
- `RAGResponseMetadata`
- `ParsedRAGResponse` and `ParsedRAGChunkResponse`
- `RetrievalConfig`
- `WorkflowConfig`
- `LLMEndpointConfig`
- `RerankerConfig`
- `QuivrQARAG` and `QuivrQARAGLangGraph`
- web-search routing and cited-answer behavior

## What this sub-skill does not own

- document ingestion, chunking, or storage lifecycle -> `../brain-ingestion/SKILL.md`
- optional parser stacks such as unstructured, Tika, or MegaParse -> root references only
- non-Quivr repository maintenance -> outside this skill

## Practical rule

Always supply a `run_id` and prefer the async-safe API (`Brain.aask(...)` or
`Brain.ask_streaming(...)`). Reserve `Brain.ask(...)` for a plain synchronous
script that is not already inside a running event loop.
