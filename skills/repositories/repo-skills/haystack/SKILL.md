---
name: haystack
description: "Use Haystack to build, debug, evaluate, and maintain RAG, agent,
  pipeline, component, ingestion, retrieval, generator, tool-calling, and
  observability workflows for the haystack-ai package and repository."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Haystack

Use this skill when the task names Haystack, `haystack-ai`, `Pipeline`, `AsyncPipeline`, `Document`, Haystack components, document stores, retrievers, rankers, agents, tools, generators, embedders, evaluators, tracing, or repository development in this checkout.

## Route By Task

- **Pipeline mechanics and custom components**: use `sub-skills/pipelines-and-components/SKILL.md` for `Pipeline`, `AsyncPipeline`, `@component`, socket wiring, loop limits, serialization, breakpoints, snapshots, and `SuperComponent`.
- **Data ingestion and conversion**: use `sub-skills/data-ingestion/SKILL.md` for `Document`, `ByteStream`, file converters, cleaners, splitters, preprocessors, file/document/metadata routers, and fetch/cache checks.
- **Retrieval and RAG**: use `sub-skills/retrieval-and-rag/SKILL.md` for document stores, writers, BM25/embedding retrievers, metadata filters, rankers, joiners, readers, and local RAG skeletons.
- **Model-facing components**: use `sub-skills/generation-and-model-components/SKILL.md` for prompt builders, chat/text generators, embedders, classifiers, samplers, validators, provider credentials, and optional local/API model backends.
- **Agents, tools, and HITL**: use `sub-skills/agents-tools-and-hitl/SKILL.md` for `Agent`, `Tool`, `Toolset`, `ComponentTool`, `PipelineTool`, `ToolInvoker`, MCP/OpenAPI connectors, state, breakpoints, and human confirmation.
- **Evaluation and observability**: use `sub-skills/evaluation-and-observability/SKILL.md` for retrieval/answer evaluators, `EvaluationRunResult`, tracing, logging, telemetry, and pipeline debug outputs.
- **Repository development**: use `sub-skills/repo-development/SKILL.md` when modifying this Haystack checkout, selecting Hatch tests, formatting, type checks, release notes, or docs checks.

## Fast Start

1. Check the execution context. For package-user workflows, any Python environment with `haystack-ai` is enough for local smoke checks. For repository development inside the checkout, follow `AGENTS.md` and use Hatch.
2. Start with the workflow-owning sub-skill, then follow cross-links for adjacent concerns such as ingestion -> retrieval -> generation -> evaluation.
3. Keep provider credentials and model downloads explicit. Many generator, embedder, reader, and LLM evaluator components require optional dependencies or API keys.
4. For local validation, prefer in-memory stores, tiny `Document` lists, mocked or placeholder generators, and bundled smoke scripts before adding network or GPU dependencies.

## References

- `references/component-selection.md` maps common goals to sub-skills and component families.
- `references/troubleshooting.md` covers cross-cutting install/import, optional dependency, credential, pipeline, telemetry, and repository failures.
- `references/repo-provenance.md` records the source revision and extraction evidence.
- `scripts/haystack_smoke_check.py` validates basic public imports and a tiny custom component pipeline.

## Avoid

- Do not use repository Hatch commands for ordinary package-user examples unless the user is editing the checkout.
- Do not assume optional integrations are installed. Name the extra dependency or provider credential before recommending code that requires it.
- Do not route generic vector database, LangChain, LlamaIndex, or OpenAI-client tasks here unless Haystack is the orchestrating framework.
